"""
api/social.py
Approval flow endpoints: approve, reject, get states, and ignore drafts.
"""
import uuid
import datetime
import json

from fastapi import APIRouter, HTTPException

import backend.core.dependencies as deps
from backend.core.dependencies import data_controller
from backend.core.config import TELEGRAM_BOT_TOKEN
from backend.models.schemas import SocialApprovalRequest, SocialRejectRequest, SocialConflictResponseRequest
from pydantic import BaseModel
from backend.services.social_service import generate_social_draft
from backend.services.calendar_service import check_event_conflict, build_master_calendar

router = APIRouter()


@router.post("/api/social/approve")
async def approve_social_event(request: SocialApprovalRequest):
    """
    UI Popup approval endpoint.
    Executes the dual-action: Send Telegram message and inject Calendar event.
    """
    # 1. Send the message via Telegram API
    try:
        if (
            deps.ptb_application
            and deps.ptb_application.bot
            and TELEGRAM_BOT_TOKEN != "MOCK_TOKEN"
        ):
            await deps.ptb_application.bot.send_message(
                chat_id=request.chat_id, text=request.approved_message
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send Telegram message: {e}"
        )

    # 0. HARD GUARD — Conflict check BEFORE any side effects.
    # This is the backend source of truth. Even if the frontend is stale or bypassed,
    # this prevents any double-booking from being committed to the database or Telegram.
    conflict_type, reason = check_event_conflict(request.event_start, request.event_end)
    if conflict_type == "hard":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve event: Calendar conflict detected. {reason}"
        )
    
    displaced_event_title = None
    if conflict_type == "soft" and "Conflicts with flexible event: " in reason:
        displaced_event_title = reason.split("Conflicts with flexible event: ")[1].strip()

    # Fetch state to preserve metadata
    state = data_controller.read_json("conversation_states.json", default_val={})
    event_state = {}
    if request.chat_id in state:
        event_state = state[request.chat_id].get("event_state", {})

    # Update approved_social_events.json for quota tracking
    social_log = data_controller.read_json(
        "approved_social_events.json", default_val={"events": []}
    )
    
    # Check for duplicates before appending
    is_duplicate = any(
        str(ev.get("chat_id")) == str(request.chat_id) and 
        ev.get("event_start") == request.event_start
        for ev in social_log.get("events", [])
    )
    
    if not is_duplicate:
        social_log["events"].append(
            {
                "event_title": request.event_title,
                "event_start": request.event_start,
                "event_end": request.event_end,
                "who": event_state.get("who"),
                "what": event_state.get("what"),
                "where": event_state.get("where"),
                "chat_id": request.chat_id,
            }
        )
        data_controller.write_json("approved_social_events.json", social_log)

    # 3. Cleanup conversation state
    if request.chat_id in state:
        state.pop(request.chat_id)
        data_controller.write_json("conversation_states.json", state)

    # Update message history — promote agent_draft → agent
    history = data_controller.read_json("message_history.json", default_val={})
    chat_history = history.get(str(request.chat_id), [])
    if chat_history and chat_history[-1].get("sender") == "agent_draft":
        chat_history[-1]["text"] = request.approved_message
        chat_history[-1]["sender"] = "agent"
        chat_history[-1]["pending_approval"] = False
        
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        chat_history.append({
            "message_id": f"sys-{now}",
            "sender": "system",
            "name": "System",
            "text": "--- EVENT FINALIZED ---",
            "timestamp": now
        })
        history[str(request.chat_id)] = chat_history
        data_controller.write_json("message_history.json", history)

    # Rebuild Master Calendar
    new_calendar = await build_master_calendar()

    detail_message = "Event approved, message sent, and calendar updated."

    # Gap-Scan Verification Payload
    if displaced_event_title:
        try:
            import pytz
            user_goals = data_controller.read_json("user_goals.json", default_val={})
            tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
            local_tz = pytz.timezone(tz_name)
            
            target_date = datetime.datetime.fromisoformat(request.event_start.replace("Z", "+00:00")).astimezone(local_tz).date()
            for ev in new_calendar:
                if ev.get("title") == displaced_event_title:
                    ev_date = datetime.datetime.fromisoformat(ev["start"].replace("Z", "+00:00")).astimezone(local_tz).date()
                    if ev_date == target_date:
                        new_time_local = datetime.datetime.fromisoformat(ev["start"].replace("Z", "+00:00")).astimezone(local_tz)
                        new_time = new_time_local.strftime("%I:%M %p").lstrip("0")
                        detail_message = f"Social event approved. {displaced_event_title} successfully moved to {new_time}."
                        print(f"[Verification] {detail_message}")
                        break
        except Exception as e:
            print(f"Error extracting gap-scan result: {e}")

    return {
        "status": "success",
        "detail": detail_message,
        "message": detail_message,
    }


@router.post("/api/social/reject")
async def reject_social_event(request: SocialRejectRequest):
    state = data_controller.read_json("conversation_states.json", default_val={})
    if request.chat_id not in state:
        raise HTTPException(status_code=404, detail="Conversation state not found")

    current_state = state[request.chat_id].get("event_state", {})
    interests = data_controller.read_json("interests.json", default_val={})

    prompt = "The user (you) has rejected the current proposal. "
    if request.reason:
        prompt += f"The reason is: '{request.reason}'. Suggest an alternative that respects this reason."
    else:
        prompt += f"Proactively suggest a completely different activity based on the user's interests: {json.dumps(interests)}."

    new_draft_dict = await generate_social_draft(request.chat_id, prompt, current_state)
    new_draft = new_draft_dict.get("draft", "")
    updated_state = new_draft_dict.get("updated_state", current_state)

    # Strictly enforce negotiating
    updated_state["status"] = "negotiating"

    state[request.chat_id] = {
        "status": "negotiating",
        "draft": new_draft,
        "event_state": updated_state,
        "original_message": "",
        "conflict": None,
        "proposed_time": None,
    }
    data_controller.write_json("conversation_states.json", state)

    # Automatically send the new draft via Telegram
    try:
        if (
            deps.ptb_application
            and deps.ptb_application.bot
            and TELEGRAM_BOT_TOKEN != "MOCK_TOKEN"
        ):
            message_obj = await deps.ptb_application.bot.send_message(
                chat_id=request.chat_id, text=new_draft
            )
            message_id = str(message_obj.message_id)
        else:
            message_id = str(uuid.uuid4())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send Telegram message: {e}"
        )

    # Log to message history
    history = data_controller.read_json("message_history.json", default_val={})
    chat_history = history.get(request.chat_id, [])

    # Remove the pending draft so it doesn't appear as a sent message
    if chat_history and chat_history[-1].get("sender") == "agent_draft":
        chat_history.pop()

    chat_history.append(
        {
            "message_id": message_id,
            "sender": "agent",
            "name": "Social Butterfly",
            "text": new_draft,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pending_approval": False,
        }
    )
    history[request.chat_id] = chat_history
    data_controller.write_json("message_history.json", history)

    return {"status": "success", "message": "Rejection sent and state reverted."}

@router.post("/api/social/send_conflict_response")
async def send_conflict_response(request: SocialConflictResponseRequest):
    """
    Sends the conflict-apology message to the friend via Telegram WITHOUT creating a
    calendar event. Resets the conversation state back to 'negotiating' with date and
    time cleared so the two parties can propose a new time.
    """
    # Send the apology message via Telegram
    try:
        if (
            deps.ptb_application
            and deps.ptb_application.bot
            and TELEGRAM_BOT_TOKEN != "MOCK_TOKEN"
        ):
            msg_obj = await deps.ptb_application.bot.send_message(
                chat_id=request.chat_id, text=request.approved_message
            )
            message_id = str(msg_obj.message_id)
        else:
            message_id = str(uuid.uuid4())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send Telegram message: {e}")

    # Reset conversation to negotiating — keep who/what/where but clear date/time/proposed_time
    state = data_controller.read_json("conversation_states.json", default_val={})
    current = state.get(request.chat_id, {})
    event_state = current.get("event_state", {})
    event_state["date"] = None
    event_state["time"] = None
    event_state["status"] = "negotiating"

    state[request.chat_id] = {
        "status": "negotiating",
        "draft": request.approved_message,
        "event_state": event_state,
        "original_message": current.get("original_message", ""),
        "conflict": None,
        "proposed_time": None,
    }
    data_controller.write_json("conversation_states.json", state)

    # Update message history — promote the draft to a sent agent message
    history = data_controller.read_json("message_history.json", default_val={})
    chat_history = history.get(str(request.chat_id), [])
    if chat_history and chat_history[-1].get("sender") == "agent_draft":
        chat_history[-1]["text"] = request.approved_message
        chat_history[-1]["sender"] = "agent"
        chat_history[-1]["pending_approval"] = False
        history[str(request.chat_id)] = chat_history
        data_controller.write_json("message_history.json", history)

    return {
        "status": "success",
        "message": "Conflict response sent. No event created. Conversation reset to negotiating.",
    }


@router.get("/api/social/states")
async def get_social_states():
    """Returns conversation states to power the Approval Modal trigger."""
    return data_controller.read_json("conversation_states.json", default_val={})


@router.post("/api/ignore/{contact_id}")
async def ignore_social_draft(contact_id: str):
    """Kills the zombie notification by popping it from conversation states."""
    state = data_controller.read_json("conversation_states.json", default_val={})
    if contact_id in state:
        state.pop(contact_id)
        data_controller.write_json("conversation_states.json", state)
    return {"status": "success", "message": "Draft ignored and state cleared."}


class ProposeNewTimeRequest(BaseModel):
    chat_id: str
    new_start: str
    new_end: str

@router.post("/api/social/propose")
async def propose_new_time(request: ProposeNewTimeRequest):
    """Handles manual renegotiation from the frontend Date/Time picker."""
    state = data_controller.read_json("conversation_states.json", default_val={})
    if request.chat_id not in state:
        raise HTTPException(status_code=404, detail="Conversation state not found")

    current_state = state[request.chat_id].get("event_state", {})

    # Generate a draft proposing the new time
    try:
        import dateparser
        import pytz
        user_goals = data_controller.read_json("user_goals.json")
        tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
        tz = pytz.timezone(tz_name)
        new_start_dt = datetime.datetime.fromisoformat(request.new_start.replace("Z", "+00:00")).astimezone(tz)
        formatted_time = new_start_dt.strftime("%A, %b %d at %I:%M %p")
    except Exception:
        formatted_time = request.new_start

    prompt = f"The user had a schedule conflict with the originally proposed time. They have manually selected a new time: {formatted_time}. Draft a short, warm message proposing this new time to the friend."
    
    new_draft_dict = await generate_social_draft(request.chat_id, prompt, current_state)
    new_draft = new_draft_dict.get("draft", f"I actually have a conflict at that time. Could we do {formatted_time} instead?")
    updated_state = new_draft_dict.get("updated_state", current_state)

    updated_state["status"] = "negotiating"

    state[request.chat_id] = {
        "status": "negotiating",
        "draft": new_draft,
        "event_state": updated_state,
        "original_message": state[request.chat_id].get("original_message", ""),
        "conflict": None,
        "proposed_time": {
            "start": request.new_start,
            "end": request.new_end
        },
    }
    data_controller.write_json("conversation_states.json", state)

    # Automatically send the new draft via Telegram
    try:
        if (
            deps.ptb_application
            and deps.ptb_application.bot
            and TELEGRAM_BOT_TOKEN != "MOCK_TOKEN"
        ):
            message_obj = await deps.ptb_application.bot.send_message(
                chat_id=request.chat_id, text=new_draft
            )
            message_id = str(message_obj.message_id)
        else:
            message_id = str(uuid.uuid4())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send Telegram message: {e}"
        )

    # Log to message history
    history = data_controller.read_json("message_history.json", default_val={})
    chat_history = history.get(request.chat_id, [])

    if chat_history and chat_history[-1].get("sender") == "agent_draft":
        chat_history.pop()

    chat_history.append(
        {
            "message_id": message_id,
            "sender": "agent",
            "name": "Social Butterfly",
            "text": new_draft,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "pending_approval": False,
        }
    )
    history[request.chat_id] = chat_history
    data_controller.write_json("message_history.json", history)

    return {"status": "success", "message": "New time proposed and state reverted to negotiating."}

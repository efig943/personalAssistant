"""
telegram/handler.py
PTB MessageHandler callback: receives incoming Telegram messages and orchestrates
the full Social Butterfly negotiation pipeline.
"""
import uuid
import datetime
import dateparser

from telegram import Update
from telegram.ext import ContextTypes

import backend.core.dependencies as deps
from backend.core.dependencies import data_controller
from backend.core.config import TELEGRAM_BOT_TOKEN
from backend.services.social_service import generate_social_draft
from backend.services.time_service import extract_proposed_time
from backend.services.calendar_service import check_event_conflict


async def telegram_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming Telegram messages and updates history and conversation states."""
    user_text = update.message.text
    chat_id = update.effective_chat.id
    sender_name = update.effective_chat.first_name or "Friend"
    username = update.effective_chat.username

    # ── 1. Whitelist resolution ───────────────────────────────────────────────
    contacts_data = data_controller.read_json(
        "contacts_registry.json", default_val={"contacts": []}
    )
    contacts = contacts_data.get("contacts", [])

    whitelisted_contact = None

    # Priority 1: Check if this chat_id is already bound to a contact
    for c in contacts:
        if str(c.get("chat_id")) == str(chat_id):
            whitelisted_contact = c
            break

    # Priority 2: If not bound, try to find by username (The Handshake)
    if not whitelisted_contact and username:
        for c in contacts:
            if (
                str(c.get("username")).replace("@", "").lower()
                == str(username).replace("@", "").lower()
            ):
                whitelisted_contact = c
                # AUTO-LINK: Bind the chat_id now that we know who it is!
                whitelisted_contact["chat_id"] = chat_id
                data_controller.write_json("contacts_registry.json", contacts_data)
                print(f"Auto-linked {sender_name} (ID: {chat_id}) to username {username}")
                break

    # Cache all incoming users regardless of whitelist status
    if username:
        user_cache = data_controller.read_json(
            "telegram_user_cache.json", default_val={}
        )
        user_cache[str(username).replace("@", "").lower()] = chat_id
        data_controller.write_json("telegram_user_cache.json", user_cache)

    if not whitelisted_contact:
        print(f"Ignored message from unknown: {sender_name} (@{username})")
        return

    # Update last contact time
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    whitelisted_contact["last_contact_time"] = now_str
    data_controller.write_json("contacts_registry.json", contacts_data)

    # ── 2. Update message_history.json ───────────────────────────────────────
    history = data_controller.read_json("message_history.json", default_val={})
    chat_history = history.get(str(chat_id), [])
    chat_history.append(
        {
            "message_id": str(uuid.uuid4()),
            "sender": "contact",
            "name": sender_name,
            "text": user_text,
            "timestamp": now_str,
        }
    )
    history[str(chat_id)] = chat_history
    data_controller.write_json("message_history.json", history)

    # ── 3. Check for proposed time in message text ────────────────────────────
    # First load current state so we can guard conflict checks
    state_pre = data_controller.read_json("conversation_states.json", default_val={})
    current_state_pre = state_pre.get(str(chat_id), {})
    current_event_state_pre = current_state_pre.get("event_state", {})

    proposed_time_info = await extract_proposed_time(user_text)

    conflict_reason = ""
    if proposed_time_info:
        start_iso = proposed_time_info.get("start")
        end_iso = proposed_time_info.get("end")
        already_has_date = bool(current_event_state_pre.get("date"))
        already_has_time = bool(current_event_state_pre.get("time"))
        if start_iso and end_iso and already_has_date and already_has_time:
            conflict_type, reason = check_event_conflict(start_iso, end_iso)
            if conflict_type == "hard":
                conflict_reason = reason

    # ── 3.5 Fetch current EventState ─────────────────────────────────────────
    state = data_controller.read_json("conversation_states.json", default_val={})
    current_chat_state = state.get(str(chat_id), {})
    current_event_state = current_chat_state.get(
        "event_state",
        {
            "who": sender_name,
            "what": None,
            "where": None,
            "date": None,
            "time": None,
            "status": "negotiating",
        },
    )

    if not current_event_state.get("who"):
        current_event_state["who"] = sender_name

    # Context injection: recent chat history (up to 3 previous messages)
    recent_history_context = []
    # Extract up to 3 messages prior to the current user message
    for msg in chat_history[-4:-1]:
        sender = "You" if msg.get("sender") in ["agent", "agent_draft"] else "User"
        recent_history_context.append(f"{sender}: '{msg.get('text')}'")
    
    if recent_history_context:
        history_str = " | ".join(recent_history_context)
        user_reply_context = f"Recent History: {history_str} | User's Current Reply: '{user_text}'."
    else:
        user_reply_context = f"User's Current Reply: '{user_text}'."

    # ── 4. Draft response using Groq ──────────────────────────────────────────
    if conflict_reason:
        prompt = (
            f"Friend ({sender_name}) proposed a plan in response. "
            f"However, there is a scheduling conflict: {conflict_reason}. "
            "Draft a warm reply stating that you have a conflict at that time, "
            f"and asking to reschedule or propose a different time.\nContext: {user_reply_context}"
        )
    else:
        prompt = (
            f"Friend ({sender_name}) replied. Draft a reply following the Social Butterfly rules.\n"
            f"Context: {user_reply_context}"
        )

    draft_data = await generate_social_draft(str(chat_id), prompt, current_event_state)

    # Deep merge to prevent the LLM from dropping previously negotiated fields
    llm_state = draft_data.get("updated_state", {})
    updated_state = current_event_state.copy()
    if isinstance(llm_state, dict):
        for k, v in llm_state.items():
            if v is not None and str(v).strip() != "" and str(v).strip().lower() != "null":
                updated_state[k] = v

    draft_text = draft_data.get("draft", "I'm not sure how to respond.")

    # If the AI forgot to set pending_approval when everything is filled
    if (
        not conflict_reason
        and updated_state.get("who")
        and updated_state.get("what")
        and updated_state.get("where")
        and updated_state.get("date")
        and updated_state.get("time")
    ):
        if updated_state.get("status") == "negotiating":
            updated_state["status"] = "pending_approval"
            # The LLM may have output a question rather than a confirmation because
            # it didn't know the state was fully accumulated. Synthesize a proper
            # confirmation message so the approval modal always shows a sensible draft.
            if not any(phrase in draft_text.lower() for phrase in ["see you", "send this", "boss for approval", "locked in", "confirmed", "it's a date"]):
                who = updated_state.get("who", "")
                what = updated_state.get("what", "")
                where = updated_state.get("where", "")
                date = updated_state.get("date", "")
                time_val = updated_state.get("time", "")
                draft_text = f"Sounds like a plan! See you {date} at {time_val} for {what} at {where}. Can't wait! 🎉"

    # ── PROGRAMMATIC FAILSAFE ──────────────────────────────────────────────────
    # If the LLM successfully negotiated a complete time, we must double-check it before 
    # we send it to the UI / user. If the LLM hallucinated or bypassed the tool, 
    # this catches the Hard Collision and forces a renegotiation.
    date_str = updated_state.get("date")
    time_str = updated_state.get("time")
    
    date_changed = date_str != current_event_state.get("date")
    time_changed = time_str != current_event_state.get("time")
    status_changed_to_pending = (updated_state.get("status") == "pending_approval" and current_event_state.get("status") != "pending_approval")
    
    should_run_failsafe = (date_changed or time_changed or status_changed_to_pending) and (date_str and time_str)
    
    proposed_time_info_override = None
    if should_run_failsafe and not conflict_reason:
            proposed_time_info_override = await extract_proposed_time(f"{time_str} on {date_str}")
            if proposed_time_info_override:
                st_iso = proposed_time_info_override.get("start")
                en_iso = proposed_time_info_override.get("end")
                if st_iso and en_iso:
                    ctype, c_reason = check_event_conflict(st_iso, en_iso)
                    if ctype == "hard":
                        # We caught a hallucination! Override the LLM.
                        print(f"[FAILSAFE] Caught hallucinated conflict: {c_reason}. Forcing renegotiation.")
                        override_prompt = (
                            f"SYSTEM OVERRIDE: The time you just agreed to ({time_str} on {date_str}) has a Hard Collision "
                            f"on the user's calendar: {c_reason}. Generate a new message apologizing to {sender_name}, "
                            "stating you double-checked your calendar and are actually busy, and propose a new time. "
                            "DO NOT agree to the current time."
                        )
                        # Clear invalid time BEFORE generating override
                        current_event_state["date"] = None
                        current_event_state["time"] = None
                        
                        # Re-run LLM
                        override_data = await generate_social_draft(str(chat_id), override_prompt, current_event_state)
                        updated_state = override_data.get("updated_state", updated_state)
                        updated_state["status"] = "negotiating" # Force regression
                        draft_text = override_data.get("draft", "Actually, wait, I double-checked and I'm busy then. How about another time?")
                        conflict_reason = c_reason

            else:
                print(f"[FAILSAFE] Extraction failed for {time_str} on {date_str}. Forcing renegotiation.")
                override_prompt = (
                    f"SYSTEM OVERRIDE: The time you just agreed to ({time_str} on {date_str}) could not be securely parsed. "
                    f"Generate a new message apologizing to {sender_name}, stating you got confused about the time, "
                    "and ask them to explicitly clarify the date and time. "
                    "DO NOT agree to the current time."
                )
                current_event_state["date"] = None
                current_event_state["time"] = None
                
                # Re-run LLM
                override_data = await generate_social_draft(str(chat_id), override_prompt, current_event_state)
                updated_state = override_data.get("updated_state", updated_state)
                updated_state["status"] = "negotiating" # Force regression
                draft_text = override_data.get("draft", "Sorry, I got a bit confused. What exact date and time were you thinking again?")
                conflict_reason = "Parsing failed."

    # Force push to pending_approval so the modal opens when all fields are resolved,
    # regardless of whether the LLM explicitly remembered to set the status string.
    if (
        updated_state.get("who")
        and updated_state.get("what")
        and updated_state.get("where")
        and updated_state.get("date")
        and updated_state.get("time")
    ):
        updated_state["status"] = "pending_approval"

    is_resolved = updated_state.get("status") == "pending_approval"

    # Log agent draft to history
    agent_message_id = str(uuid.uuid4())
    chat_history.append(
        {
            "message_id": agent_message_id,
            "sender": "agent_draft",
            "name": "Social Butterfly",
            "text": draft_text,
            "timestamp": now_str,
            "pending_approval": is_resolved,
        }
    )
    history[str(chat_id)] = chat_history
    data_controller.write_json("message_history.json", history)

    # Resolve final proposed_time
    if conflict_reason:
        final_time = None
    elif proposed_time_info_override:
        final_time = proposed_time_info_override
    elif proposed_time_info:
        final_time = proposed_time_info
    else:
        final_time = current_chat_state.get("proposed_time")

    # If state is pending_approval and we have date+time, parse a concrete ISO time
    if (
        updated_state.get("status") == "pending_approval"
        and updated_state.get("date")
        and updated_state.get("time")
        and not final_time
    ):
        try:
            import pytz

            user_goals = data_controller.read_json("user_goals.json")
            tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
            tz = pytz.timezone(tz_name)
            now_local = datetime.datetime.now(tz)
            dt_str = f"{updated_state['date']} {updated_state['time']}"
            dt_obj = dateparser.parse(
                dt_str,
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": now_local,
                    "TIMEZONE": tz_name,
                },
            )
            if dt_obj:
                if not dt_obj.tzinfo:
                    dt_obj = tz.localize(dt_obj)
                if final_time is None:
                    final_time = {}
                final_time["start"] = dt_obj.astimezone(
                    datetime.timezone.utc
                ).isoformat()
                final_time["end"] = (
                    dt_obj + datetime.timedelta(hours=1)
                ).astimezone(datetime.timezone.utc).isoformat()
        except Exception as e:
            print(f"Error parsing combined date/time: {e}")

    # ── 5. Save updated state ─────────────────────────────────────────────────
    state[str(chat_id)] = {
        "status": updated_state.get("status", "negotiating"),
        "draft": draft_text,
        "event_state": updated_state,
        "original_message": user_text,
        "conflict": conflict_reason if conflict_reason else None,
        "proposed_time": final_time,
    }
    data_controller.write_json("conversation_states.json", state)

    # ── 6. Auto-send if still negotiating ────────────────────────────────────
    if not is_resolved:
        if (
            deps.ptb_application
            and deps.ptb_application.bot
            and TELEGRAM_BOT_TOKEN != "MOCK_TOKEN"
        ):
            try:
                await deps.ptb_application.bot.send_message(
                    chat_id=chat_id, text=draft_text
                )
                # Promote draft → sent in history
                chat_history[-1]["sender"] = "agent"
                chat_history[-1]["pending_approval"] = False
                history[str(chat_id)] = chat_history
                data_controller.write_json("message_history.json", history)
            except Exception as e:
                print(f"Failed to auto-send message: {e}")

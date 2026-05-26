"""
tools/agent_tools.py
Concrete Python implementations of the Groq tool-call functions.
These are dispatched by social_service.py after the LLM requests a tool call.
"""
import datetime
import pytz

from backend.core.dependencies import data_controller
from backend.services.calendar_service import build_master_calendar, check_event_conflict
from backend.services.time_service import extract_proposed_time


async def execute_remove_event_tool(
    chat_id: str,
    reason: str = ""
) -> str:
    """Removes a social event from the calendar if the caller is the owner."""
    print(
        f"DEBUG: execute_remove_event_tool called with chat_id={chat_id}"
    )

    # ── Priority 1: Check for an in-flight pending negotiation ───────────────
    # If the contact cancels BEFORE the user has clicked "Approve" in the UI,
    # the event only exists in conversation_states.json (never written to
    # approved_social_events.json). We must clear THAT state, not mistakenly
    # remove an old stale approved event from a prior session.
    conv_states = data_controller.read_json("conversation_states.json", default_val={})
    active_state = conv_states.get(str(chat_id), {})
    event_state = active_state.get("event_state", {})
    has_pending_negotiation = any(
        event_state.get(k) for k in ["what", "date", "time"]
    )

    if has_pending_negotiation:
        what = event_state.get("what") or "plan"
        del conv_states[str(chat_id)]
        data_controller.write_json("conversation_states.json", conv_states)
        print(f"[REMOVE] Cleared pending (unapproved) negotiation for chat_id={chat_id}: {what}")
        return f"Successfully cancelled the pending plan to {what} with this contact."

    # ── Priority 2: Remove an already-approved event from the calendar ───────
    social_log = data_controller.read_json(
        "approved_social_events.json", default_val={"events": []}
    )
    events = social_log.get("events", [])
    removed = False

    # Since the LLM often hallucinates the target_date or event_title,
    # the most robust way to find the event is to match the chat_id for the most recently scheduled event.
    for i in range(len(events) - 1, -1, -1):
        if str(events[i].get("chat_id")) == str(chat_id):
            removed_title = events[i].get("event_title", "Event")
            events.pop(i)
            removed = True
            break

    if removed:
        data_controller.write_json("approved_social_events.json", social_log)
        await build_master_calendar()
        return f"Successfully removed the upcoming event with this contact."
    else:
        return f"Could not find any scheduled event with this contact."


async def execute_calendar_tool(target_date: str) -> str:
    """Fetches free/busy blocks for a specific date from the compiled Master Calendar."""
    compiled_data = data_controller.read_json(
        "compiled_master_calendar.json", default_val={"events": []}
    )
    master_events = compiled_data.get("events", [])
    user_goals = data_controller.read_json("user_goals.json")
    tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
    tz = pytz.timezone(tz_name)

    try:
        target_dt = datetime.datetime.strptime(target_date, "%Y-%m-%d").replace(
            tzinfo=tz
        )
    except Exception:
        return f"Error: Invalid target_date format '{target_date}'. Expected YYYY-MM-DD."

    start_of_day = target_dt
    end_of_day = target_dt + datetime.timedelta(days=1)

    day_events = []
    for ev in master_events:
        try:
            ev_start = datetime.datetime.fromisoformat(
                ev["start"].replace("Z", "+00:00")
            ).astimezone(tz)
            ev_end = datetime.datetime.fromisoformat(
                ev["end"].replace("Z", "+00:00")
            ).astimezone(tz)
            if max(start_of_day, ev_start) < min(end_of_day, ev_end):
                day_events.append(
                    (ev_start, ev_end, ev.get("title", "Event"), ev.get("type", "work"))
                )
        except Exception:
            pass

    if not day_events:
        return f"No events scheduled for {target_date}. The entire day is free."

    day_events.sort(key=lambda x: x[0])
    lines = [f"Busy blocks for {target_date} ({tz_name} timezone):"]
    for s, e, title, type_ in day_events:
        lines.append(
            f"- {s.strftime('%H:%M')} to {e.strftime('%H:%M')} ({type_.capitalize()}: {title})"
        )

    lines.append("\nNote: Any time not listed above is FREE and available to schedule.")
    lines.append("CRITICAL INSTRUCTION: If the contact only proposed a day (e.g., 'Saturday') and did NOT propose a specific time, DO NOT say you have a conflict. Instead, pick a specific time from the FREE periods and propose it to the contact.")
    return "\n".join(lines)


async def check_specific_time_availability(proposed_time_phrase: str) -> str:
    """
    Evaluates a specific time phrase (e.g., 'Tuesday at 2pm') against the Master Calendar
    and returns whether it is a Hard Conflict, Soft Conflict, or Clear.
    """
    print(f"DEBUG: check_specific_time_availability called for '{proposed_time_phrase}'")
    try:
        proposed_time_info = await extract_proposed_time(proposed_time_phrase)
        if not proposed_time_info:
            return "Error: Could not parse the proposed time. Please ask the user to clarify."
        
        st_iso = proposed_time_info.get("start")
        en_iso = proposed_time_info.get("end")
        
        if not st_iso or not en_iso:
            return "Error: Incomplete time extraction."

        ctype, c_reason = check_event_conflict(st_iso, en_iso)
        
        # Bug 3 Fix: Reject past dates before any conflict check.
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        proposed_start_dt = datetime.datetime.fromisoformat(st_iso.replace("Z", "+00:00"))
        if proposed_start_dt < now_utc:
            return (
                "Error: Proposed time is in the past. "
                "Tell the contact you can only schedule future events and ask them to suggest a future date."
            )
        
        if ctype == "hard":
            return f"Hard Conflict (Anchor Event): {c_reason}. You MUST politely decline this time and suggest a different time."
        elif ctype == "soft":
            return f"Soft Conflict (Flexible): {c_reason}. You may agree to this time, as the flexible event can be moved."
        else:
            return "Clear. The schedule is free. You may agree to this time."

    except Exception as e:
        print(f"Error in check_specific_time_availability: {e}")
        return f"Error checking calendar: {e}"

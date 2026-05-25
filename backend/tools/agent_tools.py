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
    social_log = data_controller.read_json(
        "approved_social_events.json", default_val={"events": []}
    )
    events = social_log.get("events", [])
    removed = False

    # Since the LLM often hallucinates the target_date (e.g. 'tomorrow') or event_title ('getting some boba'),
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
        
        if ctype == "hard":
            return f"Hard Conflict (Anchor Event): {c_reason}. You MUST politely decline this time and suggest a different time."
        elif ctype == "soft":
            return f"Soft Conflict (Flexible): {c_reason}. You may agree to this time, as the flexible event can be moved."
        else:
            return "Clear. The schedule is free. You may agree to this time."

    except Exception as e:
        print(f"Error in check_specific_time_availability: {e}")
        return f"Error checking calendar: {e}"

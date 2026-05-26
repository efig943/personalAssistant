"""
services/calendar_service.py
Tier 1+2+3 master calendar compilation, Google Calendar OAuth, and conflict detection.
"""
import os
import datetime
import pytz

from backend.core.dependencies import data_controller
from backend.core.config import GOOGLE_CALENDAR_WORK_ID


def get_calendar_service():
    """Builds and returns the Google Calendar API service using token.json."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    token_path = os.path.join(root_dir, "token.json")
    
    if not os.path.exists(token_path):
        return None
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(
            token_path, ["https://www.googleapis.com/auth/calendar"]
        )
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request

            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        return build("calendar", "v3", credentials=creds)
    except Exception as e:
        print(f"Error initializing calendar service: {e}")
        return None


async def build_master_calendar() -> list:
    """Builds and merges Tier 1 (Work), Tier 2 (Habits), and Tier 3 (Social) into a compiled view."""
    events = []

    # ── Tier 1 (Work) ────────────────────────────────────────────────────────
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    calendar_service = get_calendar_service()
    if calendar_service:
        try:
            time_min_dt = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
            time_min = time_min_dt.isoformat()
            time_max = (time_min_dt + datetime.timedelta(days=30)).isoformat()

            events_result = (
                calendar_service.events()
                .list(
                    calendarId=GOOGLE_CALENDAR_WORK_ID,
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            for item in events_result.get("items", []):
                start = item["start"].get("dateTime") or item["start"].get("date")
                end = item["end"].get("dateTime") or item["end"].get("date")
                events.append(
                    {
                        "title": item.get("summary", "Work Event"),
                        "start": start,
                        "end": end,
                        "type": "work",
                        "is_anchor": True,
                    }
                )
        except Exception as e:
            print(f"Error fetching Google Calendar events: {e}")

    # Mock fallback for Tier 1
    if not events:
        mock_cal = data_controller.read_json(
            "mock_work_calendar.json", default_val={"events": []}
        )
        for item in mock_cal.get("events", []):
            events.append(
                {
                    "title": item.get("summary", "Work Event"),
                    "start": item.get("start"),
                    "end": item.get("end"),
                    "type": "work",
                    "is_anchor": True,
                }
            )

    # ── Helper utilities ──────────────────────────────────────────────────────
    def overlaps(start1, end1, start2, end2):
        return max(start1, start2) < min(end1, end2)

    def find_gap(search_start, search_end, duration_minutes, tz):
        current = search_start
        while current + datetime.timedelta(minutes=duration_minutes) <= search_end:
            slot_end = current + datetime.timedelta(minutes=duration_minutes)
            collision = False
            for ev in events:
                try:
                    ev_start = datetime.datetime.fromisoformat(
                        ev["start"].replace("Z", "+00:00")
                    ).astimezone(tz)
                    ev_end = datetime.datetime.fromisoformat(
                        ev["end"].replace("Z", "+00:00")
                    ).astimezone(tz)
                    if overlaps(current, slot_end, ev_start, ev_end):
                        collision = True
                        break
                except Exception:
                    pass
            if not collision:
                return current, slot_end
            current += datetime.timedelta(minutes=15)
        return None, None

    # ── Tier 3 (Social) ───────────────────────────────────────────────────────
    social_events_data = data_controller.read_json(
        "approved_social_events.json", default_val={"events": []}
    )
    for ev in social_events_data.get("events", []):
        events.append(
            {
                "title": ev.get("event_title", "Social Plan"),
                "start": ev.get("event_start"),
                "end": ev.get("event_end"),
                "type": "social",
                "is_anchor": True,
                "extendedProps": {
                    "who": ev.get("who"),
                    "what": ev.get("what"),
                    "where": ev.get("where"),
                },
            }
        )

    # ── Tier 2 (Habits) ───────────────────────────────────────────────────────
    user_goals = data_controller.read_json("user_goals.json", default_val={})
    tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
    tz = pytz.timezone(tz_name)
    now = datetime.datetime.now(tz)

    for i in range(-1, 30):
        current_day = now + datetime.timedelta(days=i)
        day_str = current_day.strftime("%A")

        # Sleep
        sleep_settings = user_goals.get("sleep_settings", {})
        wake_time_str = sleep_settings.get("target_wake_time", "07:00")
        try:
            wake_h, wake_m = map(int, wake_time_str.split(":"))
        except:
            wake_h, wake_m = 7, 0
            
        sleep_duration = sleep_settings.get("required_duration_hours", 8)
        
        # Calculate the wake up time on the current day + 1 (since current day usually means the day the night starts)
        # Wait, if we are mapping days, usually "Sleep Block" spans from night to morning.
        # Let's say sleep_end is the morning of the NEXT day if current_day is the start of the night.
        # Actually, let's keep the existing semantic: it ends at target_wake_time on current_day + 1.
        sleep_end = current_day.replace(hour=wake_h, minute=wake_m, second=0, microsecond=0) + datetime.timedelta(days=1)
        sleep_start = sleep_end - datetime.timedelta(hours=sleep_duration)
        events.append(
            {
                "title": "Sleep Block",
                "start": sleep_start.isoformat(),
                "end": sleep_end.isoformat(),
                "type": "habit",
                "is_anchor": True,
            }
        )

        # Meals
        nutrition = user_goals.get("nutrition", {})
        meals_per_day = nutrition.get("meals_per_day", 4)
        time_to_eat = nutrition.get("time_to_eat", 30)
        target_hours = [8, 12, 16, 20]
        if meals_per_day != 4:
            target_hours = [
                8 + i * (12 // max(1, meals_per_day)) for i in range(meals_per_day)
            ]

        for h in target_hours[:meals_per_day]:
            target_start = current_day.replace(hour=h, minute=0, second=0, microsecond=0)
            scan_start = max(
                current_day.replace(hour=7, minute=0),
                target_start - datetime.timedelta(hours=2),
            )
            scan_end = min(
                current_day.replace(hour=22, minute=30),
                target_start + datetime.timedelta(hours=2),
            )

            start_slot, end_slot = find_gap(scan_start, scan_end, time_to_eat, tz)
            
            # Fallback 1: Scan entire waking day if no gap found within ±2 hours
            if not start_slot:
                full_scan_start = current_day.replace(hour=7, minute=0)
                full_scan_end = current_day.replace(hour=23, minute=0)
                start_slot, end_slot = find_gap(full_scan_start, full_scan_end, time_to_eat, tz)
            
            # Fallback 2: Force it at the original target time so it is NEVER skipped
            if not start_slot:
                start_slot = target_start
                end_slot = target_start + datetime.timedelta(minutes=time_to_eat)

            events.append(
                {
                    "title": "Meal",
                    "start": start_slot.isoformat(),
                    "end": end_slot.isoformat(),
                    "type": "habit",
                    "is_anchor": False,
                }
            )

        # Gym
        template = user_goals.get("weekly_template_registry", {}).get(day_str, {})
        state = template.get("training_state", "REST")

        # Step A — Skip REST days
        if state == "REST":
            continue

        # Step B — Strict Anchored sessions
        if template.get("is_anchor", False) is True:
            anchor_start = template.get("anchor_start")
            anchor_end = template.get("anchor_end")
            if anchor_start and anchor_end:
                h_s, m_s = map(int, anchor_start.split(":"))
                h_e, m_e = map(int, anchor_end.split(":"))
                ev_start = current_day.replace(
                    hour=h_s, minute=m_s, second=0, microsecond=0
                )
                ev_end = current_day.replace(
                    hour=h_e, minute=m_e, second=0, microsecond=0
                )
                events.append(
                    {
                        "title": f"{state} Session",
                        "start": ev_start.isoformat(),
                        "end": ev_end.isoformat(),
                        "type": "habit",
                        "is_anchor": True,
                    }
                )

        # Step C — Flexible sessions
        elif template.get("is_anchor", False) is False:
            duration = user_goals.get("gym_scheduling", {}).get(
                "session_duration_minutes", 45
            )
            scan_start = current_day.replace(hour=16, minute=0, second=0, microsecond=0)
            scan_end = current_day.replace(hour=22, minute=0, second=0, microsecond=0)

            start_slot, end_slot = find_gap(scan_start, scan_end, duration, tz)
            if start_slot:
                events.append(
                    {
                        "title": f"{state} Session",
                        "start": start_slot.isoformat(),
                        "end": end_slot.isoformat(),
                        "type": "habit",
                        "is_anchor": False,
                    }
                )


    # ── Sort & persist ────────────────────────────────────────────────────────
    def get_sort_key(e):
        try:
            return datetime.datetime.fromisoformat(e["start"].replace("Z", "+00:00"))
        except Exception:
            return datetime.datetime.now(datetime.timezone.utc)

    events.sort(key=get_sort_key)

    compiled_data = {
        "last_compiled": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "events": events,
    }
    data_controller.write_json("compiled_master_calendar.json", compiled_data)

    return events


def check_event_conflict(start_iso: str, end_iso: str) -> tuple[bool, str]:
    """
    Checks if the proposed event time conflicts with any anchored events
    in the compiled Master Calendar.
    Returns (has_conflict, reason).
    """
    try:
        if "T" in start_iso:
            proposed_start = datetime.datetime.fromisoformat(
                start_iso.replace("Z", "+00:00")
            )
            proposed_end = datetime.datetime.fromisoformat(
                end_iso.replace("Z", "+00:00")
            )
        else:
            proposed_start = datetime.datetime.strptime(
                start_iso, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=datetime.timezone.utc)
            proposed_end = datetime.datetime.strptime(
                end_iso, "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=datetime.timezone.utc)
    except Exception as e:
        print(f"Error parsing dates {start_iso} / {end_iso}: {e}")
        return False, ""

    compiled_data = data_controller.read_json(
        "compiled_master_calendar.json", default_val={"events": []}
    )

    soft_conflict = None

    for event in compiled_data.get("events", []):
        try:
            ev_start_str = event.get("start", "")
            ev_end_str = event.get("end", "")
            if not ev_start_str or not ev_end_str:
                continue

            ev_start = datetime.datetime.fromisoformat(
                ev_start_str.replace("Z", "+00:00")
            )
            ev_end = datetime.datetime.fromisoformat(
                ev_end_str.replace("Z", "+00:00")
            )

            overlap_start = max(proposed_start, ev_start)
            overlap_end = min(proposed_end, ev_end)

            if overlap_start < overlap_end:
                if event.get("is_anchor"):
                    # Social events (Tier 3) are now hard blocks.
                    # Tier 1 (work) or Tier 2 (habit) anchors are hard blocks.
                    return "hard", f"Time slot blocked by a fixed anchor event: {event.get('title')}"
                else:
                    # Record soft conflict but keep scanning for hard conflicts
                    soft_conflict = ("soft", f"Conflicts with flexible event: {event.get('title')}")
        except Exception as e:
            print(f"Error checking overlap for event {event.get('title')}: {e}")

    if soft_conflict:
        return soft_conflict

    return None, ""

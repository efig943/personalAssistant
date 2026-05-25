import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.main import get_calendar_service

service = get_calendar_service()
calendar_id = os.getenv("GOOGLE_CALENDAR_WORK_ID", "primary")

events_result = service.events().list(calendarId=calendar_id, singleEvents=True, maxResults=2500).execute()
events = events_result.get('items', [])
deleted = 0
for ev in events:
    desc = ev.get('description', '')
    if 'Meeting with' in desc or ev.get('summary', '') not in ['1on1 meeting', 'Architecture Review', 'Daily Standup', 'Work Lunch']:
        print(f"Deleting event: {ev.get('summary')} ({ev.get('id')}) - Desc: {desc}")
        service.events().delete(calendarId=calendar_id, eventId=ev['id']).execute()
        deleted += 1

print(f"Deleted {deleted} events.")

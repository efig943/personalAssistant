import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.main import get_calendar_service

def run_cleanup():
    service = get_calendar_service()
    if not service:
        print("Could not get calendar service.")
        return
        
    calendar_id = os.getenv("GOOGLE_CALENDAR_WORK_ID", "primary")
    print(f"Fetching events from calendar: {calendar_id}")
    
    events_result = service.events().list(calendarId=calendar_id, singleEvents=True, maxResults=2500).execute()
    events = events_result.get('items', [])
    
    deleted_count = 0
    for event in events:
        summary = event.get('summary', '').lower()
        if 'social' in summary or 'meet' in summary or summary.startswith('event'):
            print(f"Deleting event: {event.get('summary')} at {event.get('start')}")
            service.events().delete(calendarId=calendar_id, eventId=event['id']).execute()
            deleted_count += 1
            
    print(f"Cleanup complete. Deleted {deleted_count} events.")

if __name__ == '__main__':
    run_cleanup()

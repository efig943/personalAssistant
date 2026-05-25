import asyncio
import datetime
import dateparser
import pytz
import sys
import json
import os

from backend.main import extract_proposed_time, check_event_conflict, data_controller

async def test_1():
    print("Running Test 1: Dateparser Localization / Extraction")
    # Base time: Saturday, May 23, 2026, 19:30:00 America/Los_Angeles
    # We will mock datetime.datetime.now inside extract_proposed_time by changing the global or patching
    # But wait, we can't easily patch datetime in python without mock.
    # Actually we can patch user_goals or just pass the text.
    
    # We'll call extract_proposed_time("Monday at 8 PM").
    # For a robust test, we can mock datetime
    import builtins
    
    res = await extract_proposed_time("Monday at 8 PM")
    print(f"Extract result: {res}")
    
    # Check if the output equates to 2026-05-25 20:00:00
    if not res:
        raise Exception("extract_proposed_time returned None")
    
    start_iso = res.get("start")
    start_dt = datetime.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    # The timezone returned by Groq might be UTC. Let's convert to LA time to check local day
    la_tz = pytz.timezone("America/Los_Angeles")
    local_start = start_dt.astimezone(la_tz)
    
    date_str = local_start.strftime("%Y-%m-%d")
    time_str = local_start.strftime("%H:%M:%S")
    
    print(f"Local parsed: {date_str} {time_str}")
    assert date_str == "2026-05-25", f"Date drifted! Expected 2026-05-25, got {date_str}"
    assert time_str == "20:00:00", f"Time drifted! Expected 20:00:00, got {time_str}"
    print("Test 1 Passed\n")

def test_2():
    print("Running Test 2: The State Merge (String to ISO)")
    date_str = "2026-05-25"
    time_str = "8:00 PM"
    
    tz = pytz.timezone("America/Los_Angeles")
    dt_str = f"{date_str} {time_str}"
    
    dt_obj = dateparser.parse(dt_str)
    if dt_obj:
        if not dt_obj.tzinfo:
            dt_obj = tz.localize(dt_obj)
        utc_str = dt_obj.astimezone(datetime.timezone.utc).isoformat()
        print(f"UTC string generated: {utc_str}")
        
        # We expect "2026-05-26T03:00:00+00:00" or "Z"
        assert utc_str in ["2026-05-26T03:00:00+00:00", "2026-05-26T03:00:00Z"], f"Merge failed! Got {utc_str}"
    else:
        raise Exception("dateparser returned None")
    print("Test 2 Passed\n")

def test_3():
    print("Running Test 3: Anchor Conflict Checking")
    start_iso = "2026-05-26T03:00:00Z"
    end_iso = "2026-05-26T04:00:00Z"
    
    mock_events = {
        "last_compiled": "test",
        "events": [
            {
                "title": "LIFT Session",
                "start": "2026-05-26T02:00:00Z",
                "end": "2026-05-26T04:00:00Z",
                "is_anchor": True
            }
        ]
    }
    
    data_controller.write_json("compiled_master_calendar.json", mock_events)
    
    has_conflict, reason = check_event_conflict(start_iso, end_iso)
    print(f"Conflict: {has_conflict}, Reason: {reason}")
    assert has_conflict == True, "Conflict checking failed! Expected True."
    print("Test 3 Passed\n")

if __name__ == "__main__":
    async def main():
        try:
            await test_1()
            test_2()
            test_3()
            print("All temporal tests passed! Pipeline is solid.")
        except AssertionError as e:
            print(f"AssertionError: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    asyncio.run(main())

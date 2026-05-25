import datetime
import pytz

def overlaps(start1, end1, start2, end2):
    return max(start1, start2) < min(end1, end2)

def generate_events(user_goals, work_events):
    events = []
    events.extend(work_events)
    
    tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
    tz = pytz.timezone(tz_name)
    now = datetime.datetime.now(tz)
    
    # 30 days starting from today (0)
    for i in range(0, 30):
        current_day = now + datetime.timedelta(days=i)
        day_str = current_day.strftime("%A")
        
        # 1. Sleep (23:00 to 07:00 next day)
        sleep_start = current_day.replace(hour=23, minute=0, second=0, microsecond=0)
        sleep_end = sleep_start + datetime.timedelta(hours=8)
        events.append({
            "title": "Sleep Block",
            "start": sleep_start.isoformat(),
            "end": sleep_end.isoformat(),
            "type": "habit"
        })
        
        # Helper to find gap
        def find_gap(search_start, search_end, duration_minutes):
            current = search_start
            while current + datetime.timedelta(minutes=duration_minutes) <= search_end:
                slot_end = current + datetime.timedelta(minutes=duration_minutes)
                
                # Check collision with existing events
                collision = False
                for ev in events:
                    ev_start = datetime.datetime.fromisoformat(ev["start"].replace("Z", "+00:00")).astimezone(tz)
                    ev_end = datetime.datetime.fromisoformat(ev["end"].replace("Z", "+00:00")).astimezone(tz)
                    if overlaps(current, slot_end, ev_start, ev_end):
                        collision = True
                        break
                        
                if not collision:
                    return current, slot_end
                current += datetime.timedelta(minutes=15) # step size
            return None, None
            
        # 2. Meals
        nutrition = user_goals.get("nutrition", {})
        meals_per_day = nutrition.get("meals_per_day", 4)
        time_to_eat = nutrition.get("time_to_eat", 30)
        
        # We try to place them roughly at [8, 12, 16, 20]
        target_hours = [8, 12, 16, 20]
        if meals_per_day != 4:
            # simple fallback
            target_hours = [8 + i*(12//meals_per_day) for i in range(meals_per_day)]
            
        for h in target_hours[:meals_per_day]:
            # scan window: +/- 2 hours from target
            target_start = current_day.replace(hour=h, minute=0, second=0, microsecond=0)
            scan_start = max(current_day.replace(hour=7, minute=0), target_start - datetime.timedelta(hours=2))
            scan_end = min(current_day.replace(hour=22, minute=30), target_start + datetime.timedelta(hours=2))
            
            start_slot, end_slot = find_gap(scan_start, scan_end, time_to_eat)
            if start_slot:
                events.append({
                    "title": "Meal",
                    "start": start_slot.isoformat(),
                    "end": end_slot.isoformat(),
                    "type": "habit"
                })
        
        # 3. Gym
        template = user_goals.get("weekly_template_registry", {}).get(day_str, {})
        state = template.get("training_state", "REST")
        if state == "LIFT":
            gym_dur = user_goals.get("gym_scheduling", {}).get("session_duration_minutes", 45)
            # Try finding a gap between 16:00 and 22:00
            scan_start = current_day.replace(hour=16, minute=0, second=0, microsecond=0)
            scan_end = current_day.replace(hour=22, minute=0, second=0, microsecond=0)
            
            start_slot, end_slot = find_gap(scan_start, scan_end, gym_dur)
            if start_slot:
                events.append({
                    "title": "LIFT Session",
                    "start": start_slot.isoformat(),
                    "end": end_slot.isoformat(),
                    "type": "habit"
                })
        elif template.get("is_anchor"):
            anchor_start = template.get("anchor_start")
            anchor_end = template.get("anchor_end")
            if anchor_start and anchor_end:
                h_s, m_s = map(int, anchor_start.split(":"))
                h_e, m_e = map(int, anchor_end.split(":"))
                ev_start = current_day.replace(hour=h_s, minute=m_s, second=0, microsecond=0)
                ev_end = current_day.replace(hour=h_e, minute=m_e, second=0, microsecond=0)
                events.append({
                    "title": f"{state} Session",
                    "start": ev_start.isoformat(),
                    "end": ev_end.isoformat(),
                    "type": "habit"
                })
                
    return events

print("Script written successfully")

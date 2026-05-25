import json

with open("data/conversation_states.json", "r") as f:
    state = json.load(f)

state["8241224953"] = {
    "status": "pending_approval",
    "draft": "Great, I'll send this to the boss for approval.",
    "event_state": {
        "who": "Ethan",
        "what": "hike",
        "where": "Citrus park",
        "date": "Saturday",
        "time": "8pm",
        "status": "pending_approval"
    },
    "original_message": "Saturday 8pm",
    "conflict": None,
    "proposed_time": {
        "start": "2026-05-31T03:00:00+00:00",
        "end": "2026-05-31T04:00:00+00:00"
    }
}

with open("data/conversation_states.json", "w") as f:
    json.dump(state, f, indent=4)

import requests

url = "http://localhost:8000/api/social/approve"
payload = {
    "chat_id": "8241224953",
    "approved_message": "Great, I'll send this to the boss for approval.",
    "event_start": "2026-05-31T03:00:00+00:00",
    "event_end": "2026-05-31T04:00:00+00:00",
    "event_title": "Social Plan"
}

response = requests.post(url, json=payload)
print(response.status_code)
print(response.text)

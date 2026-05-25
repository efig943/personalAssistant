import requests

res = requests.post("http://localhost:8000/api/social/reject", json={"chat_id": "8845734832", "reason": "Too far"})
print(res.status_code)
print(res.text)

import requests
import json

try:
    res = requests.get('http://127.0.0.1:8000/api/crm/contacts')
    data = res.json()
    print("Fetched contacts:", data.get("contacts", []))
except Exception as e:
    print("Error:", e)

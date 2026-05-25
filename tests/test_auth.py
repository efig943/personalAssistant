import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.main import get_calendar_service
import socket
socket.setdefaulttimeout(3)

print("Starting get_calendar_service...")
try:
    svc = get_calendar_service()
    print("Success!" if svc else "Failed to get svc.")
except Exception as e:
    print(f"Exception: {e}")

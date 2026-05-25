"""
api/calendar.py
Fast-read calendar endpoint — returns the compiled master calendar instantly.
"""
from fastapi import APIRouter

from backend.core.dependencies import data_controller

router = APIRouter()


@router.get("/api/calendar/events")
async def get_calendar_events():
    """Fast Read Path: Returns the compiled master calendar instantly."""
    compiled_data = data_controller.read_json(
        "compiled_master_calendar.json", default_val={"events": []}
    )
    events = compiled_data.get("events", [])
    return {"status": "success", "data": {"events": events}}

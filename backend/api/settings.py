"""
api/settings.py
CRUD endpoints for user configuration: goals, contacts, and interests.
"""
import asyncio

from fastapi import APIRouter

from backend.core.dependencies import data_controller
from backend.core.utils import deep_update
from backend.services.calendar_service import build_master_calendar
from backend.services.social_service import evaluate_proactive_messaging

router = APIRouter()


@router.get("/api/goals")
async def get_user_goals():
    """Returns user goals for dynamic frontend rendering."""
    return data_controller.read_json("user_goals.json", default_val={})


@router.put("/api/goals")
async def update_user_goals(payload: dict):
    """Deep merges incoming user goals with the existing goals file."""
    current_goals = data_controller.read_json("user_goals.json", default_val={})
    updated_goals = deep_update(current_goals, payload)
    data_controller.write_json("user_goals.json", updated_goals)
    # Rebuild master calendar since anchors may have changed
    await build_master_calendar()
    asyncio.create_task(evaluate_proactive_messaging())
    return {"status": "success", "message": "Goals updated successfully"}


@router.get("/api/contacts")
async def get_contacts():
    return data_controller.read_json(
        "contacts_registry.json", default_val={"contacts": []}
    )


@router.post("/api/contacts")
async def update_contacts(payload: dict):
    # Before saving, try to resolve any null chat_ids using the cache
    user_cache = data_controller.read_json("telegram_user_cache.json", default_val={})
    for contact in payload.get("contacts", []):
        if not contact.get("chat_id") and contact.get("username"):
            username_key = str(contact["username"]).replace("@", "").lower()
            if username_key in user_cache:
                contact["chat_id"] = user_cache[username_key]
                print(
                    f"Retroactively linked {contact.get('name')} to chat_id {contact['chat_id']}"
                )

    data_controller.write_json("contacts_registry.json", payload)
    asyncio.create_task(evaluate_proactive_messaging())
    return {"status": "success"}


@router.get("/api/interests")
async def get_interests():
    return data_controller.read_json("interests.json", default_val={"interests": []})


@router.post("/api/interests")
async def update_interests(payload: dict):
    data_controller.write_json("interests.json", payload)
    return {"status": "success"}

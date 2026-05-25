"""
api/crm.py
CRM endpoints: message thread read, message edit, and contacts sidebar.
"""
from fastapi import APIRouter, HTTPException

from backend.core.dependencies import data_controller
from backend.models.schemas import EditMessageRequest

router = APIRouter()


@router.get("/api/crm/contacts")
async def get_crm_contacts():
    """Returns contacts registry for the CRM Sidebar."""
    return data_controller.read_json(
        "contacts_registry.json", default_val={"contacts": []}
    )


@router.get("/api/crm/messages/{chat_id}")
async def get_crm_messages(chat_id: str):
    """Returns a specific contact's thread from message history."""
    history = data_controller.read_json("message_history.json", default_val={})
    return {"chat_id": chat_id, "messages": history.get(chat_id, [])}


@router.put("/api/crm/messages/{chat_id}/{message_id}")
async def edit_message(chat_id: str, message_id: str, request: EditMessageRequest):
    """Atomically edit a message payload by unique message_id."""
    history = data_controller.read_json("message_history.json", default_val={})
    chat_history = history.get(chat_id, [])

    message_found = False
    for msg in chat_history:
        if msg.get("message_id") == message_id:
            msg["text"] = request.new_text
            message_found = True
            break

    if not message_found:
        raise HTTPException(status_code=404, detail="Message not found.")

    history[chat_id] = chat_history
    data_controller.write_json("message_history.json", history)

    # If the message being edited is the active pending_approval draft, sync conversation_states too
    state = data_controller.read_json("conversation_states.json", default_val={})
    if chat_id in state and state[chat_id].get("status") == "pending_approval":
        if chat_history[-1].get("message_id") == message_id:
            state[chat_id]["draft"] = request.new_text
            data_controller.write_json("conversation_states.json", state)

    return {"status": "success", "message": "Message edited successfully."}

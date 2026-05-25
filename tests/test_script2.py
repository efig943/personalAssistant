import asyncio
from backend.services.social_service import generate_social_draft
import json

async def main():
    current_state = {
        "who": "Ethan",
        "what": "soccer",
        "where": "Myford park",
        "date": "Tuesday",
        "time": "2pm"
    }
    chat_id = "8241224953"
    prompt = "Tuesday at 2pm"
    
    print("Generating social draft...")
    result = await generate_social_draft(chat_id, prompt, current_state)
    print("Result:", json.dumps(result, indent=2))

asyncio.run(main())

import asyncio
from backend.services.social_service import generate_social_draft
from backend.core.dependencies import groq_client

async def main():
    if not groq_client: return
    current_state = {
        "who": "ethan",
        "what": "getting some boba",
        "where": "Class 302",
        "date": "tomorrow",
        "time": "8pm",
        "status": "pending_approval"
    }
    res = await generate_social_draft("8241224953", "Could you remove boba event I can't go", current_state)
    print(res)

asyncio.run(main())

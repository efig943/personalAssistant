import asyncio
from backend.services.social_service import generate_social_draft
from backend.core.dependencies import groq_client

async def main():
    if not groq_client: return
    current_state = {
        "who": "Ethan",
        "what": "hike",
        "where": "Citrus park",
        "date": "Saturday",
        "time": "8pm",
        "status": "pending_approval"
    }
    res = await generate_social_draft("8241224953", "Remove the hike at citrus park I got injured", current_state)
    print("Result:", res)

asyncio.run(main())

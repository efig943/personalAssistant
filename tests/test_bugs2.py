import asyncio
from backend.main import groq_client
import json

async def extract_proposed_time_debug(text: str):
    system_prompt = (
        "You are a parsing assistant. Your task is to extract proposed meeting start and end times from the message as EXACT text phrases. "
        "Return ONLY a JSON object in the following format: "
        "{\"start_text\": \"the raw string for start time\", \"end_text\": \"the raw string for end time\"}. "
        "If no specific time is proposed, return empty JSON: {}. "
        "Example: For 'tomorrow at 5pm to 6pm', return {\"start_text\": \"tomorrow at 5pm\", \"end_text\": \"tomorrow at 6pm\"}."
    )
    response = await groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.0,
        response_format={"type": "json_object"}
    )
    print("Raw LLM response:", response.choices[0].message.content)
    
async def main():
    await extract_proposed_time_debug("How about next Saturday around 14:00")

asyncio.run(main())

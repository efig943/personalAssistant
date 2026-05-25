import asyncio
import json
import datetime
import pytz
import dateparser
from backend.core.dependencies import groq_client

async def extract_proposed_time(text: str) -> dict | None:
    tz = pytz.timezone("America/Los_Angeles")
    now_local = datetime.datetime.now(tz)
    
    system_prompt = (
        "You are a parsing assistant. Extract the proposed meeting start and end times from the message. "
        "Return ONLY a JSON object with 'start' and 'end' keys. "
        "IMPORTANT: Provide the exact relative or absolute phrases as stated (e.g., 'Tuesday at 2pm', 'tomorrow at 5pm', '2024-05-24 18:00:00'). "
        "If no end time is specified, infer it as 1 hour after the start time in the same format. "
        "If no specific time is proposed, return an empty JSON: {}. "
    )

    response = await groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model="llama-3.1-8b-instant",
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    print("LLM extracted:", data)

    if data.get("start") and data.get("end"):
        start_obj = dateparser.parse(
            str(data["start"]),
            settings={
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": now_local,
                "TIMEZONE": "America/Los_Angeles",
            },
        )
        end_obj = dateparser.parse(
            str(data["end"]),
            settings={
                "PREFER_DATES_FROM": "future",
                "RELATIVE_BASE": now_local,
                "TIMEZONE": "America/Los_Angeles",
            },
        )
        print("Parsed Start:", start_obj)
        print("Parsed End:", end_obj)

async def main():
    await extract_proposed_time("2pm on Tuesday")

if __name__ == "__main__":
    asyncio.run(main())

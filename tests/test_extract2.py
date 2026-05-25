import asyncio
import os
import sys
import json
import pytz
import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from backend.core.dependencies import groq_client, data_controller

async def main():
    text = "That works"
    user_goals = data_controller.read_json("user_goals.json")
    worker_model = user_goals.get("llm_model_routing", {}).get("tool_worker", "llama-3.1-8b-instant")
    system_prompt = (
        "You are a parsing assistant. Extract the proposed meeting start and end times from the message. "
        "Return ONLY a JSON object with 'start' and 'end' keys. "
        "IMPORTANT: Provide the exact relative or absolute phrases as stated (e.g., 'Tuesday at 2pm', 'tomorrow at 5pm', '2024-05-24 18:00:00'). "
        "If no end time is specified, infer it as 1 hour after the start time in the same format. "
        "If no specific time is proposed, return an empty JSON: {}. "
        'Example Output: {"start": "Tuesday at 2pm", "end": "Tuesday at 3pm"}'
    )
    response = await groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model=worker_model,
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    print("LLM OUTPUT:", response.choices[0].message.content)

asyncio.run(main())

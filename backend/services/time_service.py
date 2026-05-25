"""
services/time_service.py
LLM-powered temporal extraction pipeline: raw phrase → normalized UTC ISO string.
Uses Groq for NLP extraction, then dateparser for normalization.
"""
import json
import datetime
import pytz
import dateparser

from backend.core.dependencies import data_controller, groq_client


async def extract_proposed_time(text: str) -> dict | None:
    """
    Uses Groq to extract raw time phrases, then normalizes them using dateparser.
    Returns a dict with 'start' and 'end' ISO UTC strings, or None.
    """
    if not groq_client:
        return None

    user_goals = data_controller.read_json("user_goals.json")
    worker_model = user_goals.get("llm_model_routing", {}).get(
        "tool_worker", "llama-3.1-8b-instant"
    )
    tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
    tz = pytz.timezone(tz_name)
    now_local = datetime.datetime.now(tz)
    now_str = now_local.strftime("%Y-%m-%d %H:%M:%S")

    system_prompt = (
        "You are a parsing assistant. Your ONLY job is to extract explicit meeting start and end times proposed in the user's message.\n"
        "Return ONLY a JSON object with 'start' and 'end' keys.\n"
        "IMPORTANT RULES:\n"
        "1. If the user explicitly proposes a time (e.g., 'Tuesday at 2pm', 'tomorrow at 5pm'), extract the exact phrase.\n"
        "2. If the user DOES NOT explicitly propose a time, or merely agrees to a time someone else proposed (e.g., 'Yes', 'That works', 'Sounds good', 'Sure'), YOU MUST return an empty JSON: {}\n"
        "3. DO NOT hallucinate times. DO NOT output 'tomorrow at 5pm' unless the user literally typed it.\n"
        "4. If no end time is specified, infer it as 1 hour after the start time in the same format. Do not leave it null."
    )

    try:
        response = await groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            model=worker_model,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)

        if data.get("start") and data.get("end"):
            start_obj = dateparser.parse(
                str(data["start"]),
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": now_local,
                    "TIMEZONE": tz_name,
                },
            )
            end_obj = dateparser.parse(
                str(data["end"]),
                settings={
                    "PREFER_DATES_FROM": "future",
                    "RELATIVE_BASE": now_local,
                    "TIMEZONE": tz_name,
                },
            )
            if start_obj and end_obj:
                if not start_obj.tzinfo:
                    start_obj = tz.localize(start_obj)
                if not end_obj.tzinfo:
                    end_obj = tz.localize(end_obj)
                return {
                    "start": start_obj.astimezone(datetime.timezone.utc).isoformat(),
                    "end": end_obj.astimezone(datetime.timezone.utc).isoformat(),
                }
        return None
    except Exception as e:
        print(f"Error in time extraction: {e}")
        return None

"""
services/social_service.py
Core Social Butterfly agent logic:
  - generate_social_draft: 2-pass Groq tool-calling loop
  - perform_social_gap_analysis: checks contact urgency thresholds
  - evaluate_proactive_messaging: quota-aware autonomous outbound routing
"""
import json
import datetime

import backend.core.dependencies as deps
from backend.core.dependencies import data_controller, groq_client
from backend.tools.agent_tools import execute_calendar_tool, execute_remove_event_tool, check_specific_time_availability


async def generate_social_draft(
    chat_id: str, prompt: str, current_state: dict
) -> dict:
    """Uses Groq to generate a JSON response with the updated state and draft using Tool Calling."""
    if not groq_client:
        return {
            "updated_state": current_state,
            "draft": "Mock response: Groq client not initialized.",
        }

    interests_data = data_controller.read_json(
        "interests.json", default_val={"interests": []}
    )
    interests_str = ", ".join(interests_data.get("interests", []))

    user_goals = data_controller.read_json("user_goals.json")
    quota = user_goals.get("profile", {}).get("social_events_per_week", "Unlimited")
    llm_routing = user_goals.get("llm_model_routing", {})
    tool_worker = llm_routing.get("tool_worker", "llama-3.1-8b-instant")
    reasoning_worker = llm_routing.get("reasoning_worker", "llama-3.3-70b-versatile")

    social_log = data_controller.read_json(
        "approved_social_events.json", default_val={"events": []}
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    current_year, current_week, _ = now.isocalendar()
    current_week_count = sum(
        1
        for ev in social_log.get("events", [])
        if datetime.datetime.fromisoformat(
            ev["event_start"].replace("Z", "+00:00")
        ).isocalendar()[:2]
        == (current_year, current_week)
    )

    import pytz

    tz_name = user_goals.get("profile", {}).get("timezone", "America/Los_Angeles")
    now_local = now.astimezone(pytz.timezone(tz_name))

    contact_approved_events = []
    for ev in social_log.get("events", []):
        if str(ev.get("chat_id")) == str(chat_id):
            ev_start = datetime.datetime.fromisoformat(ev["event_start"].replace("Z", "+00:00"))
            if ev_start >= now:
                contact_approved_events.append(f"- {ev.get('what', 'Social Plan')} on {ev_start.astimezone(pytz.timezone(tz_name)).strftime('%A, %b %d at %I:%M %p')}")

    approved_events_str = "\n".join(contact_approved_events) if contact_approved_events else "None."

    calendar_state_msg = (
        f"Weekly Social Quota limit: {current_week_count}/{quota} events used. "
        f"Current local time is {now_local.strftime('%Y-%m-%d %H:%M %A')}.\n"
        f"Already Approved Upcoming Events with this contact:\n{approved_events_str}"
    )
    # Fetch the full conversation state for this chat_id to give the LLM explicit context
    full_conv_states = data_controller.read_json("conversation_states.json", default_val={})
    full_conv_state = full_conv_states.get(str(chat_id), {})
    conv_status = full_conv_state.get("status", "negotiating")
    conv_conflict = full_conv_state.get("conflict") or "None"
    conv_proposed_time = full_conv_state.get("proposed_time") or "None"
    conv_event_state = full_conv_state.get("event_state") or {"who": None, "what": None, "where": None, "date": None, "time": None}
    
    # Revert Opt 1a: The 8B model MUST see explicit null fields to understand the schema.
    # Otherwise it panics on an empty state and hallucinates tool calls.
    import json as _json
    active_plan_str = _json.dumps(conv_event_state, indent=None)

    messages = [
        {
            "role": "system",
            "content": f"""You are the 'Social Butterfly,' a sophisticated and warm personal relationship assistant. Your goal is to guide the user's friends toward finalizing a social plan.

<USER_INTERESTS>
{interests_str}
</USER_INTERESTS>

<CURRENT_STATE>
{calendar_state_msg}
Active negotiation status: {conv_status}
Current plan in progress: {active_plan_str}
Last known conflict: {conv_conflict}
Last proposed time (ISO): {conv_proposed_time}
</CURRENT_STATE>

### CORE PERSONALITY & CONVERSATION
- Be natural, conversational, and enthusiastic. Never sound like a bot.
- Keep responses to 1-2 sentences.
- Do NOT mention quotas, limits, or system rules to the user. Keep it conversational.
- If a variable is missing, pivot the conversation to pin down that specific detail.
- Proactively suggest activities based on the User's Interests listed above. These are YOUR boss's interests, not necessarily the contact's. If suggesting an unlisted activity, you MUST provide a natural reason why.
- ONE PLAN AT A TIME: If the contact proposes multiple events or ideas at once (e.g., "let's do coffee AND tennis this week"), warmly acknowledge both but redirect: lock down the details for the first one before moving on. Never try to negotiate two events simultaneously.

### TOOL CALLING PROTOCOLS (CRITICAL)
Evaluate the user's latest message. If any of these conditions are met, you MUST invoke the corresponding tool IMMEDIATELY and halt all other generation:
1. THE CANCELLATION TRIGGER: If the user indicates ANY unavailability ('I can't go', 'cancel that', 'something came up', 'I am busy', 'I can't do [activity]', or words similar to not attending), you MUST call the remove_social_event tool IMMEDIATELY.
2. THE TIME PROPOSAL TRIGGER: If the user proposes a specific day AND time, you MUST call the check_specific_time_availability tool before agreeing.
*(Note: If the tool returns 'Hard Conflict', apologize and MUST propose a specific free slot from the calendar. DO NOT ask the user to guess another time. If 'Clear' or 'Soft Conflict', immediately finalize the plan. If the tool returns a past-date error, politely tell the contact you can only schedule future events.)*
 
### REMOVE EVENT TOOL — CRITICAL RESPONSE RULES
- If remove_social_event returns "No approved event found": You MUST say there was no confirmed event to remove (e.g., "Looks like we didn't have anything locked in yet."). NEVER say an event was removed if this result is returned. Reset the conversation and ask what they'd like to do instead.
- If remove_social_event returns "Successfully removed": Confirm the removal naturally and ask what they'd like to do instead.

### STATE MANAGEMENT & JSON OUTPUT
If no tools are required, you MUST output ONLY a single JSON object containing exactly two keys: "updated_state" (the full EventState model with your updates), and "draft" (the text of your conversational response). Follow these strict rules for the JSON:
- NO ASSUMPTIONS: DO NOT invent, assume, or guess values for Who, What, Where, Date, or Time. Only populate a null field in updated_state if the user explicitly provided or agreed to that specific detail. If unsure, leave it null.
- DATE FORMAT: Always copy the exact words the user used for the date (e.g., 'Thursday', 'tomorrow'). NEVER calculate or output an absolute YYYY-MM-DD date.
- NEVER RE-ASK POPULATED FIELDS: Never ask for a field (Who, What, Where, Date, Time) that is already non-null in the Current EventState. If `time` is already set, do not ask for time again.
- FINALIZING CHECK: Before generating any follow-up question, check all 5 EventState fields. If Who, What, Where, Date, and Time are ALL non-null, you MUST output a short final confirmation (e.g., 'Great, I will see you then.') and set status to 'pending_approval' immediately. Do NOT ask sub-questions about already-confirmed fields (e.g., 'which part of the venue', 'which entrance').
- NO EARLY CONFIRMATION: NEVER use phrases like 'see you', 'I will see you', 'locked in', or 'it's a date' unless ALL 5 fields (who, what, where, date, time) are non-null in the updated_state. If even ONE field is null, you MUST ask for that missing field instead. A confirmation with a missing field is a critical error.
- VERIFY YOUR OWN COUNTER-PROPOSALS: If you are suggesting a specific time to the user (e.g., 'how about 4pm?'), you MUST first call check_specific_time_availability to confirm that slot is truly free before offering it. Do not suggest a time you haven't verified.""",
        },
        {
            "role": "user",
            "content": (
                f"Current EventState: {json.dumps(current_state)}\n\nUser Message: {prompt}"
            ),
        },
    ]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_calendar_availability",
                "description": (
                    "Fetches the user's free and busy blocks for a specific date from the Master Calendar. "
                    "Use this whenever the user proposes a day, or when you need to suggest a day."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "target_date": {
                            "type": "string",
                            "description": "The date to check availability for, in YYYY-MM-DD format. If the date is unknown, pass an empty string ''.",
                        }
                    },
                    "required": ["target_date"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "remove_social_event",
                "description": "CRITICAL: You MUST use this tool immediately whenever the user explicitly requests an event to be deleted, OR when they implicitly cancel by expressing that they cannot attend, got busy, or need to call off plans. Fire this tool even if you think there is no event currently scheduled.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "The exact reason the user provided for cancelling or not attending (e.g., 'got busy', 'can't go')."
                        }
                    },
                    "required": ["reason"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "check_specific_time_availability",
                "description": "Checks if a specific time is free on the Master Calendar. Use this BEFORE agreeing to a proposed time.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "proposed_time_phrase": {
                            "type": "string",
                            "description": "The exact time phrase proposed, e.g., 'Tuesday at 2pm'.",
                        }
                    },
                    "required": ["proposed_time_phrase"],
                },
            },
        },
    ]

    # ── PASS 1: Tool Calling ──────────────────────────────────────────────────
    try:
        response = await groq_client.chat.completions.create(
            messages=messages,
            model=tool_worker,
            temperature=0.5,
            tools=tools,
            tool_choice="auto",
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        if tool_calls:
            # Circuit Breaker: 8B models can hallucinate massive repetitive tool arrays when confused.
            # Hard-cap execution to the first 2 tools to prevent infinite processing loops.
            tool_calls = tool_calls[:2]
            
            # Append the assistant's tool call request
            messages.append(
                {
                    "role": "assistant",
                    "content": response_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            # Execute tool(s)
            for tool_call in tool_calls:
                function_args = json.loads(tool_call.function.arguments)
                if tool_call.function.name == "check_calendar_availability":
                    target_date = function_args.get("target_date") or current_state.get(
                        "date"
                    )
                    tool_result = await execute_calendar_tool(target_date)
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "check_calendar_availability",
                            "content": tool_result,
                        }
                    )
                elif tool_call.function.name == "remove_social_event":
                    reason_arg = function_args.get("reason", "")
                    # Pass chat_id securely from execution context
                    tool_result = await execute_remove_event_tool(chat_id, reason=reason_arg)
                    # Bug 4 Fix: Always wipe the negotiation state for this chat
                    # when a cancellation fires — whether or not an approved event existed.
                    # This prevents the agent from referencing a dead proposal on the next turn.
                    from backend.core.dependencies import data_controller as _dc
                    _conv_states = _dc.read_json("conversation_states.json", default_val={})
                    if str(chat_id) in _conv_states:
                        del _conv_states[str(chat_id)]
                        _dc.write_json("conversation_states.json", _conv_states)
                        print(f"[REMOVE] Cleared conversation state for chat_id={chat_id}")
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "remove_social_event",
                            "content": tool_result,
                        }
                    )
                elif tool_call.function.name == "check_specific_time_availability":
                    phrase = function_args.get("proposed_time_phrase", "")
                    # Bug B Fix: If the phrase contains a time but no date anchor, inject
                    # the current event_state date so the tool can parse "Tuesday at 5 pm"
                    # instead of just "5 pm", which would fail to parse and crash to fallback.
                    _date_anchor_words = {
                        "monday","tuesday","wednesday","thursday","friday","saturday","sunday",
                        "today","tomorrow","next","jan","feb","mar","apr","may","jun",
                        "jul","aug","sep","oct","nov","dec",
                    }
                    _current_date = current_state.get("date") or ""
                    if _current_date and not any(w in phrase.lower() for w in _date_anchor_words):
                        phrase = f"{_current_date} at {phrase}"
                        print(f"[BUG B FIX] Enriched time phrase to: '{phrase}'")
                    tool_result = await check_specific_time_availability(phrase)
                    messages.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": "check_specific_time_availability",
                            "content": tool_result,
                        }
                    )

            # ── PASS 2: Final JSON Generation ─────────────────────────────────
            second_response = await groq_client.chat.completions.create(
                messages=messages,
                model=reasoning_worker,
                temperature=0.5,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            final_content = second_response.choices[0].message.content
        else:
            final_content = response_message.content

        content = json.loads(final_content)
        if "updated_state" in content and "status" not in content["updated_state"]:
            content["updated_state"]["status"] = "negotiating"
        return content

    except json.JSONDecodeError:
        # Fallback if first pass didn't format as JSON
        try:
            fallback_response = await groq_client.chat.completions.create(
                messages=messages,
                model=reasoning_worker,
                temperature=0.5,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            content = json.loads(fallback_response.choices[0].message.content)
            if "updated_state" in content and "status" not in content["updated_state"]:
                content["updated_state"]["status"] = "negotiating"
            return content
        except Exception as e:
            print(f"Error parsing draft JSON fallback: {e}")
            return {
                "updated_state": current_state,
                "draft": "I'm having trouble thinking of a response right now.",
            }
    except Exception as e:
        print(f"Error in generate_social_draft Pass 1: {e}")
        try:
            fallback_response = await groq_client.chat.completions.create(
                messages=messages,
                model=reasoning_worker,
                temperature=0.5,
                max_tokens=300,
                response_format={"type": "json_object"},
            )
            content = json.loads(fallback_response.choices[0].message.content)
            if "updated_state" in content and "status" not in content["updated_state"]:
                content["updated_state"]["status"] = "negotiating"
            return content
        except Exception as fallback_err:
            print(f"Error in generate_social_draft fallback: {fallback_err}")
            return {
                "updated_state": current_state,
                "draft": "I'm having trouble thinking of a response right now.",
            }


async def perform_social_gap_analysis():
    """
    Checks if any whitelisted contact has not been contacted within their urgency threshold.
    If so, calls Groq API to draft a re-engagement message and saves it to conversation_states.json.
    """
    contacts_data = data_controller.read_json(
        "contacts_registry.json", default_val={"contacts": []}
    )
    contacts = contacts_data.get("contacts", [])
    if not contacts:
        return

    now = datetime.datetime.now(datetime.timezone.utc)

    for contact in contacts:
        chat_id = str(contact["chat_id"])
        last_contact_str = contact.get("last_contact_time")
        threshold_days = contact.get("urgency_threshold_days", 7)

        if not last_contact_str:
            continue

        last_contact = datetime.datetime.fromisoformat(
            last_contact_str.replace("Z", "+00:00")
        )
        gap = now - last_contact

        if gap.days >= threshold_days:
            prompt = (
                f"It has been {gap.days} days since we last spoke with {contact['name']}. "
                "Draft a warm message to check in and see if they want to catch up."
            )

            states = data_controller.read_json(
                "conversation_states.json", default_val={}
            )
            current_chat_state = states.get(chat_id, {})
            current_event_state = current_chat_state.get(
                "event_state",
                {
                    "who": None,
                    "what": None,
                    "where": None,
                    "date": None,
                    "time": None,
                    "status": "negotiating",
                },
            )

            draft_data = await generate_social_draft(chat_id, prompt, current_event_state)
            updated_state = draft_data.get("updated_state", current_event_state)
            draft = draft_data.get("draft", "Hey! It's been a while, how are you?")

            states[chat_id] = {
                "status": updated_state.get("status", "negotiating"),
                "draft": draft,
                "event_state": updated_state,
                "reason": f"Urgency threshold of {threshold_days} days exceeded (last contact: {last_contact_str})",
                "proposed_time": None,
                "recipient_name": contact["name"],
            }
            data_controller.write_json("conversation_states.json", states)


async def evaluate_proactive_messaging():
    """Evaluates whether to queue a reach-out draft or send it autonomously based on quota."""
    try:
        contacts_data = data_controller.read_json(
            "contacts_registry.json", default_val={"contacts": []}
        )
        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Quota Checking
        social_log = data_controller.read_json(
            "approved_social_events.json", default_val={"events": []}
        )
        current_year, current_week, _ = now.isocalendar()
        current_week_count = sum(
            1
            for ev in social_log.get("events", [])
            if datetime.datetime.fromisoformat(
                ev["event_start"].replace("Z", "+00:00")
            ).isocalendar()[:2]
            == (current_year, current_week)
        )

        user_goals = data_controller.read_json("user_goals.json")
        quota_val = user_goals.get("profile", {}).get("social_events_per_week", 2)
        quota = float("inf") if quota_val == "Unlimited" else int(quota_val)

        # Circuit Breaker
        if current_week_count >= quota:
            print(
                f"Weekly social quota reached ({current_week_count}/{quota}). "
                "Proactive messaging paused."
            )
            return

        for contact in contacts_data.get("contacts", []):
            last_contact_str = contact.get("last_contact_time")
            threshold_days = contact.get("urgency_threshold_days", 7)
            chat_id = (
                str(contact.get("chat_id")) if contact.get("chat_id") else None
            )

            if not chat_id or chat_id == "None":
                continue

            is_overdue = False
            if last_contact_str:
                last_contact = datetime.datetime.fromisoformat(last_contact_str)
                if (now - last_contact).days > threshold_days:
                    is_overdue = True
            else:
                # Never contacted — automatically overdue
                is_overdue = True

            if is_overdue:
                state = data_controller.read_json(
                    "conversation_states.json", default_val={}
                )

                # Clear stalled negotiation state
                if chat_id in state:
                    del state[chat_id]

                if chat_id not in state:
                    # 2. Autonomous Outbound Routing (Under Quota)
                    prompt = (
                        f"You are initiating contact with {contact.get('name')} because it has been a while. "
                        "Draft a spontaneous, warm message checking in and subtly proposing a casual catch-up."
                    )
                    current_state = {
                        "who": contact.get("name"),
                        "what": None,
                        "where": None,
                        "date": None,
                        "time": None,
                        "status": "negotiating",
                    }

                    draft_data = await generate_social_draft(
                        chat_id, prompt, current_state
                    )
                    draft_text = draft_data.get(
                        "draft",
                        f"Hey {contact.get('name')}, it's been a while! How have you been?",
                    )

                    updated_state = draft_data.get("updated_state", current_state)
                    updated_state["status"] = "negotiating"

                    # Execute Outbound Send
                    if deps.ptb_application and deps.ptb_application.bot:
                        await deps.ptb_application.bot.send_message(
                            chat_id=chat_id, text=draft_text
                        )

                    # Commit to History
                    history = data_controller.read_json(
                        "message_history.json", default_val={}
                    )
                    if chat_id not in history:
                        history[chat_id] = []
                    import uuid
                    history[chat_id].append(
                        {
                            "message_id": str(uuid.uuid4()),
                            "sender": "agent",
                            "name": "Social Butterfly",
                            "text": draft_text,
                            "timestamp": datetime.datetime.now(
                                datetime.timezone.utc
                            ).isoformat(),
                            "pending_approval": False,
                        }
                    )
                    data_controller.write_json("message_history.json", history)

                    # Save Live State
                    state[chat_id] = {
                        "status": "negotiating",
                        "draft": draft_text,
                        "event_state": updated_state,
                        "original_message": "System: Autonomous Proactive Reach Out",
                        "conflict": None,
                        "proposed_time": None,
                    }
                    data_controller.write_json("conversation_states.json", state)

                    # Update Last Contact Time
                    contact["last_contact_time"] = datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat()
                    data_controller.write_json("contacts_registry.json", contacts_data)

                    print(
                        f"Sent autonomous proactive reach out to {contact.get('name')}"
                    )

    except Exception as e:
        print(f"Error in evaluate_proactive_messaging: {e}")

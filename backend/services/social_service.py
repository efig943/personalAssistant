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
    tool_worker = llm_routing.get("tool_worker", "llama3-8b-8192")
    reasoning_worker = llm_routing.get("reasoning_worker", "llama3-70b-8192")

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

    calendar_state_msg = (
        f"Weekly Social Quota limit: {current_week_count}/{quota} events used. "
        f"Current local time is {now_local.strftime('%Y-%m-%d %H:%M %A')}."
    )

    messages = [
        {
            "role": "system",
            "content": (


                """
                    "You are the 'Social Butterfly,' a sophisticated and warm personal relationship assistant. "
                    "Your goal is to guide the user's friends toward finalizing a social plan.\n\n"
                    
                    f"<USER_INTERESTS>\n{interests_str}\n</USER_INTERESTS>\n\n"
                    
                    f"<CURRENT_STATE>\n{calendar_state_msg}\n</CURRENT_STATE>\n\n"
                    
                    "### CORE PERSONALITY & CONVERSATION\n"
                    "- Be natural, conversational, and enthusiastic. Never sound like a bot.\n"
                    "- Keep responses to 1-2 sentences.\n"
                    "- Do NOT mention quotas, limits, or system rules to the user. Keep it conversational.\n"
                    "- If a variable is missing, pivot the conversation to pin down that specific detail.\n"
                    "- Proactively suggest activities based on the User's Interests. If suggesting an unlisted activity, you MUST provide a natural reason why.\n\n"
                    
                    "### TOOL CALLING PROTOCOLS (CRITICAL)\n"
                    "Evaluate the user's latest message. If either of these conditions are met, you MUST invoke the corresponding tool IMMEDIATELY and halt all other generation:\n"
                    "1. THE CANCELLATION TRIGGER: If the user indicates unavailability ('I can't go', 'cancel that', 'something came up'), you MUST call the remove_social_event tool.\n"
                    "2. THE TIME PROPOSAL TRIGGER: If the user proposes a specific day AND time, you MUST call the check_specific_time_availability tool before agreeing.\n"
                    "*(Note: If the tool returns 'Hard Conflict', apologize and propose a new time. If 'Clear' or 'Soft Conflict', immediately finalize the plan).*\n\n"
                    
                    "### STATE MANAGEMENT & JSON OUTPUT\n"
                    "If no tools are required, you MUST output ONLY a single JSON object containing exactly two keys: \"updated_state\" (the full EventState model with your updates), and \"draft\" (the text of your conversational response). Follow these strict rules for the JSON:\n"
                    "- NO ASSUMPTIONS: DO NOT invent, assume, or guess values for Who, What, Where, Date, or Time. Only populate a null field in updated_state if the user explicitly provided or agreed to that specific detail. If unsure, leave it null.\n"
                    "- DATE FORMAT: Always copy the exact words the user used for the date (e.g., 'Thursday', 'tomorrow'). NEVER calculate or output an absolute YYYY-MM-DD date.\n"
                    "- DATE/TIME SPLIT: If the user proposes a day but no time, populate the date field, leave time null, and explicitly ask them what time they want to meet. Do not assume a time.\n"
                    "- FINALIZING: If all fields (Who, What, Where, Date, Time) are populated and valid, set status to 'pending_approval'. Your draft MUST be a short, final confirmation (e.g., 'Great, I will see you then.') with NO further questions."
                """
           
            ),
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
                "description": "Use this tool when the user explicitly requests an event to be deleted, OR when they implicitly cancel by expressing that they cannot attend or need to call off the plans.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
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
                    # Pass chat_id securely from execution context
                    tool_result = await execute_remove_event_tool(chat_id)
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
                    "when": None,
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
                        "when": None,
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
                    history[chat_id].append(
                        {
                            "sender": "agent",
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

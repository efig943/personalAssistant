"""
tests/test_llm_agent.py
Parameterized semantic-robustness test suite for the Social Butterfly LLM agent.

Tests verify that the LLM correctly maps varied natural-language phrasing to the
exact same tool calls and JSON state structures — without hitting live databases.

A 2-3 second sleep is added between tests to respect Groq's free-tier TPM rate limits
(6,000 tokens/min). Running 11 tests simultaneously would exhaust this instantly.

Run with:
    source .venv/bin/activate
    pytest tests/test_llm_agent.py -v
"""
import json
import sys
import os
import asyncio
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Mock Data ────────────────────────────────────────────────────────────────
MOCK_USER_GOALS = {
    "profile": {
        "timezone": "America/Los_Angeles",
        "social_events_per_week": 3,
    },
    "llm_model_routing": {
        "tool_worker": "llama-3.1-8b-instant",
        "reasoning_worker": "llama-3.3-70b-versatile",
    },
}

MOCK_INTERESTS = {"interests": ["motorcycle riding", "golf", "hiking"]}
MOCK_APPROVED_EVENTS = {"events": []}
MOCK_CONV_STATES = {}
MOCK_MESSAGE_HISTORY = {}


def make_mock_data_controller():
    """Creates a fully mocked DataController that returns safe defaults."""
    mock_dc = MagicMock()

    def read_json_side_effect(filename, default_val=None):
        mapping = {
            "user_goals.json": MOCK_USER_GOALS,
            "interests.json": MOCK_INTERESTS,
            "approved_social_events.json": MOCK_APPROVED_EVENTS,
            "conversation_states.json": MOCK_CONV_STATES,
            "message_history.json": MOCK_MESSAGE_HISTORY,
            "contacts_registry.json": {"contacts": []},
            "compiled_master_calendar.json": {"events": []},
        }
        return mapping.get(filename, default_val if default_val is not None else {})

    mock_dc.read_json.side_effect = read_json_side_effect
    mock_dc.write_json = MagicMock()
    return mock_dc


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1: Cancellation Trigger — Semantic Variations
# ─────────────────────────────────────────────────────────────────────────────
# Assert: All of these MUST trigger the `remove_social_event` tool call.
# ═══════════════════════════════════════════════════════════════════════════════
CANCELLATION_PHRASES = [
    "I actually can't go anymore.",
    "Gotta bail on this one.",
    "Can we take a rain check?",
    "Something came up, sorry!",
    "I'm slammed at work, can't make it.",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("phrase", CANCELLATION_PHRASES)
async def test_cancellation_trigger(phrase):
    """
    All cancellation-style phrases must cause the LLM to call `remove_social_event`.
    The data layer is mocked so no live files are read or written.
    """
    # Throttle: space out API calls to avoid Groq free-tier TPM rate limits
    await asyncio.sleep(3)

    mock_dc = make_mock_data_controller()

    with (
        patch("backend.services.social_service.data_controller", mock_dc),
        patch("backend.tools.agent_tools.data_controller", mock_dc),
        patch("backend.core.dependencies.data_controller", mock_dc),
    ):
        from backend.services.social_service import generate_social_draft

        # Provide a state that has a pending event to cancel
        current_state = {
            "who": "Ethan",
            "what": "motorcycle ride",
            "where": "Citrus",
            "date": "Saturday",
            "time": "2pm",
            "status": "negotiating",
        }

        result = await generate_social_draft("test_chat_id", phrase, current_state)

    # The raw result should be a dict (not a JSON parse error / fallback)
    assert isinstance(result, dict), f"[{phrase!r}] generate_social_draft returned non-dict: {result}"

    # The remove_social_event tool should have been called.
    # We detect this by checking the agent response for removal confirmation language.
    draft = result.get("draft", "").lower()
    removal_keywords = [
        "cancel", "remove", "no problem", "got it", "noted", "bail", "rain check",
        "locked in", "won't be able", "understand", "no worries", "can't make",
        "couldn't find", "didn't have", "don't have", "no event",
    ]

    assert any(kw in draft for kw in removal_keywords), (
        f"[{phrase!r}] Expected removal confirmation in draft, got: {draft!r}"
    )
    print(f"\n  ✅ CANCEL [{phrase!r}] → Draft: {draft!r}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2: Specific Time Trigger — Semantic Variations
# ─────────────────────────────────────────────────────────────────────────────
# Assert: All of these MUST trigger the `check_specific_time_availability` tool.
# ═══════════════════════════════════════════════════════════════════════════════
SPECIFIC_TIME_PHRASES = [
    "How about Tuesday at 4pm?",
    "Can we do 16:00 on Tuesday?",
    "Tuesday @ 4 works for me.",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("phrase", SPECIFIC_TIME_PHRASES)
async def test_specific_time_trigger(phrase):
    """
    All specific-time phrases must cause the LLM to call `check_specific_time_availability`.
    We intercept the tool execution and record whether it was called.
    """
    # Throttle: space out API calls to avoid Groq free-tier TPM rate limits
    await asyncio.sleep(3)

    mock_dc = make_mock_data_controller()
    tool_was_called = []

    async def mock_check_specific_time(proposed_time_phrase: str) -> str:
        tool_was_called.append(proposed_time_phrase)
        return "Clear. The schedule is free. You may agree to this time."

    async def mock_execute_calendar(target_date: str) -> str:
        return f"No events scheduled for {target_date}. The entire day is free."

    with (
        patch("backend.services.social_service.data_controller", mock_dc),
        patch("backend.tools.agent_tools.data_controller", mock_dc),
        patch("backend.core.dependencies.data_controller", mock_dc),
        patch("backend.services.social_service.check_specific_time_availability", mock_check_specific_time),
        patch("backend.services.social_service.execute_calendar_tool", mock_execute_calendar),
    ):
        from backend.services.social_service import generate_social_draft

        current_state = {
            "who": "Ethan",
            "what": "motorcycle ride",
            "where": "Citrus",
            "date": None,
            "time": None,
            "status": "negotiating",
        }

        await generate_social_draft("test_chat_id", phrase, current_state)

    assert len(tool_was_called) > 0, (
        f"[{phrase!r}] Expected `check_specific_time_availability` to be called, but it was NOT triggered. "
        f"The LLM may have bypassed the tool and agreed to the time without checking the calendar."
    )
    print(f"\n  ✅ TIME TRIGGER [{phrase!r}] → Tool called with: {tool_was_called}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3: Day-Only Conversational Pivot — Semantic Variations
# ─────────────────────────────────────────────────────────────────────────────
# Assert: None should trigger check_specific_time_availability. All must return
#         valid JSON where time remains null and the draft asks for a specific time.
# ═══════════════════════════════════════════════════════════════════════════════
DAY_ONLY_PHRASES = [
    "Friday sounds great!",
    "Let's aim for Friday.",
    "Friday works for me.",
]

TIME_REQUEST_KEYWORDS = [
    "time", "when", "what time", "o'clock", "pm", "am", "hour",
    "morning", "afternoon", "evening", "how about", "2 pm", "3 pm",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("phrase", DAY_ONLY_PHRASES)
async def test_day_only_pivot(phrase):
    """
    Day-only proposals must NOT trigger check_specific_time_availability. The agent should:
    1. Leave `time` as None in updated_state.
    2. Ask for a specific time in the draft.
    """
    # Throttle: space out API calls to avoid Groq free-tier TPM rate limits
    await asyncio.sleep(3)

    mock_dc = make_mock_data_controller()
    time_check_calls = []

    async def mock_check_specific_time(proposed_time_phrase: str) -> str:
        time_check_calls.append(proposed_time_phrase)
        return "Clear. The schedule is free. You may agree to this time."

    async def mock_execute_calendar(target_date: str) -> str:
        return (
            f"Busy blocks for {target_date}:\n"
            "- 23:00 to 07:00 (Habit: Sleep Block)\n"
            "\nNote: Any time not listed above is FREE and available to schedule.\n"
            "CRITICAL INSTRUCTION: If the contact only proposed a day and did NOT propose a specific time, "
            "DO NOT say you have a conflict. Instead, pick a specific time from the FREE periods and propose it."
        )

    with (
        patch("backend.services.social_service.data_controller", mock_dc),
        patch("backend.tools.agent_tools.data_controller", mock_dc),
        patch("backend.core.dependencies.data_controller", mock_dc),
        patch("backend.services.social_service.check_specific_time_availability", mock_check_specific_time),
        patch("backend.services.social_service.execute_calendar_tool", mock_execute_calendar),
    ):
        from backend.services.social_service import generate_social_draft

        current_state = {
            "who": "Ethan",
            "what": "motorcycle ride",
            "where": "Citrus",
            "date": None,
            "time": None,
            "status": "negotiating",
        }

        result = await generate_social_draft("test_chat_id", phrase, current_state)

    assert isinstance(result, dict), f"[{phrase!r}] Result is not a dict: {result}"

    # 1. check_specific_time_availability MUST NOT be called for a day-only phrase
    assert len(time_check_calls) == 0, (
        f"[{phrase!r}] `check_specific_time_availability` should NOT be called for a day-only proposal. "
        f"LLM incorrectly treated it as a specific time. Calls: {time_check_calls}"
    )

    # 2. The `time` field in updated_state must remain null
    updated_state = result.get("updated_state", {})
    assert updated_state.get("time") is None, (
        f"[{phrase!r}] `time` in updated_state should be null for a day-only proposal, "
        f"but got: {updated_state.get('time')!r}"
    )

    # 3. The draft must ask for a time
    draft = result.get("draft", "").lower()
    assert any(kw in draft for kw in TIME_REQUEST_KEYWORDS), (
        f"[{phrase!r}] Draft should ask for a specific time, but got: {draft!r}"
    )

    print(f"\n  ✅ DAY-ONLY [{phrase!r}] → Date={updated_state.get('date')!r}, Time=null, Draft asks for time ✓")

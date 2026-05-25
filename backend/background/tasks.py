"""
background/tasks.py
Long-running asyncio coroutines started during FastAPI lifespan.
Each loop runs indefinitely and is cancelled cleanly on shutdown.
"""
import asyncio

from backend.services.calendar_service import build_master_calendar
from backend.services.social_service import evaluate_proactive_messaging


async def gmail_polling_loop():
    """Background task to poll Gmail for Tier 1 Work events."""
    while True:
        try:
            print("Polling Gmail for Tier 1 events...")
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            print("Gmail polling stopped.")
            break
        except Exception as e:
            print(f"Error in Gmail polling: {e}")
            await asyncio.sleep(60)


async def calendar_polling_loop():
    """Background task to compile the master calendar every 15 minutes."""
    while True:
        try:
            print("Background compiling Master Calendar...")
            await build_master_calendar()
        except Exception as e:
            print(f"Error in calendar polling loop: {e}")
        await asyncio.sleep(900)  # 15 minutes


async def proactive_messaging_loop():
    """Periodically triggers the proactive messaging evaluation (every hour)."""
    while True:
        await evaluate_proactive_messaging()
        await asyncio.sleep(3600)  # 1 hour

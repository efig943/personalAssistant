import asyncio
import os
import sys

# Ensure backend can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import TELEGRAM_BOT_TOKEN
import backend.core.dependencies as deps
from backend.services.social_service import evaluate_proactive_messaging
from telegram.ext import Application

async def main():
    print(f"TELEGRAM_BOT_TOKEN present: {TELEGRAM_BOT_TOKEN != 'MOCK_TOKEN'}")
    
    # Initialize application
    deps.ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    await deps.ptb_application.initialize()
    
    print("Running evaluate_proactive_messaging...")
    try:
        await evaluate_proactive_messaging()
        print("evaluate_proactive_messaging completed successfully!")
    except Exception as e:
        print(f"Exception raised in test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

"""
core/config.py
All environment variable loading and global constants for the application.
"""
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "MOCK_TOKEN")
GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
GOOGLE_CALENDAR_WORK_ID: str = os.getenv("GOOGLE_CALENDAR_WORK_ID", "primary")

"""
core/dependencies.py
Module-level singletons shared across the entire backend.

Usage pattern for the mutable ptb_application reference:
    import backend.core.dependencies as deps
    deps.ptb_application = Application.builder()...build()   # set in lifespan
    deps.ptb_application.bot.send_message(...)               # read everywhere else
"""
from groq import AsyncGroq
from backend.controllers.DataController import DataController
from backend.core.config import GROQ_API_KEY

# Shared data persistence layer
data_controller = DataController(data_dir="data")

# Shared Groq async client
groq_client: AsyncGroq | None = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Mutable PTB Application reference — set during FastAPI lifespan startup,
# then read by telegram/handler.py, api/social.py, and services/social_service.py.
ptb_application = None

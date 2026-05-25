"""
backend/main.py
Application entry point — wires FastAPI, CORSMiddleware, lifespan, and all routers.
All business logic lives in the modules imported below.
"""
import asyncio
import os
import sys

# Ensure the project root is on sys.path so 'backend.*' imports resolve.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telegram.ext import Application, MessageHandler, filters

import backend.core.dependencies as deps
from backend.core.config import TELEGRAM_BOT_TOKEN
from backend.tg.handler import telegram_message_handler
from backend.background.tasks import (
    gmail_polling_loop,
    proactive_messaging_loop,
    calendar_polling_loop,
)
from backend.api.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages startup and graceful shutdown of all backend services."""
    print("Starting backend services...")

    # Initialize PTB Application and register the message handler
    deps.ptb_application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    deps.ptb_application.add_handler(
        MessageHandler(filters.ALL, telegram_message_handler)
    )
    print(f"DEBUG: Handlers currently registered: {deps.ptb_application.handlers}")
    await deps.ptb_application.initialize()
    await deps.ptb_application.start()

    if TELEGRAM_BOT_TOKEN != "MOCK_TOKEN":
        await deps.ptb_application.updater.start_polling()
        print("Telegram bot polling started.")
    else:
        print("Warning: Telegram bot token missing, skipping polling.")

    # Start background asyncio tasks
    gmail_task = asyncio.create_task(gmail_polling_loop())
    proactive_task = asyncio.create_task(proactive_messaging_loop())
    calendar_task = asyncio.create_task(calendar_polling_loop())

    yield

    # ── Graceful shutdown ─────────────────────────────────────────────────────
    print("Shutting down backend services...")
    gmail_task.cancel()
    proactive_task.cancel()
    calendar_task.cancel()

    if deps.ptb_application.updater and deps.ptb_application.updater.running:
        await deps.ptb_application.updater.stop()
    await deps.ptb_application.stop()
    await deps.ptb_application.shutdown()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

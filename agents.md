# Omni-Assistant: Tri-Pillar Project Specification

## 1. Project Overview
A full-stack, event-driven Personal Assistant designed to manage the user's entire life schedule across three distinct pillars: Work (Email/Calendar integration), Personal Habits (Health/Routines), and Social Life (Telegram CRM). 

## 2. The Priority Engine (Hard Constraints)
The system must resolve all scheduling and suggestion conflicts using the following strict hierarchy:
- **Tier 1: Work (Highest Priority).** Ingested from work emails and master calendar. Cannot be moved or overwritten by any other tier.
- **Tier 2: Personal Habits.** Eat, Sleep, and Gym (LIFT/REST) schedules. These act as "Hard Blocks" that protect the user's health. Work can overlap them, but Social cannot.
- **Tier 3: Social Butterfly (Lowest Priority).** Telegram-based relationship management. The agent may ONLY suggest social events in the remaining "white space" left after Tier 1 and Tier 2 are plotted.

## 3. Tech Stack & Environment
- **Runtime:** Python 3.12 (Backend), Node 20 (Frontend).
- **Backend:** FastAPI, python-telegram-bot (v20+ async), Antigravity SDK, Google Workspace APIs (Gmail/Calendar).
- **Frontend:** React, Vite, Tailwind CSS.
- **Data Persistence:** Atomic JSON via `portalocker`.

## 4. The Three Pillars (Operational Workflows)

### Pillar 1: Work (Ingestion & Sync)
- **Email Listener:** The backend periodically polls the user's connected Gmail/Workspace account.
- **Extraction:** Uses agentic extraction to identify meetings, deadlines, or mandatory work events from emails and automatically syncs them to the Master Calendar as Tier 1 blocks.

### Pillar 2: Personal Habits (The Baseline)
- **Routine Mapping:** The system maintains a baseline schedule of sleep, meals, and gym sessions.
- **Nutrition Context:** Tracks the user's physical status (e.g., LIFT vs. REST days, calculating 184g total/46g per meal protein targets on LIFT days).

### Pillar 3: Social Butterfly (Telegram CRM)
- **Two-Way Sync:** Listens to incoming Telegram messages from a hardcoded whitelist of contacts (`contacts_registry.json`).
- **Negotiation:** The agent drafts responses to figure out the "Who, What, Where, When" of a social event, strictly constrained by the availability left by Tier 1 and Tier 2.
- **Drafting:** Queues proposed messages in `conversation_states.json` awaiting user approval.

## 5. UI/UX: The Dashboard Architecture
The React frontend MUST implement a responsive Split-Screen Layout that merges all three pillars:

### Left Panel: The Merged Master Calendar
- **Unified View:** A dynamic calendar (e.g., `react-big-calendar`) defaulting to a Week view.
- **Data Display:** Visually merges and color-codes all three tiers: Work Events (Red/Urgent), Habits/Gym (Blue/Routine), and Social (Green).
- **Context:** Displays daily habit metrics (like the protein goals) alongside the time blocks.

### Right Panel: Telegram Messaging & CRM
- **Contact Sidebar:** Whitelisted friends with status indicators.
- **Chat Canvas:** Displays the real-time 2-way Telegram conversation history.
- **Manual Input:** Allows the user to manually type and send messages directly through the dashboard.

## 6. The Approval Flow (Dashboard UI Popup)
The system must NOT execute social events autonomously. It must use the following UI-driven approval loop:
1. **Trigger:** When the agent finalizes a social draft or successfully negotiates a "Who, What, Where, When", it triggers a state change.
2. **The Popup:** The React UI must display a clear notification popup/modal on the screen stating: **"Approve Social Event"**.
3. **User Action:** The user reviews the drafted message and proposed time inside the modal and clicks "Approve".
4. **Execution:** Upon approval, the backend atomically executes two tasks simultaneously:
   - Dispatches the confirmation text message via the Telegram API.
   - Injects the finalized event into the Google Calendar as a Tier 3 block.

## 7. Integrations & Security Constraints
- **LLM Provider:** Groq API via the `groq` SDK. The default model must be `llama3-70b-8192` or `llama3-8b-8192` for low-latency text drafting.
- **Calendar Deduplication:** Before creating any event, perform a GET request to Google Calendar API to check for existing events within a ±2 hour window. Do not create duplicates.
- **CORS:** FastAPI MUST initialize `CORSMiddleware` configured to allow all origins from `http://localhost:5173`.
- **Event Loops:** Use FastAPI `lifespan` context manager to initialize the PTB application. Do not start separate threads for the event loops (prevents "RuntimeError: Event loop is already running").
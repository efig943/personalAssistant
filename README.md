# 🧠 Life Control Panel & Autonomous Social CRM

> **A proactive AI backend that manages your life calendar, guards your habits, and autonomously maintains your relationships.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20API-F55036?style=flat-square&logo=groq&logoColor=white)](https://groq.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

## Setup Instructions

## 🚀 Installation & Setup

### Prerequisites
* Python 3.10+
* Node.js (v18+)
* Git

### Step 1: Clone & Install Dependencies
First, pull the code and set up your local environments.

```bash
# Clone the repository
git clone [https://github.com/yourusername/social-butterfly.git](https://github.com/yourusername/social-butterfly.git)
cd social-butterfly

# Set up the Python Backend
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

# Set up the React Frontend
cd frontend
npm install
cd ..
Step 2: Environment Variables (.env)
Create a .env file in the root directory and add the following keys:
```bash

Code snippet
GROQ_API_KEY=your_groq_api_key
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
Groq: Get your API key from the Groq Console.

Telegram: * Talk to @BotFather on Telegram to create a bot and get your TELEGRAM_BOT_TOKEN.

Get your TELEGRAM_API_ID and TELEGRAM_API_HASH from my.telegram.org.

Step 3: Google Calendar Integration
The system needs access to your calendar to perform gap-scanning and collision detection.

Create a Project: Go to the Google Cloud Console. Click the project drop-down at the top left and select New Project. Name it Social Butterfly.

Enable the API: In the left sidebar, go to APIs & Services > Library. Search for Google Calendar API and click Enable.

Configure Consent Screen:

Go to APIs & Services > OAuth consent screen.

Choose External and click Create. Fill in the mandatory app name and developer email.

Crucial Step: On the "Test Users" step, click Add Users and add your own Google email address.

Create the Credentials:

Go to APIs & Services > Credentials.

Click + Create Credentials > OAuth client ID.

Select Desktop app (or Web application). Name it and click Create.

Download & Rename: Click the Download JSON button. Rename that file strictly to credentials.json and place it inside the data/ folder in your project directory.

Work Calendar ID: Locate your Work Calendar ID in your Google Calendar settings and ensure the system maps it correctly to avoid booking social events over work blocks.

Step 4: Boot the System
Start both the backend API and the frontend UI. You will need two terminal windows.

Terminal 1 (Backend):

Bash
source venv/bin/activate
uvicorn app.main:app --reload
Terminal 2 (Frontend):

Bash
cd frontend
npm start
Step 5: The "Cold Start" Handshake (Critical)
Because Telegram strictly protects user IDs, you must register your username in the local database before texting the bot. Do NOT press /start in your Telegram app yet.

Open the React UI at http://localhost:3000.

Navigate to the Settings and Goals tabs to configure your life anchors and social quotas.

Navigate to the Contacts tab and add a new contact for yourself. You must enter your exact Telegram @username. Leave the Chat ID field blank.

Click Save & Apply.

Now, open Telegram on your phone, find your bot, and press /start.

The backend will instantly intercept your message, match your @username to the database, silently cache your secure chat_id, and bind your profile to the bot. You are now ready to add your friends to the UI and let the agent take over!



## 🔥 The Problem

Modern life is ruthlessly demanding. Between back-to-back meetings, aggressive deadlines, and the constant pressure to perform, **the things that actually matter quietly slip away.**

- 📉 **Relationships decay.** You haven't texted your college friend in three months. It's not intentional — life just fills the gaps.
- 🏋️ **Habits collapse.** Your gym block gets eaten by a last-minute call. Your sleep schedule drifts. Your protein goals go untracked.
- 🧩 **Coordination is exhausting.** Scheduling a single coffee meetup requires a 15-message thread, two reschedulings, and a calendar invite you forget to send.

The result: busy professionals become social ghosts — not because they don't care, but because **managing a full life manually is cognitively impossible.**

---

## ✅ The Solution

The **Life Control Panel** is an autonomous background AI agent that runs continuously, doing the relationship and schedule management work *for* you.

It does three things simultaneously:

1. 📅 **Reads your weekly goals and master calendar** — understanding what is locked in (Work), what is sacred (Habits), and what is negotiable (Social).
2. 🔍 **Scans for availability gaps** — finding the white space between Tier 1 and Tier 2 blocks where social events *could* safely live.
3. 💬 **Proactively reaches out via Telegram** — sending warm, context-aware messages to your friends to schedule real-world meetups, *but only if you are under your weekly social quota.*

The agent doesn't just draft messages — it **negotiates the Who, What, Where, and When**, queues a finalized proposal, and waits for your one-click approval before dispatching anything or touching your calendar.

---

## 🎬 User Scenarios

### 🌱 Scenario 1: "The Cold Start"

> *You've just added a new contact — Alex — to your whitelist via the React Settings UI.*

The background loop picks up the new entry on its next evaluation cycle. It checks the `conversation_states.json` and finds **zero message history** with Alex. The agent classifies this as a **Cold Start** and instructs the LLM to draft a warm, personalized introductory message based on your shared interests from `interests.json`.

The draft is surfaced in the **Approval Modal**. You click **Approve**. The message is dispatched to Alex via Telegram. Your friendship is rekindled — with zero manual effort.

---

### ⚡ Scenario 2: "The Circuit Breaker"

> *Your weekly social quota is set to 2 events. It's Wednesday, and the 2nd event just got booked.*

The moment the second social event is injected into your calendar, the **Circuit Breaker** activates. The proactive outreach loop evaluates your approved event count for the week, finds it equals your quota, and **immediately halts all outgoing message drafts** until the following Monday.

No more pings. No more proposals. Your weekend stays yours.

This isn't just a UX nicety — it's a **token-saving optimization** that prevents the LLM from doing expensive reasoning work when the answer is already known: *you're full*.

---

### 🏋️ Scenario 3: "The Habit Anchor"

> *You update your wake-up time from 6:00 AM to 7:30 AM via the Settings UI.*

The backend's `PUT /api/settings/goals` endpoint receives the update and performs a **deep-merge** into `user_goals.json`. The calendar service immediately triggers a **gap-scan** of the current day, locates the next available 45-minute window *after* your updated wake-up time and *before* your first Tier 1 work block, and **re-injects your gym session** into that slot.

Your Tier 2 habit block moves automatically. Your work calendar is untouched. Your health is protected.

---

## 🏗️ Architecture

The system is built on a **modular, Domain-Driven Design (DDD)** with strict separation of concerns.

### Directory Structure

```
personalAssistantAgent/
│
├── backend/                        # Python 3.12 FastAPI Application
│   ├── main.py                     # App entry point: lifespan, CORS, router mounting
│   │
│   ├── api/                        # 🌐 HTTP Route Handlers (Thin Controllers)
│   │   ├── router.py               # Master router — aggregates all sub-routers
│   │   ├── social.py               # Approval flow, draft dispatch, event injection
│   │   ├── calendar.py             # Calendar CRUD, gap-scan trigger endpoints
│   │   ├── crm.py                  # Contact registry management
│   │   └── settings.py             # Life config hot-swap (goals, habits, interests)
│   │
│   ├── services/                   # 🧠 Business Logic (The "Brain")
│   │   ├── social_service.py       # Proactive loop, quota check, draft generation
│   │   ├── calendar_service.py     # Gap detection, event deduplication, tier injection
│   │   └── time_service.py         # Timezone-aware time utilities
│   │
│   ├── tg/                         # 📨 Telegram I/O Layer
│   │   └── handler.py              # PTB webhook handler, Caller ID cache lookup
│   │
│   ├── tools/                      # 🔧 LLM Tool Definitions
│   │   └── agent_tools.py          # Tool schemas for Groq function-calling (2-pass)
│   │
│   ├── background/                 # ⏱️ Async Background Tasks
│   │   └── tasks.py                # Hourly evaluation loop, circuit breaker logic
│   │
│   ├── core/                       # ⚙️ Cross-Cutting Infrastructure
│   │   ├── config.py               # Pydantic Settings — env vars, API keys
│   │   ├── utils.py                # Shared helpers, safe JSON loading
│   │   └── dependencies.py         # FastAPI dependency injectors
│   │
│   ├── models/                     # 📐 Data Contracts
│   │   └── schemas.py              # Pydantic request/response models
│   │
│   ├── controllers/
│   │   └── DataController.py       # Atomic JSON read/write via portalocker
│   │
│   └── data/                       # 🗄️ JSON File Databases
│       ├── contacts_registry.json          # Whitelisted Telegram contacts
│       ├── conversation_states.json        # Per-contact draft & negotiation state
│       ├── message_history.json            # Full Telegram message log
│       ├── approved_social_events.json     # Finalized events (post-approval)
│       ├── user_goals.json                 # Weekly quotas, wake-up time, targets
│       ├── interests.json                  # User interest graph for warm messaging
│       ├── compiled_master_calendar.json   # Merged Tier 1+2+3 calendar view
│       └── telegram_user_cache.json        # Caller ID cache: username → chat_id
│
└── frontend/                       # Node 20 React Application
    ├── src/
    │   ├── components/
    │   │   ├── Calendar.jsx         # react-big-calendar week view, color-coded tiers
    │   │   ├── TelegramPanel.jsx    # Real-time chat canvas + CRM sidebar
    │   │   ├── ApprovalModal.jsx    # "Approve Social Event" popup with draft preview
    │   │   └── SettingsModal.jsx    # React Settings UI for hot-swapping life configs
    │   └── App.jsx                  # Split-screen layout orchestrator
    ├── vite.config.js
    └── tailwind.config.js
```

---

### The 3-Tier Priority Engine

The system's core invariant is a **strict scheduling hierarchy**. All conflicts are resolved deterministically:

| Tier | Domain | Color | Rule |
|------|--------|-------|------|
| 🔴 **Tier 1** | Work (Email/Calendar) | Red | **Immovable.** Cannot be overwritten by any other tier. |
| 🔵 **Tier 2** | Personal Habits (Sleep/Gym/Meals) | Blue | **Hard Blocks.** Work can overlap; Social cannot. |
| 🟢 **Tier 3** | Social Life (Telegram CRM) | Green | **White Space only.** Fills gaps left by Tier 1 & 2. |

---

### LLM Routing

Two models are used in a **2-pass architecture** to balance intelligence and speed:

```
Pass 1 → llama-3.3-70b-versatile   (Reasoning: calendar analysis, social context)
Pass 2 → llama-3.1-8b-instant      (Tool Worker: JSON draft generation, function calls)
```

This keeps latency low for tool execution while reserving the heavyweight model for nuanced social reasoning.

---

### Telegram Caller ID Caching

A common friction point with Telegram bots is linking a *username* (what you store in your contacts list) to a *chat_id* (what the API needs to send a message). Manual lookup is insecure and brittle.

Our solution: **passive Caller ID caching**.

```
User sends ANY message to the bot
         ↓
tg/handler.py intercepts the update
         ↓
Extracts username + chat_id from the update payload
         ↓
Writes to telegram_user_cache.json atomically
         ↓
All future outgoing messages resolve chat_id from cache
```

No manual lookup. No hardcoded IDs. The system self-populates as contacts naturally interact.

---

### The Approval Flow

The agent **never acts autonomously** on social events. Every outgoing action passes through the UI-driven approval loop:

```
Agent drafts message & proposes time slot
            ↓
Draft queued in conversation_states.json
            ↓
React UI detects pending draft → fires ApprovalModal
            ↓
User reviews "Who, What, Where, When" → clicks APPROVE
            ↓
         ┌──┴──┐
         ↓     ↓
  Send Telegram    Inject event into
    message via     Google Calendar
    Bot API         as Tier 3 block
```

Both actions execute **atomically on approval** — the calendar and the message are always in sync.

---

## 🚀 The Ultimate Scalability Vision: Bot-to-Bot Scheduling

Today, the agent negotiates social events *with humans* over Telegram. But the real endgame is a world where **agents negotiate directly with each other.**

Imagine this:

> My agent knows I have **1 social slot left this week** and I want to grab coffee with a friend.
> Your agent knows **you're free Thursday at 10 AM**.
>
> Instead of a 10-message back-and-forth between us, our bots perform a **secure API handshake**:
>
> ```
> My Agent  →  POST /api/negotiate  →  Your Agent
>              { "event": "coffee", "slots": ["Thu 10AM", "Thu 2PM"] }
>
> Your Agent →  200 OK  →  My Agent
>              { "confirmed_slot": "Thu 10AM", "location": "Blue Bottle, SoMa" }
>
> My Agent   →  injects event → My Google Calendar
> Your Agent →  injects event → Your Google Calendar
> ```
>
> **The coffee meeting is booked. Neither of us typed a single word.**

This is not science fiction. It is the natural extension of the protocol already built here. When this system becomes ubiquitous, human social coordination overhead drops to **zero**.

---

## ✨ Features (Current State)

| Feature | Description |
|---------|-------------|
| 🎛️ **React Settings Modal** | Hot-swap life configs (goals, contacts, interests) without restarting the backend. Deep-merge PUT endpoints ensure partial updates never corrupt state. |
| 🔄 **Decoupled Proactive Loop** | The hourly evaluation loop runs as an async background task, fully decoupled from the API layer. The UI can trigger immediate re-evaluation via `POST /api/social/trigger`. |
| 📲 **Telegram Caller ID Caching** | Passive auto-linking of Telegram usernames to chat IDs. Self-populating on first message received. Zero manual config required. |
| ⚡ **Quota Circuit Breakers** | When the weekly social quota is reached, the entire proactive reasoning pipeline is bypassed. No LLM calls are made. Protects token budget and the user's peace. |
| ✅ **UI Approval Flow** | All agent-drafted social events surface in a React modal awaiting explicit user approval before any Telegram message is dispatched or calendar event is created. |
| 🗂️ **Modular FastAPI Architecture** | Full Domain-Driven Design refactor: `api/`, `services/`, `tools/`, `background/`, `core/`, `models/`. |

---

## 🗺️ Roadmap

### 🏗️ Infrastructure
- [ ] **PostgreSQL / SQLite migration** — Replace atomic JSON file databases with a proper relational store. Enables concurrent access, complex queries, and enterprise-scale contact lists.
- [ ] **Redis pub/sub** — Replace polling-based UI refresh with real-time WebSocket pushes for instant draft notifications.

### 🤖 AI & Agents
- [ ] **Gemini Live API — Voice Receptionist** — Replace the Telegram text interface with a voice-activated receptionist. The agent picks up incoming calls, negotiates social plans verbally, and transcribes the outcome to the calendar.
- [ ] **Multi-Agent Bot-to-Bot Negotiation Protocol** — Implement the secure handshake API described in the [Scalability Vision](#-the-ultimate-scalability-vision-bot-to-bot-scheduling) above. Standardize the negotiation schema as an open protocol.

### 📊 Observability
- [ ] **LLM Cost Dashboard** — Track Groq API token usage per contact, per week, and surface it in the React UI alongside social metrics.
- [ ] **Relationship Health Score** — Compute a per-contact score based on recency, frequency, and sentiment of interactions. Surface it in the CRM sidebar.

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.12+
- Node 20+
- A [Groq API key](https://console.groq.com/)
- A [Telegram Bot token](https://core.telegram.org/bots#how-do-i-create-a-bot) (via `@BotFather`)
- Google Cloud project with Gmail & Calendar APIs enabled

### Backend Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/personalAssistantAgent.git
cd personalAssistantAgent

# 2. Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Fill in: GROQ_API_KEY, TELEGRAM_BOT_TOKEN, GOOGLE_CLIENT_ID, etc.

# 5. Start the FastAPI backend
cd backend
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
# From the project root
cd frontend
npm install
npm run dev
# Vite serves at http://localhost:5173
```

The React dashboard will be available at **`http://localhost:5173`**.
The FastAPI backend (with auto-generated docs) at **`http://localhost:8000/docs`**.

---

## ⚙️ Configuration

All life configurations are editable live via the **React Settings Modal** or by directly editing the JSON files in `backend/data/`:

| File | Purpose |
|------|---------|
| `user_goals.json` | Weekly social quota, wake-up time, gym schedule, protein targets |
| `contacts_registry.json` | Whitelisted Telegram contacts for CRM tracking |
| `interests.json` | Your interest graph — used to personalize outreach messages |

---

## 🔐 Security Notes

- **Whitelist-only CRM:** The agent will only initiate or respond to conversations with contacts explicitly listed in `contacts_registry.json`. No strangers.
- **Approval gate:** The agent has **no autonomous send capability**. Every outgoing Telegram message requires explicit user approval through the UI modal.
- **Local-first data:** All personal data (calendar events, message history, contact states) lives in your local `data/` directory. Nothing is sent to external servers except the Groq API for LLM inference and the Telegram/Google APIs for I/O.

---

## 🧰 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend Runtime** | Python 3.12 |
| **API Framework** | FastAPI + Uvicorn |
| **Telegram Integration** | python-telegram-bot v22.7 (async) |
| **LLM Provider** | Groq API (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`) |
| **Calendar & Email** | Google Workspace APIs (Gmail + Google Calendar) |
| **Data Persistence** | Atomic JSON via `portalocker` |
| **Frontend Runtime** | Node 20 |
| **UI Framework** | React 18 + Vite |
| **Styling** | Tailwind CSS |
| **Calendar Component** | react-big-calendar |

---

## 📄 License

MIT © 2026. Built with intention. Ship your life.

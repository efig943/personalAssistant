# 🧠 Omni-Assistant

> **A proactive AI backend that manages your life calendar, guards your habits, and autonomously maintains your relationships.**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20API-F55036?style=flat-square&logo=groq&logoColor=white)](https://groq.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?style=flat-square&logo=telegram&logoColor=white)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)

---

## 🔥 The Problem

Modern life is ruthlessly demanding. Between back-to-back meetings, aggressive deadlines, and the constant pressure to perform, **the things that actually matter quietly slip away.**

- 📉 **Relationships decay.** You haven't texted your college friend in three months. It's not intentional — life just fills the gaps.
- 🏋️ **Habits collapse.** Your gym block gets eaten by a last-minute call. Your sleep schedule drifts. Your protein goals go untracked.
- 🧩 **Coordination is exhausting.** Scheduling a single coffee meetup requires a 15-message thread, two reschedulings, and a calendar invite you forget to send.

The result: busy professionals become social ghosts — not because they don't care, but because **managing a full life manually is cognitively impossible.**

---

## ✅ The Solution

The **Omni-Assistant** is an autonomous background AI agent that runs continuously, doing the relationship and schedule management work *for* you.

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
Pass 1 → meta-llama/llama-4-scout-17b-16e-instruct  (Reasoning: calendar analysis, social context)
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

## 🏗️ Infrastructure
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
- A Groq API key
- A Telegram Bot token (via @BotFather)
- Google Cloud project with Gmail & Calendar APIs enabled

## Setup Instructions

```bash
# 1. Clone the repo
git clone https://github.com/your-username/personalAssistantAgent.git
cd personalAssistantAgent
```

Rename .env.example to .env and fill in your API keys
Telegram
1. Open your Telegram app (on your phone or desktop) and search for @BotFather in the search bar.
2. Send a message to @BotFather: /newbot
3. Follow the instructions to create your bot named Social Butterfly.
4. BotFather will give you a **HTTP API token**.
5. Save this token in your `.env` file as `TELEGRAM_BOT_TOKEN=`.
6. Log in to the Telegram Core Portal
7. Open your web browser and go to my.telegram.org.
8. Enter the phone number associated with your Telegram account in the international format (e.g., +12345678900).
9. Click Next.
10. Enter the Confirmation Code
11. Telegram will not send this code via SMS text message. Will send on telegram app
12. Click API development tools
13. Save your API ID and API Hash in your `.env` file as `TELEGRAM_API_ID` and `TELEGRAM_API_HASH`.

Groq
1. Go to https://groq.com/signup and create an account.
2. Copy your API key from the dashboard.
3. Save it in your `.env` file as `GROQ_API_KEY=`.
4. Go to settings, go to organization limits, Add the two models meta-llama/llama-4-scout-17b-16e-instruct and llama-3.1-8b-instant

Google Cloud
1. Go to https://console.cloud.google.com/ and create a project.
2. Enable the Gmail API and Google Calendar API.
3. Download the credentials.json file.
4. Save it in your `.env` file as `GOOGLE_CREDENTIALS_PATH=`.

google-auth-calendar.json (a.k.a crendentials.json)
1. Go to Google Cloud console, Search for redentials, click create credentials, OAuth 2.0 Client ID, Desktop App, Name Personal-assistant
2. Download the json file and rename file to google-auth-calendar.json 
3. Save this file in the backend/data/ folder.
*** When running will need to sign into google on first Run this creates your token.json ***

Google Calendar (work schedule)
1. Connect Google Calendar, rename it work-calendar
2. Click settings and sharing, then click integrate calendar
3. Copy the Calendar ID
4. Save it in your `.env` file as `GOOGLE_CALENDAR_WORK_ID=`.


```
./start
```
Once we start it go to [http://localhost:5173](http://localhost:5173) in your browser. 
Sign into your google account and sync your calendar.
Click the settings button fill out the 
1. Profile & AI: enter your name, social quota,
2. Core Habits: protein goals, meals per day, what time you want to wake up, how many hours you want to sleep
3. Weekly Template: I used this as a place to put daily events such as gym, or sports, but can put any topic that is recurring to your personal habits, for now we can only add one
4. Contacts: IMPORTANT - Put name as any name,(nickname), add the username to your friends account. if you dont have one, you can get one from settings on the phone app, and set it. This must be exact.
5. Interests: Add as many interest you would like, I chose to add 3, this only suggest activities you like, we dont deny events that don't align with your interests though, since we should be open to new things.
Hit save.

Once this is done, go to the Social Butterfly bot and run /start in the chat of telegrams bot that we just created
---

## How to use
After settings are configured, as well as a contact is added, Google calendar service is getting your work calendar, we are calculated personal tasks, and the chat is ready

This dashboard is meant mostly for viewing however, we added human in loop functionality, so that we approvae the tasks and suggested events.

Once contact is added, contact can message and respond to the social butterfly bot, and the messages will be displayed on the dashboard, they can also schedule events with you through the bot checking your master calendar, it can move events around if it is not an anchor event. An anchor event is sleep, and the rest can be configured in the UI. 


**Future implementations**: 
1. Agent - Agent communication = Agent is able to chat to Agent owner by another user who has the same setup 
2. Voice messages = Use Whisper API to transcribe voice messages, and Gemini API to generate voice responses
3. Voice calls = Use Gemini Live to create agent that can answer phone calls for you, and scheulde events if needed 
4. Limit the amount of events scheudled in a week -> currently proactive message is limited by this quota only.
5. More Customization of the UI, and more filters to display events and tasks, 
6. Email scraping Calendar scheudling = Add ability to look at calendar events from emails and auto scheudle them 

**Scalability**: 
This basically keeps someone disciplined, it holds you accountable for your goals and tasks, it reminds you of your goals and tasks, as well as lets you balence life with a friend. Talking with freinds is hard. This can also allow you to be more social with people you care about, since it takes the load off of you to remember things. You can focus more on the tasks at hand than rememebr did I respond to Aran, I should ask him to do something this week, mayb the times he can text is different that yours. we can scale this to work around your life. 


## ⚙️ Configuration

All life configurations are editable live via the **React Settings Modal** or by directly editing the JSON files in `backend/data/`:

| File | Purpose |
|------|---------|
| `user_goals.json` | Weekly social quota, wake-up time, gym schedule, protein targets |
| `contacts_registry.json` | Whitelisted Telegram contacts for CRM tracking |
| `interests.json` | Your interest graph — used to personalize outreach messages |
| `message_history.json` | History of messages received and sent  |
| `compiled_master_calendar.json` | Your combined calendar |
| `approved_social_events.json` | Social events that have been approved and added to the calendar |
| `conversation_states.json` | Tracks current conversation states to resume where left off |


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
| **LLM Provider** | Groq API (`meta-llama/llama-4-scout-17b-16e-instruct`, `llama-3.1-8b-instant`) |
| **Calendar & Email** | Google Workspace APIs (Gmail + Google Calendar) |
| **Data Persistence** | Atomic JSON via `portalocker` |
| **Frontend Runtime** | Node 20 |
| **UI Framework** | React 18 + Vite |
| **Styling** | Tailwind CSS |
| **Calendar Component** | react-big-calendar |

---

# Omni-Assistant Project Architecture

UML architecture diagram mapping out the Frontend, Backend, External APIs, and Storage for the Omni-Assistant project.

## System Architecture

```mermaid
graph TD
    subgraph Frontend [Frontend: Node 20, React, Vite, Tailwind]
        Dash[Dashboard]
        Dash --> LeftPanel[Left Panel: Unified Master Calendar]
        Dash --> RightPanel[Right Panel: Telegram CRM]
        RightPanel --> ChatCanvas[Chat Canvas & Contact Sidebar]
        Dash --> ApprovalModal[Approval Modal Popup]
    end

    subgraph Backend [Backend: Python 3.12, FastAPI]
        API[FastAPI Lifespan]
        Priority[Priority Engine]
        EmailSync[Email Listener & Agentic Extractor]
        TGBot[Telegram Poller - PTB v20+ async]
        LLM[Groq LLM Client - Llama3]
        
        API --> Priority
        Priority --> T1[Tier 1: Work - Highest]
        Priority --> T2[Tier 2: Habits - Hard Blocks]
        Priority --> T3[Tier 3: Social - White Space]
    end
    
    subgraph External_APIs [External Services]
        GoogleCal[Google Calendar API]
        Gmail[Gmail API]
        Telegram[Telegram API]
        GroqAPI[Groq LLM API]
    end

    subgraph Storage [Data Persistence]
        DB[(Atomic JSON w/ portalocker)]
        Contacts[contacts_registry.json]
        ConvState[conversation_states.json]
        DB --- Contacts
        DB --- ConvState
    end

    %% Interactions
    LeftPanel -.-> |Fetches unified calendar| API
    RightPanel -.-> |Reads/Writes chats| API
    ApprovalModal -.-> |Approves social event draft| API

    EmailSync --> |Polls emails| Gmail
    EmailSync --> |Syncs T1 events| GoogleCal
    
    TGBot <--> |2-way sync| Telegram
    TGBot --> |Drafts context-aware responses| LLM
    LLM -.-> GroqAPI
    
    TGBot --> |Calculates availability| Priority
    Priority --> |Fetches existing events| GoogleCal
    
    API <--> |Persists state| DB
```

## Social Event Approval Flow

This sequence diagram illustrates the required UI-driven approval loop for Tier 3 Social Events, highlighting the strict constraints mentioned in the rules.

```mermaid
sequenceDiagram
    participant User as User (React UI)
    participant Backend as FastAPI Backend
    participant LLM as Groq LLM (Llama3)
    participant TG as Telegram API
    participant Calendar as Google Calendar API

    Note over Backend, TG: Background Listening
    TG-->>Backend: Incoming message from whitelisted contact
    Backend->>Calendar: GET request (±2 hour window check)
    Backend->>Backend: Priority Engine validates T1 & T2 constraints
    Backend->>LLM: Drafts negotiation reply / event proposal
    LLM-->>Backend: Proposed text & time
    Backend->>Backend: Queues draft in conversation_states.json
    
    Note over User, Backend: UI Interaction
    Backend-->>User: State change triggers "Approve Social Event" popup
    User->>User: Reviews drafted message & proposed time
    User->>Backend: Clicks "Approve"
    
    Note over Backend, Calendar: Atomic Execution
    par Send Message
        Backend->>TG: Dispatches text message
    and Inject Calendar Block
        Backend->>Calendar: Injects event as Tier 3 block
    end
```

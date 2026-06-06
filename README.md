# AI Customer Support & Ticket Routing Agent

An AI-powered customer support workflow that automatically classifies, prioritizes, and routes incoming support tickets using OpenAI's GPT-4o-mini.

## Project Overview

Customer support teams spend significant time manually triaging tickets before they reach the right person. This system automates that entire intake pipeline: it receives a support request via REST API, enriches it with the customer's account data, uses an LLM to classify the issue and draft a response, routes the ticket to the correct team, and returns a structured result — all in a single synchronous API call.

## Features

- **AI Classification** — Categorizes each ticket into Billing, Technical, Account Access, Feature Request, or General Inquiry
- **Priority Detection** — Assigns High, Medium, or Low priority based on the message content and customer plan
- **Response Drafting** — Generates a professional reply draft ready for a human agent to review and send
- **Smart Routing** — Deterministically maps each category to the correct internal team
- **Customer Enrichment** — Looks up customer plan and status to inform the AI analysis
- **Persistent Storage** — All tickets and analyses are stored in SQLite via SQLAlchemy
- **Structured Notifications** — Logs a formatted alert to stdout for every new ticket
- **Robust JSON Parsing** — Handles markdown-wrapped and prose-embedded AI responses gracefully

## Architecture

```
Customer Request
       ↓
FastAPI Endpoint  (POST /tickets)
       ↓
Input Validation  (Pydantic)
       ↓
SQLite Storage    (SQLAlchemy)
       ↓
Customer Lookup   (mock customer database)
       ↓
OpenAI Analysis   (gpt-4o-mini)
       ↓
Ticket Routing    (deterministic category → team mapping)
       ↓
Notification      (stdout log)
       ↓
Structured JSON Response
```

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Database ORM | SQLAlchemy 2.0 |
| Database | SQLite |
| AI model | OpenAI gpt-4o-mini |
| Data validation | Pydantic v2 |
| Testing | Pytest |
| Config | python-dotenv |

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd customer-support-agent
```

### 2. Create and activate a virtual environment

```bash
# macOS / Linux
python -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-...
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key from platform.openai.com |

## Running the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at **http://127.0.0.1:8000**

Interactive API docs (Swagger UI): **http://127.0.0.1:8000/docs**

## Running Tests

Tests do not require an OpenAI API key — the AI service is mocked automatically.

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

## API Reference

### Health Check

```
GET /health
```

```json
{"status": "ok"}
```

---

### Create Ticket

```
POST /tickets
Content-Type: application/json
```

**Request body:**

```json
{
  "customer_name": "John Smith",
  "email": "john@example.com",
  "message": "I was charged twice this month."
}
```

**Response:**

```json
{
  "ticket_id": 1,
  "category": "Billing",
  "priority": "High",
  "assigned_team": "Billing Team",
  "summary": "Customer reports a duplicate charge on their account.",
  "suggested_response": "Thank you for reaching out. We have escalated this billing discrepancy to our Billing Team and will resolve it within 24 hours."
}
```

**Error responses:**

| Status | Cause |
|---|---|
| `422 Unprocessable Entity` | Missing or invalid request fields |
| `502 Bad Gateway` | OpenAI service unavailable or API key missing |

---

### Get All Tickets

```
GET /tickets
```

Returns all tickets with their associated analysis, ordered newest first.

---

### Get Ticket by ID

```
GET /tickets/{id}
```

**Response:**

```json
{
  "id": 1,
  "customer_name": "John Smith",
  "email": "john@example.com",
  "message": "I was charged twice this month.",
  "created_at": "2026-06-06T10:00:00",
  "analysis": {
    "id": 1,
    "ticket_id": 1,
    "category": "Billing",
    "priority": "High",
    "summary": "Customer reports a duplicate charge on their account.",
    "suggested_response": "Thank you for reaching out...",
    "assigned_team": "Billing Team",
    "created_at": "2026-06-06T10:00:00"
  }
}
```

**Error:** `404 Not Found` if the ticket does not exist.

---

### Customer Lookup (built-in test accounts)

Two mock accounts are pre-loaded for testing:

| Email | Plan | Status |
|---|---|---|
| `premium@example.com` | Premium | Active |
| `basic@example.com` | Basic | Active |

Any other email resolves to `Unknown / Unknown`.

## Project Structure

```
app/
├── main.py                         # FastAPI app entry point
├── database.py                     # SQLAlchemy engine, session, Base
├── models/
│   ├── ticket.py                   # Ticket ORM model
│   └── analysis.py                 # TicketAnalysis ORM model
├── schemas/
│   ├── ticket.py                   # Request / response Pydantic schemas
│   └── analysis.py                 # Analysis Pydantic schema
├── routes/
│   └── tickets.py                  # All API endpoints
├── services/
│   ├── ai_service.py               # OpenAI integration and JSON parsing
│   ├── routing_service.py          # Category → team routing
│   ├── notification_service.py     # Ticket alert output
│   └── customer_lookup_service.py  # Customer data enrichment
└── utils/                          # Reserved for shared utilities

tests/
├── conftest.py                     # Shared fixtures (in-memory DB, test client)
├── test_routes.py                  # Endpoint integration tests
├── test_routing.py                 # Routing logic unit tests
└── test_ai_parser.py               # AI response parser unit tests
```

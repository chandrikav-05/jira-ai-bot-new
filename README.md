# Jira AI Bot

AI-powered Jira ticket creation via chat and document upload.

---

## What This Does

* User types a task in plain English → AI generates full Jira ticket → User confirms → Ticket created
* User uploads a PDF / Word / TXT document → AI extracts all tasks → User selects which to create → Tickets created

---

## Tech Stack

* Frontend  : HTML + CSS + JavaScript
* Backend   : FastAPI (Python)
* AI Model  : GPT-4o-mini (OpenAI)
* Jira      : jira Python library + REST API
* Doc Parse : PyMuPDF (PDF), python-docx (Word), built-in (TXT)

---

## Project Structure

```
jira-ai-bot/
├── frontend/
│   └── index.html              ← Chatbot UI
├── backend/
│   ├── main.py                 ← FastAPI app + all endpoints
│   ├── ai_service.py           ← GPT-4o-mini calls
│   ├── jira_service.py         ← Jira create operations
│   ├── document_parser.py      ← PDF / DOCX / TXT text extraction
│   ├── models.py               ← Pydantic request/response models
│   └── config.py               ← Load .env variables
├── .env                        ← Your API keys (never commit this)
├── .env.example                ← Template for .env
├── requirements.txt            ← Python dependencies
└── README.md
```

---

## Setup — Step by Step

### Step 1 — Clone or download the project

Place all files in a folder called `jira-ai-bot` on your machine.

### Step 2 — Create your .env file

Copy `.env.example` to `.env` and fill in your details:

```
OPENAI_API_KEY=sk-your-openai-key-here
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token-here
DEFAULT_PROJECT_KEY=AP
```

How to get each value:

* OPENAI_API_KEY    → https://platform.openai.com/api-keys
* JIRA_URL          → Your Jira URL from the browser address bar
* JIRA_EMAIL        → The email you use to log in to Jira
* JIRA_API_TOKEN    → https://id.atlassian.com/manage-profile/security/api-tokens
* DEFAULT_PROJECT_KEY → Your Jira project key e.g. AP (visible in any ticket number like AP-101)

### Step 3 — Create a Python virtual environment

```bash
cd jira-ai-bot
python -m venv venv
```

Activate it:

* Mac / Linux : source venv/bin/activate
* Windows     : venv\Scripts\activate

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Run the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

You will see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 6 — Open the chatbot

Open your browser and go to:

```
http://127.0.0.1:8000
```

The chatbot will load automatically.

---

## API Endpoints

| Method | Endpoint                 | What it does                                      |
| ------ | ------------------------ | ------------------------------------------------- |
| POST   | /generate-ticket         | Takes user text, returns AI-generated ticket      |
| POST   | /update-preview          | Takes ticket + feedback, returns updated ticket   |
| POST   | /create-ticket           | Creates single confirmed ticket in Jira           |
| POST   | /upload-document         | Reads document, returns list of extracted tickets |
| POST   | /create-selected-tickets | Creates multiple selected tickets in Jira         |
| GET    | /health                  | Health check                                      |

---

## How to Use

### Option 1 — Type your ticket

1. Type your task in plain English in the chat box
2. AI generates summary, description, and all fields
3. Review the preview
4. Say Yes to create or tell the bot what to change
5. Ticket is created in Jira — bot shows ticket ID

### Option 2 — Upload a document

1. Click the upload area or drag and drop a PDF / DOCX / TXT file
2. AI reads the document and extracts all tasks as tickets
3. Review the list — uncheck any you don't want
4. Click Create Selected Tickets
5. All selected tickets are created in Jira

---

## Deployment (When Ready for Team Use)

### Option A — Simple server deployment

1. Upload the project to any Linux server or cloud VM
2. Run: uvicorn main:app --host 0.0.0.0 --port 8000
3. Share the server IP with your team: http://your-server-ip:8000

### Option B — Deploy to Railway / Render (Free hosting)

1. Push the project to GitHub
2. Connect the repo to Railway (https://railway.app) or Render (https://render.com)
3. Set the environment variables in the dashboard
4. Deploy — you get a public URL to share with your team

---

## Important Notes

* Reporter: In Jira Cloud, the reporter is always the API token owner. This cannot be changed via API.
* Assignee: The email must be the exact Jira login email. If not found, ticket will be unassigned.
* OpenAI cost: GPT-4o-mini is very cost effective — approximately $0.001 per ticket or less.
* The .env file must never be committed to Git. It is already in .gitignore.

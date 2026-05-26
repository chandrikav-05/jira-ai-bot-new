import json
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, DEFAULT_PROJECT_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

TICKET_SCHEMA = """
{
  "project_key":    "string — Jira project key e.g. AP. Use default if not mentioned.",
  "summary":        "string — short clear title for the ticket",
  "description":    "string — detailed, professional description. Use markdown (bullet points, bolding) where appropriate. DO NOT mention parent ticket IDs (e.g. AP-123) in this field.",
  "issue_type":     "string — one of: Task, Bug, Story, Epic, Subtask",
  "priority":       "string — one of: High, Medium, Low",
  "reporter_email": "string — email of person requesting the ticket, empty if not mentioned",
  "assignee_email": "string — email of person doing the work, empty if not mentioned",
  "start_date":     "string — DD-MM-YYYY format, use today's date if not mentioned",
  "due_date":       "string — DD-MM-YYYY format, empty if not mentioned",
  "epic_link":      "string — epic ticket number e.g. AP-10, empty if not mentioned",
  "parent_task":    "string — parent ticket number for sub-tasks only, empty if not mentioned",
  "temp_id":        "string — a unique internal ID for this ticket (e.g. T1, T2) to establish hierarchy",
  "temp_parent_id": "string — the temp_id of the parent ticket (Epic or Task) if it is also being created from this document"
}
"""


def generate_ticket_from_text(user_text: str) -> dict:
    """
    Takes user's free text input and generates a full Jira ticket using GPT-4o-mini.
    Returns a single ticket dict.
    """
    prompt = f"""
You are a Jira ticket creation assistant. The user will describe a task in plain English.
Your job is to extract all relevant information and generate a complete Jira ticket.

Default project key if not mentioned: {DEFAULT_PROJECT_KEY}
Today's date: {datetime.now().strftime("%A, %d %B %Y")}

Return ONLY a valid JSON object with exactly these fields:
{TICKET_SCHEMA}

Rules:
- Generate a professional, clear summary (not more than 10 words)
- Generate a comprehensive, professional description based on the user's input. 
- If the user asks for bullet points, expansion, or specific additions, implement them clearly in the description.
- NEVER include the parent ticket number or epic ID (e.g., AP-115) in the "description" field; keep it strictly for the task details.
- Detect issue type from context: words like "fix", "crash", "error" = Bug; "build", "create", "implement" = Task or Story; "document", "write" = Task; if "under" or "child of" an EPIC is mentioned, use Task; if "under" or "child of" a TASK is mentioned, use Subtask
- Detect priority from urgency words: "urgent", "ASAP", "critical", "high" = High; "low", "minor", "whenever" = Low; else = Medium
- Extract emails exactly as mentioned
- Convert date references like "15th May", "next Friday", "end of month" to DD-MM-YYYY format using current year 2026
- If "under" or "parent" is mentioned followed by a ticket ID (e.g., AP-123):
    - If the parent is an Epic, put the ID in "epic_link" and set issue_type to "Task"
    - If the parent is a Task/Story, put the ID in "parent_task" and set issue_type to "Subtask"
- If "start_date" is not mentioned, use today's date in DD-MM-YYYY format.
- Return empty string for any other field not mentioned.

User input:
{user_text}

Return ONLY valid JSON. No explanation. No markdown. No extra text.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    return json.loads(response.choices[0].message.content)


def apply_changes_to_ticket(current_ticket: dict, feedback: str) -> dict:
    """
    Takes the current ticket data and user feedback,
    returns the updated ticket with changes applied.
    """
    prompt = f"""
You are a Jira ticket editor. The user wants to make changes to an existing ticket preview.

Current ticket:
{json.dumps(current_ticket, indent=2)}

User feedback (what they want to change):
{feedback}

Today's date: {datetime.now().strftime("%A, %d %B %Y")}

Rules:
- Apply the changes the user requested (e.g., expand the description, convert to bullet points, add specific details, or modify any other field).
- Maintain a high-quality, professional tone.
- NEVER include parent ticket IDs or epic IDs in the "description" field.
- Keep all fields that were not mentioned in the feedback exactly the same.

Return ONLY valid JSON. No explanation. No markdown.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3
    )
    return json.loads(response.choices[0].message.content)


def extract_tickets_from_document(document_text: str) -> list:
    """
    Reads the full document text and extracts multiple Jira tickets from it.
    Returns a list of ticket dicts.
    """
    prompt = f"""
You are a Jira project manager assistant. You will be given a document — it could be a 
project requirement document, meeting notes, a feature spec, or any project related text.

Your job is to:
1. Read the entire document carefully
2. Identify ALL distinct tasks, features, bugs, stories, or work items mentioned
3. Generate a separate Jira ticket for each one

Default project key: {DEFAULT_PROJECT_KEY}
Today's date: {datetime.now().strftime("%A, %d %B %Y")}

Return ONLY a valid JSON object in this exact format:
{{
  "tickets": [
    {TICKET_SCHEMA},
    ...
  ]
}}

Rules:
- Extract as many tickets as you find — do not miss any task or work item
- Each ticket must have a unique, specific summary
- Write detailed, professional descriptions for each ticket. Use markdown formatting (like bullet points) if it improves clarity.
- NEVER include parent ticket numbers or IDs in the "description" field.
- Detect issue type from context for each ticket. Prefer "Task" for items under an Epic, and "Subtask" for items under a Task.
- Set priority based on context clues in the document
- If the document mentions assignees or dates, extract them
- Use "temp_id" and "temp_parent_id" to represent the hierarchy within the document.
    - Example: If an Epic has a Task, and that Task has a Subtask:
      - Epic: temp_id="E1", temp_parent_id=""
      - Task: temp_id="T1", temp_parent_id="E1"
      - Subtask: temp_id="S1", temp_parent_id="T1"
- If a ticket already belongs to an existing Jira ticket (e.g. "under AP-123"), use "epic_link" or "parent_task" instead.
- If "start_date" is not mentioned, use today's date in DD-MM-YYYY format.
- If not mentioned, leave other fields as empty string.
- Do not create duplicate tickets

Document content:
{document_text}

Return ONLY valid JSON. No explanation. No markdown. No extra text.
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=4000
    )
    result = json.loads(response.choices[0].message.content)
    return result.get("tickets", [])
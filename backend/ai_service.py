import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from config import OPENAI_API_KEY, DEFAULT_PROJECT_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

TICKET_SCHEMA = """
{
  "project_key":    "string — Jira project key e.g. AP. Use default if not mentioned.",
  "summary":        "string — short clear title for the ticket",
  "description":    "string — a brief 1-sentence draft of the task details (this will be fully expanded later). DO NOT mention parent ticket IDs (e.g. AP-123) in this field.",
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


def generate_rich_description(summary: str, issue_type: str, context: str) -> str:
    """
    Generates a highly structured, professional description based on the issue type
    and the user's provided explanation/context.
    """
    issue_type_lower = issue_type.lower()
    
    # Custom template per issue type
    if issue_type_lower == "epic":
        template_instruction = """
Generate a clean, structured description for a Jira EPIC using this exact layout:
**Overview**
[Brief overview of the Epic and what it accomplishes]

**Business Goal**
- [Goal 1]
- [Goal 2]

**In Scope**
- [Scope item 1]
- [Scope item 2]

**Out of Scope**
- [Out of scope item 1 or "N/A" if none]
"""
    elif issue_type_lower == "bug":
        template_instruction = """
Generate a clean, structured description for a Jira BUG using this exact layout:
**Overview**
[Short summary of the bug and its impact]

**Steps to Reproduce**
1. [Step 1]
2. [Step 2]

**Expected Behavior**
[What should have happened]

**Actual Behavior**
[What actually happened/error message]

**Environment**
- [Browser/OS details if mentioned, otherwise "N/A"]
"""
    elif issue_type_lower in ["story", "task"]:
        template_instruction = """
Generate a clean, structured description for a Jira STORY/TASK using this exact layout:
**User Story**
As a [User Role / Persona],
I want to [Action / Feature],
So that [Benefit / Goal].

**Acceptance Criteria**
- [Criteria 1]
- [Criteria 2]

**Technical / Implementation Details**
- [Detail 1]
- [Detail 2]
"""
    else:  # Subtask or default
        template_instruction = """
Generate a clean, structured description for a Jira SUBTASK using this exact layout:
**Goal**
[Clear technical objective of this subtask]

**Checklist / Tasks**
- [Task 1]
- [Task 2]
"""

    prompt = f"""
You are a Jira expert writing a highly professional, detailed ticket description.
You are given:
- Issue Type: {issue_type}
- Ticket Summary: {summary}
- Context/Explanation:
{context}

Please write the description for this ticket following this structural template:
{template_instruction}

Guidelines:
1. Ensure the description is completely professional and detailed, corresponding ONLY to the given Ticket Summary: "{summary}".
2. Do NOT describe or include requirements/scope for other tasks, epics, or features mentioned in the Context/Explanation, unless they are directly relevant context or dependencies for "{summary}". The User Story, Acceptance Criteria, and Technical Details MUST be entirely specific to "{summary}".
3. If some sections in the template are not mentioned or cannot be inferred from the context specifically for "{summary}", write a reasonable, professional placeholder/draft or state "TBD".
4. Use bold text for headings (e.g., **User Story**, **Acceptance Criteria**). Do NOT use # headers. Use - for bullet points, and do NOT use brackets like [ ] or checkboxes in acceptance criteria or tasks.
5. NEVER include any parent ticket IDs (e.g., AP-123) in the description text itself.
6. Return ONLY the description. Do not wrap in ```markdown blocks, and do not add any intro or outro text.
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI Service] Error generating description: {e}")
        return f"Draft description for {summary}. Details:\n{context}"


def generate_ticket_from_text(user_text: str) -> dict:
    """
    Takes user's free text input, determines if it is a greeting/general inquiry,
    a single Jira ticket request, or a request to create multiple tickets (e.g., an Epic with child tasks,
    or a list of multiple distinct tasks).
    Returns a dict with keys: is_greeting, greeting_message, is_multi_ticket, ticket, tickets.
    """
    prompt = f"""
You are a Jira ticket creation assistant.
First, analyze the user's input.
Determine if the user's input is:
1. A greeting (e.g., "hi", "hello", "hey", "good morning"), a general question/pleasantry (e.g., "how are you", "what's up", "who are you"), or a general question about your capabilities (e.g., "what can you do?", "help", "how does this work").
2. A request that describes MULTIPLE tasks, a project plan, or an Epic with sub-tasks/linked tasks.
3. A single task, bug, story, or ticket request.

If the input is a greeting, pleasantry, or capability question:
- Set "is_greeting" to true.
- Set "greeting_message" to a personalized, natural, and friendly response that directly answers the user's specific greeting, pleasantry, or question. For example:
  - If they say "hi" or "hello", greet them back warmly and ask how you can help them.
  - If they ask "how are you", reply politely (e.g., "I'm doing great, thank you! Ready to help you with some Jira tickets.") and ask how they are doing.
  - If they ask "who are you" or "what can you do", explain clearly and conversationally that you are a Jira AI Assistant here to help them create single tickets, extract multiple tickets from documents, or modify ticket details.
  Make sure each response feels conversational, directly addresses their input, and is not a static/repetitive copy-paste response.
- Set "is_multi_ticket" to false.
- Set "ticket" to null.
- Set "tickets" to null.

If the input describes MULTIPLE distinct tasks, an Epic with child tasks, or a set of different tasks to be created:
- Set "is_greeting" to false.
- Set "greeting_message" to "".
- Set "is_multi_ticket" to true.
- Set "ticket" to null.
- Set "tickets" to an array of ticket objects representing all the tasks/epics to be created.
- Establish the hierarchy using "temp_id" and "temp_parent_id".
  For example, if an Epic has tasks:
    - Epic ticket: temp_id="E1", temp_parent_id=""
    - Task 1: temp_id="T1", temp_parent_id="E1"
    - Task 2: temp_id="T2", temp_parent_id="E1"

If the input describes a SINGLE task, bug, story, epic, or ticket request:
- Set "is_greeting" to false.
- Set "greeting_message" to "".
- Set "is_multi_ticket" to false.
- Set "ticket" to a single ticket object.
- Set "tickets" to null.

Ticket Generation Rules (apply to both "ticket" and items in "tickets"):
Default project key if not mentioned: {DEFAULT_PROJECT_KEY}
Today's date: {datetime.now().strftime("%A, %d %B %Y")}
Ticket Schema:
{TICKET_SCHEMA}

Rules for Ticket Generation:
- Generate a professional, clear summary (not more than 10 words).
- The summary must represent the feature, bug, or topic itself, NOT the action or request phrase (do NOT prefix with "Create epic for", "Create task for", "Create", "Implement", "Build", "Add", "create an epic", etc.).
- If the user provides a title/name in quotes (e.g., "Testing Document-Reader" or "Zoho crm Existing customer checking chatbot"), use the exact content inside the quotes as the summary.
- Do NOT include the issue type name (like "Epic", "Task", "Subtask", "Story", "Bug") inside the summary itself.
- Generate a brief 1-sentence draft of the description. This will be fully expanded in a separate step.
- NEVER include the parent ticket number or epic ID (e.g., AP-115) in the "description" field; keep it strictly for the task details.
- Detect issue type from context: words like "fix", "crash", "error" = Bug; "build", "create", "implement" = Task or Story; "document", "write" = Task; if "under" or "child of" an EPIC is mentioned, use Task; if "under" or "child of" a TASK is mentioned, use Subtask. If an Epic is explicitly requested, use Epic.
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
    result = json.loads(response.choices[0].message.content)

    # If it is a greeting, return immediately
    if result.get("is_greeting", False):
        return result

    # Otherwise, enrich descriptions in a second step
    if result.get("is_multi_ticket", False) and result.get("tickets"):
        tickets = result["tickets"]
        with ThreadPoolExecutor() as executor:
            # Run description generation in parallel
            futures = [
                executor.submit(
                    generate_rich_description,
                    t.get("summary", ""),
                    t.get("issue_type", "Task"),
                    user_text
                )
                for t in tickets
            ]
            for t, future in zip(tickets, futures):
                t["description"] = future.result()
    elif result.get("ticket"):
        ticket = result["ticket"]
        ticket["description"] = generate_rich_description(
            ticket.get("summary", ""),
            ticket.get("issue_type", "Task"),
            user_text
        )

    return result


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
- If modifying the description, ensure all headings are in bold (e.g., **User Story**) rather than using '#' characters, and ensure acceptance criteria or checklists use standard bullet points (- ) without brackets like [ ] or checkboxes.
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
- Provide a brief 1-sentence description placeholder. A detailed, structured description will be generated separately.
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
    tickets = result.get("tickets", [])

    # Enrich descriptions in parallel
    if tickets:
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(
                    generate_rich_description,
                    t.get("summary", ""),
                    t.get("issue_type", "Task"),
                    document_text
                )
                for t in tickets
            ]
            for t, future in zip(tickets, futures):
                t["description"] = future.result()

    return tickets
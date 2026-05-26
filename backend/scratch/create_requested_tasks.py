from jira_service import create_jira_ticket

epic_id = "AP-144"

tasks = [
    {
        "summary": "AI backend logic for automatic email triggering",
        "description": "Implement the AI logic to detect P1 tickets and trigger automated emails with Google Meet links.",
        "issue_type": "Task",
        "due_date": "20-05-2026",
        "epic_link": epic_id
    },
    {
        "summary": "UI/UX design for the frontend",
        "description": "Design the user interface and experience for the P1 ticket management dashboard.",
        "issue_type": "Task",
        "due_date": "17-05-2026",
        "epic_link": epic_id
    },
    {
        "summary": "Frontend code implementation",
        "description": "Implement the frontend components and screens based on the UI/UX designs.",
        "issue_type": "Task",
        "due_date": "25-05-2026",
        "epic_link": epic_id
    },
    {
        "summary": "Backend integration",
        "description": "Integrate the frontend with the AI backend logic and Jira services.",
        "issue_type": "Task",
        "due_date": "30-05-2026", # Corrected from 2025 to 2026 based on context
        "epic_link": epic_id
    }
]

for task in tasks:
    try:
        result = create_jira_ticket(task)
        print(f"Created: {result['ticket_id']} - {result['summary']}")
    except Exception as e:
        print(f"Failed to create '{task['summary']}': {e}")

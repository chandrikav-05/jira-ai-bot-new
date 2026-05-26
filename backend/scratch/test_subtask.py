from jira_service import create_jira_ticket
import json

def test_create_subtask():
    ticket_data = {
        "project_key": "AP",
        "summary": "Signup Button Subtask",
        "description": "Creating one button for the signup where new people can login",
        "issue_type": "Subtask",
        "priority": "Medium",
        "parent_task": "AP-139"
    }
    
    try:
        print("Attempting to create subtask...")
        result = create_jira_ticket(ticket_data)
        print(f"Success! Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_create_subtask()

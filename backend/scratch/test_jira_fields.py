from jira_service import create_jira_ticket
from unittest.mock import MagicMock, patch

def test_jira_creation_fields():
    ticket_data = {
        "project_key": "AP",
        "summary": "Test Start Date",
        "description": "Testing if start date is sent to Jira",
        "issue_type": "Task",
        "priority": "Medium",
        "start_date": "13-05-2026",
        "due_date": "20-05-2026"
    }

    with patch('jira_service.get_jira_client') as mock_get_client:
        mock_jira = MagicMock()
        mock_get_client.return_value = mock_jira
        
        # Mock issue creation to return a key
        mock_jira.create_issue.return_value.key = "AP-999"
        
        result = create_jira_ticket(ticket_data)
        
        # Check if create_issue was called with the correct fields
        args, kwargs = mock_jira.create_issue.call_args
        fields = kwargs['fields']
        
        print(f"Summary: {fields['summary']}")
        print(f"Due Date (duedate): {fields.get('duedate')}")
        print(f"Start Date (customfield_10015): {fields.get('customfield_10015')}")
        
        if fields.get('customfield_10015') == "2026-05-13":
            print("SUCCESS: Start date correctly mapped and formatted!")
        else:
            print(f"FAILURE: Start date was {fields.get('customfield_10015')}")

if __name__ == "__main__":
    test_jira_creation_fields()

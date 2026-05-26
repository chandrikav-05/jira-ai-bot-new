from jira import JIRA
from config import JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN

# Cache account IDs so we don't keep calling Jira API for same email
_account_id_cache = {}


def get_jira_client() -> JIRA:
    return JIRA(server=JIRA_URL, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))


def get_account_id(email: str) -> str | None:
    """Convert email address to Jira Account ID. Jira Cloud requires Account ID."""
    if not email or not email.strip():
        return None

    email = email.strip().lower()

    if email in _account_id_cache:
        return _account_id_cache[email]

    try:
        jira  = get_jira_client()
        users = jira.search_users(query=email)
        for user in users:
            if hasattr(user, "emailAddress") and user.emailAddress.lower() == email:
                _account_id_cache[email] = user.accountId
                return user.accountId
        _account_id_cache[email] = None
        return None
    except Exception as e:
        print(f"[Jira] Could not find account for email {email}: {e}")
        return None


def format_date_for_jira(date_str: str) -> str | None:
    """Convert DD-MM-YYYY to YYYY-MM-DD which Jira requires."""
    if not date_str or not date_str.strip():
        return None
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str.strip(), "%d-%m-%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def create_jira_ticket(ticket: dict) -> dict:
    """
    Create a single Jira ticket from the ticket dict.
    Returns dict with ticket_id and status.
    """
    jira = get_jira_client()

    project_key = ticket.get("project_key", "AP")
    summary     = ticket.get("summary", "")
    description = ticket.get("description", "")
    issue_type  = ticket.get("issue_type", "Task")
    priority    = ticket.get("priority", "Medium")
    assignee    = ticket.get("assignee_email", "")
    due_date    = format_date_for_jira(ticket.get("due_date", ""))
    start_date  = format_date_for_jira(ticket.get("start_date", ""))
    epic_link   = ticket.get("epic_link", "")
    parent_task = ticket.get("parent_task", "")

    if not summary:
        raise ValueError("Summary is required to create a ticket.")

    # Normalize issue type (especially Sub-task vs Subtask)
    if issue_type.lower() in ["sub-task", "subtask"]:
        issue_type = "Subtask"
    
    # Build issue fields
    issue_fields = {
        "project":   {"key": project_key},
        "summary":   summary,
        "description": description,
        "issuetype": {"name": issue_type},
        "priority":  {"name": priority},
    }

    # Assignee — convert email to account ID
    if assignee:
        account_id = get_account_id(assignee)
        if account_id:
            issue_fields["assignee"] = {"accountId": account_id}
        else:
            print(f"[Jira] Assignee email '{assignee}' not found. Ticket will be unassigned.")

    # Due date
    if due_date:
        issue_fields["duedate"] = due_date
    
    # Start date (customfield_10015)
    if start_date:
        issue_fields["customfield_10015"] = start_date

    # Parent linking (for Subtasks or tasks under Epics)
    # In modern Jira Cloud, 'parent' is the standard field for both subtasks and epic links.
    if parent_task or epic_link:
        parent_key = (parent_task or epic_link).strip()
        issue_fields["parent"] = {"key": parent_key}
        
        # Hierarchy Check & Field Adjustments
        try:
            parent_issue = jira.issue(parent_key)
            parent_type  = parent_issue.fields.issuetype.name.lower()
            
            if parent_type == "epic":
                # If parent is an Epic, and we were going to make a subtask, change it to Task
                if issue_type.lower() == "subtask":
                    issue_type = "Task"
                    issue_fields["issuetype"] = {"name": issue_type}
                
                # In many Jira Cloud projects, 'parent' is sufficient.
                # We removed the hardcoded 'customfield_10014' to avoid errors in Team-managed projects.
                pass
            else:
                # If parent is NOT an Epic (it's a Task/Story/etc), it MUST be a subtask
                if issue_type.lower() != "subtask":
                    issue_type = "Subtask"
                    issue_fields["issuetype"] = {"name": issue_type}
        except Exception as e:
            print(f"[Jira] Could not verify parent {parent_key} type: {e}")

    # Final check: Jira REQUIRES a parent for Subtasks.
    # If we still have Subtask but no parent was provided/found, we must switch to Task
    # to avoid a 400 error.
    if issue_type.lower() == "subtask" and "parent" not in issue_fields:
        print(f"[Jira] No parent provided for Subtask. Falling back to 'Task' type.")
        issue_type = "Task"
        issue_fields["issuetype"] = {"name": issue_type}

    # Create the ticket
    try:
        new_issue = jira.create_issue(fields=issue_fields)
    except Exception as e:
        # Better error reporting for Jira errors
        error_msg = str(e)
        if hasattr(e, 'text'):
            try:
                import json as json_lib
                err_data = json_lib.loads(e.text)
                if 'errors' in err_data:
                    error_msg = "; ".join([f"{k}: {v}" for k, v in err_data['errors'].items()])
                elif 'errorMessages' in err_data and err_data['errorMessages']:
                    error_msg = "; ".join(err_data['errorMessages'])
            except:
                pass
        raise Exception(f"Jira Error: {error_msg}")

    return {
        "ticket_id":  new_issue.key,
        "ticket_url": f"{JIRA_URL.rstrip('/')}/browse/{new_issue.key}",
        "status":     "To Do",
        "summary":   summary,
        "assignee":  assignee or "Unassigned",
    }
from jira_service import get_jira_client

def list_issue_types():
    try:
        jira = get_jira_client()
        project = jira.project("AP")
        issue_types = project.issueTypes
        print("Issue Types for project AP:")
        for it in issue_types:
            print(f"- {it.name} (Subtask: {it.subtask})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_issue_types()

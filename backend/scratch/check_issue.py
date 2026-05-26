from jira_service import get_jira_client
import json

def check_issue(key):
    try:
        jira = get_jira_client()
        issue = jira.issue(key)
        print(f"Key: {issue.key}")
        print(f"Type: {issue.fields.issuetype.name}")
        print(f"Summary: {issue.fields.summary}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_issue("AP-139")

from jira_service import get_jira_client
import json

def check_all_fields():
    try:
        jira = get_jira_client()
        # Search for any field with "Start" in the name
        fields = jira.fields()
        print("Fields containing 'Start':")
        for f in fields:
            if "start" in f['name'].lower():
                print(f"- {f['name']} ({f['id']})")
                
        # Also check for 'Target start' which is common in Jira
        print("\nFields containing 'Target':")
        for f in fields:
            if "target" in f['name'].lower():
                print(f"- {f['name']} ({f['id']})")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_fields()

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_service import generate_ticket_from_text
import json

def test_generation():
    # Prompt 1: Single quoted title
    prompt1 = 'create an epic "Zoho crm Existing customer checking chatbot"'
    print(f"\n--- Testing Prompt 1 (Single) ---")
    try:
        result1 = generate_ticket_from_text(prompt1)
        print(f"Result:\n{json.dumps(result1, indent=2)}")
    except Exception as e:
        print(f"Prompt 1 failed: {e}")

    # Prompt 2: Multi-ticket prompt
    prompt2 = (
        'create on epic with the title "Testing Document-Reader". '
        'In this project will build one ai agent with RAG pipeline where users can upload their pdf,docx,xlsheets and ask questions . '
        'Frontend is also their like chatbot interface and backend integration also there . '
        'Ai backend logic assign to chandrika.v@brilyant.com and frontend task assign to kavya.tn@brilyant.com and backend integration is assign to sangili.boopathi@brilyant.com '
        'due date fro all is 30-05-2026 . all these should consider as different tasks under this epic'
    )
    print(f"\n--- Testing Prompt 2 (Multi) ---")
    try:
        result2 = generate_ticket_from_text(prompt2)
        print(f"Result:\n{json.dumps(result2, indent=2)}")
    except Exception as e:
        print(f"Prompt 2 failed: {e}")

if __name__ == "__main__":
    test_generation()

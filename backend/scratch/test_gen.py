from ai_service import generate_ticket_from_text
import json

def test_generation():
    prompt = "create one subtask under the AP-139 that is craeting one button for the sinup where new people can login"
    try:
        ticket = generate_ticket_from_text(prompt)
        print(f"Generated Ticket:\n{json.dumps(ticket, indent=2)}")
    except Exception as e:
        print(f"Generation failed: {e}")

if __name__ == "__main__":
    test_generation()

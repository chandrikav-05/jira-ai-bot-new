from ai_service import generate_ticket_from_text
import json

def test_generation():
    # Test case 1: Greeting
    greetings = ["Hello there!", "hi", "how are you?"]
    for prompt in greetings:
        print(f"\n--- Testing Greeting: '{prompt}' ---")
        try:
            result = generate_ticket_from_text(prompt)
            print(f"Result:\n{json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"Greeting failed: {e}")

    # Test case 2: Ticket Generation
    ticket_prompt = "create one subtask under the AP-139 that is craeting one button for the sinup where new people can login"
    print(f"\n--- Testing Ticket Gen: '{ticket_prompt}' ---")
    try:
        result = generate_ticket_from_text(ticket_prompt)
        print(f"Result:\n{json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"Ticket Gen failed: {e}")

if __name__ == "__main__":
    test_generation()

import os
from dotenv import load_dotenv
from agent import Agent

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise SystemExit("ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key.")

agent = Agent()

print("Cascadia Agent — backcountry ski planning for the Washington Cascades and Mt. Hood.")
print("Type your question or plan. Ctrl+C to exit.\n")

while True:
    try:
        user_input = input("You: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nStay safe out there.")
        break

    if not user_input:
        continue

    response = agent.chat(user_input)
    print(f"\nAgent: {response}\n")

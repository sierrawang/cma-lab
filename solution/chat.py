"""My Travel App, in the terminal."""
from travel_agent import run_turn, start_session

print("Travel Agent. Type a message, or press Enter on an empty line to quit.")
session_id = start_session()
while True:
    text = input("\nyou › ").strip()
    if not text:
        break
    run_turn(session_id, text)

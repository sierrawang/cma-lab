"""My Travel App's custom tools. They run on your computer, not at Anthropic."""
import json
import webbrowser
from pathlib import Path

POINTS_FILE = Path("points.json")


def get_points_balance():
    if not POINTS_FILE.exists():  # start with some sample points
        POINTS_FILE.write_text(json.dumps({"United MileagePlus": 45000, "Chase Ultimate Rewards": 60000}))
    points = json.loads(POINTS_FILE.read_text())
    return ", ".join(f"{program}: {amount:,}" for program, amount in points.items())


def book_flight(flight, price, link):
    """Show the traveler where to book, then wait for them to decide."""
    print(f"\n  Book {flight} for {price}?")
    if input("  Open it on Google Flights to book? [y/n] ").strip().lower() != "y":
        return "The traveler said no. Nothing was booked."
    webbrowser.open(link)
    if input("  Did you finish booking? [y/n] ").strip().lower() != "y":
        return "The traveler looked at it but didn't book."
    return f"The traveler booked {flight} for {price}."


TOOLS = {"get_points_balance": get_points_balance, "book_flight": book_flight}

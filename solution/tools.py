"""My Travel App's custom tools. They run on your computer, not at Anthropic."""
import json
from pathlib import Path

POINTS_FILE = Path("points.json")


def get_points_balance():
    if not POINTS_FILE.exists():  # start with some sample points
        POINTS_FILE.write_text(json.dumps({"United MileagePlus": 45000, "Chase Ultimate Rewards": 60000}))
    points = json.loads(POINTS_FILE.read_text())
    return ", ".join(f"{program}: {amount:,}" for program, amount in points.items())


TOOLS = {"get_points_balance": get_points_balance}

"""Sample award prices from My Travel App's own chart (not real airline prices).
Usage: python compute_points.py FLIGHT_HOURS CABIN [round]"""
import sys

hours, cabin = float(sys.argv[1]), sys.argv[2].lower()
base = 12500 if hours < 3 else 17500 if hours < 6 else 30000 if hours < 10 else 40000
multiplier = {"economy": 1, "premium": 1.6, "business": 2.2, "first": 3}[cabin]
trips = 2 if sys.argv[-1] == "round" else 1
print(f"{round(base * multiplier * trips, -3):,.0f} miles, {cabin} (sample award price, not live)")

"""Cents per point for paying with miles. Usage: python cpp.py CASH_PRICE MILES"""
import sys

cash, miles = float(sys.argv[1]), float(sys.argv[2])
cents = cash / miles * 100
verdict = "great" if cents >= 1.5 else "good" if cents >= 1.3 else "poor"
print(f"{cents:.2f} cents per point ({verdict})")

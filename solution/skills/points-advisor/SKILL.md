---
name: points-advisor
description: Price a flight in miles and decide whether to pay with points or cash. Use whenever the traveler asks about points or miles.
---
To price a flight in miles, run (FLIGHT_HOURS is the flight time, like 5.5):

    python award_price.py FLIGHT_HOURS CABIN [round]

CABIN is economy, premium, business, or first. These are sample prices, not live; always say so.

Then work out what the points are worth:

    python cpp.py CASH_PRICE MILES

Using points is worth it at 1.3 cents per point or more. Put the cents-per-point number in your "Why:" line.

# Indian Stock Market — Trading Hours & Calendar

## NSE/BSE Trading Sessions (IST)

| Session | Time |
|---------|------|
| Pre-market (opening auction) | 9:00 AM - 9:15 AM |
| Regular trading session | 9:15 AM - 3:30 PM |
| Post-market (closing auction) | 3:40 PM - 4:00 PM |
| **Our active trading window** | **9:30 AM - 3:15 PM** |

## Why We Avoid the First and Last 15 Minutes

- **First 15 minutes (9:15-9:30):** The opening auction creates abnormal volatility. Prices swing sharply as overnight orders get matched and gaps get filled. Entering trades here leads to poor fills and false signals.
- **Last 15 minutes (3:15-3:30):** The closing auction effect distorts price action. Institutional rebalancing and index-tracking flows dominate, making technical signals unreliable.

Our system enforces orders only within the 9:30 AM - 3:15 PM window to avoid both effects.

## Weekly Schedule

- **Monday to Friday:** Markets open (subject to holidays).
- **Saturday and Sunday:** Markets closed.

## Major Indian Market Holidays

The following holidays typically close NSE/BSE. Exact dates vary by year:

| Holiday | Typical Date |
|---------|-------------|
| Republic Day | January 26 |
| Holi | March (varies) |
| Good Friday | March/April (varies) |
| Independence Day | August 15 |
| Gandhi Jayanti | October 2 |
| Diwali (Lakshmi Puja) | October/November (varies) |
| Christmas | December 25 |

There are additional holidays (Eid, Mahavir Jayanti, Buddha Purnima, Guru Nanak Jayanti, etc.) that vary each year. Always check the official NSE holiday calendar at the start of each calendar year for the complete list.

## Session Management

Angel One SmartAPI uses JWT-based authentication. Key points:

- JWT tokens expire after approximately 6 hours.
- Call `refresh_session()` proactively if the session has been running for a long time or if API calls start returning authentication errors.
- Call `login_session()` at the start of each trading day to establish a fresh session.

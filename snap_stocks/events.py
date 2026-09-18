import pandas as pd

EVENTS = [
    {
        "name": "Dot-Com Crash",
        "start": "2000-03-10",
        "end": "2002-10-09",
        "description": "Nasdaq peak to trough as the late-90s tech/internet bubble unwound.",
    },
    {
        "name": "Global Financial Crisis (GFC)",
        "start": "2007-10-09",
        "end": "2009-03-09",
        "description": "S&P 500 peak to trough during the 2008 subprime mortgage / banking collapse.",
    },
    {
        "name": "COVID-19 Crash",
        "start": "2020-02-19",
        "end": "2020-03-24",
        "description": "Fastest bear-market decline on record, followed by the initial snap-back recovery.",
    },
    {
        "name": "2025 Tariff Sell-Off",
        "start": "2025-02-19",
        "end": "2025-04-08",
        "description": "S&P 500 peak to trough (-18.9%) as Trump-era tariff announcements triggered a correction.",
    },
]

PERIODS = ["5d", "1mo", "3mo", "6mo", "1y", "2y", "3y", "5y", "10y", "ytd", "max"]

# yfinance only accepts a fixed set of rolling `period` strings (no "3y" among
# them), so this rolling period is resolved to an explicit start/end range
# instead of being forwarded as-is.
CUSTOM_PERIOD_YEARS = {"3y": 3}

EVENT_NAMES = [e["name"] for e in EVENTS]
EVENTS_BY_NAME = {e["name"]: e for e in EVENTS}

# A single "Time period" dropdown's options: named crash events followed by
# rolling periods, so callers don't need a second "Or view a market crash" field.
TIME_PERIOD_OPTIONS = EVENT_NAMES + PERIODS


def resolve_time_period(selection):
    """Map a TIME_PERIOD_OPTIONS selection to fetch_history's period/start/end kwargs."""
    if selection in EVENTS_BY_NAME:
        event = EVENTS_BY_NAME[selection]
        return {"start": event["start"], "end": event["end"]}
    if selection in CUSTOM_PERIOD_YEARS:
        end = pd.Timestamp.today().normalize() + pd.Timedelta(days=1)
        start = end - pd.DateOffset(years=CUSTOM_PERIOD_YEARS[selection])
        return {"start": start, "end": end}
    return {"period": selection}

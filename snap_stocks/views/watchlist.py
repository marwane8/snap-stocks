import datetime

import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_history

WATCHLIST_TICKERS = [
    "VUG",
    "IAUM", 
    "USO", 
    "AAPL",
]
TICKER_COLORS = {
    "VUG": "#2663dc",
    "IAUM": "#d4af37", 
    "USO": "#8b4513", 
}  

SLIDER_LOOKBACK_YEARS = 10
DATE_RANGE_KEY = "watchlist_date_range"
PILLS_CONTAINER_KEY = "watchlist_pills"
TICKERS_CONTAINER_KEY = "watchlist_ticker_selector"
# label -> days back from today; "YTD" and "Max" are special-cased below.
PILL_RANGES = {"1M": 30, "3M": 91, "6M": 182, "YTD": None, "1Y": 365, "5Y": 365 * 5, "Max": None}


def _fetch_52_week_stats(ticker):
    history = fetch_history(ticker, period="1y")
    if history.empty:
        return None
    return {"ticker": ticker, **metrics.compute_price_range(history)}


def _apply_pill_range():
    """Callback for the quick-range pills - runs before the script reruns,
    so writing the slider's own key here is the safe way to move it (setting
    a key-bound widget's value only works before that widget is created)."""
    selection = st.session_state.get("watchlist_pill")
    if not selection:
        return

    today = datetime.date.today()
    earliest = today - datetime.timedelta(days=365 * SLIDER_LOOKBACK_YEARS)
    if selection == "YTD":
        start = datetime.date(today.year, 1, 1)
    elif selection == "Max":
        start = earliest
    else:
        start = today - datetime.timedelta(days=PILL_RANGES[selection])

    st.session_state[DATE_RANGE_KEY] = (max(start, earliest), today)


def render():
    st.title("Watch List")
    st.caption("IAUM, USO, and VUG tracked against their own 52-week trading range.")

    stats = [s for s in (_fetch_52_week_stats(t) for t in WATCHLIST_TICKERS) if s is not None]
    missing = set(WATCHLIST_TICKERS) - {s["ticker"] for s in stats}
    if missing:
        st.warning(f"No data found for: {', '.join(sorted(missing))}")
    if not stats:
        return

    st.subheader("52-Week Range Gauges")
    cols = st.columns(len(stats))
    for col, s in zip(cols, stats):
        with col, st.container(border=True):
            charts.render_range_gauge(s["ticker"], s["price"], s["low"], s["high"])

    st.subheader("Price")

    today = datetime.date.today()
    if DATE_RANGE_KEY not in st.session_state:
        st.session_state[DATE_RANGE_KEY] = (today - datetime.timedelta(days=365), today)

    start_date, end_date = st.slider(
        "Time period",
        min_value=today - datetime.timedelta(days=365 * SLIDER_LOOKBACK_YEARS),
        max_value=today,
        key=DATE_RANGE_KEY,
    )

    # Hidden on narrow/mobile widths - both controls add little value on a
    # small screen (the slider above is already the primary way to set a
    # range, and mobile just shows every tracked ticker rather than picking).
    st.markdown(
        "<style>@media (max-width: 640px) { div[class*='st-key-"
        + PILLS_CONTAINER_KEY
        + "'], div[class*='st-key-"
        + TICKERS_CONTAINER_KEY
        + "'] { display: none; } }</style>",
        unsafe_allow_html=True,
    )
    with st.container(key=PILLS_CONTAINER_KEY):
        st.pills(
            "Quick range",
            options=list(PILL_RANGES.keys()),
            key="watchlist_pill",
            on_change=_apply_pill_range,
            label_visibility="collapsed",
        )

    visible_tickers = []
    with st.container(key=TICKERS_CONTAINER_KEY):
        show_cols = st.columns(len(WATCHLIST_TICKERS))
        for col, ticker in zip(show_cols, WATCHLIST_TICKERS):
            with col:
                if st.checkbox(ticker, value=True, key=f"watchlist_show_{ticker}"):
                    visible_tickers.append(ticker)

    if not visible_tickers:
        st.info("Select at least one ticker to show its price.")
        return

    prices = {}
    missing_prices = []
    for ticker in visible_tickers:
        history = fetch_history(ticker, start=start_date, end=end_date + pd.Timedelta(days=1))
        if history.empty:
            missing_prices.append(ticker)
        else:
            prices[ticker] = history["Close"]

    if missing_prices:
        st.warning(f"No data found for: {', '.join(sorted(missing_prices))}")
    if prices:
        colors = [TICKER_COLORS.get(ticker) for ticker in prices]
        charts.render_price_chart(prices, colors=colors)

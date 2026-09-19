import datetime

import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_history

WATCHLIST_TICKERS = ["IAUM", "USO", "VUG"]
TICKER_COLORS = {"IAUM": "#d4af37", "USO": "#8b4513", "VUG": "#dc2626"}  # gold, brown, red
SLIDER_LOOKBACK_YEARS = 10


def _fetch_52_week_stats(ticker):
    history = fetch_history(ticker, period="1y")
    if history.empty:
        return None
    return {"ticker": ticker, **metrics.compute_price_range(history)}


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
    start_date, end_date = st.slider(
        "Time period",
        min_value=today - datetime.timedelta(days=365 * SLIDER_LOOKBACK_YEARS),
        max_value=today,
        value=(today - datetime.timedelta(days=365), today),
    )

    show_cols = st.columns(len(WATCHLIST_TICKERS))
    visible_tickers = []
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
        colors = [TICKER_COLORS[ticker] for ticker in prices]
        charts.render_price_chart(prices, colors=colors)

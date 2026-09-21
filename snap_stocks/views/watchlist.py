import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_history
from ..time_period import render_time_period

WATCHLISTS = {
    "ETF": ["VUG", "IAUM", "USO"],
    "Stocks": ["AAPL", "TSM", "IBIT", "SNDK"],
}
TICKER_COLORS = {
    "VUG": "#2663dc",
    "IAUM": "#d4af37",
    "USO": "#8b4513",
    "AAPL": "#a3aab8",
    "TSM": "#dc2626",
    "IBIT": "#f7931a",
    "SNDK": "#16a34a",
}

TICKERS_CONTAINER_KEY = "watchlist_ticker_selector"


def _fetch_52_week_stats(ticker):
    history = fetch_history(ticker, period="1y")
    if history.empty:
        return None
    return {"ticker": ticker, **metrics.compute_price_range(history)}


def render():
    st.title("Watch List")
    for tab, (name, tickers) in zip(st.tabs(list(WATCHLISTS)), WATCHLISTS.items()):
        with tab:
            _render_watchlist(name, tickers)


def _render_watchlist(name, tickers):
    key = name.lower()
    st.caption(f"{', '.join(tickers)} tracked against their own 52-week trading range.")

    stats = [s for s in (_fetch_52_week_stats(t) for t in tickers) if s is not None]
    missing = set(tickers) - {s["ticker"] for s in stats}
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

    start_date, end_date, _ = render_time_period(f"watchlist_{key}")

    # Hidden on narrow/mobile widths - mobile just shows every tracked ticker
    # rather than picking.
    st.markdown(
        "<style>@media (max-width: 640px) { div[class*='st-key-"
        + f"{TICKERS_CONTAINER_KEY}_{key}"
        + "'] { display: none; } }</style>",
        unsafe_allow_html=True,
    )
    visible_tickers = []
    with st.container(key=f"{TICKERS_CONTAINER_KEY}_{key}"):
        show_cols = st.columns(len(tickers))
        for col, ticker in zip(show_cols, tickers):
            with col:
                if st.checkbox(ticker, value=True, key=f"watchlist_{key}_show_{ticker}"):
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

        st.subheader("Normalized")
        charts.render_normalized_chart(
            {ticker: metrics.normalize_to_start(close) for ticker, close in prices.items()},
            colors=colors,
        )

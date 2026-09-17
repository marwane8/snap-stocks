import pandas as pd
import streamlit as st

import charts
import metrics
from data import fetch_history
from events import EVENTS

EVENT_NAMES = [e["name"] for e in EVENTS]
EVENTS_BY_NAME = {e["name"]: e for e in EVENTS}

PERIODS = ["5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]

BASELINE = "SPY"


def render():
    st.title("Stock Explorer")

    ticker = st.text_input("Ticker", value="AAPL").strip().upper()

    col1, col2 = st.columns(2)
    with col1:
        period = st.selectbox("Time period", PERIODS, index=1)
    with col2:
        event = st.selectbox("Or view a market crash", ["None"] + EVENT_NAMES)

    if not ticker:
        return

    if event != "None":
        selected = EVENTS_BY_NAME[event]
        history = fetch_history(ticker, start=selected["start"], end=selected["end"])
    else:
        history = fetch_history(ticker, period=period)

    if history.empty:
        st.warning(f"No data found for '{ticker}'.")
        return

    label = event if event != "None" else period

    stock_metrics = None
    if len(history) >= 2:
        stock_metrics = metrics.compute_return_metrics(history)
        charts.render_metrics_row(ticker, label, stock_metrics)
    else:
        st.info("Not enough data in this range to compute volatility metrics.")

    st.subheader(f"{ticker} — Close price ({label})")
    charts.render_line_chart({ticker: history["Close"]})

    if stock_metrics is not None:
        st.subheader(f"{ticker} vs {BASELINE} — Daily % Change ({label})")
        if ticker == BASELINE:
            charts.render_line_chart(
                {ticker: stock_metrics["returns"]}, colors=charts.PALETTE[:1]
            )
        else:
            start = history.index[0]
            end = history.index[-1] + pd.Timedelta(days=1)
            baseline_history = fetch_history(BASELINE, start=start, end=end)
            baseline_metrics = metrics.compute_return_metrics(baseline_history)
            charts.render_line_chart(
                {ticker: stock_metrics["returns"], BASELINE: baseline_metrics["returns"]},
                colors=charts.PALETTE,
            )

    st.subheader(f"{ticker} — Volume ({label})")
    charts.render_bar_chart({ticker: history["Volume"]})

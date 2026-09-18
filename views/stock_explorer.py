import pandas as pd
import streamlit as st

import charts
import metrics
from data import fetch_history
from events import resolve_time_period

BASELINE = "SPY"


def render():
    st.title("Stock Explorer")

    ticker = charts.render_ticker_selectbox("Ticker", default="AAPL", key="explorer_ticker")
    label = charts.render_time_period_selectbox()

    if not ticker:
        return

    history = fetch_history(ticker, **resolve_time_period(label))

    if history.empty:
        st.warning(f"No data found for '{ticker}'.")
        return

    stock_metrics = None
    if len(history) >= 2:
        stock_metrics = metrics.compute_return_metrics(history)
        charts.render_metrics_row(ticker, label, stock_metrics)
    else:
        st.info("Not enough data in this range to compute volatility metrics.")

    st.subheader(f"{ticker} — Price ({label})")
    charts.render_candlestick_chart(history, ticker)

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

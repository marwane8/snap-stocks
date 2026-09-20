import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_history
from ..time_period import render_time_period

BASELINE = "SPY"


def render():
    st.title("Stock Explorer")

    ticker = charts.render_ticker_selectbox("Ticker", default="AAPL", key="explorer_ticker")
    start_date, end_date, label = render_time_period("explorer")

    if not ticker:
        return

    history = fetch_history(ticker, start=start_date, end=end_date + pd.Timedelta(days=1))

    if history.empty:
        st.warning(f"No data found for '{ticker}'.")
        return

    stock_metrics = None
    baseline_metrics = None
    if len(history) >= 2:
        stock_metrics = metrics.compute_return_metrics(history)
        charts.render_metrics_row(ticker, label, stock_metrics)

        # A true 52-week window (51 weeks back from the last close of the
        # selected period), not the selected period's own span - so it
        # tracks the period's end date without stretching/shrinking to
        # match how long that period happens to be.
        week52_end = history.index[-1]
        week52_start = week52_end - pd.Timedelta(weeks=51)
        week52_history = fetch_history(ticker, start=week52_start, end=week52_end + pd.Timedelta(days=1))
        if not week52_history.empty:
            price_range = metrics.compute_price_range(week52_history)
            with st.container(border=True):
                charts.render_range_gauge(ticker, price_range["price"], price_range["low"], price_range["high"])

        if ticker != BASELINE:
            start = history.index[0]
            end = history.index[-1] + pd.Timedelta(days=1)
            baseline_history = fetch_history(BASELINE, start=start, end=end)
            baseline_metrics = metrics.compute_return_metrics(baseline_history)
    else:
        st.info("Not enough data in this range to compute volatility metrics.")

    st.subheader(f"{ticker} — Price ({label})")
    charts.render_candlestick_chart(history, ticker)

    if stock_metrics is not None:
        st.subheader(f"{ticker} vs {BASELINE} — Daily % Change ({label})")
        if ticker == BASELINE:
            charts.render_returns_chart(
                {ticker: stock_metrics["returns"]}, colors=charts.PALETTE[:1]
            )
        else:
            charts.render_returns_chart(
                {ticker: stock_metrics["returns"], BASELINE: baseline_metrics["returns"]},
                colors=charts.PALETTE,
            )

    if stock_metrics is not None:
        st.subheader(f"{ticker} — Daily % Change Distribution ({label})")
        charts.render_returns_histogram(
            stock_metrics["returns"],
            ticker,
            baseline_returns=baseline_metrics["returns"] if baseline_metrics is not None else None,
            baseline_label=BASELINE,
        )

    st.subheader(f"{ticker} — Volume ({label})")
    charts.render_bar_chart({ticker: history["Volume"]}, colors=charts.PALETTE[:1])
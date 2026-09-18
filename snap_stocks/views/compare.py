import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_history
from ..events import resolve_time_period


def render():
    st.title("Stock Compare")

    col1, col2 = st.columns(2)
    with col1:
        ticker_a = charts.render_ticker_selectbox("Ticker A", default="AAPL", key="compare_ticker_a")
    with col2:
        ticker_b = charts.render_ticker_selectbox("Ticker B", default="MSFT", key="compare_ticker_b")

    label = charts.render_time_period_selectbox()

    if not ticker_a or not ticker_b:
        return

    if ticker_a == ticker_b:
        st.warning("Enter two different tickers to compare.")
        return

    period_kwargs = resolve_time_period(label)
    history_a = fetch_history(ticker_a, **period_kwargs)
    history_b = fetch_history(ticker_b, **period_kwargs)

    if history_a.empty:
        st.warning(f"No data found for '{ticker_a}'.")
        return
    if history_b.empty:
        st.warning(f"No data found for '{ticker_b}'.")
        return

    metrics_a = metrics.compute_return_metrics(history_a) if len(history_a) >= 2 else None
    metrics_b = metrics.compute_return_metrics(history_b) if len(history_b) >= 2 else None

    if metrics_a is not None:
        charts.render_metrics_row(ticker_a, label, metrics_a)
    else:
        st.info(f"Not enough {ticker_a} data in this range to compute volatility metrics.")

    if metrics_b is not None:
        charts.render_metrics_row(ticker_b, label, metrics_b)
    else:
        st.info(f"Not enough {ticker_b} data in this range to compute volatility metrics.")

    if metrics_a is not None and metrics_b is not None:
        returns_df = pd.DataFrame(
            {ticker_a: metrics_a["returns"], ticker_b: metrics_b["returns"]}
        ).dropna()
        if len(returns_df) >= 2:
            correlation = returns_df[ticker_a].corr(returns_df[ticker_b])
            charts.render_correlation_card(ticker_a, ticker_b, correlation)

    st.subheader(f"{ticker_a} vs {ticker_b} — ({label})")
    charts.render_line_chart(
        {ticker_a: history_a["Close"], ticker_b: history_b["Close"]},
        colors=charts.PALETTE,
    )

    st.subheader(f"{ticker_a} vs {ticker_b} — Normalized ({label})")
    charts.render_normalized_chart(
        {
            ticker_a: metrics.normalize_to_start(history_a["Close"]),
            ticker_b: metrics.normalize_to_start(history_b["Close"]),
        },
        colors=charts.PALETTE,
    )

    if metrics_a is not None and metrics_b is not None:
        st.subheader(f"{ticker_a} vs {ticker_b} — Daily % Change ({label})")
        charts.render_returns_chart(
            {ticker_a: metrics_a["returns"], ticker_b: metrics_b["returns"]},
            colors=charts.PALETTE,
        )

    st.subheader(f"{ticker_a} vs {ticker_b} — Volume ({label})")
    charts.render_bar_chart(
        {ticker_a: history_a["Volume"], ticker_b: history_b["Volume"]},
        colors=charts.PALETTE,
    )

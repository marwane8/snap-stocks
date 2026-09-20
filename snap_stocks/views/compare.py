import datetime

import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_history
from ..events import EVENTS, EVENTS_BY_NAME

# Early enough to cover the oldest named event (Dot-Com Crash).
SLIDER_MIN_DATE = datetime.date(2000, 1, 1)
DATE_RANGE_KEY = "compare_date_range"
RANGE_PILL_KEY = "compare_range_pill"
EVENT_PILL_KEY = "compare_event_pill"
# label -> days back from today; "YTD" and "Max" are special-cased below.
PILL_RANGES = {"5D": 5, "1M": 30, "3M": 91, "6M": 182, "YTD": None, "1Y": 365, "2Y": 365 * 2, "3Y": 365 * 3, "5Y": 365 * 5, "10Y": 365 * 10, "Max": None}
EVENT_NAMES = [e["name"] for e in EVENTS]


def _apply_range_pill():
    """Callbacks run before the rerun, the only point a key-bound widget's
    value (the slider) can be written."""
    selection = st.session_state.get(RANGE_PILL_KEY)
    if not selection:
        return
    st.session_state[EVENT_PILL_KEY] = None

    today = datetime.date.today()
    if selection == "YTD":
        start = datetime.date(today.year, 1, 1)
    elif selection == "Max":
        start = SLIDER_MIN_DATE
    else:
        start = today - datetime.timedelta(days=PILL_RANGES[selection])
    st.session_state[DATE_RANGE_KEY] = (max(start, SLIDER_MIN_DATE), today)


def _apply_event_pill():
    selection = st.session_state.get(EVENT_PILL_KEY)
    if not selection:
        return
    st.session_state[RANGE_PILL_KEY] = None
    event = EVENTS_BY_NAME[selection]
    st.session_state[DATE_RANGE_KEY] = (
        datetime.date.fromisoformat(event["start"]),
        datetime.date.fromisoformat(event["end"]),
    )


def _clear_pills():
    st.session_state[RANGE_PILL_KEY] = None
    st.session_state[EVENT_PILL_KEY] = None


def _render_time_period():
    """Slider + range pills + event pills; returns (start, end, label)."""
    today = datetime.date.today()
    if DATE_RANGE_KEY not in st.session_state:
        st.session_state[DATE_RANGE_KEY] = (today - datetime.timedelta(days=365), today)
        st.session_state[RANGE_PILL_KEY] = "1Y"

    start, end = st.slider(
        "Time period",
        min_value=SLIDER_MIN_DATE,
        max_value=today,
        key=DATE_RANGE_KEY,
        on_change=_clear_pills,
    )
    st.pills(
        "Quick range",
        options=list(PILL_RANGES.keys()),
        key=RANGE_PILL_KEY,
        on_change=_apply_range_pill,
        label_visibility="collapsed",
    )
    st.pills(
        "Events",
        options=EVENT_NAMES,
        key=EVENT_PILL_KEY,
        on_change=_apply_event_pill,
        label_visibility="collapsed",
    )

    label = st.session_state.get(EVENT_PILL_KEY) or st.session_state.get(RANGE_PILL_KEY)
    return start, end, label or f"{start:%b %d, %Y} – {end:%b %d, %Y}"


def render():
    st.title("Stock Compare")

    col1, col2 = st.columns(2)
    with col1:
        ticker_a = charts.render_ticker_selectbox("Ticker A", default="AAPL", key="compare_ticker_a")
    with col2:
        ticker_b = charts.render_ticker_selectbox("Ticker B", default="SPY", key="compare_ticker_b")

    start_date, end_date, label = _render_time_period()

    if not ticker_a or not ticker_b:
        return

    if ticker_a == ticker_b:
        st.warning("Enter two different tickers to compare.")
        return

    period_kwargs = {"start": start_date, "end": end_date + pd.Timedelta(days=1)}
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

    returns_df = None
    if metrics_a is not None and metrics_b is not None:
        returns_df = pd.DataFrame(
            {ticker_a: metrics_a["returns"], ticker_b: metrics_b["returns"]}
        ).dropna()
        if len(returns_df) >= 2:
            correlation = returns_df[ticker_a].corr(returns_df[ticker_b])
            charts.render_correlation_card(ticker_a, ticker_b, correlation)

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
        col_scatter, col_line = st.columns(2)
        with col_scatter:
            if returns_df is not None and len(returns_df) >= 2:
                charts.render_returns_scatter(
                    returns_df[ticker_a], returns_df[ticker_b], ticker_a, ticker_b
                )
        with col_line:
            charts.render_returns_chart(
                {ticker_a: metrics_a["returns"], ticker_b: metrics_b["returns"]},
                colors=charts.PALETTE,
            )

    st.subheader(f"{ticker_a} vs {ticker_b} — Volume ({label})")
    charts.render_bar_chart(
        {ticker_a: history_a["Volume"], ticker_b: history_b["Volume"]},
        colors=charts.PALETTE,
    )

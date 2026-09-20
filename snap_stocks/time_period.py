"""Shared date-range slider + quick-range pills + event pills, so views
don't each rebuild the same time-period control."""
import datetime

import streamlit as st

from .events import EVENTS, EVENTS_BY_NAME

# Early enough to cover the oldest named event (Dot-Com Crash).
SLIDER_MIN_DATE = datetime.date(2000, 1, 1)
# label -> days back from today; "YTD" and "Max" are special-cased below.
PILL_RANGES = {"5D": 5, "1M": 30, "3M": 91, "6M": 182, "YTD": None, "1Y": 365, "2Y": 365 * 2, "3Y": 365 * 3, "5Y": 365 * 5, "10Y": 365 * 10, "Max": None}
EVENT_NAMES = [e["name"] for e in EVENTS]


def _keys(prefix):
    return f"{prefix}_date_range", f"{prefix}_range_pill", f"{prefix}_event_pill"


def _apply_range_pill(prefix):
    """Callbacks run before the rerun, the only point a key-bound widget's
    value (the slider) can be written."""
    range_key, pill_key, event_key = _keys(prefix)
    selection = st.session_state.get(pill_key)
    if not selection:
        return
    st.session_state[event_key] = None

    today = datetime.date.today()
    if selection == "YTD":
        start = datetime.date(today.year, 1, 1)
    elif selection == "Max":
        start = SLIDER_MIN_DATE
    else:
        start = today - datetime.timedelta(days=PILL_RANGES[selection])
    st.session_state[range_key] = (max(start, SLIDER_MIN_DATE), today)


def _apply_event_pill(prefix):
    range_key, pill_key, event_key = _keys(prefix)
    selection = st.session_state.get(event_key)
    if not selection:
        return
    st.session_state[pill_key] = None
    event = EVENTS_BY_NAME[selection]
    st.session_state[range_key] = (
        datetime.date.fromisoformat(event["start"]),
        datetime.date.fromisoformat(event["end"]),
    )


def _clear_pills(prefix):
    _, pill_key, event_key = _keys(prefix)
    st.session_state[pill_key] = None
    st.session_state[event_key] = None


def render_time_period(prefix):
    """Slider + range pills + event pills; returns (start, end, label).
    `prefix` namespaces the session-state keys so each view keeps its own range."""
    range_key, pill_key, event_key = _keys(prefix)
    today = datetime.date.today()
    if range_key not in st.session_state:
        st.session_state[range_key] = (today - datetime.timedelta(days=365), today)
        st.session_state[pill_key] = "1Y"

    start, end = st.slider(
        "Time period",
        min_value=SLIDER_MIN_DATE,
        max_value=today,
        key=range_key,
        on_change=_clear_pills,
        args=(prefix,),
    )
    st.pills(
        "Quick range",
        options=list(PILL_RANGES.keys()),
        key=pill_key,
        on_change=_apply_range_pill,
        args=(prefix,),
        label_visibility="collapsed",
    )
    st.pills(
        "Events",
        options=EVENT_NAMES,
        key=event_key,
        on_change=_apply_event_pill,
        args=(prefix,),
        label_visibility="collapsed",
    )

    label = st.session_state.get(event_key) or st.session_state.get(pill_key)
    return start, end, label or f"{start:%b %d, %Y} – {end:%b %d, %Y}"

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


CUSTOM_OPTION = "Custom range"
MOBILE_MAX_WIDTH = 640  # px; matches the breakpoint used elsewhere in the app


def _keys(prefix):
    return {
        "range": f"{prefix}_date_range",
        "pill": f"{prefix}_range_pill",
        "event": f"{prefix}_event_pill",
        "select": f"{prefix}_preset_select",
    }


def _select_preset(prefix, name):
    """Move the slider to preset `name` (a PILL_RANGES label, an event name,
    or CUSTOM_OPTION) and mirror it on every control. Only safe from a
    callback (or before the widgets are created), since it writes widget keys."""
    k = _keys(prefix)
    today = datetime.date.today()
    st.session_state[k["pill"]] = name if name in PILL_RANGES else None
    st.session_state[k["event"]] = name if name in EVENTS_BY_NAME else None
    st.session_state[k["select"]] = name

    if name in EVENTS_BY_NAME:
        event = EVENTS_BY_NAME[name]
        st.session_state[k["range"]] = (
            datetime.date.fromisoformat(event["start"]),
            datetime.date.fromisoformat(event["end"]),
        )
    elif name == "YTD":
        st.session_state[k["range"]] = (datetime.date(today.year, 1, 1), today)
    elif name == "Max":
        st.session_state[k["range"]] = (SLIDER_MIN_DATE, today)
    elif name in PILL_RANGES:
        start = today - datetime.timedelta(days=PILL_RANGES[name])
        st.session_state[k["range"]] = (max(start, SLIDER_MIN_DATE), today)


def _on_pick(prefix, source):
    """Callback for the pills / dropdown. `source` is the session-state key
    holding the pick; clearing a pill leaves the slider where it is."""
    name = st.session_state.get(_keys(prefix)[source])
    if name and name != CUSTOM_OPTION:
        _select_preset(prefix, name)
    else:
        _on_slider(prefix)


def _on_slider(prefix):
    k = _keys(prefix)
    st.session_state[k["pill"]] = None
    st.session_state[k["event"]] = None
    st.session_state[k["select"]] = CUSTOM_OPTION


def render_time_period(prefix):
    """Date-range slider with quick-range and event presets; returns
    (start, end, label). On desktop the presets are pills, on narrow screens
    a single dropdown (both are rendered, CSS hides the one that doesn't fit).
    `prefix` namespaces the session-state keys so each view keeps its own range."""
    k = _keys(prefix)
    today = datetime.date.today()
    if k["range"] not in st.session_state:
        st.session_state[k["range"]] = (today - datetime.timedelta(days=365), today)
        st.session_state[k["pill"]] = "1Y"
        st.session_state[k["event"]] = None
        st.session_state[k["select"]] = "1Y"

    start, end = st.slider(
        "Time period",
        min_value=SLIDER_MIN_DATE,
        max_value=today,
        key=k["range"],
        on_change=_on_slider,
        args=(prefix,),
    )

    pills_container, select_container = f"{prefix}_time_pills", f"{prefix}_time_select"
    st.markdown(
        f"<style>@media (max-width: {MOBILE_MAX_WIDTH}px) {{ div[class*='st-key-{pills_container}'] "
        "{ display: none; } }"
        f" @media (min-width: {MOBILE_MAX_WIDTH + 1}px) {{ div[class*='st-key-{select_container}'] "
        "{ display: none; } }</style>",
        unsafe_allow_html=True,
    )
    with st.container(key=pills_container):
        st.pills(
            "Quick range",
            options=list(PILL_RANGES.keys()),
            key=k["pill"],
            on_change=_on_pick,
            args=(prefix, "pill"),
            label_visibility="collapsed",
        )
        st.pills(
            "Events",
            options=EVENT_NAMES,
            key=k["event"],
            on_change=_on_pick,
            args=(prefix, "event"),
            label_visibility="collapsed",
        )
    with st.container(key=select_container):
        st.selectbox(
            "Preset range",
            options=[CUSTOM_OPTION, *PILL_RANGES, *EVENT_NAMES],
            key=k["select"],
            on_change=_on_pick,
            args=(prefix, "select"),
            label_visibility="collapsed",
        )

    label = st.session_state.get(k["select"])
    if not label or label == CUSTOM_OPTION:
        label = f"{start:%b %d, %Y} – {end:%b %d, %Y}"
    return start, end, label

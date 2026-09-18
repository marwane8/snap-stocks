import itertools

import pandas as pd
import streamlit as st

import charts
from data import fetch_closes
from events import EVENTS

PERIOD_LABELS = {"1 Year": "1y", "3 Years": "3y", "5 Years": "5y", "10 Years": "10y"}


def _init_state():
    if "corr_tickers" not in st.session_state:
        st.session_state.corr_tickers = ["VUG", "AAPL", "BRK-B"]
    if "corr_results" not in st.session_state:
        st.session_state.corr_results = None
    if "corr_results_label" not in st.session_state:
        st.session_state.corr_results_label = None


def _reset():
    st.session_state.corr_tickers = []
    st.session_state.corr_results = None
    st.session_state.corr_results_label = None


def _calculate(tickers, *, period=None, start=None, end=None):
    closes = fetch_closes(tickers, period=period, start=start, end=end)

    missing = set(tickers) - set(closes)
    if missing:
        st.warning(f"No data found for: {', '.join(sorted(missing))}")

    if len(closes) >= 2:
        prices = pd.DataFrame(closes)
        returns = prices.pct_change(fill_method=None).dropna()
        return returns.corr()
    return None


def _render_controls():
    left, right = st.columns([2, 1])

    with left:
        st.caption("ENTER STOCK OR ETF TICKERS (UP TO 10)")
        tickers = st.multiselect(
            "Tickers",
            options=st.session_state.corr_tickers,
            default=st.session_state.corr_tickers,
            accept_new_options=True,
            max_selections=10,
            placeholder="Enter ticker (e.g., AAPL, MSFT, NVDA)",
            label_visibility="collapsed",
        )
        st.session_state.corr_tickers = [t.strip().upper() for t in tickers]

    with right:
        st.caption("TIME PERIOD")
        period_label = st.pills(
            "Time period",
            options=list(PERIOD_LABELS.keys()),
            default="1 Year",
            label_visibility="collapsed",
        )

    col_reset, col_calc = st.columns([1, 1])
    with col_reset:
        st.button("🗑️ Reset", on_click=_reset, use_container_width=True, key="corr_reset")
    with col_calc:
        calculate = st.button(
            "Calculate Correlation",
            type="primary",
            use_container_width=True,
            key="corr_calculate",
        )

    if calculate:
        tickers = st.session_state.corr_tickers
        if len(tickers) < 2:
            st.warning("Enter at least 2 tickers to calculate correlation.")
            st.session_state.corr_results = None
        elif not period_label:
            st.warning("Pick a time period.")
            st.session_state.corr_results = None
        else:
            with st.spinner("Fetching data..."):
                st.session_state.corr_results = _calculate(
                    tickers, period=PERIOD_LABELS[period_label]
                )
                st.session_state.corr_results_label = period_label


def _render_events():
    st.divider()
    st.subheader("Events")
    st.caption("Analyze correlation during a specific historical market crash")

    event_cols = st.columns(len(EVENTS))
    for col, event in zip(event_cols, EVENTS):
        with col:
            st.markdown(f"**{event['name']}**")
            st.caption(f"{event['start']} to {event['end']}")
            st.caption(event["description"])
            if st.button(
                "Analyze",
                key=f"corr_event_{event['name']}",
                use_container_width=True,
            ):
                tickers = st.session_state.corr_tickers
                if len(tickers) < 2:
                    st.warning("Enter at least 2 tickers to calculate correlation.")
                else:
                    with st.spinner("Fetching data..."):
                        st.session_state.corr_results = _calculate(
                            tickers, start=event["start"], end=event["end"]
                        )
                        st.session_state.corr_results_label = event["name"]


def _render_matrix(corr):
    st.divider()
    header_col, legend_col = st.columns([2, 1])
    with header_col:
        st.subheader("Correlation Matrix")
        if st.session_state.corr_results_label:
            st.caption(f"Period: {st.session_state.corr_results_label}")
    with legend_col:
        st.markdown(
            "<div style='text-align:right; padding-top: 0.5rem;'>"
            "<span style='color:#b91c1c;'>&#9679;</span> Strong Positive &nbsp;&nbsp;"
            "<span style='color:#1d4ed8;'>&#9679;</span> Strong Negative"
            "</div>",
            unsafe_allow_html=True,
        )

    tickers_order = list(corr.columns)

    header_cells = "".join(
        f"<div style='flex:1; text-align:center; font-weight:600;'>{t}</div>"
        for t in tickers_order
    )
    rows_html = ""
    for row_ticker in tickers_order:
        cells = ""
        for col_ticker in tickers_order:
            value = corr.loc[row_ticker, col_ticker]
            bg, text_color = charts.correlation_color(value)
            cells += (
                f"<div style='flex:1; margin:4px; padding:14px 0; text-align:center;"
                f" border-radius:8px; font-family:monospace; background-color:{bg};"
                f" color:{text_color};'>{value:.2f}</div>"
            )
        rows_html += (
            "<div style='display:flex; align-items:center;'>"
            f"<div style='width:100px; font-weight:600;'>{row_ticker}</div>"
            f"<div style='display:flex; flex:1;'>{cells}</div>"
            "</div>"
        )

    st.markdown(
        "<div style='display:flex;'><div style='width:100px;'></div>"
        f"<div style='display:flex; flex:1;'>{header_cells}</div></div>"
        f"{rows_html}",
        unsafe_allow_html=True,
    )


def _render_insights(corr):
    st.subheader("Summary Insights")

    tickers_order = list(corr.columns)
    pairs = [
        (a, b, corr.loc[a, b]) for a, b in itertools.combinations(tickers_order, 2)
    ]
    highest = max(pairs, key=lambda p: p[2])
    lowest = min(pairs, key=lambda p: p[2])
    avg_corr = sum(p[2] for p in pairs) / len(pairs)

    if avg_corr < 0:
        diversification = "Strong diversification"
    elif avg_corr < 0.3:
        diversification = "Moderate diversification"
    elif avg_corr < 0.6:
        diversification = "Weak diversification"
    else:
        diversification = "Poor diversification"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f"""
            <div style='background:#fef2f2; padding:20px; border-radius:12px;'>
              <div style='color:#b91c1c; font-weight:600;'>Highest Correlation</div>
              <div style='font-size:2rem; font-weight:700; color:#b91c1c;'>{highest[2]:.2f}</div>
              <div style='color:#b91c1c;'>{highest[0]} &amp; {highest[1]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div style='background:#eff6ff; padding:20px; border-radius:12px;'>
              <div style='color:#2563eb; font-weight:600;'>Lowest Correlation</div>
              <div style='font-size:2rem; font-weight:700; color:#2563eb;'>{lowest[2]:.2f}</div>
              <div style='color:#2563eb;'>{lowest[0]} &amp; {lowest[1]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""
            <div style='background:#f8fafc; padding:20px; border-radius:12px;'>
              <div style='font-weight:600;'>Average Portfolio Correlation</div>
              <div style='font-size:2rem; font-weight:700;'>{avg_corr:.2f}</div>
              <div style='color:#64748b;'>{diversification}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render():
    _init_state()
    _render_controls()
    _render_events()

    corr = st.session_state.corr_results
    if corr is not None:
        _render_matrix(corr)
        _render_insights(corr)

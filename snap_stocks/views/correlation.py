import itertools

import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_closes, load_ticker_directory
from ..events import resolve_time_period


def _init_state():
    if "corr_tickers" not in st.session_state:
        st.session_state.corr_tickers = ["VUG", "AAPL", "BRK-B"]
    if "corr_results" not in st.session_state:
        st.session_state.corr_results = None
    if "corr_results_label" not in st.session_state:
        st.session_state.corr_results_label = None
    if "corr_prices" not in st.session_state:
        st.session_state.corr_prices = None


def _reset():
    st.session_state.corr_tickers = []
    st.session_state.corr_results = None
    st.session_state.corr_results_label = None
    st.session_state.corr_prices = None


def _calculate(tickers, *, period=None, start=None, end=None):
    closes = fetch_closes(tickers, period=period, start=start, end=end)

    missing = set(tickers) - set(closes)
    if missing:
        st.warning(f"No data found for: {', '.join(sorted(missing))}")

    if len(closes) >= 2:
        prices = pd.DataFrame(closes)
        returns = prices.pct_change(fill_method=None).dropna()
        return returns.corr(), prices
    return None, None


def _render_controls():
    st.caption("ENTER STOCK OR ETF TICKERS (UP TO 10)")

    all_symbols = [symbol for symbol, _ in load_ticker_directory()]
    # Keep any already-selected ticker that isn't in the directory (free-typed) selectable.
    extra_symbols = [t for t in st.session_state.corr_tickers if t not in all_symbols]
    options = extra_symbols + all_symbols

    tickers = st.multiselect(
        "Tickers",
        options=options,
        default=st.session_state.corr_tickers,
        accept_new_options=True,
        max_selections=10,
        placeholder="Enter ticker (e.g., AAPL, MSFT, NVDA)",
        label_visibility="collapsed",
    )
    st.session_state.corr_tickers = [t.strip().upper() for t in tickers]

    selection = charts.render_time_period_selectbox()

    col_reset, col_calc = st.columns([1, 1])
    with col_reset:
        st.button("️Reset", on_click=_reset, use_container_width=True, key="corr_reset")
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
        elif not selection:
            st.warning("Pick a time period.")
            st.session_state.corr_results = None
        else:
            with st.spinner("Fetching data..."):
                corr, prices = _calculate(tickers, **resolve_time_period(selection))
                st.session_state.corr_results = corr
                st.session_state.corr_prices = prices
                st.session_state.corr_results_label = selection


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
    tickers_order = list(corr.columns)
    pairs = [
        (a, b, corr.loc[a, b]) for a, b in itertools.combinations(tickers_order, 2)
    ]
    avg_corr = sum(p[2] for p in pairs) / len(pairs)

    if avg_corr < 0:
        diversification = "Strong diversification"
        number_color = "#16a34a"
    elif avg_corr < 0.3:
        diversification = "Moderate diversification"
        number_color = "#2563eb"
    elif avg_corr < 0.6:
        diversification = "Weak diversification"
        number_color = "#d97706"
    else:
        diversification = "Poor diversification"
        number_color = "#dc2626"

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown(
            f"""
            <div style='text-align:center; padding:8px 0;'>
              <div style='font-weight:600;'>Average Portfolio Correlation</div>
              <div style='font-size:2.5rem; font-weight:700; color:{number_color};'>{avg_corr:.2f}</div>
              <div style='color:#64748b;'>{diversification}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_normalized_chart(prices):
    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
    st.subheader("Normalized Price Comparison")
    st.caption("Each ticker rebased to 1.00 at the start of the period, for relative performance.")
    normalized = {ticker: metrics.normalize_to_start(prices[ticker]) for ticker in prices.columns}
    charts.render_line_chart(normalized)


def render():
    _init_state()
    _render_controls()

    corr = st.session_state.corr_results
    if corr is not None:
        _render_matrix(corr)
        _render_insights(corr)
        _render_normalized_chart(st.session_state.corr_prices)

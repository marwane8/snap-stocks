import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from events import TIME_PERIOD_OPTIONS

PALETTE = ["#dc2626", "#93c5fd"]  # red, light blue
POSITIVE_COLOR = "#16a34a"  # green
NEGATIVE_COLOR = "#dc2626"  # red
CLOSE_LINE_COLOR = "#0891b2"  # cyan


def render_time_period_selectbox(default="1mo"):
    """The single 'Time period' dropdown (rolling periods + named crash events)
    shared by every view, so each one doesn't build its own options list."""
    index = TIME_PERIOD_OPTIONS.index(default) if default in TIME_PERIOD_OPTIONS else 0
    return st.selectbox("Time period", TIME_PERIOD_OPTIONS, index=index)


def render_line_chart(series_by_label, colors=None):
    """Overlay one or more named series on a single line chart."""
    st.line_chart(pd.DataFrame(series_by_label), color=colors)


def render_candlestick_chart(history, ticker):
    """OHLC candlesticks with the close price overlaid as a line."""
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=history.index,
            open=history["Open"],
            high=history["High"],
            low=history["Low"],
            close=history["Close"],
            name=ticker,
            increasing_line_color=POSITIVE_COLOR,
            decreasing_line_color=NEGATIVE_COLOR,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=history.index,
            y=history["Close"],
            mode="lines",
            name="Close Price",
            line={"color": CLOSE_LINE_COLOR, "width": 2},
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig)


def render_bar_chart(series_by_label, colors=None):
    """Overlay one or more named series on a single bar chart."""
    st.bar_chart(pd.DataFrame(series_by_label), color=colors)


def signed_metric(label, value):
    """A single big metric value, colored green (positive) or red (negative)."""
    color = POSITIVE_COLOR if value >= 0 else NEGATIVE_COLOR
    st.markdown(
        f"""
        <div>
          <div style='font-size:0.875rem; color:#64748b;'>{label}</div>
          <div style='font-size:2rem; font-weight:600; color:{color};'>{value:.2f}%</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def correlation_color(value):
    if value >= 0.7:
        return "#b91c1c", "white"  # dark red
    elif value >= 0.3:
        return "#f8b4b4", "#1f2937"  # light red
    elif value >= -0.3:
        return "#d1d5db", "#1f2937"  # gray
    elif value >= -0.7:
        return "#a8c8f8", "#1f2937"  # light blue
    else:
        return "#1d4ed8", "white"  # dark blue


def render_correlation_card(ticker_a, ticker_b, correlation):
    number_color, _ = correlation_color(correlation)
    with st.container(border=True):
        st.markdown(
            f"""
            <div style='text-align:center; padding:8px 0;'>
              <div style='font-weight:600;'>{ticker_a} & {ticker_b} Correlation</div>
              <div style='font-size:2.5rem; font-weight:700; color:{number_color};'>{correlation:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_price_metric(label, price, change_pct):
    """A price value with a colored, pill-shaped daily % change badge underneath."""
    positive = change_pct is not None and change_pct >= 0
    color = POSITIVE_COLOR if positive else NEGATIVE_COLOR
    badge_bg = "rgba(22, 163, 74, 0.15)" if positive else "rgba(220, 38, 38, 0.15)"
    arrow = "↑" if positive else "↓"

    badge_html = ""
    if change_pct is not None:
        badge_html = f"""
        <div style='display:inline-flex; align-items:center; gap:4px;
                    padding:4px 12px; border-radius:999px; background:{badge_bg};
                    color:{color}; font-weight:600; font-size:0.875rem;'>
          {arrow} {abs(change_pct):.2f}%
        </div>
        """

    st.markdown(
        f"""
        <div>
          <div style='font-size:0.875rem; color:#64748b;'>\U0001f4b0 {label}</div>
          <div style='display:flex; align-items:center; gap:12px;'>
            <div style='font-size:2rem; font-weight:600;'>${price:,.2f}</div>
            {badge_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics_row(ticker, label, metrics):
    """One bordered pill of Total Return / Annual Return / Volatility / Price for a ticker."""
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            signed_metric(f"{ticker} Total Return ({label})", metrics["total_return"])
        with c2:
            annual = metrics["annual_return"]
            if annual is not None:
                signed_metric(f"{ticker} Annual Return", annual)
            else:
                st.metric(f"{ticker} Annual Return", "-")
        with c3:
            st.metric(
                f"{ticker} Annualized Volatility (Std Dev)",
                f"{metrics['annualized_volatility']:.2f}%",
            )
        with c4:
            render_price_metric(f"{ticker} Price", metrics["last_price"], metrics["last_change_pct"])

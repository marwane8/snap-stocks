import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .data import load_ticker_directory
from .events import TIME_PERIOD_OPTIONS

PALETTE = ["#dc2626", "#93c5fd"]  # red, light blue
POSITIVE_COLOR = "#16a34a"  # green
NEGATIVE_COLOR = "#dc2626"  # red
CLOSE_LINE_COLOR = "#0891b2"  # cyan
HISTOGRAM_BAR_COLOR = "#93c5fd"  # light blue
HISTOGRAM_CURVE_COLOR = "#1d4ed8"  # dark blue
DAILY_CHANGE_AXIS_LIMIT = 20  # % - default axis bound for daily-change charts; user can zoom/pan past it


def render_time_period_selectbox(default="Global Financial Crisis (GFC)"):
    """The single 'Time period' dropdown (rolling periods + named crash events)
    shared by every view, so each one doesn't build its own options list."""
    index = TIME_PERIOD_OPTIONS.index(default) if default in TIME_PERIOD_OPTIONS else 0
    return st.selectbox("Time period", TIME_PERIOD_OPTIONS, index=index)


def render_ticker_selectbox(label, default, key):
    """A single-ticker picker searchable by prefix, showing 'SYMBOL - Name',
    shared by every view that looks up one ticker at a time."""
    names_by_symbol = dict(load_ticker_directory())
    options = list(names_by_symbol) if default in names_by_symbol else [default, *names_by_symbol]

    def _format(symbol):
        name = names_by_symbol.get(symbol)
        return f"{symbol} - {name}" if name else symbol

    ticker = st.selectbox(
        label,
        options=options,
        index=options.index(default),
        format_func=_format,
        accept_new_options=True,
        filter_mode="prefix",
        key=key,
    )
    return (ticker or "").strip().upper()


def render_line_chart(series_by_label, colors=None):
    """Overlay one or more named series on a single line chart."""
    st.line_chart(pd.DataFrame(series_by_label), color=colors)


def render_returns_chart(series_by_label, colors=None):
    """Overlay one or more daily % change series on a line chart, with the
    y-axis defaulting to +/-DAILY_CHANGE_AXIS_LIMIT so it reads consistently
    across tickers and lines up with the distribution chart below it; the
    user can still zoom/pan out to see moves beyond that band."""
    fig = go.Figure()
    palette = colors or PALETTE

    for (label, series), color in zip(series_by_label.items(), palette):
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series,
                mode="lines",
                name=label,
                line={"color": color, "width": 2},
            )
        )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Daily % Change",
        yaxis={"range": [-DAILY_CHANGE_AXIS_LIMIT, DAILY_CHANGE_AXIS_LIMIT]},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig)


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


def render_returns_histogram(returns, ticker, bin_size=0.2):
    """Histogram of daily % returns bucketed at a fixed width, normalized to a
    probability density (rather than raw counts) so the shape is comparable
    across stocks and date ranges, with a fitted normal curve overlaid and a
    rug of the individual observations underneath for per-day hover detail.

    The x-axis defaults to +/-DAILY_CHANGE_AXIS_LIMIT on every chart, so
    the same-shaped distribution looks the same width across tickers and time
    periods; the underlying data (and curve) still extend past it, so a more
    volatile stock's tails are there for the user to scroll/zoom out to.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=returns,
            xbins={"size": bin_size},
            histnorm="probability density",
            name=ticker,
            marker_color=HISTOGRAM_BAR_COLOR,
        )
    )

    mean, std = returns.mean(), returns.std()
    if std > 0:
        curve_limit = max(DAILY_CHANGE_AXIS_LIMIT, abs(returns.min()), abs(returns.max()))
        x_curve = np.linspace(-curve_limit, curve_limit, 200)
        y_curve = np.exp(-0.5 * ((x_curve - mean) / std) ** 2) / (std * (2 * np.pi) ** 0.5)
        fig.add_trace(
            go.Scatter(
                x=x_curve,
                y=y_curve,
                mode="lines",
                name="Normal fit",
                line={"color": HISTOGRAM_CURVE_COLOR, "width": 2},
            )
        )

    fig.add_trace(
        go.Scatter(
            x=returns,
            y=[0] * len(returns),
            mode="markers",
            marker={
                "symbol": "line-ns-open",
                "size": 8,
                "color": HISTOGRAM_CURVE_COLOR,
                "opacity": 0.5,
            },
            customdata=returns.index.strftime("%b %d, %Y"),
            hovertemplate="%{x:.2f}%<br>%{customdata}<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        xaxis_title="Daily % Change",
        yaxis_title="Density",
        xaxis={"range": [-DAILY_CHANGE_AXIS_LIMIT, DAILY_CHANGE_AXIS_LIMIT]},
        bargap=0.02,
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

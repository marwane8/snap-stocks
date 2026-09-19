import numpy as np
import plotly.graph_objects as go
import streamlit as st

from .data import load_ticker_directory
from .events import TIME_PERIOD_OPTIONS

PALETTE = ["#dc2626", "#93c5fd"]  # red, light blue
POSITIVE_COLOR = "#16a34a"  # green
NEGATIVE_COLOR = "#dc2626"  # red
CLOSE_LINE_COLOR = "#0891b2"  # cyan
HISTOGRAM_BAR_COLOR = "#fca5a5"  # light red
HISTOGRAM_CURVE_COLOR = "#b91c1c"  # dark red
HISTOGRAM_BASELINE_CURVE_COLOR = "#93c5fd"  # light blue - for a baseline (e.g. SPY) overlay
SCATTER_MARKER_COLOR = "#dc2626"  # red
SCATTER_FIT_LINE_COLOR = "#1e293b"  # dark slate
DAILY_CHANGE_AXIS_LIMIT = 20  # % - default axis bound for daily-change charts; user can zoom/pan past it
NORMALIZED_AXIS_TICK = 0.1
NORMALIZED_AXIS_TICK_LONG_RANGE = 1 # widens past NORMALIZED_LONG_RANGE_YEARS so gridlines don't crowd
NORMALIZED_LONG_RANGE_YEARS = 5


def render_time_period_selectbox(default="Global Financial Crisis (GFC)"):
    """The single 'Time period' dropdown (rolling periods + named crash events)
    shared by every view, so each one doesn't build its own options list."""
    index = TIME_PERIOD_OPTIONS.index(default) if default in TIME_PERIOD_OPTIONS else 0
    return st.selectbox("Time period", TIME_PERIOD_OPTIONS, index=index)


def render_ticker_selectbox(label, default, key, placeholder=None, label_visibility="visible"):
    """A single-ticker picker searchable by prefix, showing 'SYMBOL - Name',
    shared by every view that looks up one ticker at a time. default=None
    starts the field empty (index=None) with `placeholder` shown, for an
    optional slot rather than one that always has a ticker pre-selected."""
    names_by_symbol = dict(load_ticker_directory())

    if default is None:
        options = list(names_by_symbol)
        index = None
    else:
        options = list(names_by_symbol) if default in names_by_symbol else [default, *names_by_symbol]
        index = options.index(default)

    def _format(symbol):
        name = names_by_symbol.get(symbol)
        return f"{symbol} - {name}" if name else symbol

    ticker = st.selectbox(
        label,
        options=options,
        index=index,
        format_func=_format,
        accept_new_options=True,
        filter_mode="prefix",
        key=key,
        placeholder=placeholder,
        label_visibility=label_visibility,
    )
    return (ticker or "").strip().upper()


def render_normalized_chart(series_by_label, colors=None):
    """Line chart of one or more series rebased to 1.00 at the start of the
    period. Y-axis gridlines default to every 0.1, widening to every 0.5 once
    the period spans more than NORMALIZED_LONG_RANGE_YEARS, since a long-run
    normalized chart can swing several multiples and 0.1 gridlines get too
    dense to read."""
    fig = go.Figure()

    for i, (label, series) in enumerate(series_by_label.items()):
        line = {"width": 2}
        if colors:
            line["color"] = colors[i % len(colors)]
        fig.add_trace(
            go.Scatter(x=series.index, y=series, mode="lines", name=label, line=line)
        )

    span_years = max(
        (series.index.max() - series.index.min()).days / 365.25
        for series in series_by_label.values()
    )
    dtick = (
        NORMALIZED_AXIS_TICK_LONG_RANGE
        if span_years > NORMALIZED_LONG_RANGE_YEARS
        else NORMALIZED_AXIS_TICK
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis={"dtick": dtick},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig)


def render_returns_chart(series_by_label, colors=None):
    """Overlay one or more daily % change series on a line chart, with the
    y-axis defaulting to +/-DAILY_CHANGE_AXIS_LIMIT so it reads consistently
    across tickers and lines up with the distribution chart below it; the
    user can still zoom/pan out to see moves beyond that band."""
    fig = go.Figure()
    palette = colors or PALETTE

    for i, (label, series) in enumerate(series_by_label.items()):
        fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series,
                mode="lines",
                name=label,
                line={"color": palette[i % len(palette)], "width": 2},
            )
        )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Daily % Change",
        yaxis={"range": [-DAILY_CHANGE_AXIS_LIMIT, DAILY_CHANGE_AXIS_LIMIT], "dtick": 5},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig)


def render_returns_scatter(returns_a, returns_b, label_a, label_b):
    """Scatter each date's two tickers' daily % changes against each other -
    the classic 'Scatter, X vs Y' chart: points strung along a diagonal mean
    the two move together that day, a shapeless cloud means they don't.
    Square in both pixel dimensions and axis units (equal % per pixel on
    both axes, via scaleanchor) so a 45-degree line always reads as true 1:1,
    never stretched by the figure's own aspect ratio. Hovering a point shows
    the date it happened on plus both tickers' % change that day. A
    least-squares fit line is overlaid, labeled with its slope (label_a's
    beta against label_b), to show how tightly the two actually track."""
    limit = DAILY_CHANGE_AXIS_LIMIT

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=returns_b,
            y=returns_a,
            mode="markers",
            marker={"size": 6, "color": SCATTER_MARKER_COLOR, "opacity": 0.6},
            customdata=returns_a.index.strftime("%b %d, %Y"),
            hovertemplate=(
                f"{label_a}: %{{y:.2f}}%<br>{label_b}: %{{x:.2f}}%<br>%{{customdata}}<extra></extra>"
            ),
            showlegend=False,
        )
    )

    slope, intercept = np.polyfit(returns_b, returns_a, 1)
    x_fit = np.array([-limit, limit])
    y_fit = slope * x_fit + intercept
    fig.add_trace(
        go.Scatter(
            x=x_fit,
            y=y_fit,
            mode="lines",
            name=f"Fit (β={slope:.2f})",
            line={"color": SCATTER_FIT_LINE_COLOR, "width": 2},
            hoverinfo="skip",
        )
    )

    axis_style = {"range": [-limit, limit], "zeroline": True, "zerolinewidth": 2, "zerolinecolor": "#94a3b8"}
    fig.update_layout(
        xaxis_title=label_b,
        yaxis_title=label_a,
        xaxis=axis_style,
        yaxis={**axis_style, "scaleanchor": "x", "scaleratio": 1},
        width=480,
        height=480,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig, width="content")


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


def render_returns_histogram(returns, ticker, baseline_returns=None, baseline_label=None, bin_size=0.2):
    """Histogram of daily % returns bucketed at a fixed width, normalized to a
    probability density (rather than raw counts) so the shape is comparable
    across stocks and date ranges, with a fitted normal curve overlaid and a
    rug of the individual observations underneath for per-day hover detail.
    When baseline_returns is given (e.g. SPY), its own normal curve is
    overlaid too, so a narrower/wider bell next to it reads as lower/higher
    volatility than the baseline.

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

    extent = [abs(returns.min()), abs(returns.max())]
    if baseline_returns is not None:
        extent += [abs(baseline_returns.min()), abs(baseline_returns.max())]
    curve_limit = max(DAILY_CHANGE_AXIS_LIMIT, *extent)
    x_curve = np.linspace(-curve_limit, curve_limit, 200)

    mean, std = returns.mean(), returns.std()
    if std > 0:
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

    if baseline_returns is not None:
        baseline_mean, baseline_std = baseline_returns.mean(), baseline_returns.std()
        if baseline_std > 0:
            y_baseline_curve = np.exp(
                -0.5 * ((x_curve - baseline_mean) / baseline_std) ** 2
            ) / (baseline_std * (2 * np.pi) ** 0.5)
            fig.add_trace(
                go.Scatter(
                    x=x_curve,
                    y=y_baseline_curve,
                    mode="lines",
                    name=f"{baseline_label} Normal fit",
                    line={"color": HISTOGRAM_BASELINE_CURVE_COLOR, "width": 2},
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
    """Overlay one or more named series on a single bar chart. Multiple
    series are layered with transparency rather than grouped side-by-side,
    since grouped bars are illegible at daily-bar time-series density."""
    fig = go.Figure()
    overlay = len(series_by_label) > 1

    for i, (label, series) in enumerate(series_by_label.items()):
        marker = {"color": colors[i % len(colors)]} if colors else {}
        fig.add_trace(
            go.Bar(x=series.index, y=series, name=label, marker=marker, opacity=0.7 if overlay else 1.0)
        )

    fig.update_layout(
        xaxis_title="Date",
        barmode="overlay" if overlay else "relative",
        bargap=0.02,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
    )

    st.plotly_chart(fig)


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

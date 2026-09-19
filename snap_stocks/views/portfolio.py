import pandas as pd
import streamlit as st

from .. import charts, metrics
from ..data import fetch_history
from ..events import resolve_time_period

BASELINE = "SPY"
MAX_ROWS = 10


def _init_row_state():
    if "portfolio_row_ids" not in st.session_state:
        st.session_state.portfolio_row_ids = [0]
        st.session_state.portfolio_next_row_id = 1


def _add_row():
    if len(st.session_state.portfolio_row_ids) < MAX_ROWS:
        st.session_state.portfolio_row_ids.append(st.session_state.portfolio_next_row_id)
        st.session_state.portfolio_next_row_id += 1


def _remove_row(row_id):
    st.session_state.portfolio_row_ids.remove(row_id)


def _render_allocation_inputs():
    """A growing list of (ticker, dollar amount) rows, starting at one and
    growing via the 'Add ticker' button up to MAX_ROWS - rather than a fixed
    block of empty inputs. Each row is keyed by an ever-incrementing row id
    (not its position), so removing a row from the middle can't collide with
    or reset another row's widget state. Ticker fields use the same
    searchable 'SYMBOL - Name' picker as the other pages."""
    _init_row_state()

    header_ticker, header_amount, _ = st.columns([2, 1, 0.4])
    with header_ticker:
        st.caption("TICKER")
    with header_amount:
        st.caption("AMOUNT ($)")

    allocations = {}
    row_ids = st.session_state.portfolio_row_ids
    for row_id in list(row_ids):
        col_ticker, col_amount, col_remove = st.columns([2, 1, 0.4])
        with col_ticker:
            ticker = charts.render_ticker_selectbox(
                f"Ticker (row {row_id})",
                default=None,
                key=f"portfolio_ticker_{row_id}",
                placeholder="e.g. AAPL",
                label_visibility="collapsed",
            )
        with col_amount:
            amount = st.number_input(
                f"Amount (row {row_id})",
                key=f"portfolio_amount_{row_id}",
                min_value=0.0,
                value=0.0,
                step=100.0,
                format="%.2f",
                label_visibility="collapsed",
            )
        with col_remove:
            if len(row_ids) > 1:
                st.button("✕", key=f"portfolio_remove_{row_id}", on_click=_remove_row, args=(row_id,))
        if ticker and amount > 0:
            allocations[ticker] = allocations.get(ticker, 0.0) + amount

    if len(row_ids) < MAX_ROWS:
        st.button("+ Add ticker", on_click=_add_row)
    else:
        st.caption(f"Maximum of {MAX_ROWS} tickers reached.")

    return allocations


def _build_portfolio_history(allocations, period_kwargs):
    """Combine each ticker's OHLC into one synthetic 'Portfolio' history:
    buy shares_i = dollar_i / close_i(first common day) of each ticker on the
    first day all of them have data, then hold that fixed share count across
    the period. Every OHLC column is that same shares-weighted sum, so the
    result behaves like an actual position's price history for every
    existing chart/metric downstream (candlestick, returns, ...)."""
    histories = {}
    missing = []
    for ticker in allocations:
        history = fetch_history(ticker, **period_kwargs)
        if history.empty:
            missing.append(ticker)
        else:
            histories[ticker] = history

    if missing:
        st.warning(f"No data found for: {', '.join(sorted(missing))}")

    allocations = {t: a for t, a in allocations.items() if t in histories}
    if not allocations:
        return None, None

    common_index = None
    for history in histories.values():
        common_index = history.index if common_index is None else common_index.intersection(history.index)
    common_index = common_index.sort_values()

    if len(common_index) < 2:
        st.warning("Not enough overlapping trading days across the selected tickers for this period.")
        return None, None

    shares = {
        ticker: amount / histories[ticker].loc[common_index, "Close"].iloc[0]
        for ticker, amount in allocations.items()
    }

    portfolio = pd.DataFrame(index=common_index)
    for column in ["Open", "High", "Low", "Close"]:
        portfolio[column] = sum(
            histories[ticker].loc[common_index, column] * shares[ticker] for ticker in allocations
        )

    return portfolio, allocations


def render():
    st.title("Portfolio Simulator")
    st.caption("Enter a ticker and dollar amount, then add up to 10 to build a hypothetical portfolio.")

    allocations = _render_allocation_inputs()
    label = charts.render_time_period_selectbox()

    if not allocations:
        st.info("Enter at least one ticker and dollar amount to simulate a portfolio.")
        return

    period_kwargs = resolve_time_period(label)
    portfolio, allocations = _build_portfolio_history(allocations, period_kwargs)
    if portfolio is None:
        return

    total_invested = sum(allocations.values())
    # Escape "$" so st.caption's markdown/KaTeX rendering doesn't treat a
    # pair of dollar signs as inline math and italicize everything between.
    composition = ", ".join(f"{t} (\\${a:,.0f})" for t, a in allocations.items())
    st.caption(f"Portfolio: {composition} — Total invested: \\${total_invested:,.0f}")

    portfolio_metrics = None
    baseline_history = None
    baseline_metrics = None
    returns_df = None

    if len(portfolio) >= 2:
        portfolio_metrics = metrics.compute_return_metrics(portfolio)

        start = portfolio.index[0]
        end = portfolio.index[-1] + pd.Timedelta(days=1)
        baseline_history = fetch_history(BASELINE, start=start, end=end)
        if len(baseline_history) >= 2:
            # Total return/annual return/volatility are scale-invariant (they
            # come from % changes), but scale Close by the same total dollar
            # amount so the "Price" tile shows what your money would be
            # worth today if it had all gone into SPY - an apples-to-apples
            # dollar figure next to the Portfolio tile, not SPY's own share price.
            spy_shares = total_invested / baseline_history["Close"].iloc[0]
            baseline_value = pd.DataFrame({"Close": baseline_history["Close"] * spy_shares})
            baseline_metrics = metrics.compute_return_metrics(baseline_value)

        charts.render_metrics_row("Portfolio", label, portfolio_metrics)
        if baseline_metrics is not None:
            charts.render_metrics_row(BASELINE, label, baseline_metrics)

            returns_df = pd.DataFrame(
                {"Portfolio": portfolio_metrics["returns"], BASELINE: baseline_metrics["returns"]}
            ).dropna()
            if len(returns_df) >= 2:
                correlation = returns_df["Portfolio"].corr(returns_df[BASELINE])
                charts.render_correlation_card("Portfolio", BASELINE, correlation)
    else:
        st.info("Not enough data in this range to compute volatility metrics.")

    st.subheader(f"Portfolio — Price ({label})")
    charts.render_candlestick_chart(portfolio, "Portfolio")

    if baseline_history is not None and len(baseline_history) >= 2:
        st.subheader(f"Portfolio vs {BASELINE} — Normalized ({label})")
        charts.render_normalized_chart(
            {
                "Portfolio": metrics.normalize_to_start(portfolio["Close"]),
                BASELINE: metrics.normalize_to_start(baseline_history["Close"]),
            },
            colors=charts.PALETTE,
        )

    if portfolio_metrics is not None:
        st.subheader(f"Portfolio vs {BASELINE} — Daily % Change ({label})")
        if baseline_metrics is not None:
            col_scatter, col_line = st.columns(2)
            with col_scatter:
                if returns_df is not None and len(returns_df) >= 2:
                    charts.render_returns_scatter(
                        returns_df["Portfolio"], returns_df[BASELINE], "Portfolio", BASELINE
                    )
            with col_line:
                charts.render_returns_chart(
                    {"Portfolio": portfolio_metrics["returns"], BASELINE: baseline_metrics["returns"]},
                    colors=charts.PALETTE,
                )
        else:
            charts.render_returns_chart(
                {"Portfolio": portfolio_metrics["returns"]}, colors=charts.PALETTE[:1]
            )

    if portfolio_metrics is not None:
        st.subheader(f"Portfolio — Daily % Change Distribution ({label})")
        charts.render_returns_histogram(
            portfolio_metrics["returns"],
            "Portfolio",
            baseline_returns=baseline_metrics["returns"] if baseline_metrics is not None else None,
            baseline_label=BASELINE,
        )

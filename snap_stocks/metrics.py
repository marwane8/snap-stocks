TRADING_DAYS_PER_YEAR = 252


def compute_return_metrics(history):
    """Total return, annualized return, and annualized volatility from close-to-close
    daily returns for a single (already-fetched) price history."""
    returns = history["Close"].pct_change(fill_method=None).dropna() * 100

    start_price = history["Close"].iloc[0]
    end_price = history["Close"].iloc[-1]
    total_return = (end_price / start_price - 1) * 100
    annualized_volatility = returns.std() * (TRADING_DAYS_PER_YEAR ** 0.5)

    days_elapsed = (history.index[-1] - history.index[0]).days
    years_elapsed = days_elapsed / 365.25
    # yfinance's "1y" period returns ~364 days due to weekend/holiday edges, so use
    # a tolerance rather than a strict >= 1 to avoid misclassifying a full year as "under".
    annual_return = (
        ((end_price / start_price) ** (1 / years_elapsed) - 1) * 100
        if days_elapsed >= 350
        else None
    )

    return {
        "returns": returns,
        "total_return": total_return,
        "annual_return": annual_return,
        "annualized_volatility": annualized_volatility,
        "last_price": end_price,
        "last_change_pct": returns.iloc[-1] if not returns.empty else None,
    }


def compute_price_range(history):
    """Last close, high, and low over a given (already-fetched) price
    history, from the High/Low columns rather than just Close so the range
    reflects true intraday extremes. The caller decides the window - a fixed
    trailing year for a "52-week range", or whatever period is selected
    elsewhere on the page."""
    return {
        "price": history["Close"].iloc[-1],
        "low": history["Low"].min(),
        "high": history["High"].max(),
    }


def normalize_to_start(series):
    """Rebase a price series so it starts at 1.00, for relative-performance comparison."""
    return series / series.iloc[0]

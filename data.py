import csv
import warnings
from pathlib import Path

import streamlit as st
import yfinance as yf

warnings.filterwarnings(
    "ignore",
    message="The default dtype for empty Series will be 'object'",
    category=FutureWarning,
)

TICKER_DIRECTORY_DIR = Path(__file__).parent / "tickers"
TICKER_DIRECTORY_FILES = ["tickers_stock.csv", "tickers_etf.csv"]


@st.cache_data
def load_ticker_directory():
    """(symbol, name) pairs for every actively listed stock and ETF ticker, in file order."""
    directory = []
    for filename in TICKER_DIRECTORY_FILES:
        with open(TICKER_DIRECTORY_DIR / filename, newline="", encoding="utf-8") as f:
            directory.extend((row["Symbol"], row["Name"]) for row in csv.DictReader(f))
    return directory


def fetch_history(ticker, *, period=None, start=None, end=None):
    """Fetch OHLCV history for a single ticker, by rolling period or explicit date range."""
    if period:
        history = yf.Ticker(ticker).history(period=period)
    else:
        history = yf.Ticker(ticker).history(start=start, end=end)
    # Drop an in-progress trading session's bar, which yfinance sometimes
    # returns with NaN OHLC (while Volume partially populates).
    return history.dropna(subset=["Close"])


def fetch_closes(tickers, *, period=None, start=None, end=None):
    """Fetch close-price series for multiple tickers, skipping any with no data."""
    closes = {}
    for ticker in tickers:
        history = fetch_history(ticker, period=period, start=start, end=end)
        if not history.empty:
            closes[ticker] = history["Close"]
    return closes

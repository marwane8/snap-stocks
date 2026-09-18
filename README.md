# 📸 Snap Stocks

A little Streamlit app for peeking at stocks and ETFs — no spreadsheets required.

**🔗 Live app:** [snap-stocks.streamlit.app](https://snap-stocks.streamlit.app/)

## What's inside

- **📈 Stock Explorer** — look up a ticker and see its price, volume, and how it's doing against SPY.
- **⚖️ Stock Compare** — put two tickers side by side and see who's winning.
- **🔗 Correlation Matrix** — pick a handful of tickers and see how much they move together (and how normalized prices stack up).

## Why correlations, though?

The real point of this app is watching how correlations between stocks and ETFs shift during market corrections — diversification you can count on in calm markets has a habit of quietly disappearing exactly when you need it most. On the Correlation Matrix page, use the **Time period** dropdown to jump straight to a specific crash or correction (Dot-Com Crash, the 2008 GFC, COVID-19, the 2025 Tariff Sell-Off, and more) instead of a rolling window, and check whether your picks moved together tighter than usual. 🐻📉

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit gives you and start snooping around. 🕵️

The app's code lives in the [`snap_stocks/`](snap_stocks) package; `app.py` at the root just wires up the pages.

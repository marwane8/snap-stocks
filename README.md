# 📸 Snap Stocks

A little Streamlit app for peeking at stocks and ETFs — no spreadsheets required.

## What's inside

- **📈 Stock Explorer** — look up a ticker and see its price, volume, and how it's doing against SPY.
- **⚖️ Stock Compare** — put two tickers side by side and see who's winning.
- **🔗 Correlation Matrix** — pick a handful of tickers and see how much they move together (and how normalized prices stack up).

## Running it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit gives you and start snooping around. 🕵️

The app's code lives in the [`snap_stocks/`](snap_stocks) package; `app.py` at the root just wires up the pages.

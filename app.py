import streamlit as st

from snap_stocks.views import compare, correlation, stock_explorer

st.set_page_config(page_title="Snap", page_icon="📊", layout="wide")

pages = [
    st.Page(
        stock_explorer.render,
        title="Stock Explorer",
        icon="📈",
        url_path="stock-explorer",
        default=True,
    ),
    st.Page(
        compare.render,
        title="Stock Compare",
        icon="⚖️",
        url_path="stock-compare",
    ),
    st.Page(
        correlation.render,
        title="Correlation Matrix",
        icon="🔗",
        url_path="correlation-matrix",
    ),
]

nav = st.navigation(pages, position="top")
nav.run()

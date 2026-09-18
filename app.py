import streamlit as st

from snap_stocks.views import compare, correlation, stock_explorer

st.set_page_config(page_title="Snap", page_icon="📊", layout="wide")

pages = [
    st.Page(
        correlation.render,
        title="Correlation Matrix",
        icon="🔗",
        url_path="correlation-matrix",
        default=True,
    ),
    st.Page(
        compare.render,
        title="Stock Compare",
        icon="⚖️",
        url_path="stock-compare",
    ),
    st.Page(
        stock_explorer.render,
        title="Stock Explorer",
        icon="📈",
        url_path="stock-explorer",
    ),
]

nav = st.navigation(pages, position="top")
nav.run()

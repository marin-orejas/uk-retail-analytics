"""Streamlit dashboard entry point."""

import streamlit as st
import plotly.express as px

from db import run_query

st.set_page_config(
    page_title="UK Retail Analytics",
    page_icon="🛒",
    layout="wide",
)


# Sidebar nav
st.sidebar.title("UK Retail Analytics")
page = st.sidebar.radio(
    "Page",
    ["Overview", "Customers", "Products", "Geography", "Trends"],
)
st.sidebar.caption("Data: UCI Online Retail (Dec 2010 – Dec 2011)")


def page_overview():
    st.title("Overview")

    kpis = run_query("""
        SELECT
            SUM(order_total)               AS revenue,
            COUNT(*)                       AS orders,
            COUNT(DISTINCT customer_id)    AS customers,
            AVG(order_total)               AS aov
        FROM v_order_totals;
    """).iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Revenue", f"£{kpis['revenue']:,.0f}")
    c2.metric("Orders", f"{int(kpis['orders']):,}")
    c3.metric("Customers", f"{int(kpis['customers']):,}")
    c4.metric("Avg order value", f"£{kpis['aov']:.2f}")

    st.subheader("Monthly revenue")
    monthly = run_query("SELECT * FROM v_monthly_revenue ORDER BY month;")
    fig = px.line(monthly, x="month", y="revenue", markers=True)
    fig.update_layout(yaxis_title="Revenue (£)", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 5 countries by revenue")
    top_c = run_query("""
        SELECT country, revenue
        FROM v_country_revenue
        ORDER BY revenue DESC
        LIMIT 5;
    """)
    st.dataframe(top_c, hide_index=True, use_container_width=True)


# Placeholders for the other pages, filled in later commits.
def page_placeholder(name: str):
    st.title(name)
    st.info("Coming soon.")


PAGES = {
    "Overview":  page_overview,
    "Customers": lambda: page_placeholder("Customers"),
    "Products":  lambda: page_placeholder("Products"),
    "Geography": lambda: page_placeholder("Geography"),
    "Trends":    lambda: page_placeholder("Trends"),
}

PAGES[page]()

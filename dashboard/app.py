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
def page_customers():
    st.title("Customers")

    rfm = run_query("""
        WITH ranked AS (
            SELECT
                customer_id,
                recency_days,
                frequency,
                monetary,
                NTILE(5) OVER (ORDER BY recency_days DESC) AS r,
                NTILE(5) OVER (ORDER BY frequency)         AS f,
                NTILE(5) OVER (ORDER BY monetary)          AS m
            FROM v_customer_rfm
        )
        SELECT *,
            CASE
                WHEN r >= 4 AND (f + m) >= 8 THEN 'Champions'
                WHEN r >= 3 AND (f + m) >= 6 THEN 'Loyal'
                WHEN r >= 4 AND (f + m) <= 5 THEN 'New / Promising'
                WHEN r <= 2 AND (f + m) >= 7 THEN 'At Risk'
                WHEN r <= 2 AND (f + m) <= 4 THEN 'Lost'
                ELSE 'Regular'
            END AS segment
        FROM ranked;
    """)

    c1, c2, c3 = st.columns(3)
    c1.metric("Customers", f"{len(rfm):,}")
    c2.metric("Avg recency (days)", f"{rfm['recency_days'].mean():.0f}")
    c3.metric("Avg spend", f"£{rfm['monetary'].mean():.0f}")

    st.subheader("Segments")
    seg = (
        rfm.groupby("segment")
        .agg(customers=("customer_id", "count"),
             revenue=("monetary", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    c1, c2 = st.columns([1, 1])
    with c1:
        fig = px.bar(seg, x="segment", y="customers", color="segment")
        fig.update_layout(showlegend=False, xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.dataframe(
            seg.assign(revenue=seg["revenue"].round(0)),
            hide_index=True, use_container_width=True,
        )

    st.subheader("RFM scatter (recency vs spend)")
    fig = px.scatter(
        rfm, x="recency_days", y="monetary",
        color="segment", size="frequency",
        hover_data=["customer_id"], opacity=0.7,
    )
    fig.update_layout(yaxis_title="Spend (£)", xaxis_title="Days since last order")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 customers")
    top = (
        rfm.sort_values("monetary", ascending=False)
        .head(10)[["customer_id", "frequency", "recency_days", "monetary", "segment"]]
    )
    st.dataframe(top, hide_index=True, use_container_width=True)


def page_placeholder(name: str):
    st.title(name)
    st.info("Coming soon.")


PAGES = {
    "Overview":  page_overview,
    "Customers": page_customers,
    "Products":  lambda: page_placeholder("Products"),
    "Geography": lambda: page_placeholder("Geography"),
    "Trends":    lambda: page_placeholder("Trends"),
}

PAGES[page]()

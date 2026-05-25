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


def page_products():
    st.title("Products")

    top_rev = run_query("""
        SELECT stock_code, description, units_sold, revenue
        FROM v_product_performance
        ORDER BY revenue DESC
        LIMIT 20;
    """)

    total_products = run_query("SELECT COUNT(*) AS n FROM v_product_performance;")["n"].iloc[0]
    c1, c2 = st.columns(2)
    c1.metric("Products sold", f"{int(total_products):,}")
    c2.metric("Top product revenue", f"£{top_rev['revenue'].iloc[0]:,.0f}")

    st.subheader("Top 20 products by revenue")
    fig = px.bar(
        top_rev.sort_values("revenue"),
        x="revenue", y="description", orientation="h",
    )
    fig.update_layout(yaxis_title="", xaxis_title="Revenue (£)", height=600)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Slow movers")
    slow = run_query("""
        SELECT stock_code, description, units_sold, revenue
        FROM v_product_performance
        WHERE units_sold > 0 AND units_sold < 10
        ORDER BY units_sold ASC
        LIMIT 25;
    """)
    st.dataframe(slow, hide_index=True, use_container_width=True)


def page_geography():
    st.title("Geography")

    geo = run_query("""
        SELECT country, orders, customers, revenue
        FROM v_country_revenue
        ORDER BY revenue DESC;
    """)

    c1, c2, c3 = st.columns(3)
    c1.metric("Countries", f"{len(geo)}")
    c2.metric("UK share",
              f"{100 * geo.loc[geo['country'] == 'United Kingdom', 'revenue'].sum() / geo['revenue'].sum():.1f}%")
    c3.metric("Non-UK revenue",
              f"£{geo.loc[geo['country'] != 'United Kingdom', 'revenue'].sum():,.0f}")

    st.subheader("Revenue by country (map)")
    fig = px.choropleth(
        geo, locations="country", locationmode="country names",
        color="revenue", color_continuous_scale="Blues",
        scope="europe",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top non-UK markets")
    non_uk = geo[geo["country"] != "United Kingdom"].head(15)
    fig = px.bar(non_uk.sort_values("revenue"),
                 x="revenue", y="country", orientation="h")
    fig.update_layout(yaxis_title="", xaxis_title="Revenue (£)")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(geo, hide_index=True, use_container_width=True)


def page_trends():
    st.title("Trends")

    monthly = run_query("""
        SELECT
            month,
            revenue,
            LAG(revenue) OVER (ORDER BY month) AS prev_month
        FROM v_monthly_revenue
        ORDER BY month;
    """)
    monthly["mom_growth_pct"] = (
        100 * (monthly["revenue"] - monthly["prev_month"]) / monthly["prev_month"]
    )

    st.subheader("Month-over-month growth")
    fig = px.bar(monthly.dropna(), x="month", y="mom_growth_pct",
                 color="mom_growth_pct", color_continuous_scale="RdYlGn")
    fig.update_layout(yaxis_title="MoM %", xaxis_title="", coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Day of week x hour")
    heat = run_query("""
        SELECT
            EXTRACT(ISODOW FROM invoice_date)::int AS dow,
            EXTRACT(HOUR   FROM invoice_date)::int AS hour,
            COUNT(DISTINCT invoice_no) AS orders
        FROM invoices
        WHERE is_cancellation = FALSE
        GROUP BY dow, hour
        ORDER BY dow, hour;
    """)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    heat["day"] = heat["dow"].map(lambda d: days[d - 1])
    pivot = heat.pivot(index="day", columns="hour", values="orders").reindex(days)
    fig = px.imshow(pivot, color_continuous_scale="Blues", aspect="auto",
                    labels=dict(color="Orders"))
    fig.update_layout(xaxis_title="Hour", yaxis_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Cancellation rate by month")
    canc = run_query("""
        SELECT
            DATE_TRUNC('month', invoice_date)::date AS month,
            COUNT(*) FILTER (WHERE is_cancellation)      AS cancellations,
            COUNT(*) FILTER (WHERE NOT is_cancellation)  AS orders
        FROM invoices
        GROUP BY 1
        ORDER BY 1;
    """)
    canc["rate_pct"] = 100 * canc["cancellations"] / (canc["orders"] + canc["cancellations"])
    fig = px.line(canc, x="month", y="rate_pct", markers=True)
    fig.update_layout(yaxis_title="Cancellation rate %", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True)


PAGES = {
    "Overview":  page_overview,
    "Customers": page_customers,
    "Products":  page_products,
    "Geography": page_geography,
    "Trends":    page_trends,
}

PAGES[page]()

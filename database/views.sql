-- Views used by the dashboard
-- These aggregate the raw tables so Streamlit can pull pre-shaped data.


-- Order totals (one row per invoice, excluding cancellations)
CREATE OR REPLACE VIEW v_order_totals AS
SELECT
    i.invoice_no,
    i.invoice_date,
    i.customer_id,
    i.country_id,
    SUM(ii.quantity * ii.unit_price) AS order_total,
    SUM(ii.quantity)                 AS units
FROM invoices i
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY i.invoice_no, i.invoice_date, i.customer_id, i.country_id;


-- Monthly revenue
CREATE OR REPLACE VIEW v_monthly_revenue AS
SELECT
    DATE_TRUNC('month', invoice_date)::date AS month,
    COUNT(*)        AS orders,
    SUM(order_total) AS revenue
FROM v_order_totals
GROUP BY 1;


-- Revenue by country
CREATE OR REPLACE VIEW v_country_revenue AS
SELECT
    co.name AS country,
    COUNT(DISTINCT vot.invoice_no)  AS orders,
    COUNT(DISTINCT vot.customer_id) AS customers,
    SUM(vot.order_total)            AS revenue
FROM v_order_totals vot
JOIN countries co ON co.country_id = vot.country_id
GROUP BY co.name;


-- Product performance
CREATE OR REPLACE VIEW v_product_performance AS
SELECT
    p.stock_code,
    p.description,
    SUM(ii.quantity)                 AS units_sold,
    SUM(ii.quantity * ii.unit_price) AS revenue
FROM products p
JOIN invoice_items ii ON ii.stock_code = p.stock_code
JOIN invoices i       ON i.invoice_no  = ii.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY p.stock_code, p.description;


-- RFM base (customer level, no segmentation labels)
CREATE OR REPLACE VIEW v_customer_rfm AS
WITH base AS (
    SELECT
        customer_id,
        MAX(invoice_date) AS last_purchase,
        COUNT(*)          AS frequency,
        SUM(order_total)  AS monetary
    FROM v_order_totals
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
),
ref AS (SELECT MAX(invoice_date) AS ref_date FROM invoices)
SELECT
    b.customer_id,
    (ref.ref_date::date - b.last_purchase::date) AS recency_days,
    b.frequency,
    b.monetary
FROM base b CROSS JOIN ref;

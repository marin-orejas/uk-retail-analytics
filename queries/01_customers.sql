-- Customer analytics queries
-- All revenue figures ignore cancellation invoices unless stated otherwise.


-- 1. Top 20 customers by total spend
SELECT
    c.customer_id,
    co.name AS country,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS total_spend,
    COUNT(DISTINCT i.invoice_no) AS orders
FROM customers c
JOIN countries co  ON co.country_id = c.country_id
JOIN invoices i    ON i.customer_id = c.customer_id AND i.is_cancellation = FALSE
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
GROUP BY c.customer_id, co.name
ORDER BY total_spend DESC
LIMIT 20;


-- 2. RFM scores
-- Recency  = days since last purchase (reference = max invoice date in the data)
-- Frequency = number of distinct invoices
-- Monetary  = total spend
-- NTILE(5) splits each metric into 5 buckets, then we glue them into an RFM code.
WITH base AS (
    SELECT
        i.customer_id,
        MAX(i.invoice_date)                              AS last_purchase,
        COUNT(DISTINCT i.invoice_no)                     AS frequency,
        SUM(ii.quantity * ii.unit_price)                 AS monetary
    FROM invoices i
    JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
    WHERE i.is_cancellation = FALSE
      AND i.customer_id IS NOT NULL
    GROUP BY i.customer_id
),
ref AS (SELECT MAX(invoice_date) AS ref_date FROM invoices),
scored AS (
    SELECT
        b.customer_id,
        (ref.ref_date::date - b.last_purchase::date) AS recency_days,
        b.frequency,
        ROUND(b.monetary::numeric, 2)                AS monetary,
        NTILE(5) OVER (ORDER BY (ref.ref_date::date - b.last_purchase::date) DESC) AS r_score,
        NTILE(5) OVER (ORDER BY b.frequency)         AS f_score,
        NTILE(5) OVER (ORDER BY b.monetary)          AS m_score
    FROM base b CROSS JOIN ref
)
SELECT
    customer_id,
    recency_days,
    frequency,
    monetary,
    r_score, f_score, m_score,
    CONCAT(r_score, f_score, m_score) AS rfm
FROM scored
ORDER BY monetary DESC;


-- 3. Simple RFM segments
-- We label customers based on R and F+M, similar to typical retail playbooks.
WITH base AS (
    SELECT
        i.customer_id,
        MAX(i.invoice_date) AS last_purchase,
        COUNT(DISTINCT i.invoice_no) AS frequency,
        SUM(ii.quantity * ii.unit_price) AS monetary
    FROM invoices i
    JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
    WHERE i.is_cancellation = FALSE AND i.customer_id IS NOT NULL
    GROUP BY i.customer_id
),
ref AS (SELECT MAX(invoice_date) AS ref_date FROM invoices),
scored AS (
    SELECT
        b.customer_id,
        (ref.ref_date::date - b.last_purchase::date) AS recency_days,
        b.frequency,
        b.monetary,
        NTILE(5) OVER (ORDER BY (ref.ref_date::date - b.last_purchase::date) DESC) AS r,
        NTILE(5) OVER (ORDER BY b.frequency)         AS f,
        NTILE(5) OVER (ORDER BY b.monetary)          AS m
    FROM base b CROSS JOIN ref
)
SELECT
    CASE
        WHEN r >= 4 AND (f + m) >= 8 THEN 'Champions'
        WHEN r >= 3 AND (f + m) >= 6 THEN 'Loyal'
        WHEN r >= 4 AND (f + m) <= 5 THEN 'New / Promising'
        WHEN r <= 2 AND (f + m) >= 7 THEN 'At Risk'
        WHEN r <= 2 AND (f + m) <= 4 THEN 'Lost'
        ELSE 'Regular'
    END AS segment,
    COUNT(*) AS customers,
    ROUND(SUM(monetary)::numeric, 2) AS segment_revenue
FROM scored
GROUP BY segment
ORDER BY segment_revenue DESC;


-- 4. One-time vs repeat customers
SELECT
    CASE WHEN orders = 1 THEN 'One-time' ELSE 'Repeat' END AS type,
    COUNT(*) AS customers,
    ROUND(AVG(orders)::numeric, 2) AS avg_orders
FROM (
    SELECT customer_id, COUNT(DISTINCT invoice_no) AS orders
    FROM invoices
    WHERE is_cancellation = FALSE AND customer_id IS NOT NULL
    GROUP BY customer_id
) t
GROUP BY type;


-- 5. Cohort retention
-- First purchase month defines the cohort. We then count how many of those
-- customers came back in each following month.
WITH first_purchase AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(invoice_date)) AS cohort_month
    FROM invoices
    WHERE is_cancellation = FALSE AND customer_id IS NOT NULL
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT
        i.customer_id,
        DATE_TRUNC('month', i.invoice_date) AS active_month
    FROM invoices i
    WHERE i.is_cancellation = FALSE AND i.customer_id IS NOT NULL
)
SELECT
    fp.cohort_month,
    a.active_month,
    EXTRACT(YEAR FROM AGE(a.active_month, fp.cohort_month)) * 12
        + EXTRACT(MONTH FROM AGE(a.active_month, fp.cohort_month)) AS months_since_first,
    COUNT(DISTINCT fp.customer_id) AS active_customers
FROM first_purchase fp
JOIN activity a USING (customer_id)
GROUP BY fp.cohort_month, a.active_month
ORDER BY fp.cohort_month, a.active_month;

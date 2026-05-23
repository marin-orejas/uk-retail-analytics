-- Sales trends queries


-- 1. Revenue by month
SELECT
    DATE_TRUNC('month', i.invoice_date)::date AS month,
    COUNT(DISTINCT i.invoice_no)              AS orders,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS revenue
FROM invoices i
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY 1
ORDER BY 1;


-- 2. Revenue by day of week
SELECT
    TO_CHAR(i.invoice_date, 'Day') AS day_name,
    EXTRACT(ISODOW FROM i.invoice_date)::int AS dow,
    COUNT(DISTINCT i.invoice_no) AS orders,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS revenue
FROM invoices i
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY day_name, dow
ORDER BY dow;


-- 3. Revenue by hour of day
SELECT
    EXTRACT(HOUR FROM i.invoice_date)::int AS hour,
    COUNT(DISTINCT i.invoice_no) AS orders,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS revenue
FROM invoices i
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY hour
ORDER BY hour;


-- 4. Day of week x hour heatmap data
SELECT
    EXTRACT(ISODOW FROM i.invoice_date)::int AS dow,
    EXTRACT(HOUR FROM i.invoice_date)::int   AS hour,
    COUNT(DISTINCT i.invoice_no)             AS orders
FROM invoices i
WHERE i.is_cancellation = FALSE
GROUP BY dow, hour
ORDER BY dow, hour;


-- 5. Month-over-month growth
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', i.invoice_date)::date AS month,
        SUM(ii.quantity * ii.unit_price) AS revenue
    FROM invoices i
    JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
    WHERE i.is_cancellation = FALSE
    GROUP BY 1
)
SELECT
    month,
    ROUND(revenue::numeric, 2) AS revenue,
    ROUND(LAG(revenue) OVER (ORDER BY month)::numeric, 2) AS prev_month,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / NULLIF(LAG(revenue) OVER (ORDER BY month), 0)::numeric,
        2
    ) AS mom_growth_pct
FROM monthly
ORDER BY month;

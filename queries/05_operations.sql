-- Operations queries


-- 1. Average order value overall
SELECT
    ROUND(AVG(order_total)::numeric, 2) AS avg_order_value,
    ROUND(
        (PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY order_total))::numeric,
        2
    ) AS median_order_value
FROM (
    SELECT i.invoice_no, SUM(ii.quantity * ii.unit_price) AS order_total
    FROM invoices i
    JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
    WHERE i.is_cancellation = FALSE
    GROUP BY i.invoice_no
) t;


-- 2. Cancellation rate by month
WITH per_month AS (
    SELECT
        DATE_TRUNC('month', invoice_date)::date AS month,
        COUNT(*) FILTER (WHERE is_cancellation)     AS cancellations,
        COUNT(*) FILTER (WHERE NOT is_cancellation) AS orders
    FROM invoices
    GROUP BY 1
)
SELECT
    month,
    orders,
    cancellations,
    ROUND(100.0 * cancellations / NULLIF(orders + cancellations, 0)::numeric, 2)
        AS cancellation_rate_pct
FROM per_month
ORDER BY month;


-- 3. Basket size distribution
SELECT
    items_per_order,
    COUNT(*) AS orders
FROM (
    SELECT i.invoice_no, COUNT(*) AS items_per_order
    FROM invoices i
    JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
    WHERE i.is_cancellation = FALSE
    GROUP BY i.invoice_no
) t
GROUP BY items_per_order
ORDER BY items_per_order;


-- 4. Peak hours overall
SELECT
    EXTRACT(HOUR FROM i.invoice_date)::int AS hour,
    COUNT(DISTINCT i.invoice_no) AS orders,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS revenue
FROM invoices i
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY hour
ORDER BY revenue DESC
LIMIT 5;

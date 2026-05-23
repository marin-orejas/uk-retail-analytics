-- Geography queries


-- 1. Revenue by country
SELECT
    co.name AS country,
    COUNT(DISTINCT i.invoice_no) AS orders,
    COUNT(DISTINCT i.customer_id) AS customers,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS revenue
FROM countries co
JOIN invoices i       ON i.country_id = co.country_id
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY co.name
ORDER BY revenue DESC;


-- 2. Top non-UK markets
SELECT
    co.name AS country,
    COUNT(DISTINCT i.customer_id) AS customers,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS revenue
FROM countries co
JOIN invoices i       ON i.country_id = co.country_id
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
  AND co.name <> 'United Kingdom'
GROUP BY co.name
ORDER BY revenue DESC
LIMIT 15;


-- 3. Average order value by country (top 15 by orders)
SELECT
    co.name AS country,
    COUNT(DISTINCT i.invoice_no) AS orders,
    ROUND(
        SUM(ii.quantity * ii.unit_price)::numeric
        / NULLIF(COUNT(DISTINCT i.invoice_no), 0),
        2
    ) AS avg_order_value
FROM countries co
JOIN invoices i       ON i.country_id = co.country_id
JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY co.name
HAVING COUNT(DISTINCT i.invoice_no) >= 20
ORDER BY orders DESC
LIMIT 15;


-- 4. Country share of revenue
WITH per_country AS (
    SELECT co.name AS country,
           SUM(ii.quantity * ii.unit_price) AS revenue
    FROM countries co
    JOIN invoices i       ON i.country_id = co.country_id
    JOIN invoice_items ii ON ii.invoice_no = i.invoice_no
    WHERE i.is_cancellation = FALSE
    GROUP BY co.name
)
SELECT
    country,
    ROUND(revenue::numeric, 2) AS revenue,
    ROUND(100.0 * revenue / SUM(revenue) OVER ()::numeric, 2) AS share_pct
FROM per_country
ORDER BY revenue DESC;

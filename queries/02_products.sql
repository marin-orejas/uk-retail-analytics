-- Product analytics queries


-- 1. Top 20 products by revenue
SELECT
    p.stock_code,
    p.description,
    SUM(ii.quantity)                            AS units_sold,
    ROUND(SUM(ii.quantity * ii.unit_price)::numeric, 2) AS revenue
FROM products p
JOIN invoice_items ii ON ii.stock_code = p.stock_code
JOIN invoices i       ON i.invoice_no = ii.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY p.stock_code, p.description
ORDER BY revenue DESC
LIMIT 20;


-- 2. Top 20 products by units sold
SELECT
    p.stock_code,
    p.description,
    SUM(ii.quantity) AS units_sold
FROM products p
JOIN invoice_items ii ON ii.stock_code = p.stock_code
JOIN invoices i       ON i.invoice_no = ii.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY p.stock_code, p.description
ORDER BY units_sold DESC
LIMIT 20;


-- 3. Slow movers - products with low sales over the full period
-- Useful for inventory review.
SELECT
    p.stock_code,
    p.description,
    SUM(ii.quantity) AS units_sold,
    COUNT(DISTINCT i.invoice_no) AS appearances
FROM products p
JOIN invoice_items ii ON ii.stock_code = p.stock_code
JOIN invoices i       ON i.invoice_no = ii.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY p.stock_code, p.description
HAVING SUM(ii.quantity) < 10
ORDER BY units_sold ASC
LIMIT 30;


-- 4. Return rate per product
-- Returned units come from cancellation invoices (negative quantities,
-- but invoice flagged as cancellation).
WITH sold AS (
    SELECT ii.stock_code, SUM(ii.quantity) AS units
    FROM invoice_items ii
    JOIN invoices i ON i.invoice_no = ii.invoice_no
    WHERE i.is_cancellation = FALSE
    GROUP BY ii.stock_code
),
returned AS (
    SELECT ii.stock_code, SUM(ABS(ii.quantity)) AS units
    FROM invoice_items ii
    JOIN invoices i ON i.invoice_no = ii.invoice_no
    WHERE i.is_cancellation = TRUE
    GROUP BY ii.stock_code
)
SELECT
    p.stock_code,
    p.description,
    s.units AS sold,
    COALESCE(r.units, 0) AS returned,
    ROUND(100.0 * COALESCE(r.units, 0) / NULLIF(s.units, 0), 2) AS return_rate_pct
FROM products p
JOIN sold s     ON s.stock_code = p.stock_code
LEFT JOIN returned r ON r.stock_code = p.stock_code
WHERE s.units >= 50
ORDER BY return_rate_pct DESC NULLS LAST
LIMIT 20;


-- 5. Frequently bought together (top product pairs)
-- Self-join invoice_items to find pairs in the same invoice.
SELECT
    a.stock_code AS product_a,
    b.stock_code AS product_b,
    pa.description AS desc_a,
    pb.description AS desc_b,
    COUNT(*) AS pair_count
FROM invoice_items a
JOIN invoice_items b
  ON a.invoice_no = b.invoice_no
 AND a.stock_code < b.stock_code
JOIN products pa ON pa.stock_code = a.stock_code
JOIN products pb ON pb.stock_code = b.stock_code
JOIN invoices i  ON i.invoice_no = a.invoice_no
WHERE i.is_cancellation = FALSE
GROUP BY a.stock_code, b.stock_code, pa.description, pb.description
ORDER BY pair_count DESC
LIMIT 25;

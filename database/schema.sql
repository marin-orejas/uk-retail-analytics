-- UK Online Retail - database schema
-- PostgreSQL

-- Drop in reverse order for clean re-runs
DROP TABLE IF EXISTS invoice_items;
DROP TABLE IF EXISTS invoices;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS countries;


-- Countries (lookup)
CREATE TABLE countries (
    country_id   SERIAL PRIMARY KEY,
    name         VARCHAR(64) NOT NULL UNIQUE
);


-- Customers
-- Rows from the source with no CustomerID are skipped here
-- and stay anonymous on the invoice level.
CREATE TABLE customers (
    customer_id  INTEGER PRIMARY KEY,            -- original CustomerID from source
    country_id   INTEGER NOT NULL REFERENCES countries(country_id)
);


-- Products
-- StockCode is the natural key from the source.
-- Description is the most common one we saw for that code.
CREATE TABLE products (
    stock_code   VARCHAR(20) PRIMARY KEY,
    description  VARCHAR(255)
);


-- Invoices
-- InvoiceNo is the natural key. Cancellations start with 'C' in the source,
-- we keep them and mark them with is_cancellation.
CREATE TABLE invoices (
    invoice_no       VARCHAR(20) PRIMARY KEY,
    invoice_date     TIMESTAMP NOT NULL,
    customer_id      INTEGER REFERENCES customers(customer_id),  -- nullable, ~25% have no customer
    country_id       INTEGER NOT NULL REFERENCES countries(country_id),
    is_cancellation  BOOLEAN NOT NULL DEFAULT FALSE
);


-- Invoice items (line level)
CREATE TABLE invoice_items (
    item_id      BIGSERIAL PRIMARY KEY,
    invoice_no   VARCHAR(20) NOT NULL REFERENCES invoices(invoice_no),
    stock_code   VARCHAR(20) NOT NULL REFERENCES products(stock_code),
    quantity     INTEGER NOT NULL,                -- can be negative on returns
    unit_price   NUMERIC(10, 2) NOT NULL,
    CHECK (unit_price >= 0)
);


-- Indexes for the queries we plan to run
CREATE INDEX idx_invoices_date        ON invoices (invoice_date);
CREATE INDEX idx_invoices_customer    ON invoices (customer_id);
CREATE INDEX idx_items_invoice        ON invoice_items (invoice_no);
CREATE INDEX idx_items_stock_code     ON invoice_items (stock_code);

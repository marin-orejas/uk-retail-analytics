# Data

## Source

UK Online Retail dataset from the UCI Machine Learning Repository:
https://archive.ics.uci.edu/ml/datasets/online+retail

It's transaction data from a UK-based online retailer that mostly sells gift items to wholesale customers.

## File

- `online_retail.xlsx` (~23 MB) — single sheet, not committed (see `.gitignore`)
- Download command:
  ```
  curl -L -o data/online_retail.xlsx \
    "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"
  ```

## Basic stats

- 541,909 rows, 8 columns
- Date range: 2010-12-01 to 2011-12-09 (about one year)
- 25,900 unique invoices
- 4,372 unique customers (where CustomerID is set)
- 4,070 unique products (StockCode)
- 38 countries, but ~91% of rows are United Kingdom

## Columns

| Column | Type | Notes |
|---|---|---|
| InvoiceNo | string | 6-digit number. Starts with `C` for cancellations. |
| StockCode | string | Product code. Mostly numeric, some have letters. |
| Description | string | Product name. 1,454 nulls. |
| Quantity | int | Can be negative (returns/cancellations). |
| InvoiceDate | datetime | |
| UnitPrice | float | In GBP. Some rows are 0 or negative. |
| CustomerID | float | 135,080 rows have no CustomerID (~25%). |
| Country | string | Customer country. |

## Things to watch out for

- **Missing CustomerID** in ~25% of rows. These can't be used for customer-level analysis (RFM etc.).
- **Negative quantities** (10,624 rows) — these are returns. Invoice numbers starting with `C` mark cancellations.
- **Zero or negative UnitPrice** — 2,515 zero-price rows and 2 negative ones. Need to filter or handle when computing revenue.
- **Duplicate rows** exist — same invoice can have the same product line repeated.
- **Country = "Unspecified"** appears for a small number of rows.

## Plan

- Load the raw file into a staging table.
- Clean and split into a normalized schema (customers, products, invoices, invoice_items, countries).
- Keep the cancellation rows — useful for return-rate analysis.

# ER diagram

```mermaid
erDiagram
    COUNTRIES ||--o{ CUSTOMERS : "based in"
    COUNTRIES ||--o{ INVOICES  : "ships to"
    CUSTOMERS ||--o{ INVOICES  : "places"
    INVOICES  ||--o{ INVOICE_ITEMS : "contains"
    PRODUCTS  ||--o{ INVOICE_ITEMS : "appears in"

    COUNTRIES {
        int country_id PK
        varchar name
    }
    CUSTOMERS {
        int customer_id PK
        int country_id FK
    }
    PRODUCTS {
        varchar stock_code PK
        varchar description
    }
    INVOICES {
        varchar invoice_no PK
        timestamp invoice_date
        int customer_id FK
        int country_id FK
        boolean is_cancellation
    }
    INVOICE_ITEMS {
        bigint item_id PK
        varchar invoice_no FK
        varchar stock_code FK
        int quantity
        numeric unit_price
    }
```

## Notes

- `customer_id` on `invoices` is nullable — about 25% of source rows have no CustomerID.
- `country_id` is stored on both `customers` and `invoices`. Customer country is their main country (most frequent), invoice country is where that specific order shipped to.
- Cancellations stay in the same `invoices` table, marked by `is_cancellation`. Their line items can have negative quantities.

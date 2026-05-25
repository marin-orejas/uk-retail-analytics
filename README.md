![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?style=flat&logo=sqlalchemy&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat&logo=plotly&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat)

# uk-retail-analytics

Analytics project on the UK Online Retail dataset. Normalized PostgreSQL schema, analytical SQL queries, and a Streamlit dashboard on top.

---

## Preview

![Overview](docs/screenshots/01_overview.jpg)
![Customers](docs/screenshots/02_customers.jpg)
![Products](docs/screenshots/03_products.jpg)
![Geography](docs/screenshots/04_geography.jpg)
![Trends](docs/screenshots/05_trends.jpg)

## Dataset

UK Online Retail from the UCI ML Repository. About 540k transactions, Dec 2010 to Dec 2011, mostly UK with some EU customers. Column-level notes and known issues are in `data/README.md`.

## Database

Five tables, normalized from the flat source file:

- `countries` lookup
- `customers` one row per CustomerID
- `products` one row per StockCode
- `invoices` invoice header with cancellation flag
- `invoice_items` line items

ER diagram is in `docs/er_diagram.md`.

## Project structure

```
.
├── data/           dataset notes, raw file not committed
├── database/       schema, views, ETL script
├── queries/        analytical SQL grouped by topic
├── dashboard/      Streamlit app
├── docs/           ER diagram and screenshots
├── requirements.txt
└── README.md
```

## SQL queries

| File | Topic |
|---|---|
| `01_customers.sql` | top customers, RFM scores, segments, cohort retention |
| `02_products.sql` | bestsellers, slow movers, return rate, frequently bought together |
| `03_sales_trends.sql` | monthly, weekday, hourly revenue, MoM growth |
| `04_geography.sql` | revenue per country, non-UK markets, country share |
| `05_operations.sql` | AOV, cancellation rate, basket size, peak hours |

## Dashboard

Streamlit app with five pages:

- Overview: KPIs, monthly revenue trend, top countries
- Customers: RFM segmentation, segment breakdown, top spenders
- Products: top by revenue, slow movers
- Geography: Europe choropleth, top non-UK markets
- Trends: MoM growth, day-of-week and hour heatmap, cancellation rate

Charts are Plotly, data comes from the views in `database/views.sql`.

## Tech stack

| Layer | Technology |
|---|---|
| Database | PostgreSQL |
| ETL | Python, pandas, psycopg2 |
| Dashboard | Streamlit, Plotly |
| Data access | SQLAlchemy |

## Running the project

```bash
# 1. Get the data
mkdir -p data
curl -L -o data/online_retail.xlsx \
  "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"

# 2. Create the database
createdb uk_retail
psql uk_retail -f database/schema.sql

# 3. Install deps and load
pip install -r requirements.txt
cp .env.example .env
python database/load_data.py

# 4. Create views
psql uk_retail -f database/views.sql

# 5. Run the dashboard
streamlit run dashboard/app.py
```

## Notes

- About 25% of source rows have no CustomerID. Those orders stay in `invoices` but skip customer-level analysis.
- Cancellations live in the same `invoices` table flagged by `is_cancellation`. Negative quantities are kept on the line items.
- UK accounts for around 85% of revenue, so non-UK charts use a separate filter to stay readable.

## License

MIT, see [LICENSE](LICENSE) for details.

# uk-retail-analytics

Small analytics project on the UK Online Retail dataset. SQL on PostgreSQL with a Streamlit dashboard on top.

## What's in here

- `database/` — schema, views, ETL script
- `queries/` — analytical SQL grouped by topic (customers, products, sales, geography, ops)
- `data/` — dataset notes, raw file not committed
- `dashboard/` — Streamlit app (work in progress)
- `docs/` — ER diagram and notes

## Dataset

UK Online Retail from UCI ML Repository. About 540k transactions, Dec 2010 – Dec 2011, mostly UK with some EU customers. See `data/README.md` for the column-level notes and known issues.

## Setup

```bash
# 1. Get the data
mkdir -p data
curl -L -o data/online_retail.xlsx \
  "https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx"

# 2. Create the database
createdb uk_retail
psql uk_retail -f database/schema.sql

# 3. Install deps and load data
pip install -r requirements.txt
cp .env.example .env   # fill in your DB credentials
python database/load_data.py

# 4. Create views
psql uk_retail -f database/views.sql
```

## Running queries

Each file in `queries/` has several standalone queries. Run them in psql or any client.

## Dashboard

Coming next. Will be a Streamlit app reading from the views above.

## Stack

- PostgreSQL
- Python (pandas, psycopg2)
- Streamlit + Plotly

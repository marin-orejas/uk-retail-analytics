"""
Load the UK Online Retail dataset into the normalized schema.

Reads data/online_retail.xlsx, cleans it, and inserts into 5 tables.
Run schema.sql first.

Usage:
    python database/load_data.py
"""

import os
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "online_retail.xlsx"

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "uk_retail"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def load_and_clean():
    print(f"Reading {DATA_FILE.name} ...")
    df = pd.read_excel(DATA_FILE)
    print(f"  raw rows: {len(df):,}")

    # Trim strings
    for col in ["InvoiceNo", "StockCode", "Description", "Country"]:
        df[col] = df[col].astype(str).str.strip()

    # Drop rows with no description or zero/negative price
    df = df[df["Description"].notna() & (df["Description"] != "nan")]
    df = df[df["UnitPrice"] > 0]

    # Cancellation flag from invoice number prefix
    df["is_cancellation"] = df["InvoiceNo"].str.startswith("C")

    # CustomerID to nullable int
    df["CustomerID"] = df["CustomerID"].astype("Int64")

    # Drop exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"  dropped {before - len(df):,} duplicate rows")
    print(f"  clean rows: {len(df):,}")

    return df


def insert_countries(cur, df):
    countries = sorted(df["Country"].unique())
    execute_values(
        cur,
        "INSERT INTO countries (name) VALUES %s ON CONFLICT (name) DO NOTHING",
        [(c,) for c in countries],
    )
    cur.execute("SELECT country_id, name FROM countries")
    mapping = {name: cid for cid, name in cur.fetchall()}
    print(f"  countries: {len(mapping)}")
    return mapping


def insert_customers(cur, df, country_map):
    cust = df.dropna(subset=["CustomerID"]).copy()
    # one country per customer - take the most frequent
    cust = (
        cust.groupby("CustomerID")["Country"]
        .agg(lambda s: s.mode().iat[0])
        .reset_index()
    )
    rows = [(int(r.CustomerID), country_map[r.Country]) for r in cust.itertuples()]
    execute_values(
        cur,
        "INSERT INTO customers (customer_id, country_id) VALUES %s "
        "ON CONFLICT (customer_id) DO NOTHING",
        rows,
    )
    print(f"  customers: {len(rows):,}")


def insert_products(cur, df):
    # take the most common description per stock_code
    prods = (
        df.groupby("StockCode")["Description"]
        .agg(lambda s: s.mode().iat[0])
        .reset_index()
    )
    rows = [(r.StockCode, r.Description[:255]) for r in prods.itertuples()]
    execute_values(
        cur,
        "INSERT INTO products (stock_code, description) VALUES %s "
        "ON CONFLICT (stock_code) DO NOTHING",
        rows,
    )
    print(f"  products: {len(rows):,}")


def insert_invoices(cur, df, country_map):
    inv = (
        df.groupby("InvoiceNo")
        .agg(
            invoice_date=("InvoiceDate", "min"),
            customer_id=("CustomerID", "first"),
            country=("Country", "first"),
            is_cancellation=("is_cancellation", "first"),
        )
        .reset_index()
    )
    rows = []
    for r in inv.itertuples():
        cid = int(r.customer_id) if pd.notna(r.customer_id) else None
        rows.append(
            (r.InvoiceNo, r.invoice_date, cid, country_map[r.country], bool(r.is_cancellation))
        )
    execute_values(
        cur,
        "INSERT INTO invoices (invoice_no, invoice_date, customer_id, country_id, is_cancellation) "
        "VALUES %s ON CONFLICT (invoice_no) DO NOTHING",
        rows,
        page_size=1000,
    )
    print(f"  invoices: {len(rows):,}")


def insert_invoice_items(cur, df):
    rows = [
        (r.InvoiceNo, r.StockCode, int(r.Quantity), float(r.UnitPrice))
        for r in df.itertuples()
    ]
    execute_values(
        cur,
        "INSERT INTO invoice_items (invoice_no, stock_code, quantity, unit_price) VALUES %s",
        rows,
        page_size=5000,
    )
    print(f"  invoice items: {len(rows):,}")


def main():
    df = load_and_clean()

    print("\nConnecting to database ...")
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            print("Inserting:")
            country_map = insert_countries(cur, df)
            insert_customers(cur, df, country_map)
            insert_products(cur, df)
            insert_invoices(cur, df, country_map)
            insert_invoice_items(cur, df)
        conn.commit()

    print("\nDone.")


if __name__ == "__main__":
    main()

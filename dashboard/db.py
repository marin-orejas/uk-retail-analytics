"""Database helpers for the Streamlit app."""

import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()


@st.cache_resource
def get_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER', 'postgres')}:"
        f"{os.getenv('DB_PASSWORD', '')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:"
        f"{os.getenv('DB_PORT', '5432')}/"
        f"{os.getenv('DB_NAME', 'uk_retail')}"
    )
    return create_engine(url)


@st.cache_data(ttl=3600)
def run_query(sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql(sql, get_engine(), params=params or {})

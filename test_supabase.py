import os
from sqlalchemy import create_engine

DB_URL = "postgresql://postgres:nehandb%40190306@db.rqutlxbanwfcaunrvxfr.supabase.co:5432/postgres"

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Successfully connected to Supabase!")
except Exception as e:
    print(f"Failed to connect: {e}")

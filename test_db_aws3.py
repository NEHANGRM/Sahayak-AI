from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os

db_url = "postgresql://postgres:nehandb%40190306@db.rqutlxbanwfcaunrvxfr.supabase.co:5432/postgres"

engine = create_engine(db_url, connect_args={'connect_timeout': 10})
try:
    with engine.connect() as conn:
        print(f"Connected to {db_url}!")
        conn.execute(text("UPDATE complaints SET timestamp = (NOW() - INTERVAL '2 hours'), sla_deadline = (NOW() + INTERVAL '46 hours'), status='Assigned', sla_breached=false, escalation_level=1;"))
        conn.commit()
        print("Fixed DB via direct connection!")
except Exception as e:
    print(f"Error:", e)

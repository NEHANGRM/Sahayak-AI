from sqlalchemy import create_engine
from sqlalchemy.sql import text
import os

db_url = "postgresql://postgres:nehandb%40190306@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"

engine = create_engine(db_url, connect_args={'connect_timeout': 10})
try:
    with engine.connect() as conn:
        print(f"Connected to {db_url}!")
        conn.execute(text("UPDATE complaints SET timestamp = to_char(NOW() - INTERVAL '2 hours', 'YYYY-MM-DD HH24:MI:SS'), sla_deadline = to_char(NOW() + INTERVAL '46 hours', 'YYYY-MM-DD HH24:MI:SS'), status='Assigned', sla_breached=false, escalation_level=1;"))
        conn.commit()
        print("Fixed DB via direct connection!")
except Exception as e:
    print(f"Error:", e)

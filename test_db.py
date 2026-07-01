from sqlalchemy import create_engine
import os

db_url = "postgresql://postgres.rqutlxbanwfcaunrvxfr:nehandb%40190306@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url, connect_args={'connect_timeout': 10})
try:
    with engine.connect() as conn:
        print("Connected!")
except Exception as e:
    print("Error:", e)

from sqlalchemy import create_engine
import os

db_url = "postgresql://postgres.rqutlxbanwfcaunrvxfr:nehandb%40190306@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"
engine = create_engine(db_url, connect_args={'connect_timeout': 10})
try:
    with engine.connect() as conn:
        print("Connected 5432!")
except Exception as e:
    print("Error 5432:", e)

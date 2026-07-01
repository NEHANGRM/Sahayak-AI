from sqlalchemy import create_engine
import os

db_url = "postgresql://postgres.rqutlxbanwfcaunrvxfr:nehandb%40190306@aws-0-ap-northeast-1.pooler.supabase.com:6543/postgres"
db_url2 = "postgresql://postgres.rqutlxbanwfcaunrvxfr:nehandb%40190306@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

for url in [db_url, db_url2]:
    engine = create_engine(url, connect_args={'connect_timeout': 10})
    try:
        with engine.connect() as conn:
            print(f"Connected to {url}!")
            # run fix
            conn.execute("UPDATE complaints SET timestamp = (NOW() - INTERVAL '2 hours'), sla_deadline = (NOW() + INTERVAL '46 hours'), status='Assigned', sla_breached=false, escalation_level=1;")
            conn.commit()
            print("Fixed DB via direct connection!")
            break
    except Exception as e:
        print(f"Error {url}:", e)

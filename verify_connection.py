from sqlalchemy import create_engine
import sys

URL = "postgresql://postgres.rqutlxbanwfcaunrvxfr:nehandb%40190306@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

try:
    engine = create_engine(URL, connect_args={"connect_timeout": 5})
    with engine.connect() as conn:
        print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
    sys.exit(1)

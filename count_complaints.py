import os
import time

# Use the real database url
os.environ["DATABASE_URL"] = "postgresql://postgres.rqutlxbanwfcaunrvxfr:nehandb%40190306@aws-1-ap-northeast-1.pooler.supabase.com:6543/postgres"

from api import SessionLocal, Complaint
db = SessionLocal()
count = db.query(Complaint).count()
print(f"Total Complaints: {count}")
db.close()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api import Base, Complaint

engine = create_engine("sqlite:///sahayak_ai.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Any complaint that has an officer assigned but is "Submitted" should be "Assigned"
comps = db.query(Complaint).filter(Complaint.status == "Submitted", Complaint.assigned_officer_id != None).all()

count = 0
for comp in comps:
    comp.status = "Assigned"
    count += 1

db.commit()
print(f"Fixed {count} complaints from Submitted to Assigned")

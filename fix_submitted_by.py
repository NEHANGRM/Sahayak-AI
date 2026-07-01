import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api import Base, User, Complaint

engine = create_engine("sqlite:///sahayak_ai.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# We want to change the 45 complaints that were originally "Open" (and are now "Submitted") to citizen2.
# Since we just updated them to "Submitted", we can just take all "Submitted" complaints that belong to citizen1.
comps = db.query(Complaint).filter(Complaint.status == "Submitted", Complaint.submitted_by == "citizen1").all()

count = 0
for comp in comps:
    comp.submitted_by = "citizen2"
    count += 1

db.commit()
print(f"Successfully reassigned {count} complaints to citizen2")

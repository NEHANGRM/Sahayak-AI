from api import SessionLocal, Complaint, Officer
from sqlalchemy import func

db = SessionLocal()
complaints = db.query(Complaint).all()
updated_count = 0
for comp in complaints:
    if comp.department and comp.department != "Not Routed":
        l1_officer = db.query(Officer).filter(
            func.lower(Officer.department) == comp.department.lower(),
            Officer.escalation_level == 1
        ).first()
        if l1_officer and comp.assigned_officer_id != l1_officer.officer_id:
            comp.assigned_officer_id = l1_officer.officer_id
            comp.escalation_level = 1
            updated_count += 1
db.commit()
print(f"Fixed assignments for {updated_count} complaints!")

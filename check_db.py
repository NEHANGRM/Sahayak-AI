from api import SessionLocal, Complaint
db = SessionLocal()
comps = db.query(Complaint).filter(Complaint.assigned_officer_id == "OFF1_W_L1").all()
for c in comps:
    print(f"ID: {c.id}, Status: {c.status}, Esc: {c.escalation_level}")

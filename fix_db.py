from api import SessionLocal, Complaint, calculate_sla_deadline
import datetime

db = SessionLocal()
comps = db.query(Complaint).all()
updated = 0
for c in comps:
    if not c.sla_deadline or c.sla_deadline == "None" or c.sla_deadline == "":
        try:
            dt = datetime.datetime.strptime(c.timestamp, "%Y-%m-%d %H:%M:%S")
        except:
            dt = datetime.datetime.now() - datetime.timedelta(hours=2)
            c.timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        c.sla_deadline = calculate_sla_deadline(c.priority_label or "Low", c.timestamp)
        updated += 1
db.commit()
print(f"Updated {updated} complaints with SLA deadlines.")

import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api import Base, User, Complaint, calculate_sla_deadline
import bcrypt

engine = create_engine("sqlite:///sahayak_ai.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Create citizen 2
cit2 = db.query(User).filter(User.username == "citizen2").first()
if not cit2:
    cit2 = User(
        user_id="USR-CIT-002",
        username="citizen2",
        password_hash=bcrypt.hashpw(b"cit123", bcrypt.gensalt()).decode('utf-8'),
        role="citizen",
        name="Citizen Two"
    )
    db.add(cit2)
    db.commit()

# Find all open complaints
open_comps = db.query(Complaint).filter(Complaint.status == "Open").all()
now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for comp in open_comps:
    comp.user_id = cit2.username
    comp.status = "Submitted"
    # recalculate SLA
    pri = comp.priority_label or "Low"
    comp.sla_deadline = calculate_sla_deadline(pri, now_str)
    comp.sla_breached = False

db.commit()
print(f"Updated {len(open_comps)} complaints to Submitted, assigned to citizen2, and generated SLA deadlines.")

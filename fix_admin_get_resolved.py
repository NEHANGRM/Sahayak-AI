import re

with open("api.py", "r") as f:
    content = f.read()

# For get_resolved_complaints
old_code_res = """@app.get("/complaints/resolved")
def get_resolved_complaints(officer_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Complaint).filter(Complaint.status.in_(["Resolved", "Closed"]))
    if officer_id:
        query = query.filter(Complaint.assigned_officer_id == officer_id)"""

new_code_res = """@app.get("/complaints/resolved")
def get_resolved_complaints(officer_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Complaint).filter(Complaint.status.in_(["Resolved", "Closed"]))
    if officer_id and officer_id != "ADMIN":
        query = query.filter(Complaint.assigned_officer_id == officer_id)"""

if "officer_id and officer_id != \"ADMIN\"" not in content.split("def get_resolved_complaints")[1][:200]:
    content = content.replace(old_code_res, new_code_res)

# For get_rejected_complaints
old_code_rej = """@app.get("/complaints/rejected")
def get_rejected_complaints(officer_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Complaint).filter(Complaint.status == "Rejected")
    if officer_id:
        query = query.filter(Complaint.assigned_officer_id == officer_id)"""

new_code_rej = """@app.get("/complaints/rejected")
def get_rejected_complaints(officer_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(Complaint).filter(Complaint.status == "Rejected")
    if officer_id and officer_id != "ADMIN":
        query = query.filter(Complaint.assigned_officer_id == officer_id)"""

if "officer_id and officer_id != \"ADMIN\"" not in content.split("def get_rejected_complaints")[1][:200]:
    content = content.replace(old_code_rej, new_code_rej)

with open("api.py", "w") as f:
    f.write(content)

print("Admin endpoints fixed!")

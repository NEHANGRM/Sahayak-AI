with open("api.py", "r") as f:
    content = f.read()

if "@app.post(\"/fix-timestamps\")" not in content:
    new_endpoint = """
@app.post("/fix-timestamps")
def fix_timestamps(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    now = datetime.now()
    comps = db.query(Complaint).all()
    updated = 0
    for c in comps:
        # Reset timestamp to 2 hours ago
        new_time = now - timedelta(hours=2)
        c.timestamp = new_time.strftime('%Y-%m-%d %H:%M:%S')
        # Reset sla_deadline to 46 hours from now
        c.sla_deadline = (new_time + timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
        # Reset SLA breach and escalation
        c.sla_breached = False
        c.escalation_level = 1
        c.status = "Assigned"
        
        # Ensure it's assigned to L1 officer for its department
        l1_officer = db.query(Officer).filter(Officer.department == c.department, Officer.escalation_level == 1).first()
        if l1_officer:
            c.assigned_officer_id = l1_officer.officer_id
            
        updated += 1
    db.commit()
    return {"updated": updated}
"""
    content = content + new_endpoint
    with open("api.py", "w") as f:
        f.write(content)
        print("Endpoint added")
else:
    print("Already added")

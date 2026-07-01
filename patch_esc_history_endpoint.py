import re

with open("api.py", "r") as f:
    content = f.read()

old_ep = """@app.get("/complaints/{complaint_id}/escalation-history")
def get_escalation_history(complaint_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(
        AuditLog.complaint_id == complaint_id,
        AuditLog.action.in_(['auto_escalation', 'manual_escalation'])
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return [
        {
            "timestamp": l.timestamp,
            "action": l.action,
            "from_level": l.from_value,
            "to_level": l.to_value,
            "reason": l.notes,
            "user": l.performed_by
        }
        for l in logs
    ]"""

new_ep = """@app.get("/complaints/{complaint_id}/escalation-history")
def get_escalation_history(complaint_id: str, db: Session = Depends(get_db)):
    logs = db.query(EscalationHistory).filter(
        EscalationHistory.complaint_id == complaint_id
    ).order_by(EscalationHistory.timestamp.desc()).all()
    
    return [
        {
            "timestamp": l.timestamp,
            "action": "auto_escalation" if l.user_responsible == "SYSTEM" else "manual_escalation",
            "from_level": l.from_level,
            "to_level": l.to_level,
            "reason": l.trigger_reason,
            "user": l.user_responsible
        }
        for l in logs
    ]"""

content = content.replace(old_ep, new_ep)

with open("api.py", "w") as f:
    f.write(content)
print("Updated escalation-history endpoint")

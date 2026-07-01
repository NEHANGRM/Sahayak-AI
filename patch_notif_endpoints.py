with open("api.py", "r") as f:
    content = f.read()

old_ep = """def get_notifications(user_id: str, db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.id.desc()).limit(20).all()
    return [{"id": n.id, "message": n.message, "type": n.type, "timestamp": n.timestamp, "is_read": n.is_read} for n in notifs]"""

new_ep = """def get_notifications(user_id: str, db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.id.desc()).limit(50).all()
    return [{
        "id": n.id, 
        "message": n.message, 
        "type": n.type, 
        "timestamp": n.timestamp, 
        "is_read": n.is_read,
        "complaint_id": getattr(n, 'complaint_id', None),
        "escalation_level": getattr(n, 'escalation_level', None),
        "priority": getattr(n, 'priority', None)
    } for n in notifs]"""

content = content.replace(old_ep, new_ep)

with open("api.py", "w") as f:
    f.write(content)
print("Updated notification endpoint!")

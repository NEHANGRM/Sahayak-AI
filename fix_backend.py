import re

# 1. Fix utils.py assign_officer logic
with open("utils.py", "r") as f:
    u_content = f.read()

u_content = u_content.replace("Officer.escalation_level == 0", "Officer.escalation_level == 1")
with open("utils.py", "w") as f:
    f.write(u_content)

# 2. Fix api.py
with open("api.py", "r") as f:
    content = f.read()

# Fix seed_database assignment (lines 1125-1128)
old_assign = """        from sqlalchemy import func
        # Assign Officer directly inside api.py to avoid circular imports during startup
        assigned_officer = db.query(Officer).filter(func.lower(Officer.department) == department.lower()).first()
        assigned_officer_id = assigned_officer.officer_id if assigned_officer else None"""

new_assign = """        from sqlalchemy import func
        # Assign to L1 officer specifically
        assigned_officer = db.query(Officer).filter(func.lower(Officer.department) == department.lower(), Officer.escalation_level == 1).first()
        assigned_officer_id = assigned_officer.officer_id if assigned_officer else None"""
content = content.replace(old_assign, new_assign)

# Fix run_escalation_checks notification (lines 564+)
old_notif = """                # Create Notification
                # Notify officers of the new level in the same department
                if next_level == 4:"""

new_notif = """                # Create Notification
                # Notify the previous assigned officer of the escalation
                if comp.assigned_officer_id:
                    notif_prev = Notification(
                        user_id=comp.assigned_officer_id,
                        message=f"Complaint {comp.id} was escalated to Level {next_level}. Reason: {trigger_reason}",
                        type="info",
                        timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
                        complaint_id=comp.id,
                        escalation_level=next_level,
                        priority=comp.severity_label
                    )
                    db.add(notif_prev)
                    
                # Notify officers of the new level in the same department
                if next_level == 4:"""
content = content.replace(old_notif, new_notif)

with open("api.py", "w") as f:
    f.write(content)

print("Backend fixes applied!")

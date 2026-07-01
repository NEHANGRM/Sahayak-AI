import re
with open("api.py", "r") as f:
    content = f.read()

# 1. Update triage_complaint to add notifications
old_triage = """        "priority_breakdown": priority_breakdown
    }
    
    comp = Complaint("""

new_triage = """        "priority_breakdown": priority_breakdown
    }
    
    import datetime
    comp = Complaint("""

# Let's insert notifications after db.commit() in triage_complaint
old_triage_commit = """    db.add(comp)
    db.commit()
    
    return {"message": "Complaint triaged successfully", "complaint": to_dict(comp)}"""

new_triage_commit = """    db.add(comp)
    db.commit()
    
    # Notify Admin
    n_admin = Notification(user_id="admin", message=f"New complaint {comp_id} raised for {department}.", type="info", timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    db.add(n_admin)
    
    if assigned_officer_id:
        n_off = Notification(user_id=assigned_officer_id, message=f"New complaint {comp_id} assigned to you.", type="assignment", timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db.add(n_off)
    else:
        # Workload alert to admin
        n_alert = Notification(user_id="admin", message=f"Workload Alert: {comp_id} in {department} is waitlisted due to capacity.", type="alert", timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        db.add(n_alert)
        
    db.commit()
    
    return {"message": "Complaint triaged successfully", "complaint": to_dict(comp)}"""

content = content.replace(old_triage_commit, new_triage_commit)

# 2. Update escalate_complaint
old_escalate = """    comp.escalation_level = new_level
    
    esc_hist = json.loads(comp.escalation_history or '[]')"""

new_escalate = """    comp.escalation_level = new_level
    
    # Reassign to higher level officer
    import utils
    new_officer_id = utils.reassign_to_escalation_level(comp.department, new_level, db)
    if new_officer_id and new_officer_id != comp.assigned_officer_id:
        comp.assigned_officer_id = new_officer_id
        n_off = Notification(user_id=new_officer_id, message=f"Complaint {comp.id} escalated to you.", type="escalation", timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        db.add(n_off)
        
    n_admin = Notification(user_id="admin", message=f"Complaint {comp.id} escalated to {ESCALATION_LEVELS.get(new_level, f'L{new_level}')}.", type="escalation", timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    db.add(n_admin)
    
    esc_hist = json.loads(comp.escalation_history or '[]')"""

content = content.replace(old_escalate, new_escalate)

# 3. Update check_and_escalate_sla
old_check_sla = """                new_level = min(current_level + 1, 3)
                comp.escalation_level = new_level
                
                # Auto-escalate status if not already escalated"""

new_check_sla = """                new_level = min(current_level + 1, 3)
                comp.escalation_level = new_level
                
                # Reassign to higher level officer
                import utils
                new_officer_id = utils.reassign_to_escalation_level(comp.department, new_level, db)
                if new_officer_id and new_officer_id != comp.assigned_officer_id:
                    comp.assigned_officer_id = new_officer_id
                    n_off = Notification(user_id=new_officer_id, message=f"SLA Breach: Complaint {comp.id} auto-escalated to you.", type="escalation", timestamp=now.strftime('%Y-%m-%d %H:%M:%S'))
                    db.add(n_off)
                    
                n_admin = Notification(user_id="admin", message=f"SLA Breach: Complaint {comp.id} auto-escalated to {ESCALATION_LEVELS.get(new_level, f'L{new_level}')}.", type="alert", timestamp=now.strftime('%Y-%m-%d %H:%M:%S'))
                db.add(n_admin)
                
                # Auto-escalate status if not already escalated"""

content = content.replace(old_check_sla, new_check_sla)

with open("api.py", "w") as f:
    f.write(content)


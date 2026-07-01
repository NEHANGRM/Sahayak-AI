import re

with open("api.py", "r") as f:
    content = f.read()

escalation_logic = """
from datetime import datetime, timedelta
import asyncio

def run_escalation_checks(db: Session):
    try:
        now = datetime.now()
        # Get unresolved complaints
        unresolved = db.query(Complaint).filter(
            Complaint.closed_at == None,
            Complaint.resolved_at == None
        ).all()
        
        # Get configs
        slas = {s.department: s for s in db.query(SLAConfiguration).all()}
        esc_configs = {e.level: e for e in db.query(EscalationConfiguration).all()}
        
        for comp in unresolved:
            current_level = comp.escalation_level
            if current_level >= 4:
                continue
                
            next_level = current_level + 1
            config = esc_configs.get(next_level)
            if not config:
                continue
                
            # Parse times
            comp_time = datetime.strptime(comp.timestamp, "%Y-%m-%d %H:%M:%S")
            unresolved_hours = (now - comp_time).total_seconds() / 3600.0
            
            sla = slas.get(comp.category)
            
            should_escalate = False
            trigger_reason = ""
            
            # SLA Breach Check
            if sla:
                if current_level == 1 and unresolved_hours > sla.accept_sla_hours and not comp.accepted_at:
                    should_escalate = True
                    trigger_reason = f"Not accepted within {sla.accept_sla_hours}h SLA"
                elif unresolved_hours > sla.resolve_sla_hours:
                    should_escalate = True
                    trigger_reason = f"Resolution SLA breached ({sla.resolve_sla_hours}h)"
            
            # Config Check
            if not should_escalate and unresolved_hours >= config.unresolved_hours_threshold:
                should_escalate = True
                trigger_reason = f"Unresolved hours exceeded {config.unresolved_hours_threshold}h threshold"
                
            if not should_escalate and comp.final_priority_score >= config.priority_threshold:
                should_escalate = True
                trigger_reason = f"Priority {comp.final_priority_score} exceeded {config.priority_threshold} threshold"
                
            if should_escalate:
                # Update complaint
                comp.escalation_level = next_level
                
                # Log history
                history = EscalationHistory(
                    complaint_id=comp.id,
                    from_level=current_level,
                    to_level=next_level,
                    timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
                    trigger_reason=trigger_reason,
                    user_responsible="SYSTEM"
                )
                db.add(history)
                
                # Create Notification
                # Notify officers of the new level in the same department
                if next_level == 4:
                    # Notify Commissioner
                    notif = Notification(
                        user_id="COMM_1",
                        message=f"Complaint {comp.id} escalated to Level 4 (Commissioner). Reason: {trigger_reason}",
                        type="error",
                        timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
                        complaint_id=comp.id,
                        escalation_level=next_level,
                        priority=comp.severity_label
                    )
                    db.add(notif)
                else:
                    # Notify respective officers
                    target_officers = db.query(Officer).filter(
                        Officer.department == comp.category,
                        Officer.escalation_level == next_level
                    ).all()
                    for off in target_officers:
                        notif = Notification(
                            user_id=off.officer_id,
                            message=f"Complaint {comp.id} escalated to Level {next_level}. Reason: {trigger_reason}",
                            type="warning",
                            timestamp=now.strftime("%Y-%m-%d %H:%M:%S"),
                            complaint_id=comp.id,
                            escalation_level=next_level,
                            priority=comp.severity_label
                        )
                        db.add(notif)
                        
                db.commit()
    except Exception as e:
        print(f"Error in escalation check: {e}")
        db.rollback()

@app.post("/system/run-escalations")
def trigger_escalations(db: Session = Depends(get_db)):
    run_escalation_checks(db)
    return {"status": "success", "message": "Escalation checks completed"}

# Background loop for escalations
async def escalation_background_task():
    while True:
        try:
            db = SessionLocal()
            run_escalation_checks(db)
            db.close()
        except Exception as e:
            print(f"Background task error: {e}")
        await asyncio.sleep(60) # run every 60 seconds

"""

if "def run_escalation_checks" not in content:
    # insert before @app.on_event("startup")
    content = content.replace("@app.on_event(\"startup\")", escalation_logic + "\n@app.on_event(\"startup\")")
    
    # insert asyncio.create_task in startup_db_init
    if "asyncio.create_task(escalation_background_task())" not in content:
        content = content.replace("print(\"Database Initialized Successfully.\")", "asyncio.create_task(escalation_background_task())\n        print(\"Database Initialized Successfully.\")")

with open("api.py", "w") as f:
    f.write(content)
print("Added Escalation Logic and Background Task!")

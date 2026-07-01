import re

with open("api.py", "r") as f:
    content = f.read()

# 1. to_dict changes
# Add new fields to returned dict
to_dict_target = """        'submitted_by': getattr(c, 'submitted_by', None),
        'llm_trigger_reasons': json.loads(getattr(c, 'llm_trigger_reasons', '[]')) if getattr(c, 'llm_trigger_reasons', '[]') else []
    }"""
to_dict_repl = """        'submitted_by': getattr(c, 'submitted_by', None),
        'llm_trigger_reasons': json.loads(getattr(c, 'llm_trigger_reasons', '[]')) if getattr(c, 'llm_trigger_reasons', '[]') else [],
        'sla_deadline': getattr(c, 'sla_deadline', None),
        'sla_breached': getattr(c, 'sla_breached', False),
        'accepted_at': getattr(c, 'accepted_at', None),
        'resolved_at': getattr(c, 'resolved_at', None),
        'closed_at': getattr(c, 'closed_at', None),
        'escalation_level': getattr(c, 'escalation_level', 0)
    }"""
content = content.replace(to_dict_target, to_dict_repl)

# Update aging condition in to_dict
content = content.replace('if c.status not in ["Resolved", "Rejected"]:', 'if c.status not in ["Resolved", "Rejected", "Closed"]:')


# 2. /triage endpoint
# Change default status
content = content.replace('status="Open" if is_admissible else "Rejected",', 'status="Assigned" if (is_admissible and assigned_officer_id) else ("Submitted" if is_admissible else "Rejected"),')

# Add SLA calculation & Audit logs after db.refresh(comp)
triage_post_target = """    db.add(comp)
    db.commit()
    db.refresh(comp)
    
    return to_dict(comp)"""

triage_post_repl = """    if is_admissible:
        comp.sla_deadline = calculate_sla_deadline(priority_label, timestamp)
        
    db.add(comp)
    db.commit()
    db.refresh(comp)
    
    # Audit logging
    if is_admissible:
        log_audit(db, comp.id, "status_change", None, "Submitted", req.submitted_by or "CITIZEN", "citizen", "Complaint submitted by citizen.")
        if assigned_officer_id:
            log_audit(db, comp.id, "status_change", "Submitted", "Assigned", "SYSTEM", "system", f"Auto-assigned to officer {assigned_officer_id}.")
        db.commit()
    else:
        log_audit(db, comp.id, "status_change", None, "Rejected", "SYSTEM", "system", f"Rejected: {rejection_reason}")
        db.commit()
        
    return to_dict(comp)"""
content = content.replace(triage_post_target, triage_post_repl)


# 3. /complaints endpoint
complaints_target = """    query = db.query(Complaint).filter(
        Complaint.admissible == True,
        Complaint.status != "Resolved",
        Complaint.status != "Rejected"
    )"""

complaints_repl = """    check_and_escalate_sla(db)
    query = db.query(Complaint).filter(
        Complaint.admissible == True,
        ~Complaint.status.in_(["Resolved", "Closed", "Rejected"])
    )"""
content = content.replace(complaints_target, complaints_repl)


# 4. /complaints/resolved endpoint
res_target = """    resolved = db.query(Complaint).filter(
        Complaint.status == "Resolved"
    ).all()"""
res_repl = """    resolved = db.query(Complaint).filter(
        Complaint.status.in_(["Resolved", "Closed"])
    ).all()"""
content = content.replace(res_target, res_repl)


# 5. /complaints/{id}/resolve endpoint
resolve_target = """            if c_item.id == id:
                c_hist.append({"status": "Resolved", "date": timestamp, "notes": req.notes})
            else:
                c_hist.append({"status": "Resolved", "date": timestamp, "notes": f"Resolved automatically with lead complaint {id}: {req.notes}"})
            c_item.resolution_history = json.dumps(c_hist)
        
    db.commit()
    return {"message": "Complaint and duplicates marked as resolved."}"""

resolve_repl = """            if c_item.id == id:
                c_hist.append({"status": "Resolved", "date": timestamp, "notes": req.notes})
            else:
                c_hist.append({"status": "Resolved", "date": timestamp, "notes": f"Resolved automatically with lead complaint {id}: {req.notes}"})
            c_item.resolution_history = json.dumps(c_hist)
            
            # Audit log
            c_item.resolved_at = timestamp
            log_audit(db, c_item.id, "status_change", c_item.status, "Resolved", c_item.assigned_officer_id or "unknown", "officer", req.notes)
        
    db.commit()
    return {"message": "Complaint and duplicates marked as resolved."}"""
content = content.replace(resolve_target, resolve_repl)


# 6. override endpoints
override_target = """    for c_item in cluster_complaints:
        c_item.officer_override = req.priority_label
        c_item.override_reason = req.reason"""
override_repl = """    for c_item in cluster_complaints:
        log_audit(db, c_item.id, "priority_override", str(c_item.priority_label), str(req.priority_label), comp.assigned_officer_id or "unknown", "officer", req.reason)
        c_item.officer_override = req.priority_label
        c_item.override_reason = req.reason"""
content = content.replace(override_target, override_repl)

override_sev_target = """    db.add(feedback)
    complaint.severity_score = req.severity_score"""
override_sev_repl = """    db.add(feedback)
    log_audit(db, complaint_id, "severity_override", str(complaint.severity_score), str(req.severity_score), req.officer_id or complaint.assigned_officer_id or "unknown", "officer", req.reason)
    complaint.severity_score = req.severity_score"""
content = content.replace(override_sev_target, override_sev_repl)

override_dep_target = """    db.add(feedback)
    complaint.department = req.new_department"""
override_dep_repl = """    db.add(feedback)
    log_audit(db, complaint_id, "department_transfer", complaint.department, req.new_department, req.officer_id or complaint.assigned_officer_id or "unknown", "officer", req.reason)
    complaint.department = req.new_department"""
content = content.replace(override_dep_target, override_dep_repl)


# 7. Add lifecycle endpoints AFTER /complaints/{id}/override
lifecycle_endpoints = """
@app.post("/complaints/{complaint_id}/accept")
def accept_complaint(complaint_id: str, req: AcceptRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Accepted")
    old_status = comp.status
    comp.status = "Accepted"
    comp.accepted_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Accepted", "date": comp.accepted_at, "notes": f"Accepted by officer {req.officer_id}"})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Accepted", req.officer_id, "officer", "Officer accepted the assignment.")
    db.commit()
    return {"message": "Complaint accepted.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/start-progress")
def start_progress(complaint_id: str, req: StartProgressRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "In Progress")
    old_status = comp.status
    comp.status = "In Progress"
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "In Progress", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": req.notes or "Officer started working on this complaint."})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "In Progress", req.officer_id, "officer", req.notes or "Started working.")
    db.commit()
    return {"message": "Complaint is now in progress.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/field-inspection")
def field_inspection(complaint_id: str, req: FieldInspectionRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Field Inspection")
    old_status = comp.status
    comp.status = "Field Inspection"
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Field Inspection", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": req.notes or "Officer conducting on-site inspection."})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Field Inspection", req.officer_id, "officer", req.notes or "Field inspection started.")
    db.commit()
    return {"message": "Complaint marked for field inspection.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/escalate")
def escalate_complaint(complaint_id: str, req: EscalateRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Escalated")
    old_status = comp.status
    comp.status = "Escalated"
    current_level = comp.escalation_level or 0
    new_level = req.escalation_level if req.escalation_level is not None else min(current_level + 1, 3)
    comp.escalation_level = new_level
    
    esc_hist = json.loads(comp.escalation_history or '[]')
    esc_hist.append({"level": ESCALATION_LEVELS.get(new_level, f"L{new_level}"), "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "reason": req.reason})
    comp.escalation_history = json.dumps(esc_hist)
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Escalated", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": f"Escalated to {ESCALATION_LEVELS.get(new_level, 'higher authority')}: {req.reason}"})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Escalated", req.officer_id, "officer", req.reason)
    db.commit()
    return {"message": f"Complaint escalated to {ESCALATION_LEVELS.get(new_level, 'higher authority')}.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/close")
def close_complaint(complaint_id: str, req: CloseRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Closed")
    old_status = comp.status
    comp.status = "Closed"
    comp.closed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Closed", "date": comp.closed_at, "notes": req.notes or "Complaint closed by admin."})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Closed", req.admin_id, "admin", req.notes or "Closed by admin.")
    db.commit()
    return {"message": "Complaint closed.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/reassign")
def reassign_complaint(complaint_id: str, req: ReassignRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    old_officer = comp.assigned_officer_id
    old_status = comp.status
    comp.assigned_officer_id = req.new_officer_id
    comp.status = "Assigned"
    comp.escalation_level = 0  # Reset escalation on reassignment
    comp.sla_breached = False  # Reset SLA
    # Recalculate SLA deadline from now
    comp.sla_deadline = calculate_sla_deadline(comp.priority_label or "Low", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Reassigned", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": f"Reassigned from {old_officer} to {req.new_officer_id}: {req.reason}"})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "officer_reassignment", old_officer or 'none', req.new_officer_id, req.admin_id, "admin", req.reason)
    log_audit(db, complaint_id, "status_change", old_status, "Assigned", req.admin_id, "admin", f"Reassigned to {req.new_officer_id}")
    db.commit()
    return {"message": f"Complaint reassigned to {req.new_officer_id}.", "complaint": to_dict(comp)}
"""
content = content.replace('    return {"message": "Override applied successfully for complaint and duplicates."}', '    return {"message": "Override applied successfully for complaint and duplicates."}\n' + lifecycle_endpoints)

# 8. Add Audit & Stats endpoints at the end of the file
audit_stats_endpoints = """

# ===================== AUDIT TRAIL ENDPOINTS =====================

@app.get("/complaints/{complaint_id}/audit-log")
def get_complaint_audit_log(complaint_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.complaint_id == complaint_id).order_by(AuditLog.timestamp).all()
    return [{
        'id': l.id, 'complaint_id': l.complaint_id, 'timestamp': l.timestamp,
        'action': l.action, 'from_value': l.from_value, 'to_value': l.to_value,
        'performed_by': l.performed_by, 'performer_role': l.performer_role, 'notes': l.notes
    } for l in logs]

@app.get("/audit-logs")
def get_all_audit_logs(action: Optional[str] = None, complaint_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if complaint_id:
        query = query.filter(AuditLog.complaint_id == complaint_id)
    logs = query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    return [{
        'id': l.id, 'complaint_id': l.complaint_id, 'timestamp': l.timestamp,
        'action': l.action, 'from_value': l.from_value, 'to_value': l.to_value,
        'performed_by': l.performed_by, 'performer_role': l.performer_role, 'notes': l.notes
    } for l in logs]

# ===================== ENHANCED STATS ENDPOINTS =====================

@app.get("/stats/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Check for SLA breaches first
    check_and_escalate_sla(db)
    
    all_complaints = db.query(Complaint).filter(Complaint.admissible == True).all()
    
    status_counts = {}
    dept_counts = {}
    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    category_counts = {}
    total_resolution_hours = 0
    resolved_count = 0
    sla_breached_count = 0
    sla_compliant_count = 0
    
    for c in all_complaints:
        status_counts[c.status] = status_counts.get(c.status, 0) + 1
        dept_counts[c.department] = dept_counts.get(c.department, 0) + 1
        label = c.officer_override or c.priority_label or "Low"
        if label in priority_counts:
            priority_counts[label] += 1
        category_counts[c.category] = category_counts.get(c.category, 0) + 1
        
        if c.status in ["Resolved", "Closed"]:
            resolved_count += 1
            if c.resolved_at and c.timestamp:
                try:
                    sub = datetime.datetime.strptime(c.timestamp, "%Y-%m-%d %H:%M:%S")
                    res = datetime.datetime.strptime(c.resolved_at, "%Y-%m-%d %H:%M:%S")
                    total_resolution_hours += (res - sub).total_seconds() / 3600
                except:
                    pass
            if getattr(c, 'sla_breached', False):
                sla_breached_count += 1
            else:
                sla_compliant_count += 1
        elif c.status not in ["Rejected"]:
            if getattr(c, 'sla_breached', False):
                sla_breached_count += 1
    
    avg_resolution_hours = round(total_resolution_hours / max(resolved_count, 1), 1)
    total_active = sum(1 for c in all_complaints if c.status not in ["Resolved", "Closed", "Rejected"])
    
    rejected_count = db.query(Complaint).filter(Complaint.admissible == False).count()
    overrides_count = db.query(OfficerFeedback).count()
    
    return {
        "total_complaints": len(all_complaints),
        "total_active": total_active,
        "resolved_count": resolved_count,
        "rejected_count": rejected_count,
        "overrides_count": overrides_count,
        "status_counts": status_counts,
        "department_counts": dept_counts,
        "priority_counts": priority_counts,
        "category_counts": category_counts,
        "avg_resolution_hours": avg_resolution_hours,
        "sla_breached_count": sla_breached_count,
        "sla_compliant_count": sla_compliant_count,
        "sla_compliance_rate": round(sla_compliant_count / max(sla_compliant_count + sla_breached_count, 1) * 100, 1)
    }

@app.get("/stats/officer/{officer_id}")
def get_officer_stats(officer_id: str, db: Session = Depends(get_db)):
    officer_complaints = db.query(Complaint).filter(
        Complaint.assigned_officer_id == officer_id,
        Complaint.admissible == True
    ).all()
    
    total = len(officer_complaints)
    resolved = sum(1 for c in officer_complaints if c.status in ["Resolved", "Closed"])
    sla_breached = sum(1 for c in officer_complaints if getattr(c, 'sla_breached', False))
    
    status_breakdown = {}
    for c in officer_complaints:
        status_breakdown[c.status] = status_breakdown.get(c.status, 0) + 1
    
    total_hours = 0
    resolved_with_time = 0
    for c in officer_complaints:
        if c.status in ["Resolved", "Closed"] and c.resolved_at and c.timestamp:
            try:
                sub = datetime.datetime.strptime(c.timestamp, "%Y-%m-%d %H:%M:%S")
                res = datetime.datetime.strptime(c.resolved_at, "%Y-%m-%d %H:%M:%S")
                total_hours += (res - sub).total_seconds() / 3600
                resolved_with_time += 1
            except:
                pass
    
    overrides = db.query(OfficerFeedback).filter(OfficerFeedback.officer_id == officer_id).count()
    
    return {
        "officer_id": officer_id,
        "total_assigned": total,
        "total_resolved": resolved,
        "resolution_rate": round(resolved / max(total, 1) * 100, 1),
        "avg_resolution_hours": round(total_hours / max(resolved_with_time, 1), 1),
        "sla_compliance_rate": round((total - sla_breached) / max(total, 1) * 100, 1),
        "sla_breached": sla_breached,
        "status_breakdown": status_breakdown,
        "overrides_count": overrides,
        "current_active": sum(1 for c in officer_complaints if c.status not in ["Resolved", "Closed", "Rejected"])
    }

@app.get("/complaints/sla-breached")
def get_sla_breached(db: Session = Depends(get_db)):
    check_and_escalate_sla(db)
    breached = db.query(Complaint).filter(
        Complaint.sla_breached == True,
        ~Complaint.status.in_(["Closed", "Rejected"])
    ).all()
    return [to_dict(c) for c in breached]

@app.get("/complaints/by-status/{status}")
def get_complaints_by_status(status: str, officer_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Complaint).filter(Complaint.status == status, Complaint.admissible == True)
    if officer_id:
        query = query.filter(Complaint.assigned_officer_id == officer_id)
    comps = query.all()
    result = [to_dict(c) for c in comps]
    result.sort(key=lambda x: x['final_priority_score'], reverse=True)
    return result
"""
content += audit_stats_endpoints


# 9. Update seed data generation
seed_target = """        else:
            db.commit()
    except Exception as e:
        print(f"Error seeding complaints: {e}")
        db.rollback()"""
seed_repl = """        else:
            db.commit()
            
            # Set SLA deadlines and create initial audit entries for all seeded complaints
            all_seeded = db.query(Complaint).filter(Complaint.id.like('CMP-2%')).all()
            for comp in all_seeded:
                if comp.admissible and not comp.sla_deadline:
                    comp.sla_deadline = calculate_sla_deadline(comp.priority_label or 'Low', comp.timestamp)
                    if not comp.status or comp.status == 'Open':
                        comp.status = 'Assigned' if comp.assigned_officer_id else 'Submitted'
            db.commit()
            
            # Distribute some complaints across different lifecycle states for realistic demo
            distributed = db.query(Complaint).filter(Complaint.id.like('CMP-2%'), Complaint.admissible == True).all()
            for i, comp in enumerate(distributed):
                now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if i < 15:
                    # Keep as Assigned (waiting for officer)
                    comp.status = 'Assigned'
                elif i < 22:
                    # Accepted
                    comp.status = 'Accepted'
                    comp.accepted_at = comp.timestamp
                elif i < 30:
                    # In Progress
                    comp.status = 'In Progress'
                    comp.accepted_at = comp.timestamp
                elif i < 33:
                    # Field Inspection
                    comp.status = 'Field Inspection'
                    comp.accepted_at = comp.timestamp
                elif i < 36:
                    # Escalated
                    comp.status = 'Escalated'
                    comp.escalation_level = 1
                    comp.accepted_at = comp.timestamp
                    esc_hist = json.loads(comp.escalation_history or '[]')
                    esc_hist.append({'level': 'L2 - Senior Inspector', 'date': now_str, 'reason': 'Unresolved beyond expected timeline'})
                    comp.escalation_history = json.dumps(esc_hist)
                elif i < 43:
                    # Resolved
                    comp.status = 'Resolved'
                    comp.accepted_at = comp.timestamp
                    comp.resolved_at = now_str
                    res_hist = json.loads(comp.resolution_history or '[]')
                    res_hist.append({'status': 'Resolved', 'date': now_str, 'notes': 'Issue addressed and resolved.'})
                    comp.resolution_history = json.dumps(res_hist)
                else:
                    # Closed
                    comp.status = 'Closed'
                    comp.accepted_at = comp.timestamp
                    comp.resolved_at = now_str
                    comp.closed_at = now_str
                    res_hist = json.loads(comp.resolution_history or '[]')
                    res_hist.append({'status': 'Resolved', 'date': now_str, 'notes': 'Issue resolved.'})
                    res_hist.append({'status': 'Closed', 'date': now_str, 'notes': 'Closed after verification.'})
                    comp.resolution_history = json.dumps(res_hist)
            db.commit()
            print('✅ Complaint lifecycle states distributed for demo.')
            
    except Exception as e:
        print(f"Error seeding complaints: {e}")
        db.rollback()"""
content = content.replace(seed_target, seed_repl)


# 10. Update stats endpoint old logic
stats_target = """    admissible_count = db.query(Complaint).filter(Complaint.admissible == True, Complaint.status != "Resolved").count()"""
stats_repl = """    admissible_count = db.query(Complaint).filter(Complaint.admissible == True, ~Complaint.status.in_(["Resolved", "Closed", "Rejected"])).count()"""
content = content.replace(stats_target, stats_repl)


with open("api.py", "w") as f:
    f.write(content)

with open("api.py", "r") as f:
    content = f.read()

endpoints = """
@app.get("/sla-configurations")
def get_sla_configurations(db: Session = Depends(get_db)):
    return db.query(SLAConfiguration).all()

@app.put("/sla-configurations/{department}")
def update_sla_configuration(department: str, data: dict, db: Session = Depends(get_db)):
    config = db.query(SLAConfiguration).filter(SLAConfiguration.department == department).first()
    if not config:
        raise HTTPException(status_code=404, detail="SLA config not found")
    
    if "resolve_sla_hours" in data:
        config.resolve_sla_hours = data["resolve_sla_hours"]
    if "accept_sla_hours" in data:
        config.accept_sla_hours = data["accept_sla_hours"]
        
    db.commit()
    return {"status": "success"}

@app.get("/escalation-configurations")
def get_escalation_configurations(db: Session = Depends(get_db)):
    return db.query(EscalationConfiguration).all()

@app.put("/escalation-configurations/{level}")
def update_escalation_configuration(level: int, data: dict, db: Session = Depends(get_db)):
    config = db.query(EscalationConfiguration).filter(EscalationConfiguration.level == level).first()
    if not config:
        raise HTTPException(status_code=404, detail="Escalation config not found")
        
    if "priority_threshold" in data:
        config.priority_threshold = data["priority_threshold"]
    if "unresolved_hours_threshold" in data:
        config.unresolved_hours_threshold = data["unresolved_hours_threshold"]
        
    db.commit()
    return {"status": "success"}
"""

if "def get_sla_configurations" not in content:
    content = content.replace("@app.get(\"/department-policies\")", endpoints + "\n@app.get(\"/department-policies\")")
    with open("api.py", "w") as f:
        f.write(content)
    print("Added SLA/Escalation config endpoints!")

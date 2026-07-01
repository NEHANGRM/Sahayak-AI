import re

with open("api.py", "r") as f:
    content = f.read()

# Add SLA seeder
sla_seeder = """
def seed_sla_configurations(db: Session):
    if db.query(SLAConfiguration).count() > 0:
        return
        
    configs = [
        SLAConfiguration(department="Water & Sewerage Board", resolve_sla_hours=72, accept_sla_hours=24),
        SLAConfiguration(department="Public Works Department (PWD)", resolve_sla_hours=168, accept_sla_hours=48), # 7 days
        SLAConfiguration(department="Health Department", resolve_sla_hours=24, accept_sla_hours=12),
        SLAConfiguration(department="Electricity Utilities Board", resolve_sla_hours=48, accept_sla_hours=12),
        SLAConfiguration(department="Police & Disaster Response", resolve_sla_hours=2, accept_sla_hours=1),
        SLAConfiguration(department="Municipal Sanitation Department", resolve_sla_hours=72, accept_sla_hours=24),
        SLAConfiguration(department="Transport & Traffic Authority", resolve_sla_hours=48, accept_sla_hours=24),
        SLAConfiguration(department="Education Department", resolve_sla_hours=168, accept_sla_hours=48),
        SLAConfiguration(department="Vigilance Bureau", resolve_sla_hours=168, accept_sla_hours=48),
        SLAConfiguration(department="General Administration Department", resolve_sla_hours=72, accept_sla_hours=24)
    ]
    for conf in configs:
        db.add(conf)
    db.commit()

def seed_escalation_configurations(db: Session):
    if db.query(EscalationConfiguration).count() > 0:
        return
        
    configs = [
        EscalationConfiguration(level=1, priority_threshold=1.0, unresolved_hours_threshold=72, description="Assigned Officer"),
        EscalationConfiguration(level=2, priority_threshold=0.7, unresolved_hours_threshold=48, description="Supervising Officer"),
        EscalationConfiguration(level=3, priority_threshold=0.85, unresolved_hours_threshold=24, description="Department Head"),
        EscalationConfiguration(level=4, priority_threshold=0.95, unresolved_hours_threshold=12, description="Commissioner")
    ]
    for conf in configs:
        db.add(conf)
    db.commit()
"""

if "def seed_sla_configurations" not in content:
    content = content.replace("def seed_department_policies(db: Session):", sla_seeder + "\ndef seed_department_policies(db: Session):")

# Add the seeders to startup
old_startup = """    seed_department_policies(db)
    seed_officers(db)"""
new_startup = """    seed_department_policies(db)
    seed_sla_configurations(db)
    seed_escalation_configurations(db)
    seed_officers(db)"""
if "seed_sla_configurations(db)" not in content:
    content = content.replace(old_startup, new_startup)

with open("api.py", "w") as f:
    f.write(content)
print("Added SLA and Escalation seeders!")

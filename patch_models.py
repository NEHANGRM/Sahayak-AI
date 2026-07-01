import re

with open("api.py", "r") as f:
    content = f.read()

# Models to add before OfficerFeedback
new_models = """# SLA Configuration
class SLAConfiguration(Base):
    __tablename__ = 'sla_configurations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String, unique=True, nullable=False)
    resolve_sla_hours = Column(Integer, default=72)
    accept_sla_hours = Column(Integer, default=24)

# Escalation Configuration
class EscalationConfiguration(Base):
    __tablename__ = 'escalation_configurations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(Integer, unique=True, nullable=False)  # 1, 2, 3, 4
    priority_threshold = Column(Float, default=0.8)
    unresolved_hours_threshold = Column(Integer, default=72)
    description = Column(String, nullable=True)

# Escalation History
class EscalationHistory(Base):
    __tablename__ = 'escalation_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String, nullable=False)
    from_level = Column(Integer, nullable=False)
    to_level = Column(Integer, nullable=False)
    timestamp = Column(String, nullable=False)
    trigger_reason = Column(String, nullable=False)
    user_responsible = Column(String, nullable=False)

"""

if "class SLAConfiguration(Base):" not in content:
    content = content.replace("# Officer Feedback for Learning", new_models + "# Officer Feedback for Learning")

# Expand Notification model
old_notif = """class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # officer_id or "admin"
    message = Column(String, nullable=False)
    type = Column(String, default="info")
    timestamp = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)"""

new_notif = """class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # officer_id, "admin", or "commissioner"
    message = Column(String, nullable=False)
    type = Column(String, default="info")
    timestamp = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    complaint_id = Column(String, nullable=True)
    escalation_level = Column(Integer, nullable=True)
    priority = Column(String, nullable=True)"""

content = content.replace(old_notif, new_notif)

# Expand Complaint model
old_comp = """    escalation_level = Column(Integer, default=0)     # 0=normal, 1=senior, 2=dept head, 3=ministry"""
new_comp = """    escalation_level = Column(Integer, default=1)     # 1=Assigned, 2=Supervisor, 3=Dept Head, 4=Commissioner
    sla_start_time = Column(String, nullable=True)"""
content = content.replace(old_comp, new_comp)

# Add migrations for the new columns in startup_db_init
migration_block = """            ("escalation_level", "INTEGER")
        ]"""
new_migration_block = """            ("escalation_level", "INTEGER"),
            ("sla_start_time", "VARCHAR")
        ]"""
content = content.replace(migration_block, new_migration_block)

migration_block_notif = """                    with conn.begin():
                        conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))"""
new_migration_block_notif = """                    with conn.begin():
                        conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass
                    
        notif_cols = [
            ("complaint_id", "VARCHAR"),
            ("escalation_level", "INTEGER"),
            ("priority", "VARCHAR")
        ]
        with engine.connect() as conn:
            for col_name, col_type in notif_cols:
                try:
                    with conn.begin():
                        conn.execute(text(f"ALTER TABLE notifications ADD COLUMN {col_name} {col_type}"))"""
if "ALTER TABLE notifications ADD COLUMN" not in content:
    content = content.replace(migration_block_notif, new_migration_block_notif)


with open("api.py", "w") as f:
    f.write(content)
print("Added SLA and Escalation models!")

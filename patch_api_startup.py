import re

with open("api.py", "r") as f:
    content = f.read()

old_block = """# Create tables
Base.metadata.create_all(bind=engine)

# Migration to add missing columns to existing SQLite/PostgreSQL database if missing
try:
    from sqlalchemy import text
    columns_to_add = [
        ("assigned_officer_id", "VARCHAR"),
        ("global_priority_score", "FLOAT"),
        ("officer_priority_score", "FLOAT"),
        ("submitted_by", "VARCHAR"),
        ("llm_reviewed", "BOOLEAN"),
        ("llm_adjustment", "FLOAT"),
        ("llm_reasoning", "TEXT"),
        ("llm_risk_summary", "TEXT"),
        ("llm_public_safety_risk", "VARCHAR"),
        ("llm_vulnerable_population_risk", "VARCHAR"),
        ("llm_infrastructure_risk", "VARCHAR"),
        ("llm_trigger_reasons", "TEXT"),
        ("sla_deadline", "VARCHAR"),
        ("sla_breached", "BOOLEAN"),
        ("accepted_at", "VARCHAR"),
        ("resolved_at", "VARCHAR"),
        ("closed_at", "VARCHAR"),
        ("escalation_level", "INTEGER")
    ]
    with engine.connect() as conn:
        for col_name, col_type in columns_to_add:
            try:
                with conn.begin():
                    conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))
            except Exception:
                pass
except Exception as e:
    print(f"Migration error: {e}")



try:
    from sqlalchemy import text
    with engine.connect() as conn:
        with conn.begin():
            # Link existing seeded complaints to citizen1 so they have previous history
            conn.execute(text("UPDATE complaints SET submitted_by = 'citizen1' WHERE submitted_by IS NULL"))
except Exception:
    pass

try:
    from sqlalchemy import text
    with engine.connect() as conn:
        with conn.begin():
            # Add profile_pic column to officers table
            conn.execute(text("ALTER TABLE officers ADD COLUMN profile_pic TEXT"))
except Exception:
    pass"""

new_block = """@app.on_event("startup")
def startup_db_init():
    print("Initializing Database...")
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Migrations
        from sqlalchemy import text
        columns_to_add = [
            ("assigned_officer_id", "VARCHAR"),
            ("global_priority_score", "FLOAT"),
            ("officer_priority_score", "FLOAT"),
            ("submitted_by", "VARCHAR"),
            ("llm_reviewed", "BOOLEAN"),
            ("llm_adjustment", "FLOAT"),
            ("llm_reasoning", "TEXT"),
            ("llm_risk_summary", "TEXT"),
            ("llm_public_safety_risk", "VARCHAR"),
            ("llm_vulnerable_population_risk", "VARCHAR"),
            ("llm_infrastructure_risk", "VARCHAR"),
            ("llm_trigger_reasons", "TEXT"),
            ("sla_deadline", "VARCHAR"),
            ("sla_breached", "BOOLEAN"),
            ("accepted_at", "VARCHAR"),
            ("resolved_at", "VARCHAR"),
            ("closed_at", "VARCHAR"),
            ("escalation_level", "INTEGER")
        ]
        with engine.connect() as conn:
            for col_name, col_type in columns_to_add:
                try:
                    with conn.begin():
                        conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass

        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("UPDATE complaints SET submitted_by = 'citizen1' WHERE submitted_by IS NULL"))
        
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("ALTER TABLE officers ADD COLUMN profile_pic TEXT"))
        print("Database Initialized Successfully.")
    except Exception as e:
        print(f"Database initialization failed during startup. Check credentials! Error: {e}")"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open("api.py", "w") as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Could not find the block to replace!")


with open("api.py", "r") as f:
    content = f.read()

old_seed = """def seed_database(db: Session):
    # Check if there are any citizen complaints (CMP-2006 or higher)
    citizen_exists = db.query(Complaint).filter(Complaint.id > "CMP-3050").count() > 0
    if citizen_exists:
        print("ℹ️ Citizen complaints exist. Skipping database wipe and seed.")
        return
        
    # Otherwise, wipe the database and re-seed the 5 complaints
    db.query(Complaint).delete()
    db.query(User).delete()
    db.query(Officer).delete()
    db.query(DepartmentPolicy).delete()
    db.commit()
    
    # We must call the other seeders here since we wiped them!
    seed_department_policies(db)
    seed_sla_configurations(db)
    seed_escalation_configurations(db)
    seed_officers(db)
    seed_users(db)
    
    print("🧹 Wiped all existing data from the database for re-seeding.")"""

new_seed = """def seed_database(db: Session):
    # Check if the NEW seeded data already exists (CMP-3001 is the first new seed)
    new_seeds_exist = db.query(Complaint).filter(Complaint.id == "CMP-3001").count() > 0
    # Also check if new officer format exists
    new_officers_exist = db.query(Officer).filter(Officer.officer_id == "OFF1_W_L1").count() > 0
    
    if new_seeds_exist and new_officers_exist:
        print("ℹ️ New seeded data already exists. Skipping database wipe and seed.")
        return
        
    # Wipe ALL tables to start fresh with new format
    print("🧹 Wiping all existing data for re-seeding with new format...")
    db.query(Complaint).delete()
    db.query(User).delete()
    db.query(Officer).delete()
    db.query(DepartmentPolicy).delete()
    db.query(SLAConfiguration).delete()
    db.query(EscalationConfiguration).delete()
    db.query(EscalationHistory).delete()
    db.query(Notification).delete()
    db.commit()
    
    # Re-seed all tables from scratch
    seed_department_policies(db)
    seed_sla_configurations(db)
    seed_escalation_configurations(db)
    seed_officers(db)
    seed_users(db)
    
    print("✅ All tables wiped and re-seeded successfully.")"""

content = content.replace(old_seed, new_seed)

with open("api.py", "w") as f:
    f.write(content)
print("Fixed seed_database condition!")

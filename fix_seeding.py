with open("api.py", "r") as f:
    content = f.read()

seeding_block = """# Run seeding and cleanups
db = SessionLocal()
seed_database(db)
seed_officers(db)
seed_users(db)
seed_department_policies(db)
try:
    deleted = db.query(Complaint).filter(Complaint.id.in_(["CMP-2006", "CMP-2007"])).delete(synchronize_session=False)
    db.commit()
    print(f"🧹 Database cleanup: deleted {deleted} complaints (CMP-2006, CMP-2007)")
except Exception as e:
    print(f"Error during db cleanup: {e}")
db.close()"""

new_startup = """        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("ALTER TABLE officers ADD COLUMN profile_pic TEXT"))
        
        # Run seeding and cleanups
        db = SessionLocal()
        seed_database(db)
        seed_officers(db)
        seed_users(db)
        seed_department_policies(db)
        try:
            deleted = db.query(Complaint).filter(Complaint.id.in_(["CMP-2006", "CMP-2007"])).delete(synchronize_session=False)
            db.commit()
            print(f"🧹 Database cleanup: deleted {deleted} complaints (CMP-2006, CMP-2007)")
        except Exception as e:
            print(f"Error during db cleanup: {e}")
        db.close()
        
        print("Database Initialized Successfully.")"""

old_startup = """        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("ALTER TABLE officers ADD COLUMN profile_pic TEXT"))
        print("Database Initialized Successfully.")"""

if seeding_block in content and old_startup in content:
    content = content.replace(seeding_block, "")
    content = content.replace(old_startup, new_startup)
    with open("api.py", "w") as f:
        f.write(content)
    print("Seeding logic successfully moved into startup event!")
else:
    print("Could not find blocks.")

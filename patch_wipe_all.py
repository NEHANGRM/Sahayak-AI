with open("api.py", "r") as f:
    content = f.read()

old_wipe = """    # Otherwise, wipe the database and re-seed the 5 complaints
    db.query(Complaint).delete()
    db.commit()
    print("🧹 Wiped all existing complaints from the database for re-seeding.")"""

new_wipe = """    # Otherwise, wipe the database and re-seed the 5 complaints
    db.query(Complaint).delete()
    db.query(User).delete()
    db.query(Officer).delete()
    db.query(DepartmentPolicy).delete()
    db.commit()
    
    # We must call the other seeders here since we wiped them!
    seed_department_policies(db)
    seed_officers(db)
    seed_users(db)
    
    print("🧹 Wiped all existing data from the database for re-seeding.")"""

content = content.replace(old_wipe, new_wipe)

with open("api.py", "w") as f:
    f.write(content)
print("Updated wipe logic in seed_database!")

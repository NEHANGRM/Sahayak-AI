with open("api.py", "r") as f:
    content = f.read()

endpoint = """
@app.get("/reseed-danger")
def reseed_danger(db: Session = Depends(get_db)):
    db.query(Complaint).delete()
    db.query(User).delete()
    db.query(Officer).delete()
    db.query(DepartmentPolicy).delete()
    db.commit()
    
    seed_department_policies(db)
    seed_officers(db)
    seed_users(db)
    seed_database(db)
    return {"status": "Database wiped and reseeded successfully."}

"""

if "/reseed-danger" not in content:
    content = content.replace('app.add_middleware(', endpoint + '\napp.add_middleware(')
    with open("api.py", "w") as f:
        f.write(content)
    print("Added /reseed-danger endpoint.")
else:
    print("Endpoint already exists.")

with open("api.py", "r") as f:
    content = f.read()

wipe_endpoint = """
@app.get("/wipe-and-reseed-db-danger")
def wipe_and_reseed_db(db: Session = Depends(get_db)):
    db.query(Complaint).delete()
    db.query(User).delete()
    db.query(Officer).delete()
    db.query(DepartmentPolicy).delete()
    db.commit()
    seed_department_policies(db)
    seed_officers(db)
    seed_users(db)
    seed_database(db)
    return {"status": "Database wiped and reseeded successfully!"}

"""

if wipe_endpoint in content:
    content = content.replace(wipe_endpoint, "")
    with open("api.py", "w") as f:
        f.write(content)
    print("Endpoint removed.")
else:
    print("Endpoint not found.")

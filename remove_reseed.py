import re

with open("api.py", "r") as f:
    content = f.read()

# The block to remove:
# @app.get("/reseed-danger")
# def reseed_danger(db: Session = Depends(get_db)):
#     db.query(Complaint).delete()
#     db.query(User).delete()
#     db.query(Officer).delete()
#     db.query(DepartmentPolicy).delete()
#     db.commit()
#     
#     seed_department_policies(db)
#     seed_officers(db)
#     seed_users(db)
#     seed_database(db)
#     return {"status": "Database wiped and reseeded successfully."}

pattern = r'@app\.get\("/reseed-danger"\).*?return \{"status": "Database wiped and reseeded successfully\."\}'
content = re.sub(pattern, '', content, flags=re.DOTALL)

with open("api.py", "w") as f:
    f.write(content)
print("Removed reseed-danger endpoint.")

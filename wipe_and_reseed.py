from api import SessionLocal, Complaint, User, Officer, DepartmentPolicy, engine, Base
from api import seed_department_policies, seed_officers, seed_users, seed_database

def wipe_and_reseed():
    db = SessionLocal()
    
    print("Wiping existing data...")
    db.query(Complaint).delete()
    db.query(User).delete()
    db.query(Officer).delete()
    db.query(DepartmentPolicy).delete()
    db.commit()
    print("Data wiped!")
    
    print("Reseeding...")
    seed_department_policies(db)
    seed_officers(db)
    seed_users(db)
    seed_database(db)
    print("Reseeding complete!")
    
    db.close()

if __name__ == "__main__":
    wipe_and_reseed()

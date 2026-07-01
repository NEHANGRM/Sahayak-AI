import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This will load the models so we can query them
from api import Base, Complaint, Officer, User, DepartmentPolicy, OfficerFeedback, AuditLog, Notification

def migrate_data(supabase_url):
    print("Connecting to local SQLite...")
    sqlite_url = "sqlite:///./sahayak_ai.db"
    sqlite_engine = create_engine(sqlite_url)
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()

    print(f"Connecting to Supabase at {supabase_url} ...")
    if supabase_url.startswith("postgres://"):
        supabase_url = supabase_url.replace("postgres://", "postgresql://", 1)
        
    try:
        supabase_engine = create_engine(supabase_url)
        # Create tables in Supabase if they don't exist
        Base.metadata.create_all(bind=supabase_engine)
    except Exception as e:
        print(f"Failed to connect to Supabase: {e}")
        sys.exit(1)

    SupabaseSession = sessionmaker(bind=supabase_engine)
    supa_session = SupabaseSession()

    tables_to_migrate = [
        (Officer, "Officers"),
        (User, "Users"),
        (Complaint, "Complaints"),
        (DepartmentPolicy, "Department Policies"),
        (OfficerFeedback, "Officer Feedback"),
        (AuditLog, "Audit Logs"),
        (Notification, "Notifications")
    ]

    for model, name in tables_to_migrate:
        print(f"Migrating {name}...")
        records = sqlite_session.query(model).all()
        print(f" Found {len(records)} records.")
        
        # We need to detach them from the sqlite session to add to supabase session
        for record in records:
            sqlite_session.expunge(record)
            from sqlalchemy.orm import make_transient
            make_transient(record)
            
        supa_session.add_all(records)
        try:
            supa_session.commit()
            print(f" Successfully migrated {name}!")
        except Exception as e:
            supa_session.rollback()
            print(f" Error migrating {name}: {e}")

    print("Migration complete!")
    sqlite_session.close()
    supa_session.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_supabase.py <SUPABASE_URL>")
        sys.exit(1)
    migrate_data(sys.argv[1])

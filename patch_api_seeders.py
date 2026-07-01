import re

with open("api.py", "r") as f:
    content = f.read()

# Fix 1: Re-order seed functions in startup_db_init
old_startup = """        # Run seeding and cleanups
        db = SessionLocal()
        seed_database(db)
        seed_officers(db)
        seed_users(db)
        seed_department_policies(db)"""

new_startup = """        # Run seeding and cleanups
        db = SessionLocal()
        seed_department_policies(db)
        seed_officers(db)
        seed_users(db)
        seed_database(db)"""

if old_startup in content:
    content = content.replace(old_startup, new_startup)
else:
    print("Could not find startup block.")

# Fix 2: Add citizen2 to seed_users
old_users = """        User(
            user_id="USR-011",
            username="citizen1",
            password_hash=bcrypt.hashpw(b"cit123", bcrypt.gensalt()).decode('utf-8'),
            role="citizen",
            officer_id=None,
            name="Demo Citizen"
        ),
    ]"""

new_users = """        User(
            user_id="USR-011",
            username="citizen1",
            password_hash=bcrypt.hashpw(b"cit123", bcrypt.gensalt()).decode('utf-8'),
            role="citizen",
            officer_id=None,
            name="Demo Citizen"
        ),
        User(
            user_id="USR-012",
            username="citizen2",
            password_hash=bcrypt.hashpw(b"cit123", bcrypt.gensalt()).decode('utf-8'),
            role="citizen",
            officer_id=None,
            name="Demo Citizen 2"
        ),
    ]"""

if old_users in content:
    content = content.replace(old_users, new_users)
else:
    print("Could not find users block.")

# Fix 3: Randomize citizen assignment in seed_database
old_citizen = """            assigned_officer_id=assigned_officer_id,
            submitted_by="citizen1"
        )"""

new_citizen = """            assigned_officer_id=assigned_officer_id,
            submitted_by="citizen2" if int(comp_id.split("-")[1]) % 2 == 0 else "citizen1"
        )"""

if old_citizen in content:
    content = content.replace(old_citizen, new_citizen)
else:
    print("Could not find citizen block.")

with open("api.py", "w") as f:
    f.write(content)

print("Patching complete.")

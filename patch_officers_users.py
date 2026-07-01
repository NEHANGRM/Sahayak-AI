with open("api.py", "r") as f:
    content = f.read()

# Replace officers
old_officers = """    officers = [
        Officer(officer_id="OFF-001", name="Rajesh Kumar", department="Water & Sewerage Board", zone="Anna Nagar", ward="Ward 5", designation="Junior Inspector", email="rajesh.water@gov.in"),
        Officer(officer_id="OFF-002", name="Priya Sharma", department="Public Works Department (PWD)", zone="T. Nagar", ward="Ward 3", designation="Senior Inspector", email="priya.pwd@gov.in"),
        Officer(officer_id="OFF-003", name="Suresh Babu", department="Electricity Utilities Board", zone="Adyar", ward="Ward 8", designation="Junior Inspector", email="suresh.elec@gov.in"),
        Officer(officer_id="OFF-004", name="Kavitha Rajan", department="Health Department", zone="Mylapore", ward="Ward 12", designation="Health Inspector", email="kavitha.health@gov.in"),
        Officer(officer_id="OFF-005", name="Arun Prakash", department="Police & Disaster Response", zone="Anna Nagar", ward="Ward 5", designation="Sub Inspector", email="arun.police@gov.in"),
        Officer(officer_id="OFF-006", name="Deepa Venkat", department="Municipal Sanitation Department", zone="Velachery", ward="Ward 15", designation="Sanitation Inspector", email="deepa.sanitation@gov.in"),
        Officer(officer_id="OFF-007", name="Mohan Das", department="Transport & Traffic Authority", zone="Guindy", ward="Ward 10", designation="Traffic Inspector", email="mohan.transport@gov.in"),
        Officer(officer_id="OFF-008", name="Lakshmi Narayanan", department="Education Department", zone="Nungambakkam", ward="Ward 7", designation="Education Officer", email="lakshmi.edu@gov.in"),
        Officer(officer_id="OFF-009", name="Ganesh Iyer", department="Vigilance Bureau", zone="Egmore", ward="Ward 2", designation="Vigilance Inspector", email="ganesh.vigilance@gov.in"),
        Officer(officer_id="OFF-010", name="Anitha Subramanian", department="General Administration Department", zone="Fort St. George", ward="Ward 1", designation="Administrative Officer", email="anitha.admin@gov.in"),
    ]"""

new_officers = """    officers = [
        Officer(officer_id="OFF1_W_L1", name="Rajesh Kumar", department="Water & Sewerage Board", zone="Anna Nagar", ward="Ward 5", designation="Junior Inspector", email="rajesh.water@gov.in"),
        Officer(officer_id="OFF2_P_L1", name="Priya Sharma", department="Public Works Department (PWD)", zone="T. Nagar", ward="Ward 3", designation="Senior Inspector", email="priya.pwd@gov.in"),
        Officer(officer_id="OFF3_E_L1", name="Suresh Babu", department="Electricity Utilities Board", zone="Adyar", ward="Ward 8", designation="Junior Inspector", email="suresh.elec@gov.in"),
        Officer(officer_id="OFF4_H_L1", name="Kavitha Rajan", department="Health Department", zone="Mylapore", ward="Ward 12", designation="Health Inspector", email="kavitha.health@gov.in"),
        Officer(officer_id="OFF5_P_L1", name="Arun Prakash", department="Police & Disaster Response", zone="Anna Nagar", ward="Ward 5", designation="Sub Inspector", email="arun.police@gov.in"),
        Officer(officer_id="OFF6_M_L1", name="Deepa Venkat", department="Municipal Sanitation Department", zone="Velachery", ward="Ward 15", designation="Sanitation Inspector", email="deepa.sanitation@gov.in"),
        Officer(officer_id="OFF7_T_L1", name="Mohan Das", department="Transport & Traffic Authority", zone="Guindy", ward="Ward 10", designation="Traffic Inspector", email="mohan.transport@gov.in"),
        Officer(officer_id="OFF8_E_L1", name="Lakshmi Narayanan", department="Education Department", zone="Nungambakkam", ward="Ward 7", designation="Education Officer", email="lakshmi.edu@gov.in"),
        Officer(officer_id="OFF9_V_L1", name="Ganesh Iyer", department="Vigilance Bureau", zone="Egmore", ward="Ward 2", designation="Vigilance Inspector", email="ganesh.vigilance@gov.in"),
        Officer(officer_id="OFF10_G_L1", name="Anitha Subramanian", department="General Administration Department", zone="Fort St. George", ward="Ward 1", designation="Administrative Officer", email="anitha.admin@gov.in"),
    ]"""

content = content.replace(old_officers, new_officers)

# Replace Admin
old_admin = """        User(
            user_id="USR-000",
            username="admin",
            password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8'),
            role="admin",
            officer_id=None,
            name="System Administrator"
        ),"""

new_admin = """        User(
            user_id="USR-000",
            username="ADM1_A_L5",
            password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8'),
            role="admin",
            officer_id=None,
            name="System Administrator"
        ),"""

content = content.replace(old_admin, new_admin)

# Replace Officer loop
old_loop = """        users.append(
            User(
                user_id=f"USR-{i+1:03d}",
                username=f"officer{i+1}",
                password_hash=bcrypt.hashpw(b"off123", bcrypt.gensalt()).decode('utf-8'),
                role="officer",
                officer_id=officer.officer_id,
                name=officer.name
            )
        )"""

new_loop = """        users.append(
            User(
                user_id=f"USR-{i+1:03d}",
                username=officer.officer_id,
                password_hash=bcrypt.hashpw(b"off123", bcrypt.gensalt()).decode('utf-8'),
                role="officer",
                officer_id=officer.officer_id,
                name=officer.name
            )
        )"""

content = content.replace(old_loop, new_loop)

with open("api.py", "w") as f:
    f.write(content)
print("Updated officers and users!")

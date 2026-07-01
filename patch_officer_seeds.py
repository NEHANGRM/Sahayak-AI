import re

with open("api.py", "r") as f:
    content = f.read()

# Current officer list ends around: Officer(officer_id="OFF10_G_L1", ...)
# I will just replace the `officers = [` block entirely up to `]`
new_officers = """    officers = [
        # Level 1 Officers (Assigned Officers)
        Officer(officer_id="OFF1_W_L1", name="Rajesh Kumar", department="Water & Sewerage Board", zone="Anna Nagar", ward="Ward 5", designation="Junior Inspector", email="rajesh.water@gov.in", escalation_level=1),
        Officer(officer_id="OFF2_P_L1", name="Priya Sharma", department="Public Works Department (PWD)", zone="T. Nagar", ward="Ward 3", designation="Senior Inspector", email="priya.pwd@gov.in", escalation_level=1),
        Officer(officer_id="OFF3_E_L1", name="Suresh Babu", department="Electricity Utilities Board", zone="Adyar", ward="Ward 8", designation="Junior Inspector", email="suresh.elec@gov.in", escalation_level=1),
        Officer(officer_id="OFF4_H_L1", name="Kavitha Rajan", department="Health Department", zone="Mylapore", ward="Ward 12", designation="Health Inspector", email="kavitha.health@gov.in", escalation_level=1),
        Officer(officer_id="OFF5_P_L1", name="Arun Prakash", department="Police & Disaster Response", zone="Anna Nagar", ward="Ward 5", designation="Sub Inspector", email="arun.police@gov.in", escalation_level=1),
        Officer(officer_id="OFF6_M_L1", name="Deepa Venkat", department="Municipal Sanitation Department", zone="Velachery", ward="Ward 15", designation="Sanitation Inspector", email="deepa.sanitation@gov.in", escalation_level=1),
        Officer(officer_id="OFF7_T_L1", name="Mohan Das", department="Transport & Traffic Authority", zone="Guindy", ward="Ward 10", designation="Traffic Inspector", email="mohan.transport@gov.in", escalation_level=1),
        Officer(officer_id="OFF8_E_L1", name="Lakshmi Narayanan", department="Education Department", zone="Nungambakkam", ward="Ward 7", designation="Education Officer", email="lakshmi.edu@gov.in", escalation_level=1),
        Officer(officer_id="OFF9_V_L1", name="Ganesh Iyer", department="Vigilance Bureau", zone="Egmore", ward="Ward 2", designation="Vigilance Inspector", email="ganesh.vigilance@gov.in", escalation_level=1),
        Officer(officer_id="OFF10_G_L1", name="Anitha Subramanian", department="General Administration Department", zone="Fort St. George", ward="Ward 1", designation="Administrative Officer", email="anitha.admin@gov.in", escalation_level=1),
        
        # Level 2 Officers (Supervisors) - We add one for each department just to be complete, or maybe a few. Let's add for all.
        Officer(officer_id="OFF1_W_L2", name="W_Supervisor", department="Water & Sewerage Board", zone="All", ward="All", designation="Supervisor", email="w.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF2_P_L2", name="P_Supervisor", department="Public Works Department (PWD)", zone="All", ward="All", designation="Supervisor", email="p.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF3_E_L2", name="E_Supervisor", department="Electricity Utilities Board", zone="All", ward="All", designation="Supervisor", email="e.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF4_H_L2", name="H_Supervisor", department="Health Department", zone="All", ward="All", designation="Supervisor", email="h.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF5_P_L2", name="Pol_Supervisor", department="Police & Disaster Response", zone="All", ward="All", designation="Supervisor", email="pol.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF6_M_L2", name="M_Supervisor", department="Municipal Sanitation Department", zone="All", ward="All", designation="Supervisor", email="m.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF7_T_L2", name="T_Supervisor", department="Transport & Traffic Authority", zone="All", ward="All", designation="Supervisor", email="t.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF8_E_L2", name="Ed_Supervisor", department="Education Department", zone="All", ward="All", designation="Supervisor", email="ed.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF9_V_L2", name="V_Supervisor", department="Vigilance Bureau", zone="All", ward="All", designation="Supervisor", email="v.sup@gov.in", escalation_level=2),
        Officer(officer_id="OFF10_G_L2", name="G_Supervisor", department="General Administration Department", zone="All", ward="All", designation="Supervisor", email="g.sup@gov.in", escalation_level=2),

        # Level 3 Officers (Department Heads)
        Officer(officer_id="OFF1_W_L3", name="W_DeptHead", department="Water & Sewerage Board", zone="All", ward="All", designation="Dept Head", email="w.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF2_P_L3", name="P_DeptHead", department="Public Works Department (PWD)", zone="All", ward="All", designation="Dept Head", email="p.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF3_E_L3", name="E_DeptHead", department="Electricity Utilities Board", zone="All", ward="All", designation="Dept Head", email="e.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF4_H_L3", name="H_DeptHead", department="Health Department", zone="All", ward="All", designation="Dept Head", email="h.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF5_P_L3", name="Pol_DeptHead", department="Police & Disaster Response", zone="All", ward="All", designation="Dept Head", email="pol.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF6_M_L3", name="M_DeptHead", department="Municipal Sanitation Department", zone="All", ward="All", designation="Dept Head", email="m.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF7_T_L3", name="T_DeptHead", department="Transport & Traffic Authority", zone="All", ward="All", designation="Dept Head", email="t.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF8_E_L3", name="Ed_DeptHead", department="Education Department", zone="All", ward="All", designation="Dept Head", email="ed.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF9_V_L3", name="V_DeptHead", department="Vigilance Bureau", zone="All", ward="All", designation="Dept Head", email="v.head@gov.in", escalation_level=3),
        Officer(officer_id="OFF10_G_L3", name="G_DeptHead", department="General Administration Department", zone="All", ward="All", designation="Dept Head", email="g.head@gov.in", escalation_level=3),
        
        # Level 4 Commissioner (We don't need a department because commissioner spans all, but we can assign a dummy department or 'All')
        Officer(officer_id="COMM_1", name="City Commissioner", department="Commissioner Office", zone="All", ward="All", designation="Commissioner", email="comm@gov.in", escalation_level=4, role="commissioner"),
    ]"""

content = re.sub(r'    officers = \[.*?\]', new_officers, content, flags=re.DOTALL)

# Add Commissioner User
old_users = """    users = [
        User(
            user_id="USR-000",
            username="ADM1_A_L5",
            password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8'),
            role="admin",
            officer_id=None,
            name="System Administrator"
        ),"""

new_users = """    users = [
        User(
            user_id="USR-000",
            username="ADM1_A_L5",
            password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8'),
            role="admin",
            officer_id=None,
            name="System Administrator"
        ),
        User(
            user_id="COMM-001",
            username="COMM_1",
            password_hash=bcrypt.hashpw(b"comm123", bcrypt.gensalt()).decode('utf-8'),
            role="commissioner",
            officer_id="COMM_1",
            name="City Commissioner"
        ),"""

if "COMM-001" not in content:
    content = content.replace(old_users, new_users)

with open("api.py", "w") as f:
    f.write(content)
print("Updated officer and user seeders for escalation levels!")

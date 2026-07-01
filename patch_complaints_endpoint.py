import re

with open("api.py", "r") as f:
    content = f.read()

old_logic = """    if officer_id:
        query = query.filter(Complaint.assigned_officer_id == officer_id)
    admissible_comps = query.all()"""

new_logic = """    if officer_id:
        officer = db.query(Officer).filter(Officer.officer_id == officer_id).first()
        if officer:
            if officer.escalation_level <= 1:
                query = query.filter(Complaint.assigned_officer_id == officer_id)
            elif officer.escalation_level > 1 and officer.role != 'commissioner':
                query = query.filter(Complaint.category == officer.department, Complaint.escalation_level == officer.escalation_level)
            elif officer.role == 'commissioner':
                query = query.filter(Complaint.escalation_level >= 4)
        else:
            query = query.filter(Complaint.assigned_officer_id == officer_id)
    admissible_comps = query.all()"""

if "if officer.escalation_level <=" not in content:
    content = content.replace(old_logic, new_logic)
    with open("api.py", "w") as f:
        f.write(content)
    print("Updated get_complaints logic!")

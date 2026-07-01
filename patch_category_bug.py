with open("api.py", "r") as f:
    content = f.read()

old_query = "query = query.filter(Complaint.category == officer.department, Complaint.escalation_level == officer.escalation_level)"
new_query = "query = query.filter(Complaint.department == officer.department, Complaint.escalation_level == officer.escalation_level)"

if old_query in content:
    content = content.replace(old_query, new_query)
    with open("api.py", "w") as f:
        f.write(content)
        print("Patched category bug")
else:
    print("Not found or already patched")

import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Update admin_dashboard signature
content = content.replace("def admin_dashboard():", "def admin_dashboard(active_tab=\"Command Center (KPIs)\"):")

# 2. Remove tabs = st.tabs([...])
# Instead of replacing the whole block, I will just comment it out.
tabs_block = """    tabs = st.tabs([
        "Command Center (KPIs)",
        "System-Wide Queue",
        "Escalation & SLA Queue",
        "Audit Trail Viewer",
        "Officer Management",
        "Department Policies",
        "Hotspot Intelligence",
        "Trust & Feedback Analytics",
        "Officer Performance",
        "Department Health",
        "Complaint Analytics"
    ])"""
content = content.replace(tabs_block, "    # Removed tabs, using active_tab from sidebar")

# 3. Replace with tabs[0]: etc. with if active_tab == "...":
tab_replacements = {
    0: "Command Center (KPIs)",
    1: "System-Wide Queue",
    2: "Escalation & SLA Queue",
    3: "Audit Trail Viewer",
    4: "Officer Management",
    5: "Department Policies",
    6: "Hotspot Intelligence",
    7: "Trust & Feedback Analytics",
    8: "Officer Performance",
    9: "Department Health",
    10: "Complaint Analytics"
}
for i, name in tab_replacements.items():
    content = content.replace(f"    with tabs[{i}]:", f"    if active_tab == \"{name}\":")

with open("app.py", "w") as f:
    f.write(content)


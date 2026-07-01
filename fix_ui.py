import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Update officer_dashboard
old_officer = """def officer_dashboard():
    \"\"\"Officer dashboard with lifecycle tracking and performance panel at top\"\"\"
    render_government_banner()"""
new_officer = """def officer_dashboard():
    \"\"\"Officer dashboard with lifecycle tracking and performance panel at top\"\"\"
    render_government_banner()
    render_notifications_bell(st.session_state.user['officer_id'])"""
if old_officer in content:
    content = content.replace(old_officer, new_officer)
    print("Patched officer_dashboard")

# 2. Update admin_dashboard
old_admin = """def admin_dashboard(active_tab="Command Center (KPIs)"):
    render_government_banner()"""
new_admin = """def admin_dashboard(active_tab="Command Center (KPIs)"):
    render_government_banner()
    render_notifications_bell("admin")"""
if old_admin in content:
    content = content.replace(old_admin, new_admin)
    print("Patched admin_dashboard")

# 3. Add escalation_level to Add Officer form
old_add_officer = """            with col2:
                new_zone = st.text_input("Zone")
                new_ward = st.text_input("Ward")
                new_desig = st.text_input("Designation")
            submit_officer = st.form_submit_button("Add Officer")
            
            if submit_officer:
                if not new_name or not new_email or not new_password or not new_dept:
                    st.error("Please fill in required fields (Name, Email, Password, Department).")
                else:
                    payload = {
                        "name": new_name,
                        "department": new_dept,
                        "zone": new_zone,
                        "ward": new_ward,
                        "designation": new_desig,
                        "email": new_email,
                        "password": new_password
                    }"""

new_add_officer = """            with col2:
                new_zone = st.text_input("Zone")
                new_ward = st.text_input("Ward")
                new_desig = st.text_input("Designation")
                new_escalation = st.selectbox("Escalation Level", options=[0, 1, 2, 3], format_func=lambda x: {0: "L1 - Junior", 1: "L2 - Senior", 2: "L3 - Dept Head", 3: "L4 - Ministry"}[x])
            submit_officer = st.form_submit_button("Add Officer")
            
            if submit_officer:
                if not new_name or not new_email or not new_password or not new_dept:
                    st.error("Please fill in required fields (Name, Email, Password, Department).")
                else:
                    payload = {
                        "name": new_name,
                        "department": new_dept,
                        "zone": new_zone,
                        "ward": new_ward,
                        "designation": new_desig,
                        "email": new_email,
                        "password": new_password,
                        "escalation_level": new_escalation
                    }"""
if old_add_officer in content:
    content = content.replace(old_add_officer, new_add_officer)
    print("Patched Add Officer form")

with open("app.py", "w") as f:
    f.write(content)


import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Add render_commissioner_dashboard before admin_dashboard
comm_code = """def render_commissioner_dashboard():
    st.header("🏢 Commissioner Dashboard")
    st.markdown("Monitor critical, disaster, and heavily escalated complaints across all departments.")
    
    col1, col2, col3 = st.columns(3)
    
    try:
        r = requests.get(f"{API_URL}/complaints?officer_id={st.session_state.user.get('officer_id')}")
        if r.status_code == 200:
            complaints = r.json()
            
            critical = [c for c in complaints if c.get('priority_score', 0) > 0.85]
            unresolved = [c for c in complaints if c.get('status') not in ['Resolved', 'Closed', 'Rejected']]
            
            col1.metric("Total L4 Escalations", len(complaints))
            col2.metric("Critical / High Impact", len(critical))
            col3.metric("Unresolved", len(unresolved))
            
            st.subheader("Actionable Escalations")
            for c in unresolved:
                with st.expander(f"{c['id']} - {c['category']} (Priority: {c.get('final_priority_score', 0)})"):
                    st.write(f"**Description:** {c['complaint_text']}")
                    st.write(f"**Status:** {c['status']}")
                    st.write(f"**Escalation Level:** {c.get('escalation_level', 4)}")
                    
                    if st.button("Close / Mark Resolved", key=f"comm_close_{c['id']}"):
                        requests.post(f"{API_URL}/complaints/{c['id']}/close", json={"admin_id": "COMM_1", "notes": "Commissioner resolved this critical issue."})
                        st.success("Complaint resolved successfully.")
                        st.rerun()
                    
                    if st.button("View Escalation History", key=f"comm_hist_{c['id']}"):
                        hr = requests.get(f"{API_URL}/complaints/{c['id']}/escalation-history")
                        if hr.status_code == 200:
                            st.json(hr.json())
        else:
            st.error("Failed to load commissioner data.")
    except Exception as e:
        st.error(f"Error: {e}")

"""
if "def render_commissioner_dashboard" not in content:
    content = content.replace("def admin_dashboard(", comm_code + "\ndef admin_dashboard(")

# 2. Fix routing
old_routing = """    elif role == 'admin':
        if st.session_state.get('admin_view') == "profile":
            officer_admin_profile_page(role)
        else:
            if admin_page == "Submit Grievance (Test)":
                citizen_portal()
            else:
                admin_dashboard(admin_page)
    
    else:"""

new_routing = """    elif role == 'commissioner':
        if st.session_state.get('commissioner_view') == "profile":
            officer_admin_profile_page(role)
        else:
            render_commissioner_dashboard()

    elif role == 'admin':
        if st.session_state.get('admin_view') == "profile":
            officer_admin_profile_page(role)
        else:
            if admin_page == "Submit Grievance (Test)":
                citizen_portal()
            else:
                admin_dashboard(admin_page)
    
    else:"""
if "elif role == 'commissioner':" not in content:
    content = content.replace(old_routing, new_routing)

with open("app.py", "w") as f:
    f.write(content)

print("App routing and commissioner dashboard fixed!")

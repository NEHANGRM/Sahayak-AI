import re

with open("app.py", "r") as f:
    content = f.read()

# Admin Radio Options
old_radio = """                    "Escalation & SLA Queue",
                    "Audit Trail Viewer","""
new_radio = """                    "Escalation & SLA Queue",
                    "Audit Trail Viewer",
                    "SLA Configurations",
                    "Escalation Configurations","""
if "SLA Configurations" not in content:
    content = content.replace(old_radio, new_radio)

# Admin logic handling
admin_logic = """
    elif page == "SLA Configurations":
        st.subheader("⏱️ SLA Configurations")
        st.write("Configure Service Level Agreements (SLAs) for different departments.")
        try:
            r = requests.get(f"{API_URL}/sla-configurations")
            if r.status_code == 200:
                configs = r.json()
                for c in configs:
                    with st.expander(f"{c['department']}"):
                        cols = st.columns(2)
                        res_hrs = cols[0].number_input(f"Resolve SLA (Hours)", value=c['resolve_sla_hours'], key=f"res_{c['department']}")
                        acc_hrs = cols[1].number_input(f"Accept SLA (Hours)", value=c['accept_sla_hours'], key=f"acc_{c['department']}")
                        if st.button("Save", key=f"save_sla_{c['department']}"):
                            requests.put(f"{API_URL}/sla-configurations/{c['department']}", json={"resolve_sla_hours": res_hrs, "accept_sla_hours": acc_hrs})
                            st.success("Saved!")
        except Exception as e:
            st.error(f"Error loading SLAs: {e}")
            
    elif page == "Escalation Configurations":
        st.subheader("📈 Escalation Configurations")
        st.write("Configure rules for automatic multi-level escalation.")
        try:
            r = requests.get(f"{API_URL}/escalation-configurations")
            if r.status_code == 200:
                configs = r.json()
                for c in configs:
                    with st.expander(f"Level {c['level']} - {c['description']}"):
                        cols = st.columns(2)
                        p_thresh = cols[0].number_input("Priority Threshold (0.0 - 1.0)", value=c['priority_threshold'], step=0.05, key=f"p_{c['level']}")
                        u_thresh = cols[1].number_input("Unresolved Hours Threshold", value=c['unresolved_hours_threshold'], key=f"u_{c['level']}")
                        if st.button("Save", key=f"save_esc_{c['level']}"):
                            requests.put(f"{API_URL}/escalation-configurations/{c['level']}", json={"priority_threshold": p_thresh, "unresolved_hours_threshold": u_thresh})
                            st.success("Saved!")
        except Exception as e:
            st.error(f"Error loading Escalation Configs: {e}")
"""

# Insert admin logic inside render_admin_dashboard
if "elif page == \"SLA Configurations\":" not in content:
    content = content.replace("elif page == \"Audit Trail Viewer\":", admin_logic + "\n    elif page == \"Audit Trail Viewer\":")

with open("app.py", "w") as f:
    f.write(content)
print("Added Admin SLA/Escalation tabs!")

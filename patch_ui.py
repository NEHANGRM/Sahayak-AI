import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Add render_notifications method
new_method = """def get_notifications(user_id):
    try:
        r = requests.get(f"{API_URL}/notifications/{user_id}")
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def mark_notification_read(notif_id):
    try:
        requests.post(f"{API_URL}/notifications/{notif_id}/read")
    except Exception:
        pass

def render_notifications_bell(user_id):
    notifs = get_notifications(user_id)
    unread = [n for n in notifs if not n.get("is_read")]
    
    col1, col2 = st.columns([10, 1])
    with col2:
        if hasattr(st, "popover"):
            with st.popover(f"🔔 ({len(unread)})"):
                st.markdown("### Notifications")
                if not notifs:
                    st.write("No notifications.")
                else:
                    for n in notifs:
                        icon = "🔴" if not n.get("is_read") else "⚪"
                        st.markdown(f"{icon} **{n.get('timestamp')}**\\n{n.get('message')}")
                        if not n.get("is_read"):
                            if st.button("Mark Read", key=f"read_{n.get('id')}"):
                                mark_notification_read(n.get("id"))
                                st.rerun()
                        st.markdown("---")
        else:
            # Fallback for older Streamlit
            st.button(f"🔔 ({len(unread)})")

def render_government_banner():"""

content = content.replace("def render_government_banner():", new_method)

# 2. Add render_notifications_bell to officer_dashboard
old_officer = """def officer_dashboard():
    render_government_banner()"""

new_officer = """def officer_dashboard():
    render_government_banner()
    render_notifications_bell(st.session_state.user['officer_id'])"""

content = content.replace(old_officer, new_officer)

# 3. Add render_notifications_bell to admin_dashboard
old_admin = """def admin_dashboard(active_tab="Command Center (KPIs)"):
    render_government_banner()"""

new_admin = """def admin_dashboard(active_tab="Command Center (KPIs)"):
    render_government_banner()
    render_notifications_bell("admin")"""

content = content.replace(old_admin, new_admin)

# 4. Add escalation_level input to Add Officer form
old_add_officer = """        add_designation = st.text_input("Designation", value="Junior Inspector")
        add_email = st.text_input("Email")
        add_pic = st.text_input("Profile Pic URL (Optional)")"""

new_add_officer = """        add_designation = st.text_input("Designation", value="Junior Inspector")
        add_email = st.text_input("Email")
        add_pic = st.text_input("Profile Pic URL (Optional)")
        add_escalation_level = st.selectbox("Escalation Level", options=[0, 1, 2, 3], format_func=lambda x: {0: "L1 - Junior", 1: "L2 - Senior", 2: "L3 - Dept Head", 3: "L4 - Ministry"}[x])"""

content = content.replace(old_add_officer, new_add_officer)

old_add_officer_payload = """                payload = {
                    "name": add_name,
                    "department": add_dept,
                    "zone": add_zone,
                    "ward": add_ward,
                    "designation": add_designation,
                    "email": add_email,
                    "profile_pic": add_pic if add_pic else None
                }"""

new_add_officer_payload = """                payload = {
                    "name": add_name,
                    "department": add_dept,
                    "zone": add_zone,
                    "ward": add_ward,
                    "designation": add_designation,
                    "email": add_email,
                    "profile_pic": add_pic if add_pic else None,
                    "escalation_level": add_escalation_level
                }"""

content = content.replace(old_add_officer_payload, new_add_officer_payload)

with open("app.py", "w") as f:
    f.write(content)


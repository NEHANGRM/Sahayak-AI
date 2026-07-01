import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Notification Center
notif_code = """
def render_notification_center():
    user = st.session_state.user
    user_id = user.get("user_id") if user.get("role") == "admin" else user.get("officer_id")
    if not user_id:
        return
        
    try:
        r = requests.get(f"{API_URL}/notifications/{user_id}")
        if r.status_code == 200:
            notifs = r.json()
            unread = sum(1 for n in notifs if not n['is_read'])
            
            with st.sidebar.expander(f"🔔 Notifications ({unread})", expanded=unread > 0):
                if not notifs:
                    st.info("No notifications.")
                for n in notifs:
                    color = "red" if n['type'] == 'error' else "orange" if n['type'] == 'warning' else "blue"
                    st.markdown(f"<div style='border-left: 3px solid {color}; padding-left: 8px; margin-bottom: 8px;'>", unsafe_allow_html=True)
                    st.write(f"**{n['timestamp']}**")
                    st.write(n['message'])
                    if n.get('complaint_id'):
                        st.caption(f"Complaint: {n['complaint_id']} | Priority: {n.get('priority', 'N/A')}")
                    if not n['is_read']:
                        if st.button("Mark Read", key=f"read_{n['id']}", help="Mark this notification as read"):
                            requests.post(f"{API_URL}/notifications/{n['id']}/read")
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.sidebar.error("Failed to load notifications.")

"""

if "def render_notification_center" not in content:
    content = content.replace("def render_sidebar_header():", notif_code + "\ndef render_sidebar_header():")
    
# Call render_notification_center() in sidebar
if "render_notification_center()" not in content:
    content = content.replace("render_sidebar_header()", "render_sidebar_header()\n        render_notification_center()")

# 2. Add Commissioner Dashboard
comm_code = """
def render_commissioner_dashboard():
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
    content = content.replace("def render_admin_dashboard():", comm_code + "\ndef render_admin_dashboard():")

# Route commissioner to their dashboard
old_route = """        if role == 'admin':
            if st.session_state.get('admin_view') == 'profile':
                render_profile_card()
            else:
                render_admin_dashboard(admin_page)
        elif role == 'officer':"""

new_route = """        if role == 'admin':
            if st.session_state.get('admin_view') == 'profile':
                render_profile_card()
            else:
                render_admin_dashboard(admin_page)
        elif role == 'commissioner':
            if st.session_state.get('commissioner_view') == 'profile':
                render_profile_card()
            else:
                render_commissioner_dashboard()
        elif role == 'officer':"""

if "elif role == 'commissioner':" not in content:
    content = content.replace(old_route, new_route)
    
# Add Commissioner options to sidebar role logic
old_sidebar = """        if role == 'admin' and st.session_state.get('admin_view') != 'profile':
            admin_page = st.sidebar.radio("""
            
new_sidebar = """        if role == 'commissioner' and st.session_state.get('commissioner_view') != 'profile':
            st.sidebar.markdown("**Role:** City Commissioner")
        elif role == 'admin' and st.session_state.get('admin_view') != 'profile':
            admin_page = st.sidebar.radio("""
            
if "role == 'commissioner'" not in content:
    content = content.replace(old_sidebar, new_sidebar)

with open("app.py", "w") as f:
    f.write(content)
print("Added Commissioner dashboard and Notification Center!")

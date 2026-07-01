import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Update render_complaint_queue signature
content = content.replace(
    "def render_complaint_queue(complaints, resolved_complaints, rejected_complaints, show_actions=True, officer_id_for_override=None, key_prefix=\"\", is_admin=False):",
    "def render_complaint_queue(complaints, resolved_complaints, rejected_complaints, show_actions=True, officer_id_for_override=None, key_prefix=\"\", is_admin=False, active_tab=None):"
)

# 2. Modify render_complaint_queue logic
queue_logic_old = """    st.markdown("---")
    tabs = st.tabs(["New Assignments", "In Progress", "Escalated", "Resolved/Closed", "Restricted"])
    
    # New Assignments
    with tabs[0]:
        if not status_groups["New Assignments"]: st.info("No new assignments.")
        else:
            for idx, c in enumerate(status_groups["New Assignments"], 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # In Progress
    with tabs[1]:
        if not status_groups["In Progress"]: st.info("No complaints currently in progress.")
        else:
            for idx, c in enumerate(status_groups["In Progress"], 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # Escalated
    with tabs[2]:
        if not status_groups["Escalated"]: st.info("No escalated complaints.")
        else:
            for idx, c in enumerate(status_groups["Escalated"], 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # Resolved
    with tabs[3]:
        if not resolved_complaints: st.info("No resolved complaints.")
        else:
            for idx, c in enumerate(resolved_complaints, 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # Restricted
    with tabs[4]:
        if not rejected_complaints: st.info("No restricted complaints.")
        else:
            for idx, c in enumerate(rejected_complaints, 1):
                with st.expander(f"Locked Ref: {c['id']} | Reason: {c.get('raw_predicted_category', 'Unknown')}", expanded=False):
                    st.warning(c['complaint_text'])
                    st.markdown(f"**Policy Violation Reason:** `{c.get('rejection_reason', 'N/A')}`")"""

queue_logic_new = """    st.markdown("---")
    
    def render_section(name):
        if name == "New Assignments":
            if not status_groups["New Assignments"]: st.info("No new assignments.")
            else:
                for idx, c in enumerate(status_groups["New Assignments"], 1):
                    render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
        elif name == "In Progress":
            if not status_groups["In Progress"]: st.info("No complaints currently in progress.")
            else:
                for idx, c in enumerate(status_groups["In Progress"], 1):
                    render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
        elif name == "Escalated":
            if not status_groups["Escalated"]: st.info("No escalated complaints.")
            else:
                for idx, c in enumerate(status_groups["Escalated"], 1):
                    render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
        elif name == "Resolved/Closed":
            if not resolved_complaints: st.info("No resolved complaints.")
            else:
                for idx, c in enumerate(resolved_complaints, 1):
                    render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
        elif name == "Restricted":
            if not rejected_complaints: st.info("No restricted complaints.")
            else:
                for idx, c in enumerate(rejected_complaints, 1):
                    with st.expander(f"Locked Ref: {c['id']} | Reason: {c.get('raw_predicted_category', 'Unknown')}", expanded=False):
                        st.warning(c['complaint_text'])
                        st.markdown(f"**Policy Violation Reason:** `{c.get('rejection_reason', 'N/A')}`")

    if active_tab:
        render_section(active_tab)
    else:
        tabs = st.tabs(["New Assignments", "In Progress", "Escalated", "Resolved/Closed", "Restricted"])
        for i, t_name in enumerate(["New Assignments", "In Progress", "Escalated", "Resolved/Closed", "Restricted"]):
            with tabs[i]:
                render_section(t_name)"""
content = content.replace(queue_logic_old, queue_logic_new)

# 3. Modify officer_dashboard signature and call
content = content.replace("def officer_dashboard():", "def officer_dashboard(active_tab=\"New Assignments\"):")
content = content.replace(
"""    render_complaint_queue(
        complaints=admissible_complaints,
        resolved_complaints=res,
        rejected_complaints=rej,
        show_actions=True,
        officer_id_for_override=officer_id,
        key_prefix="officer",
        is_admin=False
    )""",
"""    render_complaint_queue(
        complaints=admissible_complaints,
        resolved_complaints=res,
        rejected_complaints=rej,
        show_actions=True,
        officer_id_for_override=officer_id,
        key_prefix="officer",
        is_admin=False,
        active_tab=active_tab
    )"""
)

# 4. Modify main() for routing
content = content.replace(
"""        if role == 'officer':
            user = st.session_state.user
            officer_id = user.get('officer_id', '')
            perf = get_officer_stats(officer_id)
            if perf:
                st.sidebar.markdown("### My Performance")
                st.sidebar.metric("Resolution Rate", f"{perf.get('resolution_rate', 0)}%")
                st.sidebar.metric("SLA Compliance", f"{perf.get('sla_compliance_rate', 0)}%")
                st.sidebar.metric("SLA Breaches", perf.get('sla_breached', 0))
                st.sidebar.metric("Avg Resolution (hrs)", perf.get('avg_resolution_hours', 0))
                st.sidebar.metric("Total Assigned", perf.get('total_assigned', 0))
                st.sidebar.metric("Total Resolved", perf.get('total_resolved', 0))
                st.sidebar.markdown("---")""",
"""        if role == 'officer':
            user = st.session_state.user
            officer_id = user.get('officer_id', '')
            perf = get_officer_stats(officer_id)
            if perf:
                st.sidebar.markdown("### My Performance")
                st.sidebar.metric("Resolution Rate", f"{perf.get('resolution_rate', 0)}%")
                st.sidebar.metric("SLA Compliance", f"{perf.get('sla_compliance_rate', 0)}%")
                st.sidebar.metric("SLA Breaches", perf.get('sla_breached', 0))
                st.sidebar.metric("Avg Resolution (hrs)", perf.get('avg_resolution_hours', 0))
                st.sidebar.metric("Total Assigned", perf.get('total_assigned', 0))
                st.sidebar.metric("Total Resolved", perf.get('total_resolved', 0))
                st.sidebar.markdown("---")
            if st.session_state.get('officer_view') != 'profile':
                officer_page = st.sidebar.radio(
                    "Officer Navigation:",
                    ["New Assignments", "In Progress", "Escalated", "Resolved/Closed", "Restricted"],
                    label_visibility="collapsed"
                )"""
)

content = content.replace("officer_dashboard()", "officer_dashboard(officer_page)")

with open("app.py", "w") as f:
    f.write(content)


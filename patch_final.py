import re
import textwrap

with open("app.py", "r") as f:
    content = f.read()

# 1. Dedent HTML strings that are passed to st.markdown
# I will use a regex to wrap the variables in textwrap.dedent before passing to st.markdown
import_stmt = "import textwrap\n"
if "import textwrap" not in content:
    content = content.replace("import streamlit as st", "import streamlit as st\nimport textwrap")

for html_var in ["card_html", "trust_bar_html", "pri_html", "st_html", "cat_html", "dept_html"]:
    content = content.replace(
        f"st.markdown({html_var}, unsafe_allow_html=True)",
        f"st.markdown(textwrap.dedent({html_var}), unsafe_allow_html=True)"
    )

# 2. Revert render_complaint_queue to use st.tabs instead of active_tab
old_queue_def = "def render_complaint_queue(complaints, resolved_complaints, rejected_complaints, show_actions=True, officer_id_for_override=None, key_prefix=\"\", is_admin=False, active_tab=None):"
new_queue_def = "def render_complaint_queue(complaints, resolved_complaints, rejected_complaints, show_actions=True, officer_id_for_override=None, key_prefix=\"\", is_admin=False):"
content = content.replace(old_queue_def, new_queue_def)

queue_logic_old = """    st.markdown("---")
    
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

queue_logic_new = """    st.markdown("---")
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
content = content.replace(queue_logic_old, queue_logic_new)

# 3. Modify officer_dashboard signature and call
content = content.replace("def officer_dashboard(active_tab=\"New Assignments\"):", "def officer_dashboard():")
content = content.replace(
"""    render_complaint_queue(
        complaints=admissible_complaints,
        resolved_complaints=res,
        rejected_complaints=rej,
        show_actions=True,
        officer_id_for_override=officer_id,
        key_prefix="officer",
        is_admin=False,
        active_tab=active_tab
    )""",
"""    render_complaint_queue(
        complaints=admissible_complaints,
        resolved_complaints=res,
        rejected_complaints=rej,
        show_actions=True,
        officer_id_for_override=officer_id,
        key_prefix="officer",
        is_admin=False
    )"""
)

# 4. Modify main() to remove officer radio buttons and correct routing
content = content.replace(
"""            if st.session_state.get('officer_view') != 'profile':
                officer_page = st.sidebar.radio(
                    "Officer Navigation:",
                    ["New Assignments", "In Progress", "Escalated", "Resolved/Closed", "Restricted"],
                    label_visibility="collapsed"
                )""",
""
)
content = content.replace("officer_dashboard(officer_page)", "officer_dashboard()")

with open("app.py", "w") as f:
    f.write(content)


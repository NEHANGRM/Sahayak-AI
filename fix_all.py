import re
import textwrap

with open("app.py", "r") as f:
    content = f.read()

# 1. Fix render_complaint_queue
# It currently has:
#    if active_tab == "Command Center (KPIs)":
#        if not status_groups["New Assignments"]: st.info("No new assignments.")
# ...
# I will use regex to find the start of render_complaint_queue and rewrite the tabs section.
queue_start_idx = content.find('def render_complaint_queue')
sidebar_header_idx = content.find('def render_sidebar_header')

if queue_start_idx != -1 and sidebar_header_idx != -1:
    queue_func = content[queue_start_idx:sidebar_header_idx]
    
    # We want to replace the broken section inside queue_func.
    # The broken section starts after status_groups definition.
    status_groups_end = queue_func.find('    }') + 5
    broken_logic = queue_func[status_groups_end:]
    
    fixed_logic = """
    st.markdown("---")
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
                    st.markdown(f"**Policy Violation Reason:** `{c.get('rejection_reason', 'N/A')}`")

"""
    new_queue_func = queue_func[:status_groups_end] + fixed_logic
    content = content.replace(queue_func, new_queue_func)


# 2. Fix the HTML dedent for Hotspots & Analytics
# My previous attempt might have failed because the `textwrap.dedent` didn't match.
# Let's fix the f-strings directly by replacing them with dedented versions.

# First, ensure import textwrap is there
if "import textwrap" not in content:
    content = content.replace("import streamlit as st", "import streamlit as st\nimport textwrap")

# Actually, the best way to fix the HTML strings is to literally dedent them in the code.
# But it's easier to dynamically replace the st.markdown calls using regex.
import re
content = re.sub(r'st\.markdown\(\s*(card_html|trust_bar_html|pri_html|st_html|cat_html|dept_html)\s*,\s*unsafe_allow_html=True\)', 
                 r'st.markdown(textwrap.dedent(\1), unsafe_allow_html=True)', 
                 content)

# 3. "Remove the Command Centre(KPIs) from the navigation bar and make sure it appears in the dashboard normally"
# This means the user wants "Command Center (KPIs)" to be displayed on the main "Dashboard" page, not as a separate navigation item.
# So "Dashboard" should show Command Center, and "Command Center (KPIs)" should be removed from the sidebar.
# Let's modify the admin sidebar navigation list:
content = content.replace('"Command Center (KPIs)",\n', '')
# And in admin_dashboard, both "Dashboard" and "Command Center (KPIs)" should show it.
# Wait, currently it's: `if active_tab == "Command Center (KPIs)":`
# Let's change it to `if active_tab in ["Dashboard", "Command Center (KPIs)"]:`
content = content.replace('if active_tab == "Command Center (KPIs)":', 'if active_tab in ["Dashboard", "Command Center (KPIs)"]:')


with open("app.py", "w") as f:
    f.write(content)

print("Fixes applied successfully!")

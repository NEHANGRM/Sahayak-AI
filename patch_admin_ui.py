import re

with open("app.py", "r") as f:
    content = f.read()

old_logic = """            # Action states based on status
            if status in ["Assigned", "Reassigned", "Submitted"]:
                with action_cols[0]:
                    if st.button("Accept Assignment", key=f"btn_accept_{complaint['id']}"):
                        success, res = accept_complaint(complaint['id'], officer_id_for_override)
                        if success: st.success("Accepted!"); st.rerun()
                        else: st.error(res)
            
            if status in ["Accepted", "Field Inspection", "Escalated"]:
                with action_cols[0]:
                    if st.button("Start Progress", key=f"btn_prog_{complaint['id']}"):
                        success, res = start_progress(complaint['id'], officer_id_for_override, "Action initiated.")
                        if success: st.success("In Progress!"); st.rerun()
                        else: st.error(res)
            
            if status in ["In Progress"]:
                with action_cols[1]:
                    if st.button("Mark for Field Inspection", key=f"btn_field_{complaint['id']}"):
                        success, res = field_inspection(complaint['id'], officer_id_for_override, "Field team dispatched.")
                        if success: st.success("Field Inspection set!"); st.rerun()
                        else: st.error(res)
                        
                with action_cols[2]:
                    if st.button("Resolve Issue", key=f"btn_res_{complaint['id']}"):
                        st.session_state[f"show_resolve_{complaint['id']}"] = True
                        
            if status in ["Accepted", "In Progress", "Field Inspection"]:
                with action_cols[3]:
                    if st.button("Escalate to Higher Authority", key=f"btn_esc_{complaint['id']}"):
                        st.session_state[f"show_escalate_{complaint['id']}"] = True"""

new_logic = """            # Action states based on status
            if not is_admin:
                if status in ["Assigned", "Reassigned", "Submitted"]:
                    with action_cols[0]:
                        if st.button("Accept Assignment", key=f"btn_accept_{complaint['id']}"):
                            success, res = accept_complaint(complaint['id'], officer_id_for_override)
                            if success: st.success("Accepted!"); st.rerun()
                            else: st.error(res)
                
                if status in ["Accepted", "Field Inspection", "Escalated"]:
                    with action_cols[0]:
                        if st.button("Start Progress", key=f"btn_prog_{complaint['id']}"):
                            success, res = start_progress(complaint['id'], officer_id_for_override, "Action initiated.")
                            if success: st.success("In Progress!"); st.rerun()
                            else: st.error(res)
                
                if status in ["In Progress"]:
                    with action_cols[1]:
                        if st.button("Mark for Field Inspection", key=f"btn_field_{complaint['id']}"):
                            success, res = field_inspection(complaint['id'], officer_id_for_override, "Field team dispatched.")
                            if success: st.success("Field Inspection set!"); st.rerun()
                            else: st.error(res)
                            
                    with action_cols[2]:
                        if st.button("Resolve Issue", key=f"btn_res_{complaint['id']}"):
                            st.session_state[f"show_resolve_{complaint['id']}"] = True
                            
                if status in ["Accepted", "In Progress", "Field Inspection"]:
                    with action_cols[3]:
                        if st.button("Escalate to Higher Authority", key=f"btn_esc_{complaint['id']}"):
                            st.session_state[f"show_escalate_{complaint['id']}"] = True"""

content = content.replace(old_logic, new_logic)

with open("app.py", "w") as f:
    f.write(content)


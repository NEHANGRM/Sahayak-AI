with open("app.py", "r") as f:
    content = f.read()

old_code = """                    off = c.get('assigned_officer_id')
                    if off:
                        st.markdown(f"**Handling Officer:** `{get_officer_display_name(off)}`")
                        
                    if s not in ["Submitted", "Assigned", "Reassigned", "Open", "Rejected"]:"""

new_code = """                    off = c.get('assigned_officer_id')
                    if off:
                        st.markdown(f"**Handling Officer:** `{get_officer_display_name(off)}`")
                    
                    esc_level = c.get('escalation_level', 1)
                    if esc_level > 1:
                        st.markdown(f"🚨 **Escalated to Level {esc_level}** due to priority or SLA breach.")
                        
                    if s not in ["Submitted", "Assigned", "Reassigned", "Open", "Rejected"]:"""

if "🚨 **Escalated to Level" not in content:
    content = content.replace(old_code, new_code)
    with open("app.py", "w") as f:
        f.write(content)
        print("Citizen timeline patched!")
else:
    print("Already patched.")

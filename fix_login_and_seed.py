with open("app.py", "r") as f:
    content = f.read()

# Fix: Allow commissioner to log in through officer portal
old_check = """                            user_role = user_data.get('role')
                            if user_role != target_role:
                                st.session_state.login_error = f"Access denied: You are attempting to log in as a {user_role.capitalize()} on the {role_label} Portal. Please use the appropriate portal.\""""

new_check = """                            user_role = user_data.get('role')
                            # Allow commissioner to log in through officer portal
                            role_match = (user_role == target_role) or (user_role == 'commissioner' and target_role == 'officer')
                            if not role_match:
                                st.session_state.login_error = f"Access denied: You are attempting to log in as a {user_role.capitalize()} on the {role_label} Portal. Please use the appropriate portal.\""""

content = content.replace(old_check, new_check)

with open("app.py", "w") as f:
    f.write(content)
print("Fixed login role matching for commissioner!")

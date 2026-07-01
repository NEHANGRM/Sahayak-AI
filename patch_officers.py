with open("app.py", "r") as f:
    content = f.read()

old_code = """        st.markdown("#### Current Officers")
        officers = get_officers()
        if officers: st.dataframe(pd.DataFrame(officers), use_container_width=True)"""

new_code = """        st.markdown("#### Current Officers by Department")
        officers = get_officers()
        if officers:
            from collections import defaultdict
            dept_officers = defaultdict(list)
            for off in officers:
                dept_officers[off.get('department', 'Unknown')].append(off)
            
            departments = list(dept_officers.keys())
            cols_per_row = 3
            for i in range(0, len(departments), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(departments):
                        dept = departments[i + j]
                        with cols[j]:
                            st.markdown(f"**{dept}**")
                            for off in sorted(dept_officers[dept], key=lambda x: x.get('escalation_level', 1)):
                                level = off.get('escalation_level', 1)
                                if level == 4: badge = "Commissioner"
                                else: badge = f"L{level}"
                                st.markdown(f"- 🔹 **{off.get('name', 'Unknown')}** (`{off.get('officer_id')}`) - *{badge}*")
                            st.markdown("---")"""

if "Current Officers by Department" not in content:
    content = content.replace(old_code, new_code)
    with open("app.py", "w") as f:
        f.write(content)
        print("Officer management UI patched!")
else:
    print("Already patched.")

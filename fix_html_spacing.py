import re

with open("app.py", "r") as f:
    content = f.read()

# I want to change:
# st.markdown(textwrap.dedent(VARIABLE), unsafe_allow_html=True)
# To:
# st.markdown(re.sub(r'^[ \t]+', '', VARIABLE, flags=re.MULTILINE), unsafe_allow_html=True)

# First, ensure import re is there (it is, but let's be sure)
if "import re\n" not in content:
    content = content.replace("import os\n", "import os\nimport re\n")

# Replace all occurrences
for var in ["card_html", "trust_bar_html", "pri_html", "st_html", "cat_html", "dept_html"]:
    old_call = f"st.markdown(textwrap.dedent({var}), unsafe_allow_html=True)"
    new_call = f"st.markdown(re.sub(r'^[ \\t]+', '', {var}, flags=re.MULTILINE), unsafe_allow_html=True)"
    content = content.replace(old_call, new_call)

with open("app.py", "w") as f:
    f.write(content)

print("Done replacing.")

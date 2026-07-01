with open("api.py", "r") as f:
    content = f.read()

old_block = """        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("UPDATE complaints SET submitted_by = 'citizen1' WHERE submitted_by IS NULL"))
        
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text("ALTER TABLE officers ADD COLUMN profile_pic TEXT"))"""

new_block = """        try:
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("UPDATE complaints SET submitted_by = 'citizen1' WHERE submitted_by IS NULL"))
        except Exception:
            pass
            
        try:
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("ALTER TABLE officers ADD COLUMN profile_pic TEXT"))
        except Exception:
            pass"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open("api.py", "w") as f:
        f.write(content)
    print("Patched migrations successfully!")
else:
    print("Could not find the block to patch.")

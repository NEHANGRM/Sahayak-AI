with open("api.py", "r") as f:
    content = f.read()

# Extract the escalation block that's currently misplaced
block_start = "\nfrom datetime import datetime, timedelta\nimport asyncio\n"
block_end_marker = "await asyncio.sleep(60) # run every 60 seconds\n"

# Find the block
start_idx = content.index(block_start)
end_idx = content.index(block_end_marker) + len(block_end_marker)

# The block itself
escalation_block = content[start_idx:end_idx]

# Remove it from its current position
content = content[:start_idx] + "\n" + content[end_idx:]

# Now insert it right after get_db
insert_marker = "def get_db():\n    db = SessionLocal()\n    try:\n        yield db\n    finally:\n        db.close()\n"
insert_idx = content.index(insert_marker) + len(insert_marker)
content = content[:insert_idx] + "\n" + escalation_block + "\n" + content[insert_idx:]

with open("api.py", "w") as f:
    f.write(content)
print("Moved escalation block after get_db!")

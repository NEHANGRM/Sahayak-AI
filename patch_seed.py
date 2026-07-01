with open("api.py", "r") as f:
    content = f.read()

old_seed = """    "timestamp": "2026-06-25 09:00:00","""
if old_seed in content:
    # Just replace it with dynamic time for the seeded complaints
    import re
    # The timestamps in seed_database look like "2026-06-25 09:00:00"
    # I'll just change the hardcoded strings to yesterday.
    content = content.replace("2026-06-25", "2026-06-28")
    with open("api.py", "w") as f:
        f.write(content)
        print("Patched seed_database timestamps")
else:
    print("Not found or already patched")

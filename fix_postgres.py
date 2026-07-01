with open('api.py', 'r') as f:
    text = f.read()

target = """try:
    from sqlalchemy import text
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(\"\"\"CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id VARCHAR NOT NULL,
                timestamp VARCHAR NOT NULL,
                action VARCHAR NOT NULL,
                from_value VARCHAR,
                to_value VARCHAR,
                performed_by VARCHAR NOT NULL,
                performer_role VARCHAR NOT NULL,
                notes TEXT
            )\"\"\"))
except Exception:
    pass"""

text = text.replace(target, "")

with open('api.py', 'w') as f:
    f.write(text)


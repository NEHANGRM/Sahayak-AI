from sqlalchemy import create_engine
engine = create_engine("sqlite:///./sahayak.db")
with engine.connect() as con:
    try:
        con.execute("ALTER TABLE officers ADD COLUMN escalation_level INTEGER DEFAULT 0")
        print("Added escalation_level")
    except Exception as e:
        print("escalation_level exists?", e)

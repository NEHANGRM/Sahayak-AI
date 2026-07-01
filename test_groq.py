import os
from dotenv import load_dotenv
load_dotenv()
from utils import get_llm_client

client = get_llm_client()
print(type(client))
try:
    resp, action = client.generate_suggestions("Pothole on main road causing accidents", "Roads")
    print(action)
except Exception as e:
    print("Error:", e)

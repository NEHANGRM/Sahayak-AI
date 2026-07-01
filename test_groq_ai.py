import requests
import json
import os

url = "http://localhost:8000/triage"
data = {
    "complaint_text": "There is a massive pothole in front of the primary school on MG Road. It is causing accidents every day and children are at risk.",
    "submitted_by": "citizen1"
}

print("Testing Triage API...")
response = requests.post(url, json=data)

if response.status_code == 200:
    res = response.json()
    print("SUCCESS!")
    print(f"Complaint ID: {res['id']}")
    print(f"Category: {res['category']}")
    print(f"Department: {res['department']}")
    
    sj = res.get('structured_json', {})
    if isinstance(sj, str):
        sj = json.loads(sj)
        
    print(f"\n--- Suggested Response ---")
    print(sj.get('suggested_response'))
    
    print(f"\n--- Suggested Action / Handbook ---")
    print(sj.get('suggested_action') or sj.get('officer_handbook'))
    
    print(f"\n--- LLM Reviewed? ---")
    print(res.get('llm_reviewed'))
    print(res.get('llm_reasoning'))
else:
    print(f"Error {response.status_code}: {response.text}")

import requests
import json
url = "http://localhost:8000/triage"
data = {
    "complaint_text": "There is a massive pothole in front of the primary school on MG Road. It is causing accidents every day and children are at risk.",
    "submitted_by": "citizen1"
}
response = requests.post(url, json=data)
print(response.json()['structured_json'])

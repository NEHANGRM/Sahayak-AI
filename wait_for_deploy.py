import time
import requests

url = "https://sahayak-ai.onrender.com/reseed-danger"
max_retries = 30
for i in range(max_retries):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Successfully reseeded the remote database!")
            print(response.json())
            break
        else:
            print(f"Waiting for deployment... status {response.status_code}")
    except Exception as e:
        print(f"Waiting... error: {e}")
    time.sleep(15)

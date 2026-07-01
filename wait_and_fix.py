import time
import requests

for i in range(20):
    try:
        r = requests.post("https://sahayak-ai-backend.onrender.com/fix-timestamps")
        if r.status_code == 200:
            print("Success! Response:", r.json())
            break
        else:
            print(f"Attempt {i+1}: status {r.status_code}")
    except Exception as e:
        print(f"Attempt {i+1} error: {e}")
    time.sleep(30)
else:
    print("Failed after 20 attempts")

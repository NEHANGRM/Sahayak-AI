import random
import pandas as pd

NUM_COMPLAINTS = 1000

categories = {
    "Hospital Emergency": "High",
    "Women Safety": "High",
    "Corruption Bribe": "High",
    "Traffic Signal Failure": "Medium",
    "Electricity Outage": "Medium",
    "Road Damage": "Medium",
    "Water Supply": "Low",
    "Garbage Disposal": "Low"
}

locations = ["Chennai", "Mumbai", "Delhi", "Bengaluru", "Hyderabad"]

templates = {
    "Hospital Emergency": [
        "Patient not treated in emergency ward at {place}.",
        "Ambulance delayed, urgent help needed in {place}."
    ],
    "Women Safety": [
        "Harassment incidents reported near {place}. Immediate action needed.",
        "Unsafe area at night in {place}, police patrolling required."
    ],
    "Corruption Bribe": [
        "Officer demanded bribe for service approval in {place}.",
        "Illegal payments forced for basic work in {place}."
    ],
    "Traffic Signal Failure": [
        "Traffic signals not working at {place}, risk of accidents.",
        "Broken traffic lights causing congestion in {place}."
    ],
    "Electricity Outage": [
        "Power outage since morning in {place}.",
        "Frequent voltage fluctuation in {place}."
    ],
    "Road Damage": [
        "Huge potholes causing accidents near {place}.",
        "Road repair pending for months in {place}."
    ],
    "Water Supply": [
        "No water supply in {place} for 3 days.",
        "Dirty drinking water coming from taps in {place}."
    ],
    "Garbage Disposal": [
        "Garbage not collected for days in {place}.",
        "Overflowing waste bins causing bad smell in {place}."
    ]
}

data = []

for i in range(NUM_COMPLAINTS):
    cat = random.choice(list(categories.keys()))
    priority = categories[cat]
    loc = random.choice(locations)

    text = random.choice(templates[cat]).format(place=loc)

    data.append({
        "Complaint_ID": f"CMP-{1000+i}",
        "Location": loc,
        "Complaint_Text": text,
        "Category": cat,
        "Priority_Label": priority   # <-- THIS is what AI learns
    })

df = pd.DataFrame(data)
df.to_csv("ai_priority_training_dataset.csv", index=False)

print("✅ Correct dataset generated: AI must predict Priority_Label")
print(df.head())

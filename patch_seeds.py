import re

with open("api.py", "r") as f:
    content = f.read()

new_seeds = """    seeds = [
        # Citizen 2 Complaints (Mapped to 10 departments)
        {"id": "CMP-3001", "complaint_text": "The sewer line on MG Road is completely blocked and overflowing into the street, causing a foul smell and health hazard.", "timestamp": "2026-06-25 10:00:00"},
        {"id": "CMP-3002", "complaint_text": "A massive pothole has developed on the main highway bridge, threatening the structural integrity and causing severe traffic accidents.", "timestamp": "2026-06-25 10:05:00"},
        {"id": "CMP-3003", "complaint_text": "The main transformer in Sector 4 caught fire and exploded. We have been without power for 12 hours.", "timestamp": "2026-06-25 10:10:00"},
        {"id": "CMP-3004", "complaint_text": "There is a severe outbreak of dengue in our neighborhood due to stagnant water and lack of fogging by the authorities.", "timestamp": "2026-06-25 10:15:00"},
        {"id": "CMP-3005", "complaint_text": "A large mob is gathering near the town square and starting to block traffic and vandalize shops. Immediate police intervention is required.", "timestamp": "2026-06-25 10:20:00"},
        {"id": "CMP-3006", "complaint_text": "Garbage hasn't been collected from the market area for over a week. The waste is spilling onto the road.", "timestamp": "2026-06-25 10:25:00"},
        {"id": "CMP-3007", "complaint_text": "The traffic signals at the major intersection are completely dead, resulting in chaotic traffic jams and accidents.", "timestamp": "2026-06-25 10:30:00"},
        {"id": "CMP-3008", "complaint_text": "The roof of the government primary school is leaking heavily during the rains, making the classrooms unusable.", "timestamp": "2026-06-25 10:35:00"},
        {"id": "CMP-3009", "complaint_text": "The local contractor is using substandard materials for the new road construction and demanding bribes from residents.", "timestamp": "2026-06-25 10:40:00"},
        {"id": "CMP-3010", "complaint_text": "The public park's gates are broken and antisocial elements occupy the area at night, making it unsafe for residents.", "timestamp": "2026-06-25 10:45:00"},
        
        # Citizen 1 Complaints (2 Valid, 3 CPGRAMS Rejections)
        {"id": "CMP-3011", "complaint_text": "Water supply has been very muddy for the past two days in our residential complex.", "timestamp": "2026-06-25 11:00:00"},
        {"id": "CMP-3012", "complaint_text": "Streetlights on the 3rd cross street are completely non-functional, leading to safety issues at night.", "timestamp": "2026-06-25 11:05:00"},
        {"id": "CMP-3013", "complaint_text": "I submitted an RTI request last month regarding the funds allocated for the new library, but I haven't received a response. Please provide the RTI details immediately.", "timestamp": "2026-06-25 11:10:00"},
        {"id": "CMP-3014", "complaint_text": "My neighbor and I have an ongoing property dispute case in the High Court. I want the municipality to intervene and grant me the land title while the court case is pending.", "timestamp": "2026-06-25 11:15:00"},
        {"id": "CMP-3015", "complaint_text": "I am a government employee in the revenue department. My promotion has been delayed by two years and my transfer request was denied. Please approve my promotion.", "timestamp": "2026-06-25 11:20:00"}
    ]"""

# Replace the seeds list
content = re.sub(r'    seeds = \[.*?\]', new_seeds, content, flags=re.DOTALL)

# Replace the citizen assign logic
old_cit = 'submitted_by="citizen2" if int(comp_id.split("-")[1]) % 2 == 0 else "citizen1",'
new_cit = 'submitted_by="citizen2" if int(comp_id.split("-")[1]) <= 3010 else "citizen1",'
content = content.replace(old_cit, new_cit)

# Also update the logic that skips seeding if complaints exist
old_skip = 'citizen_exists = db.query(Complaint).filter(Complaint.id > "CMP-2050").count() > 0'
new_skip = 'citizen_exists = db.query(Complaint).filter(Complaint.id > "CMP-3050").count() > 0'
content = content.replace(old_skip, new_skip)

with open("api.py", "w") as f:
    f.write(content)

print("Updated seeds in api.py!")

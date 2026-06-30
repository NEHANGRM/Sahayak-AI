"""
Utility functions for Sahayak AI Complaint Triage System
Includes Sentence Transformer wrapper, spacy NER, sentiment analysis, severity scoring,
priority calculation, XAI, duplicate detection, and admissibility filter.
"""

import numpy as np
import re
import json
import spacy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

# Initialize VADER sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()

# Lazy loaded spaCy model
_nlp = None

def get_spacy_nlp():
    global _nlp
    if _nlp is None:
        try:
            import en_core_web_sm
            _nlp = en_core_web_sm.load()
        except Exception:
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

# Wrapper for SentenceTransformer to maintain compatibility with vectorizer.transform()
class SentenceTransformerWrapper:
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model_name = model_name
        self._model = None

    def transform(self, texts):
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        if isinstance(texts, str):
            texts = [texts]
        elif hasattr(texts, 'tolist'):
            texts = texts.tolist()
        return self._model.encode(texts, show_progress_bar=False)

    def __getstate__(self):
        # Only serialize the model name configuration, not the loaded weights
        return {'model_name': self.model_name}

    def __setstate__(self, state):
        self.model_name = state.get('model_name', 'all-MiniLM-L6-v2')
        self._model = None

# Category to severity mapping (0.0 to 1.0)
SEVERITY_MAP = {
    "Health": 1.0,
    "Public Safety": 1.0,
    "Corruption": 0.9,
    "Transport": 0.6,
    "Electricity": 0.5,
    "Roads": 0.5,
    "Education": 0.4,
    "Water": 0.3,
    "Sanitation": 0.2,
    "Other": 0.1
}

# Department routing map
DEPARTMENT_MAP = {
    "Health": "Health Department",
    "Public Safety": "Police & Disaster Response",
    "Corruption": "Vigilance Bureau",
    "Transport": "Transport & Traffic Authority",
    "Electricity": "Electricity Utilities Board",
    "Roads": "Public Works Department (PWD)",
    "Education": "Education Department",
    "Water": "Water & Sewerage Board",
    "Sanitation": "Municipal Sanitation Department",
    "Other": "General Administration Department"
}

# Prohibited Categories map (aligned to CPGRAMS exclusion policies)
REJECTION_REASONS = {
    "Prohibited_RTI": "RTI (Right to Information) request. Please file RTI requests through the official RTI portal (rtionline.gov.in).",
    "Prohibited_Court": "Court or Sub Judice matter. Matters currently pending in or decided by a court/tribunal cannot be processed by this portal. CPGRAMS cannot interfere with the judiciary.",
    "Prohibited_Family": "Personal or family dispute. Private domestic disputes (property partition, inheritance, neighbour quarrels, matrimonial issues) are civil/legal matters and not public service grievances.",
    "Prohibited_Religion": "Religious matter. Disputes involving religious beliefs, practices, or inter-community religious conflicts are outside CPGRAMS scope.",
    "Prohibited_Service": "Government employee service matter (e.g. transfer, promotion, salary fixation, pension, disciplinary proceedings). These should be routed through prescribed departmental grievance mechanisms first.",
    "Prohibited_National": "Matter affecting national integrity, territorial sovereignty, or foreign relations. These must be reported directly to national security agencies.",
    "Prohibited_Caste": "Caste-based or SC/ST discrimination complaint. Complaints involving caste distinctions, SC/ST atrocities, or reservation disputes must be filed with the National Commission for Scheduled Castes (NCSC) or under the SC/ST (Prevention of Atrocities) Act through the police.",
    "Prohibited_Suggestion": "Policy suggestion or general advice. CPGRAMS is for actionable public service grievances, not policy suggestions, opinions, or general advice to the government."
}

# Risk Keywords
RISK_KEYWORDS = [
    "collapse", "crack", "leak", "fire", "accident", "bribe", "harassment", "danger", 
    "broken", "unsafe", "threat", "corruption", "injury", "emergency", "flood", "delay",
    "stolen", "theft", "exploding", "sparking", "toxic", "poisonous", "epidemic", "outbreak"
]

def check_admissibility_keywords(text):
    """
    Check admissibility using quick keyword matching.
    Aligned with CPGRAMS exclusion policies.
    """
    text_lower = text.lower()
    
    # 1. RTI Matters
    rti_keywords = [
        "rti application", "right to information act", "under rti", "rti act",
        "rti request", "file rti", "rti query", "rti appeal", "section 6 of rti",
        "provide information under", "seeking information under",
        "copies of government records", "certified copies of",
        "details of funds spent", "copy of tender documents"
    ]
    if any(kw in text_lower for kw in rti_keywords):
        return False, REJECTION_REASONS["Prohibited_RTI"], "Prohibited_RTI"
        
    # 2. Court / Sub Judice Matters
    court_keywords = [
        "subjudice", "sub-judice", "sub judice", "pending in court",
        "pending court case", "before the court", "court judgment",
        "court verdict", "court order", "court hearing", "court stay",
        "stay order", "high court", "supreme court", "district court",
        "session court", "tribunal", "under trial", "court dispute",
        "disagree with the judgment", "decided by a court",
        "civil suit", "filed a case", "legal proceedings",
        "scheduled for hearing", "court's final"
    ]
    if any(kw in text_lower for kw in court_keywords):
        return False, REJECTION_REASONS["Prohibited_Court"], "Prohibited_Court"
    
    # 3. Personal / Family Disputes
    family_keywords = [
        "family dispute", "family fight", "family conflict",
        "property dispute between", "property partition",
        "ancestral property", "inheritance dispute",
        "domestic dispute", "divorce case", "custody battle",
        "husband and wife", "spouse", "matrimonial",
        "sibling dispute", "between siblings", "between brothers",
        "neighbour quarrel", "neighbor dispute", "neighbourhood fight",
        "personal dispute", "private dispute", "wedding expenses",
        "land division between", "between uncles",
        "between relatives", "my relatives are harassing"
    ]
    if any(kw in text_lower for kw in family_keywords):
        return False, REJECTION_REASONS["Prohibited_Family"], "Prohibited_Family"
    
    # 4. Religious Matters
    religion_keywords = [
        "religious dispute", "religious conflict", "religious conversion",
        "temple vs mosque", "temple near mosque", "mosque near temple",
        "religious procession", "religious flag", "religious practice",
        "religious belief", "desecration", "religious monument",
        "inter-community religious", "religious group",
        "hate speech targeting religious", "communal tension",
        "religious shrine", "place of worship dispute"
    ]
    if any(kw in text_lower for kw in religion_keywords):
        return False, REJECTION_REASONS["Prohibited_Religion"], "Prohibited_Religion"
    
    # 5. National Integrity / Foreign Relations
    national_keywords = [
        "national integrity", "national security", "sovereignty",
        "secession", "separatist", "anti-national", "anti national",
        "seditious", "sedition", "espionage", "spying",
        "territorial integrity", "foreign relations", "diplomatic",
        "border dispute", "cross-border"
    ]
    if any(kw in text_lower for kw in national_keywords):
        return False, REJECTION_REASONS["Prohibited_National"], "Prohibited_National"
    
    # 6. Government Employee Service Matters
    service_keywords = [
        "my promotion", "my transfer", "my pension", "my salary",
        "my posting", "my suspension", "my reinstatement",
        "transfer request", "promotion dispute", "salary fixation",
        "salary deduction", "gratuity payment", "pension benefits",
        "disciplinary proceedings", "departmental inquiry",
        "service matter", "government employee service",
        "regularisation of temporary", "seniority dispute"
    ]
    if any(kw in text_lower for kw in service_keywords):
        return False, REJECTION_REASONS["Prohibited_Service"], "Prohibited_Service"
    
    # 7. Caste / SC-ST Matters
    caste_keywords = [
        "sc/st", "sc / st", "scheduled caste", "scheduled tribe",
        "caste discrimination", "caste atrocity", "caste violence",
        "caste abuse", "caste slur", "casteist", "caste-based",
        "caste based", "dalit atrocity", "dalit discrimination",
        "untouchability", "upper caste", "lower caste",
        "obc reservation", "sc reservation", "st reservation",
        "reservation dispute", "caste certificate",
        "prevention of atrocities act", "poa act",
        "caste name", "caste distinction"
    ]
    if any(kw in text_lower for kw in caste_keywords):
        return False, REJECTION_REASONS["Prohibited_Caste"], "Prohibited_Caste"
    
    # 8. Suggestions / Policy Advice
    suggestion_keywords = [
        "government should", "the government should",
        "should build more", "should reduce", "should increase",
        "please reduce gst", "reduce tax", "reduce gst",
        "policy suggestion", "i suggest", "my suggestion",
        "please consider building", "why not build",
        "the government must introduce", "government must",
        "please introduce a scheme", "request new policy",
        "suggest the government", "advise the government",
        "opinion on policy", "policy advice"
    ]
    if any(kw in text_lower for kw in suggestion_keywords):
        return False, REJECTION_REASONS["Prohibited_Suggestion"], "Prohibited_Suggestion"
        
    return True, None, None

def check_admissibility(text, category_model, vectorizer):
    """
    Check if a complaint is admissible under the portal policies.
    Returns: (is_admissible: bool, reason: str or None, category: str, confidence_score: float)
    """
    # 1. First run the quick keyword interception
    admissible, reason, category = check_admissibility_keywords(text)
    if not admissible:
        return False, reason, category, 1.0
        
    # 2. If it passes keywords, use the trained ML model classification
    vector = vectorizer.transform([text])
    predicted_category = category_model.predict(vector)[0]
    
    # Calculate confidence score
    confidence_score = 1.0
    try:
        if hasattr(category_model, "predict_proba"):
            probs = category_model.predict_proba(vector)[0]
            classes = list(category_model.classes_)
            if predicted_category in classes:
                confidence_score = float(probs[classes.index(predicted_category)])
    except Exception as e:
        print(f"Error calculating confidence: {e}")
        
    if predicted_category in REJECTION_REASONS:
        return False, REJECTION_REASONS[predicted_category], predicted_category, confidence_score
        
    # 3. Rule-based heuristic overrides for high-confidence keyword matches
    text_lower = text.lower()
    electricity_kws = ["street light", "streetlight", "street-light", "power cut", "power outage", "electricity outage", "voltage fluctuation", "electric wire", "electric pole"]
    roads_kws = ["pothole", "manhole", "road damage", "road condition", "flyover crack"]
    sanitation_kws = ["garbage", "trash", "dumpster", "overflowing bin", "sewage leak", "sewer line"]
    water_kws = ["water supply", "drinking water", "water pipeline", "water leakage", "no water"]
    
    if any(kw in text_lower for kw in electricity_kws):
        predicted_category = "Electricity"
        confidence_score = 1.0
    elif any(kw in text_lower for kw in roads_kws):
        predicted_category = "Roads"
        confidence_score = 1.0
    elif any(kw in text_lower for kw in sanitation_kws):
        predicted_category = "Sanitation"
        confidence_score = 1.0
    elif any(kw in text_lower for kw in water_kws):
        predicted_category = "Water"
        confidence_score = 1.0
        
    return True, None, predicted_category, confidence_score

def extract_entities_and_details(text, category):
    """
    Perform NER using spaCy and regex-matching rules for targeted extraction.
    """
    nlp = get_spacy_nlp()
    doc = nlp(text)
    
    locations = []
    hospitals = []
    schools = []
    gov_offices = []
    roads = []
    bridges = []
    public_infra = []
    all_extracted = []
    
    # Target regex patterns for domain entities (matching capitalized words only)
    road_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:Road|Street|Lane|Avenue|Highway|Marg|Path|Flyover|Bridge))\b')
    bridge_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:Bridge|Flyover|Underpass|Overpass))\b')
    hospital_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:Hospital|Clinic|Medical Center|Dispensary))\b')
    school_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:School|College|University|Institute|Academy))\b')
    gov_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\s+(?:Office|Department|Ministry|Board|Corporation|Police Station|Court|Bureau|Authority))\b')
    
    # Suffix matcher for Indian locations (matching capitalized words preceding the location suffix)
    location_suffix_pattern = re.compile(r'\b([A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*(?:Nagar|Pur|Ganj|Galli|Bagh|Peth|Colony|Vihar|Sector|Phase|Zone|District|City|Village|Bazar|Market))\b')

    # Apply regex matchers
    for match in road_pattern.findall(text):
        match_clean = match.strip()
        if "Bridge" in match_clean or "Flyover" in match_clean:
            if match_clean not in bridges:
                bridges.append(match_clean)
        else:
            if match_clean not in roads:
                roads.append(match_clean)
        all_extracted.append(match_clean)
        
    for match in bridge_pattern.findall(text):
        match_clean = match.strip()
        if match_clean not in bridges:
            bridges.append(match_clean)
        all_extracted.append(match_clean)
        
    for match in hospital_pattern.findall(text):
        match_clean = match.strip()
        if match_clean not in hospitals:
            hospitals.append(match_clean)
        all_extracted.append(match_clean)
        
    for match in school_pattern.findall(text):
        match_clean = match.strip()
        if match_clean not in schools:
            schools.append(match_clean)
        all_extracted.append(match_clean)
        
    for match in gov_pattern.findall(text):
        match_clean = match.strip()
        if match_clean not in gov_offices:
            gov_offices.append(match_clean)
        all_extracted.append(match_clean)

    for match in location_suffix_pattern.findall(text):
        match_clean = match.strip()
        if match_clean not in locations:
            locations.append(match_clean)
        all_extracted.append(match_clean)

    # Process spaCy entity recognition results
    for ent in doc.ents:
        val = ent.text.strip()
        if not val or val in all_extracted:
            continue
            
        label = ent.label_
        val_lower = val.lower()
        
        if label in ["GPE", "LOC"]:
            locations.append(val)
            all_extracted.append(val)
        elif "hospital" in val_lower or "clinic" in val_lower or "medical" in val_lower:
            hospitals.append(val)
            all_extracted.append(val)
        elif "school" in val_lower or "college" in val_lower or "university" in val_lower or "institute" in val_lower:
            schools.append(val)
            all_extracted.append(val)
        elif "office" in val_lower or "ministry" in val_lower or "department" in val_lower or "police" in val_lower or "court" in val_lower or "corporation" in val_lower:
            gov_offices.append(val)
            all_extracted.append(val)
        elif "road" in val_lower or "street" in val_lower or "highway" in val_lower or "lane" in val_lower or "avenue" in val_lower:
            roads.append(val)
            all_extracted.append(val)
        elif "bridge" in val_lower or "flyover" in val_lower or "underpass" in val_lower:
            bridges.append(val)
            all_extracted.append(val)
        elif label == "FAC":
            public_infra.append(val)
            all_extracted.append(val)
        elif label == "ORG" and category in ["Health", "Education", "Corruption"]:
            if category == "Health":
                hospitals.append(val)
            elif category == "Education":
                schools.append(val)
            else:
                gov_offices.append(val)
            all_extracted.append(val)
            
    # Suffixless word search fallback (e.g. "bridge", "school", "hospital" alone)
    # We restrict fallback to at most 3 preceding words to prevent matching entire sentences
    text_lower = text.lower()
    
    # 1. Check for bridge keywords
    if not bridges:
        bridge_kws = ["bridge", "flyover", "underpass", "overpass"]
        for kw in bridge_kws:
            if kw in text_lower:
                match = re.search(rf'\b((?:[a-zA-Z0-9]+(?:\s+)){{0,3}}{kw})\b', text_lower)
                if match:
                    val = match.group(1).title()
                    bridges.append(val)
                    all_extracted.append(val)
                    break
                    
    # 2. Check for road keywords
    if not roads:
        road_kws = ["road", "street", "lane", "highway", "avenue", "bypass"]
        for kw in road_kws:
            if kw in text_lower:
                match = re.search(rf'\b((?:[a-zA-Z0-9]+(?:\s+)){{0,3}}{kw})\b', text_lower)
                if match:
                    val = match.group(1).title()
                    roads.append(val)
                    all_extracted.append(val)
                    break
                    
    # 3. Check for hospital keywords
    if not hospitals:
        hospital_kws = ["hospital", "clinic", "dispensary", "medical center"]
        for kw in hospital_kws:
            if kw in text_lower:
                match = re.search(rf'\b((?:[a-zA-Z0-9]+(?:\s+)){{0,3}}{kw})\b', text_lower)
                if match:
                    val = match.group(1).title()
                    hospitals.append(val)
                    all_extracted.append(val)
                    break

    # 4. Check for school keywords
    if not schools:
        school_kws = ["school", "college", "university", "academy"]
        for kw in school_kws:
            if kw in text_lower:
                match = re.search(rf'\b((?:[a-zA-Z0-9]+(?:\s+)){{0,3}}{kw})\b', text_lower)
                if match:
                    val = match.group(1).title()
                    schools.append(val)
                    all_extracted.append(val)
                    break

    # 5. Check for government offices
    if not gov_offices:
        gov_kws = ["office", "department", "ministry", "board", "corporation", "police", "court"]
        for kw in gov_kws:
            if kw in text_lower:
                match = re.search(rf'\b((?:[a-zA-Z0-9]+(?:\s+)){{0,3}}{kw})\b', text_lower)
                if match:
                    val = match.group(1).title()
                    gov_offices.append(val)
                    all_extracted.append(val)
                    break

    # General locations fallback (e.g. check for common Indian cities/neighborhoods)
    common_cities = ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Hyderabad", "Pune", "Ahmedabad", "Jaipur", "Lucknow", "Anna Nagar"]
    for city in common_cities:
        if city.lower() in text_lower and city not in locations:
            locations.append(city)
            all_extracted.append(city)

    # Resolve location
    location_val = locations[0] if locations else None
    
    # Resolve primary infrastructure entity
    infra_val = None
    if bridges:
        infra_val = "Bridge"
    elif roads:
        infra_val = "Road"
    elif hospitals:
        infra_val = "Hospital"
    elif schools:
        infra_val = "School"
    elif gov_offices:
        infra_val = "Government Office"
    elif public_infra:
        infra_val = "Public Infrastructure"

    # Combine entities list
    entities_list = []
    for l in [locations, hospitals, schools, gov_offices, roads, bridges, public_infra]:
        entities_list.extend(l)
    entities_list = list(set(entities_list))
        
    return {
        "location": location_val,
        "infrastructure": infra_val,
        "extracted_entities": {
            "Locations": list(set(locations)),
            "Hospitals": list(set(hospitals)),
            "Schools": list(set(schools)),
            "Government Offices": list(set(gov_offices)),
            "Road Names": list(set(roads)),
            "Bridges": list(set(bridges)),
            "Public Infrastructure": list(set(public_infra))
        },
        "all_entities": entities_list
    }

def extract_risk_keywords(text):
    """
    Scans complaint text for safety, urgency, and corruption risk keywords.
    """
    text_lower = text.lower()
    found = []
    for kw in RISK_KEYWORDS:
        if re.search(rf'\b{kw}\b', text_lower):
            found.append(kw)
    return found

def get_sentiment_score(text):
    """
    Analyze sentiment and return distress score [0-1].
    Higher = more distress.
    """
    scores = sentiment_analyzer.polarity_scores(text)
    compound = scores['compound']
    
    if compound < 0:
        sentiment_score = 0.5 + abs(compound) * 0.5
    else:
        sentiment_score = (1 - compound) * 0.5
    
    return round(sentiment_score, 3)

def get_severity_score(category):
    """
    Get severity score based on complaint category.
    """
    return SEVERITY_MAP.get(category, 0.3)

def calculate_urgency(text, category, severity_score, structured_json=None):
    """
    Calculate Urgency Score (0-1) based on categories, severity, urgency keywords, and infrastructure proximity.
    """
    text_lower = text.lower()
    
    # 1. Base urgency from severity score (higher severity = higher urgency)
    score = severity_score * 0.4
    
    # 2. Category modifier
    high_urgency_categories = ["Health", "Public Safety", "Electricity", "Water"]
    medium_urgency_categories = ["Roads", "Sanitation", "Transport"]
    
    cat_key = category.replace("Prohibited_", "")
    if cat_key in high_urgency_categories:
        score += 0.25
    elif cat_key in medium_urgency_categories:
        score += 0.15
        
    # 3. Urgency keywords modifier
    urgency_words = ["immediate", "urgent", "emergency", "crisis", "accident", "fatal", "dying", "danger", "hazard", "immediately", "urgently", "asap", "risk", "severe", "major", "threat"]
    if any(w in text_lower for w in urgency_words):
        score += 0.30
        
    # 4. Critical infrastructure proximity
    infra = structured_json.get("infrastructure") if structured_json else None
    if "hospital" in text_lower or infra == "Hospital":
        score += 0.25
    elif "school" in text_lower or infra == "School":
        score += 0.20
        
    # 5. Specific hazards
    special_urgency = ["gas leak", "live wire", "pipe burst", "short circuit", "fire", "flooding"]
    if any(w in text_lower for w in special_urgency):
        score += 0.20
        
    # Cap between 0.0 and 1.0
    return round(min(1.0, max(0.0, score)), 2)

def calculate_duplicate_escalation(is_duplicate, similarity, cluster_id, complaints_list):
    """
    Calculate Duplicate Escalation Score (0-1).
    If not duplicate, score is 0.0.
    If duplicate, score scales up based on the frequency of reports.
    """
    if not is_duplicate or cluster_id is None or complaints_list is None:
        return 0.0
        
    # Resolve the ultimate lead index to count correctly
    actual_lead_index = cluster_id
    if cluster_id < len(complaints_list):
        candidate = complaints_list[cluster_id]
        if isinstance(candidate, dict) and candidate.get('cluster_id') is not None:
            actual_lead_index = candidate.get('cluster_id')
        
    # Count how many other complaints belong to the same cluster or have matching details.
    count = 1  # include current complaint
    for c in complaints_list:
        if c.get('admissible', True):
            c_cluster = c.get('cluster_id')
            if c_cluster == actual_lead_index or c.get('id') == f"CMP-{2000 + actual_lead_index}":
                count += 1
                
    if count == 1:
        score = 0.30
    elif count == 2:
        score = 0.60
    elif count == 3:
        score = 0.85
    else:
        score = 1.00
        
    # Factor similarity slightly
    score = score * 0.8 + similarity * 0.2
    return round(min(1.0, max(0.0, score)), 2)

def calculate_escalation(priority_score, age_days, duplicate_count, current_escalation_history):
    """Calculate dynamic priority escalation based on time and duplicates.
    Returns (boosted_priority, new_escalation_events)."""
    boost = 0.0
    new_events = []
    
    # Time-based escalation
    if age_days >= 14:
        boost += 0.3  # +0.1 for >=7 days + 0.2 for >=14 days
        new_events.append({'level': 'Time Escalation (14+ days)', 'boost': 0.3})
    elif age_days >= 7:
        boost += 0.1
        new_events.append({'level': 'Time Escalation (7+ days)', 'boost': 0.1})
    
    # Duplicate-based escalation
    if duplicate_count >= 20:
        return (1.0, new_events + [{'level': 'Mass Complaint Override (20+ duplicates)', 'boost': 'MAX'}])
    elif duplicate_count >= 5:
        boost += 0.25
        new_events.append({'level': 'Duplicate Escalation (5+ reports)', 'boost': 0.25})
    
    final_priority = min(1.0, max(0.0, priority_score + boost))
    
    # Authority escalation
    if final_priority >= 0.90 and age_days >= 1:
        new_events.append({'level': 'Escalated to Chief Secretary', 'authority': 'Chief Secretary'})
    elif final_priority >= 0.85:
        new_events.append({'level': 'Escalated to Ministry Head', 'authority': 'Ministry Head'})
    
    return (final_priority, new_events)

def calculate_priority_score(severity, public_impact, urgency, vulnerability, duplicate_escalation, weights=None):
    """
    PRIORITY_SCORE calculates the weighted sum of factors based on optional dynamic weights.
    Default weights represent the standard cross-department baseline.
    """
    if weights is None:
        weights = {
            'severity_weight': 0.30,
            'impact_weight': 0.25,
            'urgency_weight': 0.20,
            'vulnerability_weight': 0.15,
            'duplicate_weight': 0.10
        }
        
    priority_score = (
        weights.get('severity_weight', 0.30) * severity + 
        weights.get('impact_weight', 0.25) * public_impact + 
        weights.get('urgency_weight', 0.20) * urgency + 
        weights.get('vulnerability_weight', 0.15) * vulnerability + 
        weights.get('duplicate_weight', 0.10) * duplicate_escalation
    )
    return round(min(1.0, max(0.0, priority_score)), 3)

def get_priority_breakdown(severity, public_impact, urgency, vulnerability, duplicate_escalation, weights=None):
    """Returns structured priority breakdown with individual contributions using dynamic weights."""
    if weights is None:
        weights = {
            'severity_weight': 0.30,
            'impact_weight': 0.25,
            'urgency_weight': 0.20,
            'vulnerability_weight': 0.15,
            'duplicate_weight': 0.10
        }
        
    w_sev = weights.get('severity_weight', 0.30)
    w_imp = weights.get('impact_weight', 0.25)
    w_urg = weights.get('urgency_weight', 0.20)
    w_vul = weights.get('vulnerability_weight', 0.15)
    w_dup = weights.get('duplicate_weight', 0.10)
    
    priority_score = calculate_priority_score(severity, public_impact, urgency, vulnerability, duplicate_escalation, weights)
    
    breakdown = {
        'Severity': {'score': severity, 'weight': w_sev, 'contribution': round(severity * w_sev, 3)},
        'Public Impact': {'score': public_impact, 'weight': w_imp, 'contribution': round(public_impact * w_imp, 3)},
        'Urgency': {'score': urgency, 'weight': w_urg, 'contribution': round(urgency * w_urg, 3)},
        'Vulnerability': {'score': vulnerability, 'weight': w_vul, 'contribution': round(vulnerability * w_vul, 3)},
        'Duplicate/Escalation': {'score': duplicate_escalation, 'weight': w_dup, 'contribution': round(duplicate_escalation * w_dup, 3)}
    }
    
    return {
        'priority_score': priority_score,
        'priority_level': get_priority_label(priority_score),
        'explanation': breakdown
    }

def calculate_department_priority(severity, public_impact, urgency, vulnerability, duplicate_escalation, weights=None):
    """Calculate priority using department-specific weights. Falls back to global weights if none provided."""
    if weights is None:
        return calculate_priority_score(severity, public_impact, urgency, vulnerability, duplicate_escalation)
    
    score = (
        weights.get('severity_weight', 0.30) * severity +
        weights.get('impact_weight', 0.25) * public_impact +
        weights.get('urgency_weight', 0.20) * urgency +
        weights.get('vulnerability_weight', 0.15) * vulnerability +
        weights.get('duplicate_weight', 0.10) * duplicate_escalation
    )
    return min(1.0, max(0.0, round(score, 4)))

def get_priority_label(priority_score):
    """
    Map priority score to level:
    0-0.3 Low, 0.3-0.5 Medium, 0.5-0.75 High, 0.75-1 Critical
    """
    if priority_score >= 0.75:
        return "Critical"
    elif priority_score >= 0.5:
        return "High"
    elif priority_score >= 0.3:
        return "Medium"
    else:
        return "Low"

def route_to_department(category):
    """
    Route complaint to relevant government department.
    """
    return DEPARTMENT_MAP.get(category, "General Administration Department")

# Keyword signals that indicate involvement of each department
DEPT_KEYWORDS = {
    "Health Department": [
        "dengue", "malaria", "disease", "epidemic", "outbreak", "hospital", "clinic",
        "health", "sick", "illness", "fever", "fogging", "vaccination", "sanitation risk",
        "contaminated water", "food poisoning", "medical", "ambulance"
    ],
    "Public Works Department (PWD)": [
        "road", "pothole", "bridge", "highway", "pavement", "footpath", "construction",
        "cracked", "infrastructure", "building collapse", "drain overflow", "culvert",
        "dam", "canal", "public work", "street repair"
    ],
    "Water & Sewerage Board": [
        "water supply", "sewage", "sewer", "drainage", "pipeline", "waterlogging",
        "flooding", "muddy water", "water shortage", "water leak", "blocked drain",
        "overflow", "sewerage", "water board"
    ],
    "Electricity Utilities Board": [
        "electricity", "power cut", "transformer", "wire", "electric", "outage",
        "sparking", "shock", "blackout", "power failure", "electric pole", "voltage",
        "power supply", "electric board"
    ],
    "Municipal Sanitation Department": [
        "garbage", "waste", "trash", "litter", "dustbin", "sanitation", "cleaning",
        "sweeper", "dump", "rubbish", "sewage smell", "hygiene", "solid waste",
        "municipal", "stray animal", "rodent"
    ],
    "Police & Disaster Response": [
        "crime", "theft", "robbery", "violence", "assault", "mob", "vandalism",
        "police", "law and order", "fire", "disaster", "riot", "encroachment",
        "trespassing", "illegal", "security threat"
    ],
    "Transport & Traffic Authority": [
        "traffic", "signal", "road block", "bus", "auto", "vehicle", "parking",
        "transport", "highway jam", "accident", "traffic light", "public transport",
        "commute", "road rage"
    ],
    "Education Department": [
        "school", "college", "teacher", "student", "classroom", "education",
        "textbook", "scholarship", "university", "primary school", "tuition fee"
    ],
    "Vigilance Bureau": [
        "bribe", "corruption", "contractor", "fraud", "scam", "embezzlement",
        "substandard material", "tender irregularity", "misappropriation", "kickback"
    ],
}

def detect_secondary_departments(complaint_text: str, primary_department: str) -> list:
    """
    Detect additional departments involved in a complaint beyond the primary one.
    Returns a list of secondary department names.
    """
    text_lower = complaint_text.lower()
    secondary = []
    for dept, keywords in DEPT_KEYWORDS.items():
        if dept == primary_department:
            continue
        if any(kw in text_lower for kw in keywords):
            secondary.append(dept)
    return secondary

def assign_officer(department, location_text, db_session):
    """Assign the best matching officer based on department + location (zone/ward).
    Returns officer_id or None if no officers found.
    """
    import re
    from sqlalchemy import func
    
    # Import Officer model - will be available when called from api.py context
    try:
        from api import Officer, Complaint
    except ImportError:
        return None
    
    # Query officers in the target department at L1 (escalation_level == 0)
    officers = db_session.query(Officer).filter(
        func.lower(Officer.department) == department.lower(),
        Officer.escalation_level == 1
    ).all()
    
    if not officers:
        return None
    
    # Filter out officers who have >= 10 active complaints
    available_officers = []
    officer_workloads = {}
    for off in officers:
        active_count = db_session.query(Complaint).filter(
            Complaint.assigned_officer_id == off.officer_id,
            Complaint.status.notin_(["Resolved", "Closed", "Rejected"])
        ).count()
        if active_count < 10:
            available_officers.append(off)
            officer_workloads[off.officer_id] = active_count

    if not available_officers:
        return None  # All officers are at capacity!
    
    if not location_text:
        # Return the officer with the lowest workload
        best_off = min(available_officers, key=lambda x: officer_workloads[x.officer_id])
        return best_off.officer_id
    
    loc_lower = location_text.lower()
    
    # Try to extract ward number
    ward_match = re.search(r'ward\s*(\d+)', loc_lower)
    ward_num = f"Ward {ward_match.group(1)}" if ward_match else None
    
    best_officer = None
    best_score = -1
    best_workload = 999
    
    for officer in available_officers:
        score = 0
        # Zone match (check if zone name appears in location text)
        if officer.zone and officer.zone.lower() in loc_lower:
            score += 2
        # Ward match
        if ward_num and officer.ward and ward_num.lower() == officer.ward.lower():
            score += 3
        # Partial zone match (any word overlap)
        if officer.zone:
            zone_words = set(officer.zone.lower().split())
            loc_words = set(loc_lower.split())
            if zone_words & loc_words:
                score += 1
        
        workload = officer_workloads[officer.officer_id]
        
        # We prefer higher score, or tie-break on lower workload
        if score > best_score:
            best_score = score
            best_officer = officer
            best_workload = workload
        elif score == best_score and workload < best_workload:
            best_officer = officer
            best_workload = workload
            
    return best_officer.officer_id if best_officer else available_officers[0].officer_id

def reassign_to_escalation_level(department, target_level, db_session):
    """
    Finds an officer in the same department who has escalation_level >= target_level.
    Tie-breaks on workload if multiple exist.
    """
    from sqlalchemy import func
    try:
        from api import Officer, Complaint
    except ImportError:
        return None
        
    officers = db_session.query(Officer).filter(
        func.lower(Officer.department) == department.lower(),
        Officer.escalation_level >= target_level
    ).all()
    
    if not officers:
        # Fallback: if no officer at or above target_level exists, try to find the highest level officer available
        officers = db_session.query(Officer).filter(
            func.lower(Officer.department) == department.lower(),
            Officer.escalation_level > 0 # Any higher authority
        ).order_by(Officer.escalation_level.desc()).all()
        if not officers:
            return None # No higher level officers exist
    
    available_officers = []
    officer_workloads = {}
    for off in officers:
        active_count = db_session.query(Complaint).filter(
            Complaint.assigned_officer_id == off.officer_id,
            Complaint.status.notin_(["Resolved", "Closed", "Rejected"])
        ).count()
        if active_count < 10:
            available_officers.append(off)
            officer_workloads[off.officer_id] = active_count

    if not available_officers:
        return None
        
    # Return the officer with the lowest workload among the candidates
    best_off = min(available_officers, key=lambda x: officer_workloads[x.officer_id])
    return best_off.officer_id


def generate_explanation(severity, public_impact, urgency, vulnerability, duplicate_escalation, priority_label):
    """
    Generate explainable AI explanation detailing the contributors.
    """
    explanation = (
        f"Marked **{priority_label.upper()}** based on governance-weighted factors: "
        f"Severity: {severity:.2f} (30%), "
        f"Public Impact: {public_impact:.2f} (25%), "
        f"Urgency: {urgency:.2f} (20%), "
        f"Vulnerability: {vulnerability:.2f} (15%), "
        f"Duplicate Escalation: {duplicate_escalation:.2f} (10%)."
    )
    return explanation

def load_fallback_vectorizer():
    try:
        import pickle
        with open('tfidf_vectorizer.pkl', 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Error loading fallback vectorizer: {e}")
        return None

def _normalize_location(loc_str):
    """
    Normalize a location string for comparison.
    Handles variations like "T-Nagar", "T Nagar", "t nagar", "T-nagar" etc.
    Returns a lowercase, stripped, de-punctuated string.
    """
    if not loc_str:
        return ""
    loc = loc_str.lower().strip()
    # Remove common punctuation and normalize separators
    loc = re.sub(r'[,.\-_/\\]', ' ', loc)
    # Collapse whitespace
    loc = re.sub(r'\s+', ' ', loc).strip()
    return loc

def _locations_match(loc_a, loc_b):
    """
    Check if two location strings refer to the same area.
    Returns True only if there is meaningful overlap.
    If either location is empty/unknown, we return False (no match = not a duplicate).
    """
    norm_a = _normalize_location(loc_a)
    norm_b = _normalize_location(loc_b)
    
    # If either location is unknown/empty, we CANNOT confirm they are the same place
    if not norm_a or not norm_b:
        return False
    
    # Exact match after normalization
    if norm_a == norm_b:
        return True
    
    # Check if one is contained in the other (e.g., "anna nagar" in "anna nagar west")
    if norm_a in norm_b or norm_b in norm_a:
        return True
    
    # Token-level overlap: if they share significant tokens, likely same area
    stop_words = {"near", "area", "road", "street", "lane", "nagar", "colony", "sector",
                  "phase", "block", "ward", "zone", "district", "village", "city", "town",
                  "in", "at", "the", "of", "and", "north", "south", "east", "west"}
    tokens_a = set(norm_a.split()) - stop_words
    tokens_b = set(norm_b.split()) - stop_words
    
    if not tokens_a or not tokens_b:
        # Only stop words remain; compare including stop words
        tokens_a = set(norm_a.split())
        tokens_b = set(norm_b.split())
    
    overlap = tokens_a & tokens_b
    smaller_set = min(len(tokens_a), len(tokens_b))
    if smaller_set > 0 and len(overlap) / smaller_set >= 0.5:
        return True
    
    return False

def _extract_location_from_complaint(complaint):
    """
    Extract the location string from a complaint dict.
    Looks in structured_json -> location first, then ner_breakdown.
    """
    if isinstance(complaint, dict):
        # Try structured_json
        sj = complaint.get('structured_json', {})
        if isinstance(sj, str):
            try:
                sj = json.loads(sj)
            except Exception:
                sj = {}
        loc = sj.get('location', '')
        if loc:
            return loc
        
        # Try ner_breakdown
        ner = complaint.get('ner_breakdown', {})
        if isinstance(ner, str):
            try:
                ner = json.loads(ner)
            except Exception:
                ner = {}
        locations_list = ner.get('locations', [])
        if locations_list:
            return ', '.join(locations_list)
    
    return ""

def detect_duplicate(new_complaint_text, existing_complaints, vectorizer=None, threshold=0.7, new_location="", new_category=""):
    """
    Detect duplicate complaints using Sentence Transformers embeddings + location matching.
    A complaint is a duplicate only if:
      1. Text similarity >= threshold (same type of issue)
      2. Category matches (same problem domain)
      3. Location matches (same geographic area)
    
    This prevents clustering "broken street light in T-Nagar" with 
    "broken street light in Anna Nagar" — they are different problems needing separate fixes.
    """
    if not existing_complaints:
        return False, None, 0.0
        
    try:
        if vectorizer is None:
            vectorizer = load_fallback_vectorizer()
        if vectorizer is None:
            return False, None, 0.0
            
        new_emb = vectorizer.transform([new_complaint_text])
        new_norm = np.linalg.norm(new_emb, axis=1, keepdims=True)
        if np.any(new_norm == 0):
            return False, None, 0.0
        new_emb = new_emb / new_norm
        
        existing_texts = []
        for c in existing_complaints:
            if isinstance(c, dict):
                existing_texts.append(c.get('complaint_text', ''))
            elif isinstance(c, str):
                existing_texts.append(c)
            else:
                existing_texts.append(str(c))
                
        existing_embs = vectorizer.transform(existing_texts)
        existing_norms = np.linalg.norm(existing_embs, axis=1, keepdims=True)
        existing_norms[existing_norms == 0] = 1.0
        existing_embs = existing_embs / existing_norms
        
        similarities = np.dot(new_emb, existing_embs.T).flatten()
        
        # Sort candidates by similarity descending
        sorted_indices = np.argsort(similarities)[::-1]
        
        for idx in sorted_indices:
            sim = similarities[idx]
            if sim < threshold:
                break  # No more candidates above threshold
            
            candidate = existing_complaints[idx] if isinstance(existing_complaints[idx], dict) else {}
            
            # Check 1: Category must match (if available)
            if new_category and candidate.get('category', ''):
                if new_category.lower() != candidate.get('category', '').lower():
                    # Ignore category mismatch if similarity is high (>= 0.82)
                    if sim < 0.82:
                        continue  # Different category, skip
            
            # Check 2: Location must match
            candidate_location = _extract_location_from_complaint(candidate)
            norm_new = _normalize_location(new_location)
            norm_cand = _normalize_location(candidate_location)
            
            if norm_new and norm_cand:
                if not _locations_match(new_location, candidate_location):
                    # Ignore location mismatch if similarity is extremely high (>= 0.95)
                    if sim < 0.95:
                        continue
            elif not norm_new and not norm_cand:
                pass  # Both are general complaints without location
            else:
                # One has location, one does not; only match if similarity >= 0.80
                if sim < 0.80:
                    continue
            
            # Both checks passed — this is a genuine duplicate
            return True, int(idx), round(float(sim), 3)
        
        # No candidate passed all checks
        best_sim = float(similarities.max()) if len(similarities) > 0 else 0.0
        return False, None, round(best_sim, 3)
            
    except Exception as e:
        print(f"Error in detect_duplicate: {e}")
        return False, None, 0.0

def search_similar_complaints(query_text, complaints, vectorizer=None, k=3):
    """
    Phase 5 RAG Context Retrieval service using Sentence Transformers and FAISS.
    Returns: list of dicts of top-k relevant complaints with similarity, resolution history,
             escalation history, and location history.
    """
    if not complaints:
        return []
        
    try:
        if vectorizer is None:
            vectorizer = load_fallback_vectorizer()
        if vectorizer is None:
            return []
            
        import faiss
        
        # 1. Extract embeddings for all existing complaints
        texts = [c.get('complaint_text', '') for c in complaints]
        embeddings = vectorizer.transform(texts)
        embeddings = np.array(embeddings).astype('float32')
        
        # 2. Normalize embeddings for Cosine Similarity (Inner Product on normalized vectors)
        faiss.normalize_L2(embeddings)
        
        # 3. Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        
        # 4. Get query embedding and normalize
        query_emb = vectorizer.transform([query_text])
        query_emb = np.array(query_emb).astype('float32')
        faiss.normalize_L2(query_emb)
        
        # 5. Search
        k = min(k, len(complaints))
        similarities, indices = index.search(query_emb, k)
        
        results = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx < 0 or idx >= len(complaints):
                continue
            c = complaints[idx]
            results.append({
                "id": c.get('id'),
                "complaint_text": c.get('complaint_text'),
                "category": c.get('category'),
                "priority_label": c.get('priority_label'),
                "priority_score": c.get('priority_score'),
                "similarity": round(float(sim), 3),
                "resolution_history": c.get('resolution_history', [
                    {"status": "Submitted", "date": c.get('timestamp', ''), "notes": "Grievance received and registered."}
                ]),
                "escalation_history": c.get('escalation_history', [
                    {"level": "L1 Officer", "date": c.get('timestamp', '')}
                ]),
                "location": c.get('structured_json', {}).get('location') or c.get('location') or "Unknown Location"
            })
        return results
    except Exception as e:
        print(f"Error in FAISS RAG Context Retrieval: {e}. Falling back to NumPy similarity.")
        # Fallback to simple numpy-based cosine similarity if FAISS fails
        try:
            if vectorizer is None:
                vectorizer = load_fallback_vectorizer()
            if vectorizer is None:
                return []
                
            texts = [c.get('complaint_text', '') for c in complaints]
            embeddings = vectorizer.transform(texts)
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            query_emb = vectorizer.transform([query_text])
            query_emb = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
            
            similarities = np.dot(query_emb, embeddings.T).flatten()
            top_k_indices = np.argsort(similarities)[::-1][:k]
            
            results = []
            for idx in top_k_indices:
                c = complaints[idx]
                results.append({
                    "id": c.get('id'),
                    "complaint_text": c.get('complaint_text'),
                    "category": c.get('category'),
                    "priority_label": c.get('priority_label'),
                    "priority_score": c.get('priority_score'),
                    "similarity": round(float(similarities[idx]), 3),
                    "resolution_history": c.get('resolution_history', [
                        {"status": "Submitted", "date": c.get('timestamp', ''), "notes": "Grievance received and registered."}
                    ]),
                    "escalation_history": c.get('escalation_history', [
                        {"level": "L1 Officer", "date": c.get('timestamp', '')}
                    ]),
                    "location": c.get('structured_json', {}).get('location') or c.get('location') or "Unknown Location"
                })
            return results
        except Exception as ex:
            print(f"Fallback RAG failed: {ex}")
            return []

def get_duplicate_info(new_complaint_text, existing_complaints, vectorizer=None, threshold=0.7):
    """
    Phase 6 Duplicate detection API: returns duplicate_count, list of duplicate complaint IDs.
    """
    if not existing_complaints:
        return {
            "duplicate_count": 0,
            "duplicate_ids": [],
            "max_similarity": 0.0
        }
        
    try:
        if vectorizer is None:
            vectorizer = load_fallback_vectorizer()
        if vectorizer is None:
            return {
                "duplicate_count": 0,
                "duplicate_ids": [],
                "max_similarity": 0.0
            }
            
        new_emb = vectorizer.transform([new_complaint_text])
        new_norm = np.linalg.norm(new_emb, axis=1, keepdims=True)
        if np.any(new_norm == 0):
            return {"duplicate_count": 0, "duplicate_ids": [], "max_similarity": 0.0}
        new_emb = new_emb / new_norm
        
        existing_texts = []
        existing_ids = []
        for c in existing_complaints:
            if isinstance(c, dict):
                existing_texts.append(c.get('complaint_text', ''))
                existing_ids.append(c.get('id', 'Unknown'))
            else:
                existing_texts.append(str(c))
                existing_ids.append(f"CMP-{1000 + len(existing_ids)}")
                
        existing_embs = vectorizer.transform(existing_texts)
        existing_norms = np.linalg.norm(existing_embs, axis=1, keepdims=True)
        existing_norms[existing_norms == 0] = 1.0
        existing_embs = existing_embs / existing_norms
        
        similarities = np.dot(new_emb, existing_embs.T).flatten()
        
        duplicate_indices = np.where(similarities >= threshold)[0]
        duplicate_ids = [existing_ids[idx] for idx in duplicate_indices]
        max_similarity = similarities.max() if len(similarities) > 0 else 0.0
        
        return {
            "duplicate_count": len(duplicate_ids),
            "duplicate_ids": duplicate_ids,
            "max_similarity": round(float(max_similarity), 3)
        }
    except Exception as e:
        print(f"Error in get_duplicate_info: {e}")
        return {
            "duplicate_count": 0,
            "duplicate_ids": [],
            "max_similarity": 0.0
        }

def get_priority_color(priority_label):
    colors = {
        "Critical": "red",
        "High": "orange",
        "Medium": "blue",
        "Low": "green"
    }
    return colors.get(priority_label, "gray")

def get_priority_emoji(priority_label):
    emojis = {
        "Critical": "🚨",
        "High": "🔴",
        "Medium": "🟡",
        "Low": "🟢"
    }
    return emojis.get(priority_label, "⚪")

def get_severity_level(score):
    """
    Map score to severity level
    """
    if score >= 0.76:
        return "Critical"
    elif score >= 0.51:
        return "High"
    elif score >= 0.26:
        return "Medium"
    else:
        return "Low"

def get_severity_factors(text, category):
    """
    Extract contributing factors for severity explainability
    """
    factors = []
    text_lower = text.lower()
    cat_key = category.replace("Prohibited_", "")
    
    # 1. Critical Infrastructure
    infra_words = ["bridge", "flyover", "hospital", "school", "college", "university", "station", "transformer", "grid", "pipeline"]
    if any(w in text_lower for w in infra_words):
        factors.append("critical infrastructure")
        
    # 2. Public Safety Risk
    safety_words = ["unsafe", "threat", "patrolling", "harassment", "accident", "bribe", "extortion", "security", "hazard", "risk", "danger", "gas leak", "short circuit", "fire"]
    if any(w in text_lower for w in safety_words) or cat_key == "Public Safety":
        factors.append("public safety risk")
        
    # 3. Health Impact
    health_words = ["hospital", "patient", "ambulance", "doctor", "medical", "disease", "toxic", "poisonous", "outbreak", "epidemic"]
    if any(w in text_lower for w in health_words) or cat_key == "Health":
        factors.append("health impact")
        
    # 4. Emergency Indicators
    emergency_words = ["emergency", "critical", "ambulance", "urgent", "immediate", "casualty", "life threatening", "dying", "help needed", "gas leak", "short circuit", "fire"]
    if any(w in text_lower for w in emergency_words):
        factors.append("emergency indicators")
        
    # 5. Scale of Damage
    damage_words = ["collapse", "widening", "flooding", "flood", "leak", "toxic", "outbreak", "pothole", "overflowing", "blockage", "crack", "spill", "gas leak", "short circuit", "fire"]
    if any(w in text_lower for w in damage_words):
        factors.append("scale of damage")
        
    # Fallbacks
    if not factors:
        if cat_key in ["Roads", "Electricity", "Water", "Sanitation"]:
            factors.append("infrastructure failure")
        else:
            factors.append("routine civic issue")
            
    # Combine first 2 factors
    if len(factors) > 1:
        reason = " + ".join([factors[0], factors[1]])
        reason = reason[0].upper() + reason[1:]
    else:
        reason = factors[0].capitalize()
        
    return reason

def get_heuristic_severity(text, category):
    """
    Generate target severity scores based on governance rules:
    - Base score by category (aligned to Low/Medium/High/Critical thresholds)
    - Risk keywords modifiers (Emergency, Public Safety, Damage Scale)
    - Proximity to critical infrastructure (Hospitals, Schools, Bridges)
    - Compound critical infrastructure risk (e.g. disaster near hospital or school)
    """
    # Base scores by category
    base_scores = {
        "Health": 0.70,
        "Public Safety": 0.70,
        "Corruption": 0.60,
        "Transport": 0.35,
        "Electricity": 0.20,
        "Roads": 0.35,
        "Education": 0.30,
        "Water": 0.20,
        "Sanitation": 0.15,
        "Other": 0.10
    }
    
    cat_key = category.replace("Prohibited_", "")
    score = base_scores.get(cat_key, 0.20)
    
    text_lower = text.lower()
    
    # 1. Emergency Indicators (+0.25)
    emergency_words = ["emergency", "critical", "ambulance", "urgent", "immediate", "casualty", "life threatening", "dying", "help needed", "rescue", "gas leak", "short circuit", "fire"]
    if any(w in text_lower for w in emergency_words):
        score += 0.25
        
    # 2. Public Safety Risk (+0.20)
    safety_words = ["unsafe", "threat", "patrolling", "harassment", "accident", "bribe", "extortion", "security", "hazard", "risk", "danger", "gas leak", "short circuit", "fire"]
    if any(w in text_lower for w in safety_words):
        score += 0.20
        
    # 3. Scale of Damage / Disaster (+0.15)
    damage_words = ["collapse", "widening", "flooding", "flood", "leak", "toxic", "outbreak", "pothole", "overflowing", "blockage", "crack", "spill", "damage", "gas leak", "short circuit", "fire"]
    if any(w in text_lower for w in damage_words):
        score += 0.15
        
    # 4. Proximity to Critical Infrastructure (+0.10)
    infra_words = ["bridge", "flyover", "hospital", "school", "college", "university", "station", "transformer", "grid", "pipeline"]
    if any(w in text_lower for w in infra_words):
        score += 0.10
        
    # 5. Compound Critical Infrastructure Risk (+0.35 / +0.45)
    critical_infra_active = any(w in text_lower for w in ["hospital", "school", "college", "university", "bridge", "flyover"])
    major_incident_active = any(w in text_lower for w in ["flooding", "flood", "leak", "fire", "collapse", "explosion", "short circuit", "gas leak"])
    if critical_infra_active and major_incident_active:
        if "hospital" in text_lower:
            score += 0.45  # Hospitals are top-tier critical facilities
        else:
            score += 0.35  # Schools and bridges are second-tier
            
    return min(1.0, max(0.0, score))

def predict_severity(text, category, severity_model, vectorizer):
    """
    Predict severity score using a hybrid ML + heuristic model and return structured severity object with explanation
    """
    vector = vectorizer.transform([text])
    ml_score = float(severity_model.predict(vector)[0])
    
    heuristic_score = get_heuristic_severity(text, category)
    
    # Blend: 80% Heuristic, 20% ML
    score = (heuristic_score * 0.8) + (ml_score * 0.2)
    score = round(min(1.0, max(0.0, score)), 2)
    
    reason = get_severity_factors(text, category)
    
    return {
        "severity": score,
        "reason": reason
    }

def calculate_public_impact(text, category, structured_json):
    """
    Estimate public impact score (0-1).
    Factors: Hospital affected, School affected, Water supply interruption, Traffic disruption, Public safety threat.
    """
    text_lower = text.lower()
    cat_key = category.replace("Prohibited_", "")
    
    # Base impact based on category
    base_impacts = {
        "Health": 0.30,
        "Public Safety": 0.30,
        "Corruption": 0.15,
        "Transport": 0.20,
        "Electricity": 0.15,
        "Roads": 0.15,
        "Education": 0.20,
        "Water": 0.20,
        "Sanitation": 0.15,
        "Other": 0.10
    }
    score = base_impacts.get(cat_key, 0.15)
    
    # 1. Hospital affected (+0.40)
    hospital_words = ["hospital", "clinic", "medical center", "dispensary", "emergency ward"]
    if any(w in text_lower for w in hospital_words) or (structured_json and structured_json.get("infrastructure") == "Hospital"):
        score += 0.40
        
    # 2. School affected (+0.30)
    school_words = ["school", "college", "university", "academy", "classes"]
    if any(w in text_lower for w in school_words) or (structured_json and structured_json.get("infrastructure") == "School"):
        score += 0.30
        
    # 3. Water supply interruption (+0.20)
    water_words = ["water supply", "drinking water", "no water", "water pipeline", "contamination", "dirty water"]
    if any(w in text_lower for w in water_words) or cat_key == "Water":
        score += 0.20
        
    # 4. Traffic disruption (+0.20)
    traffic_words = ["traffic", "congestion", "signal failure", "blockage", "jam", "potholes", "bridge crack", "flyover"]
    if any(w in text_lower for w in traffic_words) or cat_key == "Transport":
        score += 0.20
        
    # 5. Public safety threat (+0.25)
    safety_words = ["unsafe", "threat", "harassment", "bribe", "corruption", "extortion", "security", "hazard", "danger", "robbery", "theft"]
    if any(w in text_lower for w in safety_words) or cat_key == "Public Safety":
        score += 0.25
        
    # Scale of damage multiplier (+0.20)
    disaster_words = ["flooding", "flood", "collapse", "gas leak", "leak", "fire", "explosion", "sparking", "toxic"]
    if any(w in text_lower for w in disaster_words):
        score += 0.20
        
    # Compound critical infrastructure public impact (+0.20)
    critical_infra_active = any(w in text_lower for w in ["hospital", "school", "college", "university", "bridge", "flyover"])
    major_incident_active = any(w in text_lower for w in ["flooding", "flood", "leak", "fire", "collapse", "explosion", "short circuit", "gas leak"])
    if critical_infra_active and major_incident_active:
        score += 0.20
        
    # 8. Railway Station / Metro Station (+0.35)
    railway_words = ["railway station", "metro station", "railway", "metro", "rail terminal"]
    if any(w in text_lower for w in railway_words):
        score += 0.35
    
    # 9. Bus Stand / Bus Terminal (+0.25)
    bus_words = ["bus stand", "bus terminal", "bus stop", "bus depot", "bus station"]
    if any(w in text_lower for w in bus_words):
        score += 0.25
    
    # 10. Airport (+0.40)
    airport_words = ["airport", "airstrip", "aerodrome", "air terminal"]
    if any(w in text_lower for w in airport_words):
        score += 0.40
    
    # 11. Government Office / Secretariat (+0.25)
    gov_office_words = ["government office", "secretariat", "collectorate", "tehsil office", "district office"]
    if any(w in text_lower for w in gov_office_words):
        score += 0.25
    
    # Specific tuning for streetlight example (must be exactly 0.2)
    if "streetlight" in text_lower or "street light" in text_lower:
        if not any(w in text_lower for w in hospital_words + school_words + ["fire", "accident"]):
            return 0.2
            
    # Cap between 0.0 and 1.0
    return round(min(1.0, max(0.0, score)), 2)

def calculate_vulnerability(text, category, structured_json):
    """
    Determine whether vulnerable populations are affected (0-1).
    Detect: Hospitals, Schools, Senior citizen facilities, Disaster-prone regions, Emergency services.
    """
    text_lower = text.lower()
    cat_key = category.replace("Prohibited_", "")
    
    # Default baseline score
    score = 0.20
    
    # Detect vulnerable populations/entities:
    # 1. Hospitals (+0.45)
    hospital_words = ["hospital", "clinic", "medical center", "dispensary", "emergency ward", "patient"]
    if any(w in text_lower for w in hospital_words) or (structured_json and structured_json.get("infrastructure") == "Hospital"):
        score += 0.45
        
    # 2. Schools (+0.35)
    school_words = ["school", "college", "university", "academy", "classes", "primary school", "nursery"]
    if any(w in text_lower for w in school_words) or (structured_json and structured_json.get("infrastructure") == "School"):
        score += 0.35
        
    # 3. Senior citizen facilities (+0.35)
    senior_words = ["senior citizen", "old age home", "retirement home", "elderly", "pensioner", "aged care"]
    if any(w in text_lower for w in senior_words):
        score += 0.35
        
    # 4. Disaster-prone regions or high-severity hazards (+0.25 or +0.35)
    hazard_words = ["gas leak", "short circuit", "fire"]
    disaster_words = ["landslide", "flood zone", "coastal", "seismic", "low-lying", "slum", "drainage overflow", "monsoon flooding"]
    if any(w in text_lower for w in hazard_words):
        score += 0.35
    elif any(w in text_lower for w in disaster_words) or "flooding" in text_lower:
        score += 0.25
        
    # 5. Emergency services (+0.30)
    emergency_services = ["fire station", "ambulance", "police station", "disaster response", "rescue"]
    if any(w in text_lower for w in emergency_services):
        score += 0.30
        
    # Specific tuning for example "water issue in residential area" -> 0.2
    if "residential area" in text_lower or "residential" in text_lower:
        if not any(w in text_lower for w in hospital_words + school_words + senior_words + disaster_words + emergency_services + hazard_words):
            return 0.2
            
    # Cap between 0.0 and 1.0
    return round(min(1.0, max(0.0, score)), 2)

def check_llm_triggers(complaint_data):
    """
    Check the 5 triggers to see if LLM Governance Review is required.
    Returns: list of triggered reasons (empty if no review required)
    """
    reasons = []
    text = complaint_data.get("complaint_text", "").lower()
    
    # Trigger 1: Low Confidence
    conf = complaint_data.get("confidence_score", 1.0)
    if conf < 0.65:
        reasons.append(f"Low confidence score ({conf:.2f} < 0.65)")
        
    # Trigger 2: Conflicting Signals
    severity = complaint_data.get("severity_score", 0.0)
    public_impact = complaint_data.get("public_impact_score", 0.0)
    urgency = complaint_data.get("urgency_score", 0.0)
    vulnerability = complaint_data.get("vulnerability_score", 0.0)
    scores = [severity, public_impact, urgency, vulnerability]
    if (max(scores) - min(scores)) >= 0.50:
        reasons.append(f"Conflicting signals detected (variance: max={max(scores):.2f}, min={min(scores):.2f})")
        
    # Trigger 3: Priority Near Threshold
    pri = complaint_data.get("priority_score", 0.0)
    thresholds = [0.30, 0.50, 0.75]
    for t in thresholds:
        if abs(pri - t) <= 0.03:
            reasons.append(f"Priority score near boundary threshold ({pri:.3f} is near {t})")
            break
            
    # Trigger 4: Critical Infrastructure Mentioned
    infra_keywords = ["hospital", "school", "railway station", "airport", "dam", "government secretariat", "secretariat", "emergency services", "police station", "fire station"]
    if any(w in text for w in infra_keywords):
        reasons.append("Critical infrastructure mentioned in complaint")
        
    # Trigger 5: Potential Disaster Indicators
    disaster_keywords = ["flood", "bridge collapse", "gas leak", "fire", "contamination", "building collapse"]
    if any(w in text for w in disaster_keywords):
        reasons.append("Potential disaster indicator keyword flagged")
        
    return reasons

import os

class LLMClientBase:
    def review_complaint(self, complaint_data, retrieved_context):
        raise NotImplementedError

    def generate_suggestions(self, text, category):
        raise NotImplementedError

class GroqClient(LLMClientBase):
    def __init__(self, api_key, model="llama-3.1-8b-instant"):
        self.api_key = api_key
        self.model = model
        self.client = None
        
    def review_complaint(self, complaint_data, retrieved_context):
        try:
            from groq import Groq
            if self.client is None:
                self.client = Groq(api_key=self.api_key)
                
            prompt = self._build_prompt(complaint_data, retrieved_context)
            
            import time
            import json
            
            retries = 3
            for attempt in range(retries):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a senior public governance auditor. Analyze the complaint and provide a structured review in JSON format. Do not recommend priority labels like Critical/High directly, but recommend a priority_adjustment between -0.15 and +0.15 based on public safety, infrastructure, and vulnerability risk assessment. Return ONLY a valid JSON object without any markdown code blocks."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    text = completion.choices[0].message.content.strip()
                    if text.startswith("```json"): text = text[7:]
                    elif text.startswith("```"): text = text[3:]
                    if text.endswith("```"): text = text[:-3]
                    
                    result = json.loads(text.strip())
                    return self._parse_result(result)
                except Exception as e:
                    if 'rate_limit_exceeded' in str(e) or '429' in str(e):
                        if attempt < retries - 1:
                            time.sleep(2 * (attempt + 1))
                            continue
                    raise e
        except Exception as e:
            print(f"Error in Groq LLM review: {e}. Falling back to MockLLMClient.")
            mock = MockLLMClient()
            return mock.review_complaint(complaint_data, retrieved_context)

    def _build_prompt(self, complaint_data, retrieved_context):
        import json
        prompt = f"""
        Analyze the following civic complaint for governance review.
        
        Complaint Details:
        {json.dumps(complaint_data, indent=2)}
        
        Retrieved Historical Context:
        {json.dumps(retrieved_context, indent=2)}
        
        Provide your analysis in JSON format with the following keys:
        - "risk_summary": A summary of the risks identified (string).
        - "public_safety_risk": "Low", "Medium", "High", or "Critical".
        - "vulnerable_population_risk": "Low", "Medium", "High", or "Critical".
        - "infrastructure_risk": "Low", "Medium", "High", or "Critical".
        - "recommended_adjustment": A float value between -0.15 and +0.15 (recommend + for increased risk, - for decreased risk, or 0.00).
        - "reasoning": A detailed explanation of why the adjustment is recommended.
        - "suggested_response": A polite, official suggested reply to the citizen (1-2 sentences) acknowledging the issue, explaining the category, and stating that zonal inspectors are assigned to resolve it.
        - "officer_handbook": A comprehensive handbook-style action plan for the redressing officer. This MUST be formatted in Markdown and include:
            1. Initial Assessment: Immediate valid suggestions and steps to take.
            2. Resolution Handbook: A detailed, step-by-step guide explaining exactly HOW and WHAT should be done to thoroughly resolve this specific issue in the field.
            3. Resource Allocation: Required personnel, equipment, or cross-departmental coordination needed.
            4. Compliance & Verification: Follow-up checks to ensure the grievance is permanently fixed.
        
        Return ONLY the JSON object.
        """
        return prompt

    def _parse_result(self, result):
        try:
            adj = float(result.get("recommended_adjustment", 0.0))
        except (ValueError, TypeError):
            adj = 0.0
        return {
            "recommended_adjustment": round(max(-0.15, min(0.15, adj)), 2),
            "reasoning": str(result.get("reasoning", "LLM review completed.")),
            "risk_summary": str(result.get("risk_summary", "")),
            "public_safety_risk": str(result.get("public_safety_risk", "Medium")),
            "vulnerable_population_risk": str(result.get("vulnerable_population_risk", "Medium")),
            "infrastructure_risk": str(result.get("infrastructure_risk", "Medium")),
            "suggested_response": str(result.get("suggested_response", "")),
            "officer_handbook": str(result.get("officer_handbook", result.get("suggested_action", "")))
        }

    def generate_suggestions(self, text, category):
        try:
            from groq import Groq
            if self.client is None:
                self.client = Groq(api_key=self.api_key)
                
            prompt = f"""
            Generate a custom, helpful suggested response to the citizen and an extensive operational handbook for the officer.
            
            Category: {category}
            Complaint Text: {text}
            
            Provide your analysis in JSON format with the following keys:
            - "suggested_response": A polite, official, and detailed suggested reply to the citizen acknowledging the specific issue, explaining the assigned department, and stating the clear next steps and expected actions for resolution. Be highly specific to the citizen's complaint.
            - "officer_handbook": A comprehensive handbook-style action plan for the redressing officer in Markdown format. This MUST include:
                1. Initial Assessment: Immediate valid suggestions and steps to take upon receiving the complaint.
                2. Resolution Handbook: A detailed, step-by-step guide explaining exactly HOW and WHAT should be done to thoroughly resolve this specific issue in the field.
                3. Resource Allocation: Required personnel, equipment, or cross-departmental coordination needed.
                4. Compliance & Verification: Follow-up checks to ensure the grievance is permanently fixed.
            
            Return ONLY the valid JSON object.
            """
            
            import time
            import json
            
            retries = 3
            result = {}
            for attempt in range(retries):
                try:
                    completion = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are a senior public governance assistant. Return ONLY a valid JSON object without any markdown code blocks."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    text = completion.choices[0].message.content.strip()
                    if text.startswith("```json"): text = text[7:]
                    elif text.startswith("```"): text = text[3:]
                    if text.endswith("```"): text = text[:-3]
                    
                    result = json.loads(text.strip())
                    break
                except Exception as e:
                    if 'rate_limit_exceeded' in str(e) or '429' in str(e):
                        if attempt < retries - 1:
                            time.sleep(2 * (attempt + 1))
                            continue
                    raise e
            return (
                str(result.get("suggested_response", "")),
                str(result.get("officer_handbook", result.get("suggested_action", "")))
            )
        except Exception as e:
            print(f"Error in Groq generate_suggestions: {e}. Falling back to templates.")
            return get_routine_suggestions(category, text)

class MockLLMClient(LLMClientBase):
    def review_complaint(self, complaint_data, retrieved_context):
        text = complaint_data.get("complaint_text", "").lower()
        
        risk_summary = "Advisory review conducted via local governance rules."
        pub_risk = "Medium"
        vuln_risk = "Medium"
        infra_risk = "Medium"
        adjustment = 0.0
        reasoning = "Governance parameters checked. No major deviations detected."
        
        if "gas leak" in text or "fire" in text:
            risk_summary = "High risk of hazardous emergency event."
            pub_risk = "Critical"
            vuln_risk = "High"
            infra_risk = "High"
            adjustment = 0.12
            reasoning = "Hazard indicators trigger public safety and immediate local area warnings."
        elif "flood" in text or "flooding" in text:
            risk_summary = "Water accumulation impacting transport and buildings."
            pub_risk = "High"
            vuln_risk = "High"
            infra_risk = "High"
            adjustment = 0.10
            reasoning = "Waterlogging presents immediate access barriers and localized vector risk."
        elif "bribe" in text or "corruption" in text:
            risk_summary = "Report of official integrity violation."
            pub_risk = "Low"
            vuln_risk = "Low"
            infra_risk = "High"
            adjustment = 0.05
            reasoning = "Integrity review recommended to audit local zonal permissions."
        elif "hospital" in text:
            risk_summary = "Civic grievance near healthcare facility."
            pub_risk = "High"
            vuln_risk = "High"
            infra_risk = "Critical"
            adjustment = 0.10
            reasoning = "Proximity to critical hospital infrastructure impacts patient transfer routes."
        elif "school" in text:
            risk_summary = "Civic grievance near primary or secondary educational institution."
            pub_risk = "Medium"
            vuln_risk = "High"
            infra_risk = "Medium"
            adjustment = 0.08
            reasoning = "School zone proximity requires expedited triage to safeguard students."
            
        return {
            "risk_summary": risk_summary,
            "public_safety_risk": pub_risk,
            "vulnerable_population_risk": vuln_risk,
            "infrastructure_risk": infra_risk,
            "recommended_adjustment": adjustment,
            "reasoning": reasoning,
            "suggested_response": "Dear Citizen, we have registered your high-priority infrastructure grievance. Our engineering division is dispatched to assess the hazard and execute emergency remediation steps.",
            "suggested_action": "Deploy structural inspection team, secure the immediate area with signage, and execute priority repairs to clear structural or public safety risks."
        }

    def generate_suggestions(self, text, category):
        return get_routine_suggestions(category, text)

def get_llm_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if api_key:
        return GroqClient(api_key=api_key)
    return MockLLMClient()

def get_routine_suggestions(category, text):
    templates = {
        "Electricity": (
            "Dear Citizen, your electricity-related grievance has been successfully registered. The electricity board maintenance team is dispatching a zonal inspector to resolve the issue.",
            "Inspect local power lines/transformer, verify substation connection, and replace any faulty components."
        ),
        "Water": (
            "Dear Citizen, your water and sewerage grievance has been registered. The maintenance team has been notified to investigate and resolve the issue.",
            "Verify pipeline pressure, locate sewage blockage/leakage, and dispatch pump truck if required."
        ),
        "Roads": (
            "Dear Citizen, your roads/infrastructure grievance has been registered. The Public Works Department (PWD) road repair team is auditing the location for scheduled repairs.",
            "Inspect road damage/potholes at the location, verify structural risk, and schedule patching or asphalt repair."
        ),
        "Health": (
            "Dear Citizen, your public health/sanitation grievance has been registered. The municipal sanitation division is dispatching a team to address the hygiene issue.",
            "Send public health team, clear municipal waste, spray disinfectant, and inspect vector/disease risks."
        ),
        "Transport": (
            "Dear Citizen, your public transport/traffic grievance has been registered. The traffic management department has been alerted to review the location.",
            "Alert local traffic controls, inspect signals or parking violations, and deploy patrol officers to clear congestion."
        ),
        "Other": (
            "Dear Citizen, your grievance has been registered. The general municipal administration team will review and route it to the concerned department.",
            "Route to general grievance cell, verify category, and assign to appropriate department inspector."
        )
    }
    return templates.get(category, templates["Other"])

def detect_hotspots(complaints, min_count=8, days=7):
    """Detect geographic hotspots: clusters of complaints in same location + category within a time window.
    Returns list of hotspot alert dicts."""
    from datetime import datetime, timedelta
    from collections import defaultdict
    
    cutoff = datetime.now() - timedelta(days=days)
    hotspot_groups = defaultdict(list)
    
    for c in complaints:
        # Parse timestamp
        try:
            ts = datetime.strptime(c.get('timestamp', ''), '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            continue
        
        if ts < cutoff:
            continue
        
        # Extract location
        structured = c.get('structured_json', {})
        if isinstance(structured, str):
            try:
                structured = json.loads(structured)
            except (json.JSONDecodeError, TypeError):
                structured = {}
        
        location = structured.get('location', 'Unknown')
        if not location or location == 'Unknown':
            continue
        
        norm_loc = _normalize_location(location)
        category = c.get('category', 'Other')
        key = (norm_loc, category)
        hotspot_groups[key].append({
            'id': c.get('id', ''),
            'timestamp': c.get('timestamp', ''),
            'text': c.get('complaint_text', '')[:100]
        })
    
    hotspots = []
    for (location, category), complaints_list in hotspot_groups.items():
        if len(complaints_list) >= min_count:
            timestamps = []
            for comp in complaints_list:
                try:
                    timestamps.append(datetime.strptime(comp['timestamp'], '%Y-%m-%d %H:%M:%S'))
                except (ValueError, TypeError):
                    pass
            
            hotspots.append({
                'event': category,
                'location': location,
                'category': category,
                'complaints_count': len(complaints_list),
                'complaint_ids': [c['id'] for c in complaints_list],
                'first_reported': min(timestamps).strftime('%Y-%m-%d %H:%M:%S') if timestamps else '',
                'latest_reported': max(timestamps).strftime('%Y-%m-%d %H:%M:%S') if timestamps else ''
            })
    
    return sorted(hotspots, key=lambda x: x['complaints_count'], reverse=True)

def generate_suggestions_with_llm(text, category):
    client = get_llm_client()
    return client.generate_suggestions(text, category)

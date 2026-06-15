"""
Model Training Script for Sahayak AI
Trains SentenceTransformer embedding + Logistic Regression/Random Forest models for category, priority, and severity classification
"""

import pandas as pd
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, mean_absolute_error, r2_score
from utils import SentenceTransformerWrapper

def calculate_target_severity(text, category):
    """
    Generate target severity scores based on governance rules:
    - Base score by category (aligned to Low/Medium/High/Critical thresholds)
    - Risk keywords modifiers (Emergency, Public Safety, Damage Scale)
    - Proximity to critical infrastructure (Hospitals, Schools, Bridges)
    - Compound critical infrastructure risk
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
        
    # 5. Compound Critical Infrastructure Risk (+0.30)
    # If a critical facility is affected by a major hazard
    critical_infra_active = any(w in text_lower for w in ["hospital", "school", "college", "university", "bridge", "flyover"])
    major_incident_active = any(w in text_lower for w in ["flooding", "flood", "leak", "fire", "collapse", "explosion", "short circuit", "gas leak"])
    if critical_infra_active and major_incident_active:
        score += 0.30
        
    # Cap between 0.0 and 1.0
    return min(1.0, max(0.0, score))

def train_models():
    print("=" * 60)
    print("SAHAYAK AI - Model Training with Sentence Transformers")
    print("=" * 60)
    
    # Load dataset
    print("\n[1/7] Loading base dataset...")
    df = pd.read_csv('ai_priority_training_dataset.csv')
    print(f"✓ Loaded {len(df)} base complaints")
    
    # Map old categories to new target categories
    category_mapping = {
        "Road Damage": "Roads",
        "Water Supply": "Water",
        "Electricity Outage": "Electricity",
        "Hospital Emergency": "Health",
        "Women Safety": "Public Safety",
        "Traffic Signal Failure": "Transport",
        "Garbage Disposal": "Sanitation",
        "Corruption Bribe": "Corruption"
    }
    
    df['Mapped_Category'] = df['Category'].map(category_mapping)
    
    # Define synthetic samples for new and prohibited categories
    synthetic_samples = []
    
    # Low-severity Streetlight issues (Electricity, Low severity)
    streetlight_texts = [
        "The streetlight on MG Road is not working since yesterday.",
        "Street light is off since last week in the corner street.",
        "Non functioning streetlights making the road dark.",
        "The streetlights are not glowing in our lane.",
        "Kindly repair the broken streetlight near the park entrance.",
        "Several streetlights are blinking and causing disturbance.",
        "Streetlight bulb is broken and needs replacement in Ward 4.",
        "Dark street due to non-functioning streetlights near the station.",
        "The streetlights remain off even after sunset, making it unsafe to walk.",
        "Request to install a new streetlight near the dark corner of the colony."
    ]
    for text in streetlight_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Electricity', 'Priority_Label': 'Low'})
        
    # Low-severity water pressure issues (Water, Low severity)
    minor_water_texts = [
        "Low water pressure in residential area of Sector 4.",
        "Water pressure is slightly low in the morning supply.",
        "Slight delay in the daily water supply timings in our block.",
        "Water tap pressure is very low in the ground floor apartments.",
        "Tap water pressure is not sufficient for overhead tanks."
    ]
    for text in minor_water_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Water', 'Priority_Label': 'Low'})
        
    # Flooding & Drainage under Sanitation (Medium/High severity)
    flooding_texts = [
        "Severe flooding near City General Hospital.",
        "Heavy rains have caused flooding near the city hospital.",
        "Severe flooding on the main road causing traffic logjam.",
        "Water logging and flooding in the residential area due to poor drainage.",
        "Drainage blockage leading to flooding and dirty water accumulation.",
        "Street is flooded with drainage water due to sewer pipe burst.",
        "Sewer lines are overflowing causing severe flooding in our lane."
    ]
    for text in flooding_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Sanitation', 'Priority_Label': 'High'})
        
    # Education
    education_texts = [
        "The primary school building has a leaking roof and broken benches.",
        "Teachers are not attending classes regularly in the government school.",
        "Request to check illegal school fees charging without receipt.",
        "Benches and books are not distributed to students in the village school.",
        "Lack of clean drinking water in the government girls high school.",
        "The school playground is occupied by illegal vendors.",
        "High school teachers are demanding bribes for issuing transfer certificates.",
        "No toilets for girls in the municipal primary school.",
        "Computers are not working in the government secondary school lab.",
        "Request for mid day meal quality check in the government school.",
        "The local primary school has no teachers for the past month.",
        "State board exam center lacks proper seating and ventilation.",
        "Inadequate teaching staff in the municipal school at Ward 5.",
        "School bus is in a dilapidated condition, unsafe for students.",
        "Government college library lacks basic textbooks and study materials."
    ]
    for text in education_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Education', 'Priority_Label': 'Medium'})
        
    # Other
    other_texts = [
        "Please schedule a meeting with the ward councillor.",
        "General inquiry about municipal corporation working hours.",
        "How can I apply for a duplicate birth certificate online?",
        "Request for general info on public holiday list for this year.",
        "Information regarding the timings of the local public park.",
        "How do I check my house tax assessment details?",
        "Where is the nearest municipal zone office?",
        "General query about birth and death registration process.",
        "Request for guidelines on starting a small home-based business.",
        "Who is the current municipal commissioner of our zone?",
        "Need information on booking the community hall for an event.",
        "General feedback about the user interface of the grievance portal."
    ]
    for text in other_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Other', 'Priority_Label': 'Low'})
        
    # Prohibited RTI
    rti_texts = [
        "Please provide information under the RTI Act 2005 regarding road construction budget.",
        "Requesting certified copies of land surveys under Right to Information Act.",
        "File an RTI application for details of expenditure on public park.",
        "Seeking status of my RTI query filed on 10th January.",
        "RTI request for list of employees working in electricity office.",
        "Provide copy of tender documents under RTI act.",
        "I want to file an appeal under the Right to Information Act for delayed response.",
        "Seeking information under Section 6 of RTI Act regarding municipal expenses."
    ]
    for text in rti_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_RTI', 'Priority_Label': 'Low'})
        
    # Prohibited Court
    court_texts = [
        "This case is currently sub-judice in the high court.",
        "Pending court dispute regarding property eviction.",
        "The matter is under trial in the district civil court.",
        "Seeking intervention in a sub judice matter pending before the judge.",
        "My legal dispute is scheduled for hearing next week in court.",
        "Court stay order was issued on this property, please enforce it.",
        "Civil suit regarding property boundaries is currently active in session court.",
        "The case is subjudice, we are awaiting the court's final verdict."
    ]
    for text in court_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_Court', 'Priority_Label': 'Low'})
        
    # Prohibited Family
    family_texts = [
        "My brother has taken all my ancestral property and refuses to share.",
        "Domestic dispute with spouse regarding monthly maintenance.",
        "Family fight over land division between uncles.",
        "Divorce case and custody battle details.",
        "Personal family conflict regarding wedding expenses.",
        "Property partition dispute within the family members.",
        "My relatives are harassing me over a private gold dispute.",
        "Personal dispute between husband and wife over household issues."
    ]
    for text in family_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_Family', 'Priority_Label': 'Low'})
        
    # Prohibited Religion
    religion_texts = [
        "Dispute regarding construction of temple near local mosque.",
        "Complaint against religious conversion activities in the area.",
        "Request to remove religious flag from public junction.",
        "Conflict between two religious groups over festival procession route.",
        "Illegal building of a shrine on the footpath.",
        "Loudspeakers from religious place causing disturbance at night.",
        "Hate speech targeting a specific religious community.",
        "Desecration of a local religious monument."
    ]
    for text in religion_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_Religion', 'Priority_Label': 'Low'})
        
    # Prohibited Service
    service_texts = [
        "I am a government clerk and my promotion has been delayed by two years.",
        "Request for transfer from Delhi to Chennai office in customs department.",
        "My pension benefits have not been credited since my retirement from railways.",
        "Service matter complaint regarding salary deduction by senior officer.",
        "Departmental inquiry against me should be cancelled.",
        "Request for reinstatement in service after suspension.",
        "Discrepancy in my gratuity payment from government department.",
        "Seeking regularisation of temporary government employment."
    ]
    for text in service_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_Service', 'Priority_Label': 'Low'})
        
    # Prohibited National
    national_texts = [
        "Seditious slogans are being written on the walls of university.",
        "Activities threatening national security and sovereignty.",
        "Anti-national elements are conspiring near the border area.",
        "Sedition and threat to national integrity reported online.",
        "Illegal spying and espionage against the state.",
        "Conspiracy to disrupt national integrity and peace.",
        "Funding of illegal activities targeting national security.",
        "Separatist group holding meeting in the locality."
    ]
    for text in national_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_National', 'Priority_Label': 'Low'})
        
    # Prohibited Caste / SC-ST Matters
    caste_texts = [
        "Caste-based discrimination against SC/ST students in the government school.",
        "Dalit family denied entry into the village temple due to caste.",
        "Upper caste people are practicing untouchability in our village.",
        "Complaint regarding caste atrocity and violence against scheduled caste family.",
        "Scheduled tribe community members are being harassed by dominant caste groups.",
        "Caste slur and abuse used against a dalit worker by the supervisor.",
        "OBC reservation quota not being implemented properly in recruitment.",
        "Caste discrimination in government office, SC employees treated differently.",
        "Seeking action under SC/ST Prevention of Atrocities Act for caste violence.",
        "Caste certificate verification is being delayed intentionally for scheduled tribe applicants."
    ]
    for text in caste_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_Caste', 'Priority_Label': 'Low'})
    
    # Prohibited Suggestions / Policy Advice
    suggestion_texts = [
        "The government should build more parks in residential areas.",
        "Please reduce GST rates on essential food items.",
        "I suggest the government introduce free WiFi in all public spaces.",
        "Why not build a metro rail line connecting the suburbs to downtown?",
        "The government should increase the budget for rural healthcare.",
        "Policy suggestion: introduce cashback incentives for digital payments.",
        "I advise the government to plant more trees along national highways.",
        "The government must introduce stricter pollution control norms.",
        "Request new policy for solar panel subsidies in rural homes.",
        "My suggestion is to reduce income tax for middle class families."
    ]
    for text in suggestion_texts:
        synthetic_samples.append({'Complaint_Text': text, 'Mapped_Category': 'Prohibited_Suggestion', 'Priority_Label': 'Low'})
        
    # Append synthetic samples to dataframe
    df_synthetic = pd.DataFrame(synthetic_samples)
    df_extended = pd.concat([
        pd.DataFrame({
            'Complaint_Text': df['Complaint_Text'],
            'Mapped_Category': df['Mapped_Category'],
            'Priority_Label': df['Priority_Label']
        }),
        df_synthetic
    ], ignore_index=True)
    
    print(f"✓ Added {len(df_synthetic)} synthetic samples")
    print(f"✓ Total training dataset size: {len(df_extended)}")
    
    # Calculate Severity Target Scores
    print("\n[2/7] Generating severity target labels...")
    df_extended['Severity_Target'] = df_extended.apply(
        lambda row: calculate_target_severity(row['Complaint_Text'], row['Mapped_Category']), 
        axis=1
    )
    print(f"✓ Generated {len(df_extended)} severity targets (Range: {df_extended['Severity_Target'].min():.2f} - {df_extended['Severity_Target'].max():.2f})")
    
    # Load SentenceTransformer wrapper
    print("\n[3/7] Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
    wrapper = SentenceTransformerWrapper('all-MiniLM-L6-v2')
    
    # Extract embeddings
    print("\n[4/7] Extracting embeddings (this might take a minute)...")
    embeddings = wrapper.transform(df_extended['Complaint_Text'])
    print(f"✓ Extracted embeddings shape: {embeddings.shape}")
    
    # Train/Test Split for Category Classifier
    X = embeddings
    y_cat = df_extended['Mapped_Category']
    
    X_train_cat, X_test_cat, y_train_cat, y_test_cat = train_test_split(
        X, y_cat, test_size=0.2, random_state=42, stratify=y_cat
    )
    
    # Train Category Classifier
    print("\n[5/7] Training Category Classifier (Logistic Regression)...")
    category_model = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
    category_model.fit(X_train_cat, y_train_cat)
    
    y_pred_cat = category_model.predict(X_test_cat)
    cat_acc = accuracy_score(y_test_cat, y_pred_cat)
    print(f"✓ Category Classification Accuracy: {cat_acc:.2%}")
    
    # Filter out prohibited samples for priority and severity model training
    admissible_mask = ~df_extended['Mapped_Category'].str.startswith('Prohibited_')
    X_admissible = X[admissible_mask]
    y_pri_admissible = df_extended.loc[admissible_mask, 'Priority_Label']
    y_sev_admissible = df_extended.loc[admissible_mask, 'Severity_Target']
    
    # Split for priority evaluation
    X_train_pri, X_test_pri, y_train_pri, y_test_pri = train_test_split(
        X_admissible, y_pri_admissible, test_size=0.2, random_state=42, stratify=y_pri_admissible
    )
    
    # Train Priority Classifier
    print("\n[6/7] Training Priority Classifier (Logistic Regression)...")
    priority_model = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
    priority_model.fit(X_train_pri, y_train_pri)
    
    y_pred_pri = priority_model.predict(X_test_pri)
    pri_acc = accuracy_score(y_test_pri, y_pred_pri)
    print(f"✓ Priority Classification Accuracy: {pri_acc:.2%}")
    
    # Split and Train Severity Regressor (Random Forest Regressor)
    X_train_sev, X_test_sev, y_train_sev, y_test_sev = train_test_split(
        X_admissible, y_sev_admissible, test_size=0.2, random_state=42
    )
    
    print("\n[7/7] Training Severity Regressor (Random Forest Regressor)...")
    severity_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    severity_model.fit(X_train_sev, y_train_sev)
    
    y_pred_sev = severity_model.predict(X_test_sev)
    sev_mae = mean_absolute_error(y_test_sev, y_pred_sev)
    sev_r2 = r2_score(y_test_sev, y_pred_sev)
    print(f"✓ Severity Model Mean Absolute Error (MAE): {sev_mae:.4f}")
    print(f"✓ Severity Model R-squared Score: {sev_r2:.4f}")
    
    # Save models
    print("\n" + "=" * 60)
    print("Saving trained models...")
    print("=" * 60)
    
    # Save the wrapper as tfidf_vectorizer.pkl to maintain compatibility
    with open('tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(wrapper, f)
    print("✓ Saved wrapper: tfidf_vectorizer.pkl")
    
    with open('category_classifier.pkl', 'wb') as f:
        pickle.dump(category_model, f)
    print("✓ Saved category model: category_classifier.pkl")
    
    with open('priority_classifier.pkl', 'wb') as f:
        pickle.dump(priority_model, f)
    print("✓ Saved priority model: priority_classifier.pkl")
    
    with open('severity_model.pkl', 'wb') as f:
        pickle.dump(severity_model, f)
    print("✓ Saved severity model: severity_model.pkl")
    
    print("\n" + "=" * 60)
    print("✅ MODEL TRAINING COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    train_models()

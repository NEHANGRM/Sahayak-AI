import os
import json
import pickle
import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, Float, Boolean, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

import numpy as np
import utils

# Initialize FastAPI App
app = FastAPI(title="Sahayak AI - Civic Grievance Backend", version="1.0.0")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Configuration
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sahayak_ai.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Model for Complaint
class Complaint(Base):
    __tablename__ = 'complaints'
    
    id = Column(String, primary_key=True)
    complaint_text = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)
    admissible = Column(Boolean, default=True)
    rejection_reason = Column(String, nullable=True)
    category = Column(String, nullable=False)
    raw_predicted_category = Column(String, nullable=False)
    confidence_score = Column(Float, default=1.0)
    severity_score = Column(Float, default=0.0)
    severity_reason = Column(Text, nullable=True)
    severity_label = Column(String, default="Low")
    public_impact_score = Column(Float, default=0.0)
    vulnerability_score = Column(Float, default=0.0)
    urgency_score = Column(Float, default=0.0)
    duplicate_escalation_score = Column(Float, default=0.0)
    sentiment_score = Column(Float, default=0.0)
    priority_score = Column(Float, default=0.0) # Base priority score
    final_priority_score = Column(Float, default=0.0) # Base + LLM adjustment
    priority_label = Column(String, default="Low")
    department = Column(String, nullable=False)
    explanation = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    cluster_id = Column(Integer, nullable=True)
    similarity = Column(Float, default=0.0)
    lead_id = Column(String, nullable=True)
    status = Column(String, default="Open")
    officer_override = Column(String, nullable=True)
    override_reason = Column(Text, nullable=True)
    
    # JSON-serialized strings
    resolution_history = Column(Text, default="[]")
    escalation_history = Column(Text, default="[]")
    structured_json = Column(Text, default="{}")
    ner_breakdown = Column(Text, default="{}")
    
    # LLM Governance Review Columns
    llm_reviewed = Column(Boolean, default=False)
    llm_adjustment = Column(Float, default=0.0)
    llm_reasoning = Column(Text, nullable=True)
    llm_risk_summary = Column(Text, nullable=True)
    llm_public_safety_risk = Column(String, default="Medium")
    llm_vulnerable_population_risk = Column(String, default="Medium")
    llm_infrastructure_risk = Column(String, default="Medium")
    llm_trigger_reasons = Column(Text, default="[]")

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class TriageRequest(BaseModel):
    complaint_text: str

class OverrideRequest(BaseModel):
    priority_label: str
    reason: str

class ResolveRequest(BaseModel):
    notes: str

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Global ML Models Cache
VECTORIZER = None
CATEGORY_MODEL = None
SEVERITY_MODEL = None

def load_ml_models():
    global VECTORIZER, CATEGORY_MODEL, SEVERITY_MODEL
    try:
        with open('tfidf_vectorizer.pkl', 'rb') as f:
            VECTORIZER = pickle.load(f)
        with open('category_classifier.pkl', 'rb') as f:
            CATEGORY_MODEL = pickle.load(f)
        with open('severity_model.pkl', 'rb') as f:
            SEVERITY_MODEL = pickle.load(f)
        print("✅ Backend loaded ML models successfully.")
    except Exception as e:
        print(f"❌ Backend failed to load ML models: {e}. Running fallback vectors if needed.")

# Load models on startup
load_ml_models()

def to_dict(c: Complaint) -> Dict[str, Any]:
    try:
        dt = datetime.datetime.strptime(c.timestamp, "%Y-%m-%d %H:%M:%S")
        elapsed = datetime.datetime.now() - dt
        age_days = max(0.0, elapsed.total_seconds() / (24 * 3600))
    except Exception:
        age_days = 0.0
        
    if age_days < 0.04:
        relative_time = "Just now"
    elif age_days < 1.0:
        relative_time = "Today"
    elif age_days < 2.0:
        relative_time = "1 day ago"
    else:
        relative_time = f"{int(age_days)} days ago"
        
    # Apply aging boost only if open and admissible
    if c.admissible and c.status not in ["Resolved", "Rejected"]:
        base_label = c.priority_label or "Low"
        if base_label in ["Critical", "High"]:
            aging_boost = min(0.45, age_days * 0.45)
        elif base_label == "Medium":
            aging_boost = min(0.45, age_days * (0.45 / 5.0))
        else:
            aging_boost = min(0.45, age_days * (0.45 / 7.0))
    else:
        aging_boost = 0.0
        
    return {
        "id": c.id,
        "complaint_text": c.complaint_text,
        "timestamp": c.timestamp,
        "admissible": c.admissible,
        "rejection_reason": c.rejection_reason,
        "category": c.category,
        "raw_predicted_category": c.raw_predicted_category,
        "confidence_score": c.confidence_score,
        "severity_score": c.severity_score,
        "severity_reason": c.severity_reason,
        "severity_label": c.severity_label,
        "public_impact_score": c.public_impact_score,
        "vulnerability_score": c.vulnerability_score,
        "urgency_score": c.urgency_score,
        "duplicate_escalation_score": c.duplicate_escalation_score,
        "sentiment_score": c.sentiment_score,
        "priority_score": c.priority_score,
        "final_priority_score": c.final_priority_score,
        "priority_label": c.priority_label,
        "department": c.department,
        "explanation": c.explanation,
        "is_duplicate": c.is_duplicate,
        "cluster_id": c.cluster_id,
        "similarity": c.similarity,
        "lead_id": c.lead_id,
        "status": c.status,
        "officer_override": c.officer_override,
        "override_reason": c.override_reason,
        "resolution_history": json.loads(c.resolution_history or "[]"),
        "escalation_history": json.loads(c.escalation_history or "[]"),
        "structured_json": json.loads(c.structured_json or "{}"),
        "ner_breakdown": json.loads(c.ner_breakdown or "{}"),
        "llm_reviewed": c.llm_reviewed,
        "llm_adjustment": c.llm_adjustment,
        "llm_reasoning": c.llm_reasoning,
        "llm_risk_summary": c.llm_risk_summary,
        "llm_public_safety_risk": c.llm_public_safety_risk,
        "llm_vulnerable_population_risk": c.llm_vulnerable_population_risk,
        "llm_infrastructure_risk": c.llm_infrastructure_risk,
        "llm_trigger_reasons": json.loads(c.llm_trigger_reasons or "[]"),
        "age_days": round(age_days, 1),
        "aging_boost": round(aging_boost, 2),
        "relative_time": relative_time,
    }

# Seed database with initial complaints if table is empty
# Seed database with initial complaints if table is empty
def seed_database(db: Session):
    # Check if there are any citizen complaints (CMP-2006 or higher)
    citizen_exists = db.query(Complaint).filter(Complaint.id > "CMP-2005").count() > 0
    if citizen_exists:
        print("ℹ️ Citizen complaints exist. Skipping database wipe and seed.")
        return
        
    # Otherwise, wipe the database and re-seed the 5 complaints
    db.query(Complaint).delete()
    db.commit()
    print("🧹 Wiped all existing complaints from the database for re-seeding.")
    
    seeds = [
        {
            'id': 'CMP-2001',
            'complaint_text': "The streetlight on MG Road is not working since yesterday, making the street completely dark at night.",
            'timestamp': "2026-06-16 09:00:00"
        },
        {
            'id': 'CMP-2002',
            'complaint_text': "Low water pressure and muddy water supply in Sector 4 residential colony for the last 3 days.",
            'timestamp': "2026-06-16 10:15:00"
        },
        {
            'id': 'CMP-2003',
            'complaint_text': "Sewage water is overflowing from a broken pipeline on Anna Salai Road, causing massive public health hazard and foul smell.",
            'timestamp': "2026-06-16 11:30:00"
        },
        {
            'id': 'CMP-2004',
            'complaint_text': "Major bridge structure crack detected on the busy subway road, causing severe risk of bridge collapse and blocking traffic.",
            'timestamp': "2026-06-16 12:45:00"
        },
        {
            'id': 'CMP-2005',
            'complaint_text': "Critical gas leak reported near St. Mary's Primary School. Urgent evacuation of the area is needed to prevent explosion.",
            'timestamp': "2026-06-16 14:00:00"
        }
    ]
    
    for seed in seeds:
        text = seed['complaint_text']
        comp_id = seed['id']
        timestamp = seed['timestamp']
        
        # 1. Run admissibility check
        is_admissible, rejection_reason, predicted_category, confidence_score = utils.check_admissibility(
            text, 
            CATEGORY_MODEL, 
            VECTORIZER
        )
        
        # Default values
        severity_score = 0.0
        severity_reason = "Not evaluated."
        severity_label = "Low"
        public_impact_score = 0.0
        vulnerability_score = 0.0
        urgency_score = 0.0
        duplicate_escalation_score = 0.0
        sentiment_score = 0.0
        priority_score = 0.0
        final_priority_score = 0.0
        priority_label = "Low"
        department = "Not Routed"
        explanation = ""
        is_duplicate = False
        cluster_id = None
        similarity = 0.0
        lead_id = None
        ner_details = {"location": None, "infrastructure": None, "all_entities": [], "extracted_entities": {}}
        risk_kws = []
        similar_cases = []
        
        # LLM review outputs
        llm_reviewed = False
        llm_adjustment = 0.0
        llm_reasoning = None
        llm_risk_summary = None
        llm_public_safety_risk = "Medium"
        llm_vulnerable_population_risk = "Medium"
        llm_infrastructure_risk = "Medium"
        llm_trigger_reasons = []
        suggested_response = ""
        suggested_action = ""
        
        if is_admissible:
            department = utils.route_to_department(predicted_category)
            sentiment_score = utils.get_sentiment_score(text)
            
            # Extract NER details and risk keywords
            ner_details = utils.extract_entities_and_details(text, predicted_category)
            risk_kws = utils.extract_risk_keywords(text)
            
            # Predict Severity
            severity_details = utils.predict_severity(
                text, 
                predicted_category, 
                SEVERITY_MODEL, 
                VECTORIZER
            )
            severity_score = severity_details["severity"]
            severity_reason = severity_details["reason"]
            severity_label = utils.get_severity_level(severity_score)
            
            temp_json = {
                "location": ner_details["location"],
                "infrastructure": ner_details["infrastructure"]
            }
            public_impact_score = utils.calculate_public_impact(text, predicted_category, temp_json)
            vulnerability_score = utils.calculate_vulnerability(text, predicted_category, temp_json)
            urgency_score = utils.calculate_urgency(text, predicted_category, severity_score, temp_json)
            
            # Seed complaints have no initial duplicates
            duplicate_escalation_score = 0.0
            
            # Base Governance Priority Score
            priority_score = utils.calculate_priority_score(
                severity_score, 
                public_impact_score, 
                urgency_score, 
                vulnerability_score, 
                duplicate_escalation_score
            )
            
            # Check LLM review triggers
            complaint_data = {
                "complaint_text": text,
                "confidence_score": confidence_score,
                "severity_score": severity_score,
                "public_impact_score": public_impact_score,
                "urgency_score": urgency_score,
                "vulnerability_score": vulnerability_score,
                "priority_score": priority_score
            }
            
            llm_trigger_reasons = utils.check_llm_triggers(complaint_data)
            
            if len(llm_trigger_reasons) > 0:
                llm_reviewed = True
                try:
                    client = utils.get_llm_client()
                    review_result = client.review_complaint(complaint_data, similar_cases)
                    llm_adjustment = review_result.get("recommended_adjustment", 0.0)
                    llm_reasoning = review_result.get("reasoning", "LLM review completed.")
                    llm_risk_summary = review_result.get("risk_summary", "")
                    llm_public_safety_risk = review_result.get("public_safety_risk", "Medium")
                    llm_vulnerable_population_risk = review_result.get("vulnerable_population_risk", "Medium")
                    llm_infrastructure_risk = review_result.get("infrastructure_risk", "Medium")
                    suggested_response = review_result.get("suggested_response", "")
                    suggested_action = review_result.get("suggested_action", "")
                except Exception as e:
                    print(f"Error calling LLM Client: {e}")
                    llm_reviewed = False
                    llm_adjustment = 0.0
                    llm_reasoning = f"Failed to run LLM review: {str(e)}"
                    
            # Fallback to dynamic LLM suggestions if empty or LLM was not triggered
            if not suggested_response:
                suggested_response, suggested_action = utils.generate_suggestions_with_llm(text, predicted_category)
                
            final_priority_score = round(min(1.0, max(0.0, priority_score + llm_adjustment)), 3)
            priority_label = utils.get_priority_label(final_priority_score)
            
            explanation = utils.generate_explanation(
                severity_score,
                public_impact_score,
                urgency_score,
                vulnerability_score,
                duplicate_escalation_score,
                priority_label
            )
            
            if llm_reviewed:
                explanation += f" (LLM adjusted: {llm_adjustment:+.2f} because: {llm_reasoning})"
                
        # Set default histories
        resolution_history = [
            {"status": "Registered", "date": timestamp, "notes": "Registered automatically." if is_admissible else f"Rejected: {rejection_reason}"}
        ]
        escalation_history = []
        if is_admissible:
            resolution_history.append({"status": "Assigned", "date": timestamp, "notes": f"Assigned to {department}."})
            escalation_history.append({"level": "L1 - Junior Inspector", "date": timestamp})
            
        structured_json = {
            "category": predicted_category if is_admissible else "Other",
            "location": ner_details.get("location"),
            "infrastructure": ner_details.get("infrastructure"),
            "risk_keywords": risk_kws,
            "entities": ner_details.get("all_entities", []),
            "severity": {
                "score": severity_score,
                "level": severity_label,
                "reason": severity_reason
            },
            "public_impact_score": public_impact_score,
            "vulnerability_score": vulnerability_score,
            "urgency_score": urgency_score,
            "duplicate_escalation_score": duplicate_escalation_score,
            "priority": {
                "score": final_priority_score,
                "level": priority_label
            },
            "suggested_response": suggested_response,
            "suggested_action": suggested_action
        }
        
        comp = Complaint(
            id=comp_id,
            complaint_text=text,
            timestamp=timestamp,
            admissible=is_admissible,
            rejection_reason=rejection_reason,
            category=predicted_category if is_admissible else "Other",
            raw_predicted_category=predicted_category,
            confidence_score=confidence_score,
            severity_score=severity_score,
            severity_reason=severity_reason,
            severity_label=severity_label,
            public_impact_score=public_impact_score,
            vulnerability_score=vulnerability_score,
            urgency_score=urgency_score,
            duplicate_escalation_score=duplicate_escalation_score,
            sentiment_score=sentiment_score,
            priority_score=priority_score,
            final_priority_score=final_priority_score,
            priority_label=priority_label,
            department=department,
            explanation=explanation,
            is_duplicate=is_duplicate,
            cluster_id=cluster_id,
            similarity=similarity,
            lead_id=lead_id,
            status="Open" if is_admissible else "Rejected",
            officer_override=None,
            override_reason=None,
            resolution_history=json.dumps(resolution_history),
            escalation_history=json.dumps(escalation_history),
            structured_json=json.dumps(structured_json),
            ner_breakdown=json.dumps(ner_details.get("extracted_entities", {})),
            
            # LLM review fields
            llm_reviewed=llm_reviewed,
            llm_adjustment=llm_adjustment,
            llm_reasoning=llm_reasoning,
            llm_risk_summary=llm_risk_summary,
            llm_public_safety_risk=llm_public_safety_risk,
            llm_vulnerable_population_risk=llm_vulnerable_population_risk,
            llm_infrastructure_risk=llm_infrastructure_risk,
            llm_trigger_reasons=json.dumps(llm_trigger_reasons)
        )
        db.add(comp)
    db.commit()
    print("✅ Seed complaints triaged and inserted successfully.")

# Run seeding and cleanups
db = SessionLocal()
seed_database(db)
try:
    deleted = db.query(Complaint).filter(Complaint.id.in_(["CMP-2006", "CMP-2007"])).delete(synchronize_session=False)
    db.commit()
    print(f"🧹 Database cleanup: deleted {deleted} complaints (CMP-2006, CMP-2007)")
except Exception as e:
    print(f"Error during db cleanup: {e}")
db.close()


@app.post("/triage")
def triage_complaint(req: TriageRequest, db: Session = Depends(get_db)):
    text = req.complaint_text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Complaint text cannot be empty.")
        
    # Generate ID
    existing_count = db.query(Complaint).count()
    # Find next sequence suffix safely
    next_num = 2001 + existing_count
    # double check uniqueness
    while db.query(Complaint).filter(Complaint.id == f"CMP-{next_num}").first() is not None:
        next_num += 1
    comp_id = f"CMP-{next_num}"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Run admissibility check
    is_admissible, rejection_reason, predicted_category, confidence_score = utils.check_admissibility(
        text, 
        CATEGORY_MODEL, 
        VECTORIZER
    )
    
    # Pre-set default values in case of rejection
    severity_score = 0.0
    severity_reason = "Not evaluated due to rejection policy."
    severity_label = "Low"
    public_impact_score = 0.0
    vulnerability_score = 0.0
    urgency_score = 0.0
    duplicate_escalation_score = 0.0
    sentiment_score = 0.0
    priority_score = 0.0
    final_priority_score = 0.0
    priority_label = "Low"
    department = "Not Routed"
    explanation = f"Complaint rejected. Reason: {rejection_reason}"
    is_duplicate = False
    cluster_id = None
    similarity = 0.0
    lead_id = None
    
    ner_details = {"location": None, "infrastructure": None, "all_entities": [], "extracted_entities": {}}
    risk_kws = []
    similar_cases = []
    
    # LLM review outputs
    llm_reviewed = False
    llm_adjustment = 0.0
    llm_reasoning = None
    llm_risk_summary = None
    llm_public_safety_risk = "Medium"
    llm_vulnerable_population_risk = "Medium"
    llm_infrastructure_risk = "Medium"
    llm_trigger_reasons = []
    suggested_response = ""
    suggested_action = ""
    
    if is_admissible:
        department = utils.route_to_department(predicted_category)
        sentiment_score = utils.get_sentiment_score(text)
        
        # Extract NER details and risk keywords
        ner_details = utils.extract_entities_and_details(text, predicted_category)
        risk_kws = utils.extract_risk_keywords(text)
        
        # Predict Severity
        severity_details = utils.predict_severity(
            text, 
            predicted_category, 
            SEVERITY_MODEL, 
            VECTORIZER
        )
        severity_score = severity_details["severity"]
        severity_reason = severity_details["reason"]
        severity_label = utils.get_severity_level(severity_score)
        
        # Temp structured JSON for calculators
        temp_json = {
            "location": ner_details["location"],
            "infrastructure": ner_details["infrastructure"]
        }
        public_impact_score = utils.calculate_public_impact(text, predicted_category, temp_json)
        vulnerability_score = utils.calculate_vulnerability(text, predicted_category, temp_json)
        urgency_score = utils.calculate_urgency(text, predicted_category, severity_score, temp_json)
        
        # Fetch all open admissible complaints from DB to run duplicate detection
        open_db_complaints = db.query(Complaint).filter(
            Complaint.admissible == True,
            Complaint.status != "Resolved"
        ).all()
        existing_list = [to_dict(c) for c in open_db_complaints]
        
        # Duplicate detection (location-aware: same issue + same area only)
        new_location = ner_details.get("location", "")
        is_duplicate, cluster_idx, similarity = utils.detect_duplicate(
            text, 
            existing_list, 
            vectorizer=VECTORIZER,
            threshold=0.7,
            new_location=new_location,
            new_category=predicted_category
        )
        if is_duplicate and cluster_idx is not None and cluster_idx < len(existing_list):
            candidate = existing_list[cluster_idx]
            lead_id = candidate.get('lead_id') or candidate['id']
            # Count existing complaints in this cluster to determine correct escalation
            cluster_count = sum(1 for c in existing_list if c.get('lead_id') == lead_id or c.get('id') == lead_id)
            total_count = cluster_count + 1
            if total_count <= 1:
                duplicate_escalation_score = 0.0
            elif total_count == 2:
                duplicate_escalation_score = 0.60
            elif total_count == 3:
                duplicate_escalation_score = 0.85
            else:
                duplicate_escalation_score = 1.00
            
            # Incorporate similarity factor (80/20 blend)
            duplicate_escalation_score = round(min(1.0, max(0.0, duplicate_escalation_score * 0.8 + similarity * 0.2)), 2)
        else:
            lead_id = None
            duplicate_escalation_score = 0.0
        
        # RAG Context Retrieval
        similar_cases = utils.search_similar_complaints(
            text,
            existing_list,
            VECTORIZER,
            k=3
        )
        
        # Base Governance Priority Score
        priority_score = utils.calculate_priority_score(
            severity_score, 
            public_impact_score, 
            urgency_score, 
            vulnerability_score, 
            duplicate_escalation_score
        )
        
        # Check LLM review triggers
        complaint_data = {
            "complaint_text": text,
            "confidence_score": confidence_score,
            "severity_score": severity_score,
            "public_impact_score": public_impact_score,
            "urgency_score": urgency_score,
            "vulnerability_score": vulnerability_score,
            "priority_score": priority_score
        }
        
        llm_trigger_reasons = utils.check_llm_triggers(complaint_data)
        
        if len(llm_trigger_reasons) > 0:
            llm_reviewed = True
            try:
                client = utils.get_llm_client()
                review_result = client.review_complaint(complaint_data, similar_cases)
                llm_adjustment = review_result.get("recommended_adjustment", 0.0)
                llm_reasoning = review_result.get("reasoning", "LLM review completed.")
                llm_risk_summary = review_result.get("risk_summary", "")
                llm_public_safety_risk = review_result.get("public_safety_risk", "Medium")
                llm_vulnerable_population_risk = review_result.get("vulnerable_population_risk", "Medium")
                llm_infrastructure_risk = review_result.get("infrastructure_risk", "Medium")
                suggested_response = review_result.get("suggested_response", "")
                suggested_action = review_result.get("suggested_action", "")
            except Exception as e:
                print(f"Error calling LLM Client: {e}")
                llm_reviewed = False
                llm_adjustment = 0.0
                llm_reasoning = f"Failed to run LLM review: {str(e)}"
                
        # Fallback to dynamic LLM suggestions if empty or LLM was not triggered
        if not suggested_response:
            suggested_response, suggested_action = utils.generate_suggestions_with_llm(text, predicted_category)
            
        final_priority_score = round(min(1.0, max(0.0, priority_score + llm_adjustment)), 3)
        priority_label = utils.get_priority_label(final_priority_score)
        
        explanation = utils.generate_explanation(
            severity_score,
            public_impact_score,
            urgency_score,
            vulnerability_score,
            duplicate_escalation_score,
            priority_label
        )
        
        if llm_reviewed:
            explanation += f" (LLM adjusted: {llm_adjustment:+.2f} because: {llm_reasoning})"
            
    # Set default histories
    resolution_history = [
        {"status": "Registered", "date": timestamp, "notes": "Registered automatically." if is_admissible else f"Rejected: {rejection_reason}"}
    ]
    escalation_history = []
    if is_admissible:
        resolution_history.append({"status": "Assigned", "date": timestamp, "notes": f"Assigned to {department}."})
        escalation_history.append({"level": "L1 - Junior Inspector", "date": timestamp})
        
    structured_json = {
        "category": predicted_category if is_admissible else "Other",
        "location": ner_details.get("location"),
        "infrastructure": ner_details.get("infrastructure"),
        "risk_keywords": risk_kws,
        "entities": ner_details.get("all_entities", []),
        "severity": {
            "score": severity_score,
            "level": severity_label,
            "reason": severity_reason
        },
        "public_impact_score": public_impact_score,
        "vulnerability_score": vulnerability_score,
        "urgency_score": urgency_score,
        "duplicate_escalation_score": duplicate_escalation_score,
        "priority": {
            "score": final_priority_score,
            "level": priority_label
        },
        "suggested_response": suggested_response,
        "suggested_action": suggested_action
    }
    
    comp = Complaint(
        id=comp_id,
        complaint_text=text,
        timestamp=timestamp,
        admissible=is_admissible,
        rejection_reason=rejection_reason,
        category=predicted_category if is_admissible else "Other",
        raw_predicted_category=predicted_category,
        confidence_score=confidence_score,
        severity_score=severity_score,
        severity_reason=severity_reason,
        severity_label=severity_label,
        public_impact_score=public_impact_score,
        vulnerability_score=vulnerability_score,
        urgency_score=urgency_score,
        duplicate_escalation_score=duplicate_escalation_score,
        sentiment_score=sentiment_score,
        priority_score=priority_score,
        final_priority_score=final_priority_score,
        priority_label=priority_label,
        department=department,
        explanation=explanation,
        is_duplicate=is_duplicate,
        cluster_id=cluster_id,
        similarity=similarity,
        lead_id=lead_id,
        status="Open" if is_admissible else "Rejected",
        officer_override=None,
        override_reason=None,
        resolution_history=json.dumps(resolution_history),
        escalation_history=json.dumps(escalation_history),
        structured_json=json.dumps(structured_json),
        ner_breakdown=json.dumps(ner_details.get("extracted_entities", {})),
        
        # LLM review fields
        llm_reviewed=llm_reviewed,
        llm_adjustment=llm_adjustment,
        llm_reasoning=llm_reasoning,
        llm_risk_summary=llm_risk_summary,
        llm_public_safety_risk=llm_public_safety_risk,
        llm_vulnerable_population_risk=llm_vulnerable_population_risk,
        llm_infrastructure_risk=llm_infrastructure_risk,
        llm_trigger_reasons=json.dumps(llm_trigger_reasons)
    )
    
    db.add(comp)
    db.commit()
    db.refresh(comp)
    
    return to_dict(comp)

@app.get("/complaints")
def get_complaints(db: Session = Depends(get_db)):
    """
    Get active triage queue.
    Groups duplicate complaints by lead_id, so only one lead card is returned, 
    carrying lists of duplicate references.
    Also recalculates duplicate escalation and priority dynamically.
    """
    admissible_comps = db.query(Complaint).filter(
        Complaint.admissible == True,
        Complaint.status != "Resolved",
        Complaint.status != "Rejected"
    ).all()
    
    if not admissible_comps:
        return []
        
    # Group by lead_id or ID
    groups = {}
    for c in admissible_comps:
        lid = c.lead_id or c.id
        if lid not in groups:
            groups[lid] = []
        groups[lid].append(c)
        
    grouped_result = []
    for lid, group_list in groups.items():
        # Sort by text length descending (longest first to get the most detailed complaint), then by timestamp ascending (oldest first)
        sorted_group = sorted(group_list, key=lambda x: (-len(x.complaint_text or ""), x.timestamp))
        lead = sorted_group[0]
        lead_dict = to_dict(lead)
        
        # Recalculate duplicate escalation dynamically for the lead
        dup_count = len(sorted_group) - 1
        if dup_count == 0:
            dup_esc = 0.0
        elif dup_count == 1:
            dup_esc = 0.60
        elif dup_count == 2:
            dup_esc = 0.85
        else:
            dup_esc = 1.00
            
        lead_dict['duplicate_count'] = dup_count
        lead_dict['duplicate_escalation_score'] = dup_esc
        
        # Recalculate base priority score with dynamic dup_esc
        base_pri = utils.calculate_priority_score(
            lead_dict['severity_score'],
            lead_dict['public_impact_score'],
            lead_dict['urgency_score'],
            lead_dict['vulnerability_score'],
            dup_esc
        )
        lead_dict['priority_score'] = base_pri
        
        # Determine tiered aging boost based on base priority label
        base_label = utils.get_priority_label(base_pri)
        age_days = lead_dict.get('age_days', 0.0)
        
        if base_label in ["Critical", "High"]:
            aging_boost = min(0.45, age_days * 0.45)
        elif base_label == "Medium":
            aging_boost = min(0.45, age_days * (0.45 / 5.0))
        else:
            aging_boost = min(0.45, age_days * (0.45 / 7.0))
            
        lead_dict['aging_boost'] = round(aging_boost, 2)
        
        llm_adj = lead_dict['llm_adjustment'] if lead_dict['llm_reviewed'] else 0.0
        lead_dict['final_priority_score'] = round(min(1.0, max(0.0, base_pri + llm_adj + aging_boost)), 3)
        lead_dict['priority_label'] = utils.get_priority_label(lead_dict['final_priority_score'])
        
        lead_dict['explanation'] = utils.generate_explanation(
            lead_dict['severity_score'],
            lead_dict['public_impact_score'],
            lead_dict['urgency_score'],
            lead_dict['vulnerability_score'],
            dup_esc,
            lead_dict['priority_label']
        )
        if lead_dict['llm_reviewed']:
            lead_dict['explanation'] += f" (LLM adjusted: {lead_dict['llm_adjustment']:+.2f} because: {lead_dict['llm_reasoning']})"
        if aging_boost > 0:
            lead_dict['explanation'] += f" (Aging Escalation: +{aging_boost:.2f} - registered {lead_dict['relative_time']})"
            
        # Ensure suggested_response and suggested_action are present in structured_json for UI display
        sj = lead_dict.get('structured_json', {})
        if not isinstance(sj, dict):
            sj = {}
        if 'suggested_response' not in sj or not sj['suggested_response']:
            rep, act = utils.generate_suggestions_with_llm(lead_dict['complaint_text'], lead_dict['category'])
            sj['suggested_response'] = rep
            sj['suggested_action'] = act
            lead_dict['structured_json'] = sj
            try:
                lead.structured_json = json.dumps(sj)
                db.commit()
            except Exception as db_err:
                print(f"Error saving dynamic suggestions to database: {db_err}")
                db.rollback()
            
        # Add duplicate details
        lead_dict['duplicate_reports'] = [to_dict(x) for x in sorted_group[1:]]
        grouped_result.append(lead_dict)
        
    # Sort active queue by final_priority_score descending
    grouped_result.sort(key=lambda x: x['final_priority_score'], reverse=True)
    return grouped_result

@app.get("/complaints/resolved")
def get_resolved_complaints(db: Session = Depends(get_db)):
    resolved = db.query(Complaint).filter(
        Complaint.status == "Resolved"
    ).all()
    # Convert and return sorted by timestamp descending
    res_dicts = [to_dict(c) for c in resolved]
    res_dicts.sort(key=lambda x: x['timestamp'], reverse=True)
    return res_dicts

@app.post("/complaints/{id}/resolve")
def resolve_complaint(id: str, req: ResolveRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Resolve all complaints in this cluster (the lead itself plus all duplicates)
    actual_lead_id = comp.lead_id or comp.id
    cluster_complaints = db.query(Complaint).filter(
        (Complaint.id == actual_lead_id) | (Complaint.lead_id == actual_lead_id)
    ).all()
    
    for c_item in cluster_complaints:
        if c_item.status != "Resolved":
            c_item.status = "Resolved"
            c_hist = json.loads(c_item.resolution_history or "[]")
            if c_item.id == id:
                c_hist.append({"status": "Resolved", "date": timestamp, "notes": req.notes})
            else:
                c_hist.append({"status": "Resolved", "date": timestamp, "notes": f"Resolved automatically with lead complaint {id}: {req.notes}"})
            c_item.resolution_history = json.dumps(c_hist)
        
    db.commit()
    return {"message": "Complaint and duplicates marked as resolved."}
 
@app.post("/complaints/{id}/override")
def override_priority(id: str, req: OverrideRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
        
    actual_lead_id = comp.lead_id or comp.id
    
    # Update override on all complaints in the same cluster
    cluster_complaints = db.query(Complaint).filter(
        (Complaint.id == actual_lead_id) | (Complaint.lead_id == actual_lead_id)
    ).all()
    
    for c_item in cluster_complaints:
        c_item.officer_override = req.priority_label
        c_item.override_reason = req.reason
        
    db.commit()
    return {"message": "Override applied successfully for complaint and duplicates."}

@app.get("/complaints/rejected")
def get_rejected_complaints(db: Session = Depends(get_db)):
    rejected = db.query(Complaint).filter(
        Complaint.admissible == False
    ).all()
    res_dicts = [to_dict(c) for c in rejected]
    res_dicts.sort(key=lambda x: x['timestamp'], reverse=True)
    return res_dicts

@app.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    admissible_count = db.query(Complaint).filter(Complaint.admissible == True, Complaint.status != "Resolved").count()
    rejected_count = db.query(Complaint).filter(Complaint.admissible == False).count()
    overrides_count = db.query(Complaint).filter(Complaint.officer_override != None).count()
    return {
        "active_count": admissible_count,
        "rejected_count": rejected_count,
        "overrides_count": overrides_count
    }

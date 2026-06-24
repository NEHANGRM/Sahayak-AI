import os
from dotenv import load_dotenv
load_dotenv()
import json
import pickle
import datetime
from fastapi import FastAPI, HTTPException, Depends, Query
import bcrypt
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
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {"connect_timeout": 10}
engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args
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
    status = Column(String, default="Submitted")
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

    # Officer Assignment
    assigned_officer_id = Column(String, nullable=True)
    
    # Multi-level Priority
    global_priority_score = Column(Float, default=0.0)
    officer_priority_score = Column(Float, default=0.0)
    
    # Submitted by (Citizen username)
    submitted_by = Column(String, nullable=True)

    # Lifecycle Management
    sla_deadline = Column(String, nullable=True)      # ISO timestamp
    sla_breached = Column(Boolean, default=False)
    accepted_at = Column(String, nullable=True)
    resolved_at = Column(String, nullable=True)
    closed_at = Column(String, nullable=True)
    escalation_level = Column(Integer, default=0)     # 0=normal, 1=senior, 2=dept head, 3=ministry

# Officer Model for Smart Routing
class Officer(Base):
    __tablename__ = 'officers'
    officer_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    ward = Column(String, nullable=False)
    designation = Column(String, default="Junior Inspector")
    email = Column(String, nullable=True)
    role = Column(String, default="officer")
    profile_pic = Column(Text, nullable=True)
    escalation_level = Column(Integer, default=0)

# Notification Model
class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)  # officer_id or "admin"
    message = Column(String, nullable=False)
    type = Column(String, default="info")
    timestamp = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)

# User Model for Authentication
class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)  # citizen, officer, admin
    officer_id = Column(String, nullable=True)  # Links to Officer if role=officer
    name = Column(String, nullable=False)

# Department Policy for Custom Priority Weights
class DepartmentPolicy(Base):
    __tablename__ = 'department_policies'
    id = Column(Integer, primary_key=True, autoincrement=True)
    department = Column(String, unique=True, nullable=False)
    severity_weight = Column(Float, default=0.30)
    impact_weight = Column(Float, default=0.25)
    urgency_weight = Column(Float, default=0.20)
    vulnerability_weight = Column(Float, default=0.15)
    duplicate_weight = Column(Float, default=0.10)

# Officer Feedback for Learning
class OfficerFeedback(Base):
    __tablename__ = 'officer_feedback'
    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String, nullable=False)
    officer_id = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    override_type = Column(String, nullable=False)
    system_value = Column(String, nullable=False)
    officer_value = Column(String, nullable=False)
    reason = Column(Text, nullable=False)

# Audit Log for Lifecycle Tracking
class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, autoincrement=True)
    complaint_id = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    action = Column(String, nullable=False)        # status_change, priority_override, severity_override, department_transfer, officer_reassignment, sla_breach, auto_escalation
    from_value = Column(String, nullable=True)
    to_value = Column(String, nullable=True)
    performed_by = Column(String, nullable=False)   # user_id or SYSTEM
    performer_role = Column(String, nullable=False)  # citizen, officer, admin, system
    notes = Column(Text, nullable=True)

@app.on_event("startup")
def startup_db_init():
    print("Initializing Database...")
    try:
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        # Migrations
        from sqlalchemy import text
        columns_to_add = [
            ("assigned_officer_id", "VARCHAR"),
            ("global_priority_score", "FLOAT"),
            ("officer_priority_score", "FLOAT"),
            ("submitted_by", "VARCHAR"),
            ("llm_reviewed", "BOOLEAN"),
            ("llm_adjustment", "FLOAT"),
            ("llm_reasoning", "TEXT"),
            ("llm_risk_summary", "TEXT"),
            ("llm_public_safety_risk", "VARCHAR"),
            ("llm_vulnerable_population_risk", "VARCHAR"),
            ("llm_infrastructure_risk", "VARCHAR"),
            ("llm_trigger_reasons", "TEXT"),
            ("sla_deadline", "VARCHAR"),
            ("sla_breached", "BOOLEAN"),
            ("accepted_at", "VARCHAR"),
            ("resolved_at", "VARCHAR"),
            ("closed_at", "VARCHAR"),
            ("escalation_level", "INTEGER")
        ]
        with engine.connect() as conn:
            for col_name, col_type in columns_to_add:
                try:
                    with conn.begin():
                        conn.execute(text(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type}"))
                except Exception:
                    pass

        try:
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("UPDATE complaints SET submitted_by = 'citizen1' WHERE submitted_by IS NULL"))
        except Exception:
            pass
        
        try:
            with engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("ALTER TABLE officers ADD COLUMN profile_pic TEXT"))
        except Exception:
            pass
        
        # Run seeding and cleanups
        db = SessionLocal()
        seed_department_policies(db)
        seed_officers(db)
        seed_users(db)
        seed_database(db)
        try:
            deleted = db.query(Complaint).filter(Complaint.id.in_(["CMP-2006", "CMP-2007"])).delete(synchronize_session=False)
            db.commit()
            print(f"🧹 Database cleanup: deleted {deleted} complaints (CMP-2006, CMP-2007)")
        except Exception as e:
            print(f"Error during db cleanup: {e}")
        db.close()
        
        print("Database Initialized Successfully.")
    except Exception as e:
        print(f"Database initialization failed during startup. Check credentials! Error: {e}")

# Pydantic schemas
class TriageRequest(BaseModel):
    complaint_text: str
    submitted_by: Optional[str] = None

class SignupRequest(BaseModel):
    username: str
    password: str
    name: str

class OverrideRequest(BaseModel):
    priority_label: str
    reason: str

class ResolveRequest(BaseModel):
    notes: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateOfficerRequest(BaseModel):
    name: str
    department: str
    zone: str
    ward: str
    designation: str = "Junior Inspector"
    email: Optional[str] = None
    password: str = "off123"
    profile_pic: Optional[str] = None
    escalation_level: int = 0

class UpdatePolicyRequest(BaseModel):
    severity_weight: float = 0.30
    impact_weight: float = 0.25
    urgency_weight: float = 0.20
    vulnerability_weight: float = 0.15
    duplicate_weight: float = 0.10

class OverrideSeverityRequest(BaseModel):
    severity_score: float
    reason: str
    officer_id: Optional[str] = None

class OverrideDepartmentRequest(BaseModel):
    new_department: str
    reason: str
    officer_id: Optional[str] = None

class AcceptRequest(BaseModel):
    officer_id: str

class StartProgressRequest(BaseModel):
    officer_id: str
    notes: Optional[str] = None

class FieldInspectionRequest(BaseModel):
    officer_id: str
    notes: Optional[str] = None

class EscalateRequest(BaseModel):
    officer_id: str
    reason: str
    escalation_level: Optional[int] = None

class CloseRequest(BaseModel):
    admin_id: str
    notes: Optional[str] = None

class ReassignRequest(BaseModel):
    admin_id: str
    new_officer_id: str
    reason: str

# ===================== LIFECYCLE HELPERS =====================

VALID_TRANSITIONS = {
    "Submitted": ["Assigned", "Rejected"],
    "Assigned": ["Accepted", "Reassigned"],
    "Accepted": ["In Progress", "Escalated"],
    "In Progress": ["Field Inspection", "Escalated", "Resolved"],
    "Field Inspection": ["In Progress", "Resolved", "Escalated"],
    "Escalated": ["Assigned", "In Progress"],
    "Resolved": ["Closed"],
    "Reassigned": ["Assigned"],
}

SLA_HOURS = {"Critical": 24, "High": 72, "Medium": 120, "Low": 168}

ESCALATION_LEVELS = {
    0: "L1 - Junior Inspector",
    1: "L2 - Senior Inspector",
    2: "L3 - Department Head",
    3: "L4 - Ministry Level"
}

def validate_transition(current_status: str, new_status: str):
    """Validate that a status transition is allowed."""
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition: '{current_status}' → '{new_status}'. Allowed: {allowed}"
        )

def calculate_sla_deadline(priority_label: str, submitted_at: str) -> str:
    """Calculate SLA deadline based on priority level."""
    try:
        dt = datetime.datetime.strptime(submitted_at, "%Y-%m-%d %H:%M:%S")
    except:
        dt = datetime.datetime.now()
    hours = SLA_HOURS.get(priority_label, 168)
    deadline = dt + datetime.timedelta(hours=hours)
    return deadline.strftime("%Y-%m-%d %H:%M:%S")

def log_audit(db: Session, complaint_id: str, action: str, from_val: str, to_val: str, performed_by: str, performer_role: str, notes: str = None):
    """Create an audit log entry."""
    entry = AuditLog(
        complaint_id=complaint_id,
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        action=action,
        from_value=from_val,
        to_value=to_val,
        performed_by=performed_by,
        performer_role=performer_role,
        notes=notes
    )
    db.add(entry)

def check_and_escalate_sla(db: Session):
    """Check all active complaints for SLA breaches and auto-escalate."""
    now = datetime.datetime.now()
    active_statuses = ["Submitted", "Assigned", "Accepted", "In Progress", "Field Inspection"]
    active_complaints = db.query(Complaint).filter(
        Complaint.status.in_(active_statuses),
        Complaint.sla_breached == False,
        Complaint.sla_deadline != None
    ).all()
    
    for comp in active_complaints:
        try:
            deadline = datetime.datetime.strptime(comp.sla_deadline, "%Y-%m-%d %H:%M:%S")
            if now > deadline:
                comp.sla_breached = True
                current_level = comp.escalation_level or 0
                new_level = min(current_level + 1, 3)
                comp.escalation_level = new_level
                
                # Reassign to higher level officer
                import utils
                new_officer_id = utils.reassign_to_escalation_level(comp.department, new_level, db)
                if new_officer_id and new_officer_id != comp.assigned_officer_id:
                    comp.assigned_officer_id = new_officer_id
                    n_off = Notification(user_id=new_officer_id, message=f"SLA Breach: Complaint {comp.id} auto-escalated to you.", type="escalation", timestamp=now.strftime('%Y-%m-%d %H:%M:%S'))
                    db.add(n_off)
                    
                n_admin = Notification(user_id="admin", message=f"SLA Breach: Complaint {comp.id} auto-escalated to {ESCALATION_LEVELS.get(new_level, f'L{new_level}')}.", type="alert", timestamp=now.strftime('%Y-%m-%d %H:%M:%S'))
                db.add(n_admin)
                
                # Auto-escalate status if not already escalated
                if comp.status not in ["Escalated", "Resolved", "Closed"]:
                    old_status = comp.status
                    comp.status = "Escalated"
                    log_audit(db, comp.id, "auto_escalation", old_status, "Escalated", "SYSTEM", "system",
                             f"SLA breached. Auto-escalated from {ESCALATION_LEVELS.get(current_level, 'L1')} to {ESCALATION_LEVELS.get(new_level, 'L2')}.")
                    log_audit(db, comp.id, "sla_breach", comp.sla_deadline, now.strftime('%Y-%m-%d %H:%M:%S'), "SYSTEM", "system",
                             f"SLA deadline exceeded. Priority: {comp.priority_label}")
                    
                    # Update escalation history
                    esc_hist = json.loads(comp.escalation_history or '[]')
                    esc_hist.append({
                        "level": ESCALATION_LEVELS.get(new_level, f"L{new_level}"),
                        "date": now.strftime("%Y-%m-%d %H:%M:%S"),
                        "reason": "SLA breach - auto-escalated"
                    })
                    comp.escalation_history = json.dumps(esc_hist)
        except Exception:
            pass
    
    db.commit()


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
        "assigned_officer_id": c.assigned_officer_id,
        "submitted_by": c.submitted_by,
        "global_priority_score": round(c.global_priority_score or 0.0, 4),
        "officer_priority_score": round(c.officer_priority_score or 0.0, 4),
        "age_days": round(age_days, 1),
        "aging_boost": round(aging_boost, 2),
        "relative_time": relative_time,
        "sla_deadline": c.sla_deadline,
        "sla_breached": getattr(c, 'sla_breached', False)
    }


def seed_officers(db: Session):
    """Seed the officers table with initial data."""
    if db.query(Officer).count() > 0:
        return
    
    officers = [
        Officer(officer_id="OFF-001", name="Rajesh Kumar", department="Water & Sewerage Board", zone="Anna Nagar", ward="Ward 5", designation="Junior Inspector", email="rajesh.water@gov.in"),
        Officer(officer_id="OFF-002", name="Priya Sharma", department="Public Works Department (PWD)", zone="T. Nagar", ward="Ward 3", designation="Senior Inspector", email="priya.pwd@gov.in"),
        Officer(officer_id="OFF-003", name="Suresh Babu", department="Electricity Utilities Board", zone="Adyar", ward="Ward 8", designation="Junior Inspector", email="suresh.elec@gov.in"),
        Officer(officer_id="OFF-004", name="Kavitha Rajan", department="Health Department", zone="Mylapore", ward="Ward 12", designation="Health Inspector", email="kavitha.health@gov.in"),
        Officer(officer_id="OFF-005", name="Arun Prakash", department="Police & Disaster Response", zone="Anna Nagar", ward="Ward 5", designation="Sub Inspector", email="arun.police@gov.in"),
        Officer(officer_id="OFF-006", name="Deepa Venkat", department="Municipal Sanitation Department", zone="Velachery", ward="Ward 15", designation="Sanitation Inspector", email="deepa.sanitation@gov.in"),
        Officer(officer_id="OFF-007", name="Mohan Das", department="Transport & Traffic Authority", zone="Guindy", ward="Ward 10", designation="Traffic Inspector", email="mohan.transport@gov.in"),
        Officer(officer_id="OFF-008", name="Lakshmi Narayanan", department="Education Department", zone="Nungambakkam", ward="Ward 7", designation="Education Officer", email="lakshmi.edu@gov.in"),
        Officer(officer_id="OFF-009", name="Ganesh Iyer", department="Vigilance Bureau", zone="Egmore", ward="Ward 2", designation="Vigilance Inspector", email="ganesh.vigilance@gov.in"),
        Officer(officer_id="OFF-010", name="Anitha Subramanian", department="General Administration Department", zone="Fort St. George", ward="Ward 1", designation="Administrative Officer", email="anitha.admin@gov.in"),
    ]
    for officer in officers:
        db.add(officer)
    db.commit()

def seed_users(db: Session):
    """Seed default user accounts."""
    if db.query(User).count() > 0:
        return
    
    users = [
        User(
            user_id="USR-000",
            username="admin",
            password_hash=bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8'),
            role="admin",
            officer_id=None,
            name="System Administrator"
        ),
        User(
            user_id="USR-011",
            username="citizen1",
            password_hash=bcrypt.hashpw(b"cit123", bcrypt.gensalt()).decode('utf-8'),
            role="citizen",
            officer_id=None,
            name="Demo Citizen"
        ),
        User(
            user_id="USR-012",
            username="citizen2",
            password_hash=bcrypt.hashpw(b"cit123", bcrypt.gensalt()).decode('utf-8'),
            role="citizen",
            officer_id=None,
            name="Demo Citizen 2"
        ),
    ]
    
    # Generate user accounts for all seeded officers
    officers = db.query(Officer).all()
    for i, officer in enumerate(officers):
        users.append(
            User(
                user_id=f"USR-{i+1:03d}",
                username=f"officer{i+1}",
                password_hash=bcrypt.hashpw(b"off123", bcrypt.gensalt()).decode('utf-8'),
                role="officer",
                officer_id=officer.officer_id,
                name=officer.name
            )
        )
        
    for user in users:
        db.add(user)
    db.commit()

def seed_department_policies(db: Session):
    """Seed department-specific priority weight policies."""
    if db.query(DepartmentPolicy).count() > 0:
        return
    
    policies = [
        DepartmentPolicy(department="Water & Sewerage Board", severity_weight=0.40, impact_weight=0.30, urgency_weight=0.20, vulnerability_weight=0.05, duplicate_weight=0.05),
        DepartmentPolicy(department="Public Works Department (PWD)", severity_weight=0.30, impact_weight=0.20, urgency_weight=0.35, vulnerability_weight=0.05, duplicate_weight=0.10),
        DepartmentPolicy(department="Health Department", severity_weight=0.35, impact_weight=0.20, urgency_weight=0.10, vulnerability_weight=0.30, duplicate_weight=0.05),
        DepartmentPolicy(department="Electricity Utilities Board", severity_weight=0.30, impact_weight=0.25, urgency_weight=0.25, vulnerability_weight=0.10, duplicate_weight=0.10),
        DepartmentPolicy(department="Police & Disaster Response", severity_weight=0.25, impact_weight=0.25, urgency_weight=0.30, vulnerability_weight=0.15, duplicate_weight=0.05),
        DepartmentPolicy(department="Municipal Sanitation Department", severity_weight=0.25, impact_weight=0.30, urgency_weight=0.15, vulnerability_weight=0.10, duplicate_weight=0.20),
        DepartmentPolicy(department="Transport & Traffic Authority", severity_weight=0.25, impact_weight=0.30, urgency_weight=0.25, vulnerability_weight=0.10, duplicate_weight=0.10),
        DepartmentPolicy(department="Education Department", severity_weight=0.30, impact_weight=0.25, urgency_weight=0.15, vulnerability_weight=0.25, duplicate_weight=0.05),
        DepartmentPolicy(department="Vigilance Bureau", severity_weight=0.30, impact_weight=0.25, urgency_weight=0.20, vulnerability_weight=0.15, duplicate_weight=0.10),
        DepartmentPolicy(department="General Administration Department", severity_weight=0.30, impact_weight=0.25, urgency_weight=0.20, vulnerability_weight=0.15, duplicate_weight=0.10),
    ]
    for policy in policies:
        db.add(policy)
    db.commit()

# Seed database with initial complaints if table is empty
# Seed database with initial complaints if table is empty
def seed_database(db: Session):
    # Check if there are any citizen complaints (CMP-2006 or higher)
    citizen_exists = db.query(Complaint).filter(Complaint.id > "CMP-2050").count() > 0
    if citizen_exists:
        print("ℹ️ Citizen complaints exist. Skipping database wipe and seed.")
        return
        
    # Otherwise, wipe the database and re-seed the 5 complaints
    db.query(Complaint).delete()
    db.commit()
    print("🧹 Wiped all existing complaints from the database for re-seeding.")
    
    seeds = [
        {
            "id": "CMP-2001",
            "complaint_text": "Low water pressure and muddy water supply in Sector 4 residential colony for the last 3 days.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2002",
            "complaint_text": "Sewage water is overflowing from a broken pipeline on Anna Salai Road, causing massive public health hazard and foul smell.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2003",
            "complaint_text": "No drinking water supply in Ward 5 for the past week, residents are facing severe hardships.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2004",
            "complaint_text": "A major water pipe burst near the Central Market is wasting thousands of liters of clean water.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2005",
            "complaint_text": "Drainage is completely blocked in the 2nd cross street, causing dirty water to enter homes during rain.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2006",
            "complaint_text": "Major bridge structure crack detected on the busy subway road, causing severe risk of bridge collapse and blocking traffic.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2007",
            "complaint_text": "Deep potholes on the main highway are causing multiple two-wheeler accidents daily.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2008",
            "complaint_text": "The newly constructed retaining wall near the riverbed has collapsed after a minor shower.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2009",
            "complaint_text": "Road widening work has been abandoned for 6 months, leaving debris that blocks pedestrian paths.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2010",
            "complaint_text": "Public building roof is leaking severely in the revenue office, damaging important documents.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2011",
            "complaint_text": "Unlicensed clinic operating in the basement of a residential building is dispensing expired medicines.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2012",
            "complaint_text": "Dengue outbreak reported in the slum area; urgent mosquito fogging and medical camps are needed.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2013",
            "complaint_text": "The government hospital pharmacy has been out of essential life-saving drugs for over a month.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2014",
            "complaint_text": "Illegal bio-medical waste dumping observed near the local lake by private hospitals.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2015",
            "complaint_text": "Food poisoning cases spreading rapidly after a local festival; health inspection of vendors is urgently required.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2016",
            "complaint_text": "The streetlight on MG Road is not working since yesterday, making the street completely dark at night.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2017",
            "complaint_text": "High voltage fluctuations are burning out home appliances in the entire Gandhi Nagar neighborhood.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2018",
            "complaint_text": "A live electric wire has fallen on the street near the primary school, posing a lethal threat to children.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2019",
            "complaint_text": "Unscheduled power cuts lasting 8-10 hours daily are disrupting business and life.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2020",
            "complaint_text": "The electricity transformer caught fire yesterday and has not been repaired, leaving 500 houses without power.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2021",
            "complaint_text": "Critical gas leak reported near St. Mary's Primary School. Urgent evacuation of the area is needed to prevent explosion.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2022",
            "complaint_text": "Rampant chain-snatching incidents occurring daily at the local park after sunset.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2023",
            "complaint_text": "Illegal sand mining operations are happening at the riverbank every night with heavy machinery.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2024",
            "complaint_text": "A suspicious abandoned vehicle has been parked outside the mall for three days without license plates.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2025",
            "complaint_text": "Flash floods have trapped several families in the low-lying areas of the district.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2026",
            "complaint_text": "Garbage has not been collected from our street for over two weeks, creating a severe health hazard.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2027",
            "complaint_text": "Public toilets in the bus stand are overflowing and completely unusable, causing unhygienic conditions.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2028",
            "complaint_text": "Dead animal carcass has been lying on the road for 3 days, emitting an unbearable stench.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2029",
            "complaint_text": "Illegal dumping of construction debris is blocking the municipal storm water drains.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2030",
            "complaint_text": "Sweepers are demanding bribes from residents to clean the neighborhood streets.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2031",
            "complaint_text": "The traffic signal at the major four-way junction has been dead for a week, causing massive gridlock.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2032",
            "complaint_text": "Local city buses are skipping scheduled stops, leaving students and workers stranded daily.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2033",
            "complaint_text": "Private buses are illegally parking on the main road, choking the flow of traffic.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2034",
            "complaint_text": "Auto-rickshaws are demanding exorbitant fares and refusing to use meters at the railway station.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2035",
            "complaint_text": "The pedestrian crossing lines have completely faded, causing risk to people crossing the busy highway.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2036",
            "complaint_text": "The roof of the government primary school classroom is collapsing and unsafe for students.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2037",
            "complaint_text": "Mid-day meals being served to students contain insects and are completely unhygienic.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2038",
            "complaint_text": "The school has no dedicated subject teachers for math and science for the entire academic year.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2039",
            "complaint_text": "Private schools are illegally demanding capitation fees for kindergarten admissions.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2040",
            "complaint_text": "No drinking water or functional toilets available for girls in the high school.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2041",
            "complaint_text": "The local sub-registrar is demanding a massive bribe for property registration.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2042",
            "complaint_text": "A government official was caught on camera accepting cash to pass a building construction plan.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2043",
            "complaint_text": "Ration shop owner is illegally diverting subsidized grains to the black market.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2044",
            "complaint_text": "Funds allocated for the village road construction have been completely embezzled by the contractor.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2045",
            "complaint_text": "Fake caste certificates are being issued by agents operating near the taluk office.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2046",
            "complaint_text": "The e-Seva portal for applying for income certificates has been down for two weeks.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2047",
            "complaint_text": "No staff available at the citizen facilitation center during working hours.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2048",
            "complaint_text": "My grievance petition submitted three months ago has been closed without any action taken.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2049",
            "complaint_text": "The public notice board at the collectorate has not been updated with current government schemes.",
            "timestamp": "2026-06-16 09:00:00"
        },
        {
            "id": "CMP-2050",
            "complaint_text": "Delay of over 6 months in issuing death certificates due to administrative negligence.",
            "timestamp": "2026-06-16 09:00:00"
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
            

        # Get dynamic department policy
        policy = db.query(DepartmentPolicy).filter(DepartmentPolicy.department == department).first()
        dept_weights = None
        if policy:
            dept_weights = {
                'severity_weight': policy.severity_weight,
                'impact_weight': policy.impact_weight,
                'urgency_weight': policy.urgency_weight,
                'vulnerability_weight': policy.vulnerability_weight,
                'duplicate_weight': policy.duplicate_weight
            }

            # Base Governance Priority Score
            priority_score = utils.calculate_priority_score(
                severity_score, 
                public_impact_score, 
                urgency_score, 
                vulnerability_score, 
                duplicate_escalation_score,
                weights=dept_weights
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
                    # ALWAYS use MockLLMClient during seeding to prevent Render port scan timeouts
                    client = utils.MockLLMClient()
                    review_result = client.review_complaint(complaint_data, similar_cases)
                    llm_adjustment = review_result.get("recommended_adjustment", 0.0)
                    llm_reasoning = review_result.get("reasoning", "LLM review completed.")
                    llm_risk_summary = review_result.get("risk_summary", "")
                    llm_public_safety_risk = review_result.get("public_safety_risk", "Medium")
                    llm_vulnerable_population_risk = review_result.get("vulnerable_population_risk", "Medium")
                    llm_infrastructure_risk = review_result.get("infrastructure_risk", "Medium")
                    suggested_response = review_result.get("suggested_response", "")
                    suggested_action = review_result.get("officer_handbook", review_result.get("suggested_action", ""))
                except Exception as e:
                    print(f"Error calling LLM Client during seed: {e}")
                    llm_reviewed = False
                    llm_adjustment = 0.0
                    llm_reasoning = f"Failed to run LLM review: {str(e)}"
                    
            # Fallback to templates if empty or LLM was not triggered
            if not suggested_response:
                suggested_response, suggested_action = utils.get_routine_suggestions(predicted_category, text)
                
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
        
        from sqlalchemy import func
        # Assign Officer directly inside api.py to avoid circular imports during startup
        assigned_officer = db.query(Officer).filter(func.lower(Officer.department) == department.lower()).first()
        assigned_officer_id = assigned_officer.officer_id if assigned_officer else None
        
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
            status="Assigned" if (is_admissible and assigned_officer_id) else ("Submitted" if is_admissible else "Rejected"),
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
            llm_trigger_reasons=json.dumps(llm_trigger_reasons),
            assigned_officer_id=assigned_officer_id,
            submitted_by="citizen2" if int(comp_id.split("-")[1]) % 2 == 0 else "citizen1"
        )
        db.add(comp)
    db.commit()
    print("✅ Seed complaints triaged and inserted successfully.")




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
    assigned_officer_id = None
    officer_priority = 0.0
    priority_breakdown = {}
    
    if is_admissible:
        department = utils.route_to_department(predicted_category)
        sentiment_score = utils.get_sentiment_score(text)
        
        # Smart Officer Assignment
        structured = None
        try:
            structured = utils.extract_entities_and_details(text, predicted_category)
        except:
            pass
        location_text = structured.get('location', '') if structured else ''
        assigned_officer_id = utils.assign_officer(department, location_text, db)
        
        # Extract NER details and risk keywords
        ner_details = structured if structured else utils.extract_entities_and_details(text, predicted_category)
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

    # Get dynamic department policy
    policy = db.query(DepartmentPolicy).filter(DepartmentPolicy.department == department).first()
    dept_weights = None
    if policy:
        dept_weights = {
        'severity_weight': policy.severity_weight,
        'impact_weight': policy.impact_weight,
        'urgency_weight': policy.urgency_weight,
        'vulnerability_weight': policy.vulnerability_weight,
        'duplicate_weight': policy.duplicate_weight
        }

        priority_score = utils.calculate_priority_score(
            severity_score, 
            public_impact_score, 
            urgency_score, 
            vulnerability_score, 
            duplicate_escalation_score,
            weights=dept_weights
        )
        
        # Calculate department-specific priority
        dept_policy = db.query(DepartmentPolicy).filter(
            DepartmentPolicy.department == department
        ).first()
        dept_weights = None
        if dept_policy:
            dept_weights = {
                'severity_weight': dept_policy.severity_weight,
                'impact_weight': dept_policy.impact_weight,
                'urgency_weight': dept_policy.urgency_weight,
                'vulnerability_weight': dept_policy.vulnerability_weight,
                'duplicate_weight': dept_policy.duplicate_weight
            }
        officer_priority = utils.calculate_department_priority(
            severity_score, public_impact_score, urgency_score, vulnerability_score, duplicate_escalation_score, dept_weights
        )
        
        # Priority breakdown for explainability
        priority_breakdown = utils.get_priority_breakdown(
            severity_score, public_impact_score, urgency_score, vulnerability_score, duplicate_escalation_score
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
        if assigned_officer_id:
            resolution_history.append({"status": "Assigned", "date": timestamp, "notes": f"Assigned to {department}."})
        else:
            resolution_history.append({"status": "Submitted", "date": timestamp, "notes": f"Pending officer assignment in {department} due to workload limits."})
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
        "suggested_action": suggested_action,
        "officer_handbook": suggested_action,
        "priority_breakdown": priority_breakdown
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
        status="Assigned" if (is_admissible and assigned_officer_id) else ("Submitted" if is_admissible else "Rejected"),
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
        llm_trigger_reasons=json.dumps(llm_trigger_reasons),
        assigned_officer_id=assigned_officer_id,
        submitted_by=req.submitted_by,
        global_priority_score=round(priority_score, 4),
        officer_priority_score=round(officer_priority, 4),
    )
    
    if is_admissible:
        comp.sla_deadline = calculate_sla_deadline(priority_label, timestamp)
        
    db.add(comp)
    db.commit()
    db.refresh(comp)
    
    # Audit logging
    if is_admissible:
        log_audit(db, comp.id, "status_change", None, "Submitted", req.submitted_by or "CITIZEN", "citizen", "Complaint submitted by citizen.")
        if assigned_officer_id:
            log_audit(db, comp.id, "status_change", "Submitted", "Assigned", "SYSTEM", "system", f"Auto-assigned to officer {assigned_officer_id}.")
        db.commit()
    else:
        log_audit(db, comp.id, "status_change", None, "Rejected", "SYSTEM", "system", f"Rejected: {rejection_reason}")
        db.commit()
        
    return to_dict(comp)

@app.get("/complaints")
def get_complaints(officer_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Get active triage queue.
    Groups duplicate complaints by lead_id, so only one lead card is returned, 
    carrying lists of duplicate references.
    Also recalculates duplicate escalation and priority dynamically.
    """
    check_and_escalate_sla(db)
    query = db.query(Complaint).filter(
        Complaint.admissible == True,
        ~Complaint.status.in_(["Resolved", "Closed", "Rejected"])
    )
    if officer_id:
        query = query.filter(Complaint.assigned_officer_id == officer_id)
    admissible_comps = query.all()
    
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
        
    # Sort active queue by final_priority_score descending (or officer_priority_score if officer_id filter)
    if officer_id:
        grouped_result.sort(key=lambda x: x.get('officer_priority_score') or x.get('final_priority_score', 0.0), reverse=True)
    else:
        grouped_result.sort(key=lambda x: x['final_priority_score'], reverse=True)
    return grouped_result

@app.get("/complaints/resolved")
def get_resolved_complaints(db: Session = Depends(get_db)):
    resolved = db.query(Complaint).filter(
        Complaint.status.in_(["Resolved", "Closed"])
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
            
            # Audit log
            c_item.resolved_at = timestamp
            log_audit(db, c_item.id, "status_change", c_item.status, "Resolved", c_item.assigned_officer_id or "unknown", "officer", req.notes)
        
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
        log_audit(db, c_item.id, "priority_override", str(c_item.priority_label), str(req.priority_label), comp.assigned_officer_id or "unknown", "officer", req.reason)
        c_item.officer_override = req.priority_label
        c_item.override_reason = req.reason
    
    feedback = OfficerFeedback(
        complaint_id=id,
        officer_id=comp.assigned_officer_id or "unknown",
        timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        override_type="priority",
        system_value=str(comp.priority_label),
        officer_value=str(req.priority_label),
        reason=req.reason
    )
    db.add(feedback)
        
    db.commit()
    return {"message": "Override applied successfully for complaint and duplicates."}

@app.post("/complaints/{complaint_id}/accept")
def accept_complaint(complaint_id: str, req: AcceptRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Accepted")
    old_status = comp.status
    comp.status = "Accepted"
    comp.accepted_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Accepted", "date": comp.accepted_at, "notes": f"Accepted by officer {req.officer_id}"})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Accepted", req.officer_id, "officer", "Officer accepted the assignment.")
    db.commit()
    return {"message": "Complaint accepted.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/start-progress")
def start_progress(complaint_id: str, req: StartProgressRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "In Progress")
    old_status = comp.status
    comp.status = "In Progress"
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "In Progress", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": req.notes or "Officer started working on this complaint."})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "In Progress", req.officer_id, "officer", req.notes or "Started working.")
    db.commit()
    return {"message": "Complaint is now in progress.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/field-inspection")
def field_inspection(complaint_id: str, req: FieldInspectionRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Field Inspection")
    old_status = comp.status
    comp.status = "Field Inspection"
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Field Inspection", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": req.notes or "Officer conducting on-site inspection."})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Field Inspection", req.officer_id, "officer", req.notes or "Field inspection started.")
    db.commit()
    return {"message": "Complaint marked for field inspection.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/escalate")
def escalate_complaint(complaint_id: str, req: EscalateRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Escalated")
    old_status = comp.status
    comp.status = "Escalated"
    current_level = comp.escalation_level or 0
    new_level = req.escalation_level if req.escalation_level is not None else min(current_level + 1, 3)
    comp.escalation_level = new_level
    
    # Reassign to higher level officer
    import utils
    new_officer_id = utils.reassign_to_escalation_level(comp.department, new_level, db)
    if new_officer_id and new_officer_id != comp.assigned_officer_id:
        comp.assigned_officer_id = new_officer_id
        n_off = Notification(user_id=new_officer_id, message=f"Complaint {comp.id} escalated to you.", type="escalation", timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        db.add(n_off)
        
    n_admin = Notification(user_id="admin", message=f"Complaint {comp.id} escalated to {ESCALATION_LEVELS.get(new_level, f'L{new_level}')}.", type="escalation", timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    db.add(n_admin)
    
    esc_hist = json.loads(comp.escalation_history or '[]')
    esc_hist.append({"level": ESCALATION_LEVELS.get(new_level, f"L{new_level}"), "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "reason": req.reason})
    comp.escalation_history = json.dumps(esc_hist)
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Escalated", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": f"Escalated to {ESCALATION_LEVELS.get(new_level, 'higher authority')}: {req.reason}"})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Escalated", req.officer_id, "officer", req.reason)
    db.commit()
    return {"message": f"Complaint escalated to {ESCALATION_LEVELS.get(new_level, 'higher authority')}.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/close")
def close_complaint(complaint_id: str, req: CloseRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    validate_transition(comp.status, "Closed")
    old_status = comp.status
    comp.status = "Closed"
    comp.closed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Closed", "date": comp.closed_at, "notes": req.notes or "Complaint closed by admin."})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "status_change", old_status, "Closed", req.admin_id, "admin", req.notes or "Closed by admin.")
    db.commit()
    return {"message": "Complaint closed.", "complaint": to_dict(comp)}

@app.post("/complaints/{complaint_id}/reassign")
def reassign_complaint(complaint_id: str, req: ReassignRequest, db: Session = Depends(get_db)):
    comp = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    old_officer = comp.assigned_officer_id
    old_status = comp.status
    comp.assigned_officer_id = req.new_officer_id
    comp.status = "Assigned"
    comp.escalation_level = 0  # Reset escalation on reassignment
    comp.sla_breached = False  # Reset SLA
    # Recalculate SLA deadline from now
    comp.sla_deadline = calculate_sla_deadline(comp.priority_label or "Low", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    res_hist = json.loads(comp.resolution_history or '[]')
    res_hist.append({"status": "Reassigned", "date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "notes": f"Reassigned from {old_officer} to {req.new_officer_id}: {req.reason}"})
    comp.resolution_history = json.dumps(res_hist)
    
    log_audit(db, complaint_id, "officer_reassignment", old_officer or 'none', req.new_officer_id, req.admin_id, "admin", req.reason)
    log_audit(db, complaint_id, "status_change", old_status, "Assigned", req.admin_id, "admin", f"Reassigned to {req.new_officer_id}")
    db.commit()
    return {"message": f"Complaint reassigned to {req.new_officer_id}.", "complaint": to_dict(comp)}


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
    admissible_count = db.query(Complaint).filter(Complaint.admissible == True, ~Complaint.status.in_(["Resolved", "Closed", "Rejected"])).count()
    rejected_count = db.query(Complaint).filter(Complaint.admissible == False).count()
    overrides_count = db.query(Complaint).filter(Complaint.officer_override != None).count()
    return {
        "active_count": admissible_count,
        "rejected_count": rejected_count,
        "overrides_count": overrides_count
    }

# ===================== AUTH ENDPOINTS =====================

@app.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not bcrypt.checkpw(req.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    result = {
        'user_id': user.user_id,
        'username': user.username,
        'role': user.role,
        'name': user.name,
        'officer_id': user.officer_id
    }
    if user.officer_id:
        officer = db.query(Officer).filter(Officer.officer_id == user.officer_id).first()
        if officer:
            result['officer'] = {
                'officer_id': officer.officer_id,
                'name': officer.name,
                'department': officer.department,
                'zone': officer.zone,
                'ward': officer.ward,
                'designation': officer.designation,
                'profile_pic': officer.profile_pic
            }
    return result

@app.post("/auth/signup")
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Generate a unique user ID for citizen
    citizen_count = db.query(User).filter(User.role == "citizen").count()
    user_id = f"USR-C-{100 + citizen_count}"
    
    password_hash = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    new_user = User(
        user_id=user_id,
        username=req.username,
        password_hash=password_hash,
        role="citizen",
        officer_id=None,
        name=req.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        'user_id': new_user.user_id,
        'username': new_user.username,
        'role': new_user.role,
        'name': new_user.name
    }

@app.get("/complaints/citizen/{username}")
def get_citizen_complaints(username: str, db: Session = Depends(get_db)):
    """
    Get all complaints submitted by a specific citizen.
    Includes active, resolved, or rejected.
    """
    # Query complaints submitted by this user
    comps = db.query(Complaint).filter(Complaint.submitted_by == username).all()
    return [to_dict(c) for c in comps]

# ===================== OFFICER ENDPOINTS =====================

@app.get("/officers")
def list_officers(db: Session = Depends(get_db)):
    officers = db.query(Officer).all()
    return [{
        'officer_id': o.officer_id,
        'name': o.name,
        'department': o.department,
        'zone': o.zone,
        'ward': o.ward,
        'designation': o.designation,
        'email': o.email,
        'role': o.role,
        'profile_pic': o.profile_pic
    } for o in officers]

@app.get("/officers/{officer_id}")
def get_officer(officer_id: str, db: Session = Depends(get_db)):
    officer = db.query(Officer).filter(Officer.officer_id == officer_id).first()
    if not officer:
        raise HTTPException(status_code=404, detail="Officer not found")
    return {
        'officer_id': officer.officer_id,
        'name': officer.name,
        'department': officer.department,
        'zone': officer.zone,
        'ward': officer.ward,
        'designation': officer.designation,
        'email': officer.email,
        'role': officer.role,
        'profile_pic': officer.profile_pic
    }

@app.post("/officers")
def create_officer(req: CreateOfficerRequest, db: Session = Depends(get_db)):
    count = db.query(Officer).count()
    officer_id = f"OFF-{count + 1:03d}"
    officer = Officer(
        officer_id=officer_id,
        name=req.name,
        department=req.department,
        zone=req.zone,
        ward=req.ward,
        designation=req.designation,
        email=req.email,
        profile_pic=req.profile_pic,
        escalation_level=req.escalation_level
    )
    db.add(officer)
    
    # Create matching user account for login
    user_count = db.query(User).count()
    user_id = f"USR-{user_count + 1:03d}"
    user = User(
        user_id=user_id,
        username=req.email,
        password_hash=bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        role="officer",
        officer_id=officer_id,
        name=req.name
    )
    db.add(user)
    
    db.commit()
    
    # Auto-assign waitlisted complaints for this department
    unassigned_complaints = db.query(Complaint).filter(
        Complaint.department == req.department,
        Complaint.status == "Submitted",
        Complaint.assigned_officer_id.is_(None)
    ).limit(10).all()
    
    assigned_count = 0
    import datetime
    for comp in unassigned_complaints:
        comp.assigned_officer_id = officer_id
        comp.status = "Assigned"
        # Update resolution history safely
        import json
        try:
            history = json.loads(comp.resolution_history_raw) if comp.resolution_history_raw else []
        except:
            history = []
        history.append({
            "status": "Assigned", 
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            "notes": f"Auto-assigned to newly added officer {officer_id}."
        })
        comp.resolution_history_raw = json.dumps(history)
        assigned_count += 1
        
    if assigned_count > 0:
        db.commit()
        
    msg = f"Officer created and User account generated for {req.email}"
    if assigned_count > 0:
        msg += f". Auto-assigned {assigned_count} waitlisted complaints."
        
    return {'message': msg, 'officer_id': officer_id}

# ===================== NOTIFICATION ENDPOINTS =====================

@app.get("/notifications/{user_id}")
def get_notifications(user_id: str, db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.id.desc()).limit(20).all()
    return [{"id": n.id, "message": n.message, "type": n.type, "timestamp": n.timestamp, "is_read": n.is_read} for n in notifs]

@app.post("/notifications/{notification_id}/read")
def read_notification(notification_id: int, db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notification_id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"status": "ok"}

# ===================== DEPARTMENT POLICY ENDPOINTS =====================

@app.get("/department-policies")
def list_policies(db: Session = Depends(get_db)):
    policies = db.query(DepartmentPolicy).all()
    return [{
        'department': p.department,
        'severity_weight': p.severity_weight,
        'impact_weight': p.impact_weight,
        'urgency_weight': p.urgency_weight,
        'vulnerability_weight': p.vulnerability_weight,
        'duplicate_weight': p.duplicate_weight
    } for p in policies]

@app.put("/department-policies/{department}")
def update_policy(department: str, req: UpdatePolicyRequest, db: Session = Depends(get_db)):
    policy = db.query(DepartmentPolicy).filter(DepartmentPolicy.department == department).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Department policy not found")
    
    total = req.severity_weight + req.impact_weight + req.urgency_weight + req.vulnerability_weight + req.duplicate_weight
    if abs(total - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"Weights must sum to 1.0 (got {total:.2f})")
    
    policy.severity_weight = req.severity_weight
    policy.impact_weight = req.impact_weight
    policy.urgency_weight = req.urgency_weight
    policy.vulnerability_weight = req.vulnerability_weight
    policy.duplicate_weight = req.duplicate_weight
    db.commit()
    return {'message': f'Policy updated for {department}'}

# ===================== FEEDBACK ENDPOINTS =====================

@app.post("/complaints/{complaint_id}/override-severity")
def override_severity(complaint_id: str, req: OverrideSeverityRequest, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    feedback = OfficerFeedback(
        complaint_id=complaint_id,
        officer_id=req.officer_id or complaint.assigned_officer_id or "unknown",
        timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        override_type="severity",
        system_value=str(round(complaint.severity_score, 4)),
        officer_value=str(round(req.severity_score, 4)),
        reason=req.reason
    )
    db.add(feedback)
    log_audit(db, complaint_id, "severity_override", str(complaint.severity_score), str(req.severity_score), req.officer_id or complaint.assigned_officer_id or "unknown", "officer", req.reason)
    complaint.severity_score = req.severity_score
    complaint.severity_label = utils.get_severity_level(req.severity_score)
    db.commit()
    return {'message': 'Severity override applied'}

@app.post("/complaints/{complaint_id}/override-department")
def override_department(complaint_id: str, req: OverrideDepartmentRequest, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    feedback = OfficerFeedback(
        complaint_id=complaint_id,
        officer_id=req.officer_id or complaint.assigned_officer_id or "unknown",
        timestamp=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        override_type="department",
        system_value=complaint.department,
        officer_value=req.new_department,
        reason=req.reason
    )
    db.add(feedback)
    log_audit(db, complaint_id, "department_transfer", complaint.department, req.new_department, req.officer_id or complaint.assigned_officer_id or "unknown", "officer", req.reason)
    complaint.department = req.new_department
    # Re-assign officer for new department
    location_text = ''
    try:
        sj = json.loads(complaint.structured_json) if complaint.structured_json else {}
        location_text = sj.get('location', '')
    except Exception:
        pass
    new_officer = utils.assign_officer(req.new_department, location_text, db)
    if new_officer:
        complaint.assigned_officer_id = new_officer
    db.commit()
    return {'message': 'Department override applied', 'new_officer_id': new_officer}

@app.get("/feedback/stats")
def feedback_stats(db: Session = Depends(get_db)):
    all_feedback = db.query(OfficerFeedback).all()
    if not all_feedback:
        return {'total_overrides': 0, 'officers': {}}
    
    from collections import defaultdict
    officer_stats = defaultdict(lambda: {'total_overrides': 0, 'severity_overrides': 0, 'priority_overrides': 0, 'department_overrides': 0})
    
    for fb in all_feedback:
        stats = officer_stats[fb.officer_id]
        stats['total_overrides'] += 1
        if fb.override_type == 'severity':
            stats['severity_overrides'] += 1
        elif fb.override_type == 'priority':
            stats['priority_overrides'] += 1
        elif fb.override_type == 'department':
            stats['department_overrides'] += 1
    
    result = {}
    for officer_id, stats in officer_stats.items():
        total_assigned = db.query(Complaint).filter(
            Complaint.assigned_officer_id == officer_id
        ).count()
        total_assigned = max(total_assigned, 1)
        override_rate = stats['total_overrides'] / total_assigned
        agreement_rate = 1.0 - override_rate
        trust_score = max(0.0, min(1.0, agreement_rate))
        
        result[officer_id] = {
            **stats,
            'total_assigned': total_assigned,
            'override_rate': round(override_rate, 4),
            'agreement_rate': round(agreement_rate, 4),
            'trust_score': round(trust_score, 4)
        }
    
    return {'total_overrides': len(all_feedback), 'officers': result}

@app.get("/feedback/export")
def export_feedback(db: Session = Depends(get_db)):
    all_feedback = db.query(OfficerFeedback).all()
    return [{
        'id': fb.id,
        'complaint_id': fb.complaint_id,
        'officer_id': fb.officer_id,
        'timestamp': fb.timestamp,
        'override_type': fb.override_type,
        'system_value': fb.system_value,
        'officer_value': fb.officer_value,
        'reason': fb.reason
    } for fb in all_feedback]

@app.post("/feedback/apply-learning")
def apply_feedback_learning(db: Session = Depends(get_db)):
    """Adjust department policy weights based on high-trust officer override patterns.
    Officers with trust_score >= 0.70 are considered reliable. Their override patterns
    shift department weights by up to 5% in the direction of their overrides."""
    from collections import defaultdict

    all_feedback = db.query(OfficerFeedback).all()
    if not all_feedback:
        return {'message': 'No feedback data to learn from.', 'updated': []}

    # Compute per-officer trust scores
    officer_trust = {}
    officer_override_counts = defaultdict(int)
    for fb in all_feedback:
        officer_override_counts[fb.officer_id] += 1

    for officer_id, total_overrides in officer_override_counts.items():
        total_assigned = db.query(Complaint).filter(
            Complaint.assigned_officer_id == officer_id
        ).count()
        total_assigned = max(total_assigned, 1)
        override_rate = total_overrides / total_assigned
        trust_score = max(0.0, min(1.0, 1.0 - override_rate))
        officer_trust[officer_id] = trust_score

    # Only use feedback from high-trust officers (>= 0.70)
    reliable_feedback = [fb for fb in all_feedback if officer_trust.get(fb.officer_id, 0) >= 0.70]
    if not reliable_feedback:
        return {'message': 'No high-trust officer feedback available (trust >= 0.70). No changes applied.', 'updated': []}

    # Map complaint_id -> department
    complaint_dept_map = {}
    for fb in reliable_feedback:
        if fb.complaint_id not in complaint_dept_map:
            comp = db.query(Complaint).filter(Complaint.id == fb.complaint_id).first()
            if comp:
                complaint_dept_map[fb.complaint_id] = comp.department

    PRIORITY_ORDER = ["Low", "Medium", "High", "Critical"]
    dept_drift = defaultdict(lambda: {'severity': 0.0, 'impact': 0.0, 'urgency': 0.0, 'count': 0})

    for fb in reliable_feedback:
        dept = complaint_dept_map.get(fb.complaint_id)
        if not dept:
            continue
        drift_amount = 0.01
        if fb.override_type == 'severity':
            try:
                sys_val = float(fb.system_value)
                off_val = float(fb.officer_value)
                direction = 1 if off_val > sys_val else -1
            except (ValueError, TypeError):
                direction = 0
            dept_drift[dept]['severity'] += direction * drift_amount
        elif fb.override_type == 'priority':
            sys_idx = PRIORITY_ORDER.index(fb.system_value) if fb.system_value in PRIORITY_ORDER else 1
            off_idx = PRIORITY_ORDER.index(fb.officer_value) if fb.officer_value in PRIORITY_ORDER else 1
            direction = 1 if off_idx > sys_idx else -1
            dept_drift[dept]['urgency'] += direction * drift_amount * 0.5
            dept_drift[dept]['impact'] += direction * drift_amount * 0.5
        dept_drift[dept]['count'] += 1

    MAX_DRIFT = 0.05
    updated = []
    for dept, drift in dept_drift.items():
        if drift['count'] == 0:
            continue
        policy = db.query(DepartmentPolicy).filter(DepartmentPolicy.department == dept).first()
        if not policy:
            continue

        old_weights = {
            'severity': policy.severity_weight,
            'impact': policy.impact_weight,
            'urgency': policy.urgency_weight,
            'vulnerability': policy.vulnerability_weight,
            'duplicate': policy.duplicate_weight
        }

        new_severity = round(min(0.60, max(0.05, policy.severity_weight + max(-MAX_DRIFT, min(MAX_DRIFT, drift['severity'])))), 4)
        new_impact = round(min(0.60, max(0.05, policy.impact_weight + max(-MAX_DRIFT, min(MAX_DRIFT, drift['impact'])))), 4)
        new_urgency = round(min(0.60, max(0.05, policy.urgency_weight + max(-MAX_DRIFT, min(MAX_DRIFT, drift['urgency'])))), 4)
        new_vuln = policy.vulnerability_weight
        new_dup = policy.duplicate_weight

        # Renormalize to sum to 1.0
        total = new_severity + new_impact + new_urgency + new_vuln + new_dup
        if abs(total - 1.0) > 0.001:
            factor = 1.0 / total
            new_severity = round(new_severity * factor, 4)
            new_impact = round(new_impact * factor, 4)
            new_urgency = round(new_urgency * factor, 4)
            new_vuln = round(new_vuln * factor, 4)
            new_dup = round(max(0.01, 1.0 - new_severity - new_impact - new_urgency - new_vuln), 4)

        policy.severity_weight = new_severity
        policy.impact_weight = new_impact
        policy.urgency_weight = new_urgency
        policy.vulnerability_weight = new_vuln
        policy.duplicate_weight = new_dup

        updated.append({
            'department': dept,
            'feedback_count': drift['count'],
            'old_weights': old_weights,
            'new_weights': {
                'severity': new_severity,
                'impact': new_impact,
                'urgency': new_urgency,
                'vulnerability': new_vuln,
                'duplicate': new_dup
            }
        })

    db.commit()
    return {
        'message': f'Learning applied from {len(reliable_feedback)} reliable overrides across {len(updated)} department(s).',
        'high_trust_officers': [oid for oid, ts in officer_trust.items() if ts >= 0.70],
        'updated': updated
    }

# ===================== HOTSPOT & CONTEXT ENDPOINTS =====================

@app.get("/hotspots")
def get_hotspots(db: Session = Depends(get_db)):
    complaints = db.query(Complaint).filter(
        Complaint.admissible == True,
        Complaint.status.notin_(["Resolved", "Closed", "Rejected"])
    ).all()
    complaint_dicts = [to_dict(c) for c in complaints]

    # Enrich complaint dicts: fallback location = department + ward when structured_json.location is null
    officers_by_id = {o.officer_id: o for o in db.query(Officer).all()}
    for cd in complaint_dicts:
        sj = cd.get('structured_json', {})
        if isinstance(sj, str):
            try:
                import json as _json
                sj = _json.loads(sj)
            except Exception:
                sj = {}
        loc = sj.get('location') if sj else None
        if not loc or loc.lower() in ('unknown', 'none', ''):
            # Use ward if officer is assigned, else department
            oid = cd.get('assigned_officer_id')
            officer = officers_by_id.get(oid)
            if officer and officer.ward:
                loc = f"{officer.ward}, {officer.zone}"
            elif officer and officer.zone:
                loc = officer.zone
            else:
                loc = cd.get('department', '')
            if sj is None:
                sj = {}
            sj['location'] = loc
            cd['structured_json'] = sj

    # Lower threshold to 3, extend window to 30 days to cover historical complaint clusters
    hotspots = utils.detect_hotspots(complaint_dicts, min_count=3, days=30)


    # Enrich each hotspot with severity info and officer load data
    officers_in_db = db.query(Officer).all()
    officer_map = {o.officer_id: o for o in officers_in_db}

    for hotspot in hotspots:
        ids = hotspot.get('complaint_ids', [])
        cluster = db.query(Complaint).filter(Complaint.id.in_(ids)).all()
        if cluster:
            scores = [c.final_priority_score or 0 for c in cluster]
            avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0.0
        hotspot['severity_score'] = round(avg_score, 3)
        if avg_score >= 0.75:
            hotspot['severity_label'] = 'Critical'
        elif avg_score >= 0.50:
            hotspot['severity_label'] = 'High'
        elif avg_score >= 0.30:
            hotspot['severity_label'] = 'Medium'
        else:
            hotspot['severity_label'] = 'Low'

        # Officer load per hotspot zone (match by zone substring)
        hotspot_loc = hotspot.get('location', '').lower()
        hotspot_dept = hotspot.get('category', '')
        assigned_officer_ids = set(c.assigned_officer_id for c in cluster if c.assigned_officer_id)
        officers_in_zone = []
        for o in officers_in_db:
            if hotspot_loc and (hotspot_loc in o.zone.lower() or o.zone.lower() in hotspot_loc):
                officers_in_zone.append(o.officer_id)
        hotspot['officers_in_zone'] = officers_in_zone
        hotspot['assigned_officer_ids'] = list(assigned_officer_ids)

        # Recommendation: flag if zone is understaffed
        if len(officers_in_zone) == 0:
            hotspot['recommend_officer'] = True
            hotspot['recommendation_reason'] = f"No officer mapped to this zone. Add an officer for {hotspot_dept}."
        else:
            # Check if mapped officers are overloaded (>10 active complaints)
            overloaded = []
            for oid in officers_in_zone:
                active_count = db.query(Complaint).filter(
                    Complaint.assigned_officer_id == oid,
                    Complaint.status.notin_(["Resolved", "Closed", "Rejected"])
                ).count()
                if active_count > 10:
                    overloaded.append(oid)
            if len(overloaded) == len(officers_in_zone):
                hotspot['recommend_officer'] = True
                hotspot['recommendation_reason'] = f"All {len(overloaded)} officer(s) in zone are handling >10 active complaints each. Additional officer recommended."
            else:
                hotspot['recommend_officer'] = False
                hotspot['recommendation_reason'] = ''

    return hotspots

@app.get("/complaints/{complaint_id}/similar")
def get_similar(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    all_complaints = db.query(Complaint).filter(
        Complaint.admissible == True,
        Complaint.id != complaint_id
    ).all()
    complaint_dicts = [to_dict(c) for c in all_complaints]
    
    vectorizer = utils.load_fallback_vectorizer()
    similar = utils.search_similar_complaints(
        complaint.complaint_text, complaint_dicts, vectorizer, k=5
    )
    return similar

@app.get("/complaints/{complaint_id}/duplicates")
def get_duplicates(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    duplicates = []
    if complaint.lead_id:
        cluster = db.query(Complaint).filter(
            Complaint.lead_id == complaint.lead_id,
            Complaint.id != complaint_id
        ).all()
        duplicates = [to_dict(c) for c in cluster]
    else:
        cluster = db.query(Complaint).filter(
            Complaint.lead_id == complaint_id
        ).all()
        duplicates = [to_dict(c) for c in cluster]
    
    return {
        'complaint_id': complaint_id,
        'duplicate_count': len(duplicates),
        'duplicates': duplicates
    }

@app.get("/complaints/{complaint_id}/escalation-history")
def get_escalation_history(complaint_id: str, db: Session = Depends(get_db)):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    try:
        history = json.loads(complaint.escalation_history) if complaint.escalation_history else []
    except Exception:
        history = []
    return {'complaint_id': complaint_id, 'escalation_history': history}


# ===================== AUDIT TRAIL ENDPOINTS =====================

@app.get("/complaints/{complaint_id}/audit-log")
def get_complaint_audit_log(complaint_id: str, db: Session = Depends(get_db)):
    logs = db.query(AuditLog).filter(AuditLog.complaint_id == complaint_id).order_by(AuditLog.timestamp).all()
    return [{
        'id': l.id, 'complaint_id': l.complaint_id, 'timestamp': l.timestamp,
        'action': l.action, 'from_value': l.from_value, 'to_value': l.to_value,
        'performed_by': l.performed_by, 'performer_role': l.performer_role, 'notes': l.notes
    } for l in logs]

@app.get("/audit-logs")
def get_all_audit_logs(action: Optional[str] = None, complaint_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if complaint_id:
        query = query.filter(AuditLog.complaint_id == complaint_id)
    logs = query.order_by(AuditLog.timestamp.desc()).limit(500).all()
    return [{
        'id': l.id, 'complaint_id': l.complaint_id, 'timestamp': l.timestamp,
        'action': l.action, 'from_value': l.from_value, 'to_value': l.to_value,
        'performed_by': l.performed_by, 'performer_role': l.performer_role, 'notes': l.notes
    } for l in logs]

# ===================== ENHANCED STATS ENDPOINTS =====================

@app.get("/stats/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db)):
    # Check for SLA breaches first
    check_and_escalate_sla(db)
    
    all_complaints = db.query(Complaint).filter(Complaint.admissible == True).all()
    
    status_counts = {}
    dept_counts = {}
    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    category_counts = {}
    total_resolution_hours = 0
    resolved_count = 0
    sla_breached_count = 0
    sla_compliant_count = 0
    
    for c in all_complaints:
        status_counts[c.status] = status_counts.get(c.status, 0) + 1
        dept_counts[c.department] = dept_counts.get(c.department, 0) + 1
        label = c.officer_override or c.priority_label or "Low"
        if label in priority_counts:
            priority_counts[label] += 1
        category_counts[c.category] = category_counts.get(c.category, 0) + 1
        
        if c.status in ["Resolved", "Closed"]:
            resolved_count += 1
            if c.resolved_at and c.timestamp:
                try:
                    sub = datetime.datetime.strptime(c.timestamp, "%Y-%m-%d %H:%M:%S")
                    res = datetime.datetime.strptime(c.resolved_at, "%Y-%m-%d %H:%M:%S")
                    total_resolution_hours += (res - sub).total_seconds() / 3600
                except:
                    pass
            if getattr(c, 'sla_breached', False):
                sla_breached_count += 1
            else:
                sla_compliant_count += 1
        elif c.status not in ["Rejected"]:
            if getattr(c, 'sla_breached', False):
                sla_breached_count += 1
    
    avg_resolution_hours = round(total_resolution_hours / max(resolved_count, 1), 1)
    total_active = sum(1 for c in all_complaints if c.status not in ["Resolved", "Closed", "Rejected"])
    
    rejected_count = db.query(Complaint).filter(Complaint.admissible == False).count()
    overrides_count = db.query(OfficerFeedback).count()
    
    return {
        "total_complaints": len(all_complaints),
        "total_active": total_active,
        "resolved_count": resolved_count,
        "rejected_count": rejected_count,
        "overrides_count": overrides_count,
        "status_counts": status_counts,
        "department_counts": dept_counts,
        "priority_counts": priority_counts,
        "category_counts": category_counts,
        "avg_resolution_hours": avg_resolution_hours,
        "sla_breached_count": sla_breached_count,
        "sla_compliant_count": sla_compliant_count,
        "sla_compliance_rate": round(sla_compliant_count / max(sla_compliant_count + sla_breached_count, 1) * 100, 1)
    }

@app.get("/stats/officer/{officer_id}")
def get_officer_stats(officer_id: str, db: Session = Depends(get_db)):
    officer_complaints = db.query(Complaint).filter(
        Complaint.assigned_officer_id == officer_id,
        Complaint.admissible == True
    ).all()
    
    total = len(officer_complaints)
    resolved = sum(1 for c in officer_complaints if c.status in ["Resolved", "Closed"])
    sla_breached = sum(1 for c in officer_complaints if getattr(c, 'sla_breached', False))
    
    status_breakdown = {}
    for c in officer_complaints:
        status_breakdown[c.status] = status_breakdown.get(c.status, 0) + 1
    
    total_hours = 0
    resolved_with_time = 0
    for c in officer_complaints:
        if c.status in ["Resolved", "Closed"] and c.resolved_at and c.timestamp:
            try:
                sub = datetime.datetime.strptime(c.timestamp, "%Y-%m-%d %H:%M:%S")
                res = datetime.datetime.strptime(c.resolved_at, "%Y-%m-%d %H:%M:%S")
                total_hours += (res - sub).total_seconds() / 3600
                resolved_with_time += 1
            except:
                pass
    
    overrides = db.query(OfficerFeedback).filter(OfficerFeedback.officer_id == officer_id).count()
    
    return {
        "officer_id": officer_id,
        "total_assigned": total,
        "total_resolved": resolved,
        "resolution_rate": round(resolved / max(total, 1) * 100, 1),
        "avg_resolution_hours": round(total_hours / max(resolved_with_time, 1), 1),
        "sla_compliance_rate": round((total - sla_breached) / max(total, 1) * 100, 1),
        "sla_breached": sla_breached,
        "status_breakdown": status_breakdown,
        "overrides_count": overrides,
        "current_active": sum(1 for c in officer_complaints if c.status not in ["Resolved", "Closed", "Rejected"])
    }

@app.get("/complaints/sla-breached")
def get_sla_breached(db: Session = Depends(get_db)):
    check_and_escalate_sla(db)
    breached = db.query(Complaint).filter(
        Complaint.sla_breached == True,
        ~Complaint.status.in_(["Closed", "Rejected"])
    ).all()
    return [to_dict(c) for c in breached]

@app.get("/complaints/by-status/{status}")
def get_complaints_by_status(status: str, officer_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Complaint).filter(Complaint.status == status, Complaint.admissible == True)
    if officer_id:
        query = query.filter(Complaint.assigned_officer_id == officer_id)
    comps = query.all()
    result = [to_dict(c) for c in comps]
    result.sort(key=lambda x: x['final_priority_score'], reverse=True)
    return result


# ===================== BATCH OFFICER STATS =====================

@app.get("/stats/all-officers")
def get_all_officer_stats(db: Session = Depends(get_db)):
    """Returns aggregated stats for ALL officers in a single call (avoids N+1 queries)."""
    officers = db.query(Officer).all()
    result = []

    for officer in officers:
        oid = officer.officer_id
        officer_complaints = db.query(Complaint).filter(
            Complaint.assigned_officer_id == oid,
            Complaint.admissible == True
        ).all()

        total = len(officer_complaints)
        resolved = sum(1 for c in officer_complaints if c.status in ["Resolved", "Closed"])
        active = sum(1 for c in officer_complaints if c.status not in ["Resolved", "Closed", "Rejected"])
        sla_breached = sum(1 for c in officer_complaints if getattr(c, 'sla_breached', False))

        total_hours = 0.0
        resolved_with_time = 0
        for c in officer_complaints:
            if c.status in ["Resolved", "Closed"] and c.resolved_at and c.timestamp:
                try:
                    sub = datetime.datetime.strptime(c.timestamp, "%Y-%m-%d %H:%M:%S")
                    res = datetime.datetime.strptime(c.resolved_at, "%Y-%m-%d %H:%M:%S")
                    total_hours += (res - sub).total_seconds() / 3600
                    resolved_with_time += 1
                except Exception:
                    pass

        overrides_count = db.query(OfficerFeedback).filter(OfficerFeedback.officer_id == oid).count()

        status_breakdown = {}
        for c in officer_complaints:
            status_breakdown[c.status] = status_breakdown.get(c.status, 0) + 1

        result.append({
            'officer_id': oid,
            'name': officer.name,
            'department': officer.department,
            'zone': officer.zone,
            'ward': officer.ward,
            'designation': officer.designation,
            'total_assigned': total,
            'total_resolved': resolved,
            'current_active': active,
            'resolution_rate': round(resolved / max(total, 1) * 100, 1),
            'avg_resolution_hours': round(total_hours / max(resolved_with_time, 1), 1),
            'sla_compliance_rate': round((total - sla_breached) / max(total, 1) * 100, 1),
            'sla_breached': sla_breached,
            'overrides_count': overrides_count,
            'status_breakdown': status_breakdown
        })

    result.sort(key=lambda x: x['resolution_rate'], reverse=True)
    return result

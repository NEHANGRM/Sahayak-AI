"""
Sahayak AI - Intelligent NLP-Driven Complaint Triage System
Streamlit Application with Role-Based Dashboards
  - Login Page (default entry point)
  - Citizen Portal (role=citizen)
  - Officer Dashboard (role=officer, filtered by officer_id)
  - Admin Dashboard (role=admin, full access)
"""

import streamlit as st
import textwrap
import pandas as pd
from datetime import datetime
import requests
import os
import re
import base64

API_URL = os.environ.get("SAHAYAK_API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Sahayak AI - Smart Complaint Triage",
    page_icon="SA",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def get_logo_base64():
    try:
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""

# ════════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ════════════════════════════════════════════════════════════════════════════════

if 'user' not in st.session_state:
    st.session_state.user = None

if 'officer_overrides' not in st.session_state:
    st.session_state.officer_overrides = []

if 'login_error' not in st.session_state:
    st.session_state.login_error = None

if 'login_role' not in st.session_state:
    st.session_state.login_role = None


# ════════════════════════════════════════════════════════════════════════════════
# API HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def api_login(username, password):
    """Authenticate user via backend API"""
    try:
        r = requests.post(f"{API_URL}/auth/login", json={"username": username, "password": password})
        if r.status_code == 200:
            return r.json(), None
        else:
            detail = r.json().get('detail', 'Invalid credentials')
            return None, detail
    except Exception as e:
        return None, f"Cannot connect to backend server: {e}"


def api_signup(username, password, name):
    """Register citizen via backend API"""
    try:
        r = requests.post(f"{API_URL}/auth/signup", json={"username": username, "password": password, "name": name})
        if r.status_code == 200:
            return r.json(), None
        else:
            detail = r.json().get('detail', 'Username already exists')
            return None, detail
    except Exception as e:
        return None, f"Cannot connect to backend server: {e}"


def get_citizen_complaints(username):
    """Fetch complaints submitted by a specific citizen"""
    try:
        r = requests.get(f"{API_URL}/complaints/citizen/{username}")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_stats():
    """Fetch system-wide stats"""
    try:
        r = requests.get(f"{API_URL}/stats")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"active_count": 0, "rejected_count": 0, "overrides_count": 0}


def get_sla_breached():
    """Fetch SLA breached complaints"""
    try:
        r = requests.get(f"{API_URL}/complaints/sla-breached")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_complaints(officer_id=None):
    """Fetch active complaints, optionally filtered by officer_id"""
    try:
        params = {}
        if officer_id:
            params["officer_id"] = officer_id
        r = requests.get(f"{API_URL}/complaints", params=params)
        if r.status_code == 200:
            return r.json()
    except Exception:
        st.warning("Cannot connect to backend server. Make sure api.py is running.")
    return []


def get_resolved_complaints():
    """Fetch resolved complaints"""
    try:
        r = requests.get(f"{API_URL}/complaints/resolved")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_rejected_complaints():
    """Fetch rejected/restricted complaints"""
    try:
        r = requests.get(f"{API_URL}/complaints/rejected")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def predict_complaint(complaint_text, submitted_by=None):
    """Submit a complaint for triage"""
    try:
        payload = {"complaint_text": complaint_text}
        if submitted_by:
            payload["submitted_by"] = submitted_by
        r = requests.post(f"{API_URL}/triage", json=payload)
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Error processing grievance: {r.text}")
            return None
    except Exception as e:
        st.error(f"Failed to connect to triage API server: {e}")
        return None


def get_officers():
    """Fetch list of all officers"""
    try:
        r = requests.get(f"{API_URL}/officers")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_officer_display_name(off_id):
    if not off_id:
        return "Not Assigned"
    officers = get_officers() or []
    for o in officers:
        if o.get('officer_id') == off_id:
            return f"{o.get('name', 'Unknown')} (ID: {off_id})"
    return f"ID: {off_id}"


def add_officer(officer_data):
    """Add a new officer"""
    try:
        r = requests.post(f"{API_URL}/officers", json=officer_data)
        if r.status_code == 200:
            return r.json(), None
        else:
            return None, r.text
    except Exception as e:
        return None, str(e)


def get_department_policies():
    """Fetch department weight policies"""
    try:
        r = requests.get(f"{API_URL}/department-policies")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def update_department_policy(department, weights):
    """Update weights for a department"""
    try:
        r = requests.put(f"{API_URL}/department-policies/{department}", json=weights)
        if r.status_code == 200:
            return r.json(), None
        else:
            return None, r.text
    except Exception as e:
        return None, str(e)


def get_feedback_stats():
    """Fetch officer feedback/trust score stats"""
    try:
        r = requests.get(f"{API_URL}/feedback/stats")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_feedback_export():
    """Export all feedback records"""
    try:
        r = requests.get(f"{API_URL}/feedback/export")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_hotspots():
    """Fetch hotspot alerts"""
    try:
        r = requests.get(f"{API_URL}/hotspots")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_similar_complaints(complaint_id):
    """Fetch similar complaints via RAG"""
    try:
        r = requests.get(f"{API_URL}/complaints/{complaint_id}/similar")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_duplicate_cluster(complaint_id):
    """Fetch duplicate cluster for a complaint"""
    try:
        r = requests.get(f"{API_URL}/complaints/{complaint_id}/duplicates")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def get_escalation_history(complaint_id):
    """Fetch escalation history for a complaint"""
    try:
        r = requests.get(f"{API_URL}/complaints/{complaint_id}/escalation-history")
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


# ════════════════════════════════════════════════════════════════════════════════
# CSS AND STYLING
# ════════════════════════════════════════════════════════════════════════════════


def accept_complaint(complaint_id, officer_id):
    try:
        r = requests.post(f"{API_URL}/complaints/{complaint_id}/accept", json={"officer_id": officer_id})
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def start_progress(complaint_id, officer_id, notes=""):
    try:
        r = requests.post(f"{API_URL}/complaints/{complaint_id}/start-progress", json={"officer_id": officer_id, "notes": notes})
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def field_inspection(complaint_id, officer_id, notes=""):
    try:
        r = requests.post(f"{API_URL}/complaints/{complaint_id}/field-inspection", json={"officer_id": officer_id, "notes": notes})
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def escalate_complaint(complaint_id, officer_id, reason=""):
    try:
        r = requests.post(f"{API_URL}/complaints/{complaint_id}/escalate", json={"officer_id": officer_id, "reason": reason})
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def close_complaint(complaint_id, admin_id, notes=""):
    try:
        r = requests.post(f"{API_URL}/complaints/{complaint_id}/close", json={"admin_id": admin_id, "notes": notes})
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def reassign_complaint(complaint_id, admin_id, new_officer_id, reason=""):
    try:
        r = requests.post(f"{API_URL}/complaints/{complaint_id}/reassign", json={"admin_id": admin_id, "new_officer_id": new_officer_id, "reason": reason})
        return r.status_code == 200, r.json() if r.status_code == 200 else r.text
    except Exception as e:
        return False, str(e)

def get_dashboard_stats():
    try:
        r = requests.get(f"{API_URL}/stats/dashboard")
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def get_officer_stats(officer_id):
    try:
        r = requests.get(f"{API_URL}/stats/officer/{officer_id}")
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def get_audit_logs(complaint_id=None):
    try:
        params = {}
        if complaint_id:
            params["complaint_id"] = complaint_id
        r = requests.get(f"{API_URL}/audit-logs", params=params)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def get_all_officer_stats():
    """Fetch stats for all officers in one batch call"""
    try:
        r = requests.get(f"{API_URL}/stats/all-officers")
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def apply_feedback_learning():
    """Trigger feedback-based weight learning in backend"""
    try:
        r = requests.post(f"{API_URL}/feedback/apply-learning")
        if r.status_code == 200:
            return r.json(), None
        else:
            return None, r.text
    except Exception as e:
        return None, str(e)

def inject_custom_css():
    """Inject government-themed styling"""
    css = """
    <style>
    /* Reset background colors */
    .stApp {
        background-color: #f8f9fa !important;
    }
    
    /* Base typography (excluding .stApp to protect icon fonts from inheriting Arial) */
    p, label, li, td, th, h1, h2, h3, h4, h5, h6, input, textarea, button, select {
        font-family: Arial, Helvetica, sans-serif;
    }
    
    /* Default dark headings color (no !important so inline styles override it) */
    h1, h2, h3, h4, h5, h6 {
        color: #0f294a;
    }
    
    /* Default dark text color for contrast on the light background (no !important) */
    p, li, label, td, th, [data-testid="stMarkdownContainer"] {
        color: #2d3748;
    }
    
    .stWidgetLabel p, label {
        color: #2d3748;
    }
    
    /* Captions */
    small, .stCaptionContainer, div[data-testid="stCaptionContainer"] p {
        color: #4a5568;
    }
    
    /* Metrics labels and values visibility */
    div[data-testid="stMetricLabel"] > div, div[data-testid="stMetricValue"] > div {
        color: #2d3748 !important;
    }
    
    /* Streamlit tabs text visibility */
    button[role="tab"] p {
        color: #2d3748 !important;
    }
    button[role="tab"][aria-selected="true"] p {
        color: #0f294a !important;
        font-weight: bold !important;
    }
    
    /* Sidebar text colors */
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label {
        color: #2d3748;
    }
    
    /* Selectbox selected option text color */
    div[data-baseweb="select"] span, div[data-baseweb="select"] div {
        color: #2d3748 !important;
    }
    
    /* Buttons style */
    .stButton>button {
        background-color: #0f294a !important;
        color: white !important;
        border: 1px solid #0f294a !important;
        border-radius: 4px !important;
        padding: 6px 16px !important;
        font-weight: bold !important;
        font-size: 14px !important;
        box-shadow: 0px 1px 3px rgba(0,0,0,0.1) !important;
        transition: none !important;
    }
    
    .stButton>button:hover {
        background-color: #1a3d66 !important;
        border-color: #1a3d66 !important;
        color: white !important;
    }
    
    /* Protect button text colors */
    .stButton>button p, .stButton>button span {
        color: white !important;
    }
    
    /* Text inputs */
    .stTextArea textarea {
        border: 1px solid #cbd5e0 !important;
        border-radius: 4px !important;
        background-color: #ffffff !important;
        color: #2d3748 !important;
        font-size: 14px !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #0f294a !important;
        box-shadow: 0 0 0 1px #0f294a !important;
    }
    
    .stTextInput input {
        border: 1px solid #cbd5e0 !important;
        border-radius: 4px !important;
        background-color: #ffffff !important;
        color: #2d3748 !important;
        font-size: 14px !important;
    }
    
    .stTextInput input:focus {
        border-color: #0f294a !important;
        box-shadow: 0 0 0 1px #0f294a !important;
    }
    
    /* Expanders */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 4px !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
        margin-bottom: 15px !important;
    }
    
    /* Sidebar container styling */
    section[data-testid="stSidebar"] {
        background-color: #eef2f6 !important;
        border-right: 1px solid #cbd5e0 !important;
    }
    
    /* Banner overrides to force white/light text on dark navy backgrounds */
    .gov-banner h1, h1.gov-banner-title {
        color: #ffffff !important;
    }
    .gov-banner p, p.gov-banner-subtitle {
        color: #e2e8f0 !important;
    }
    
    .sidebar-gov-header h4, h4.sidebar-gov-title {
        color: #ffffff !important;
    }
    
    /* Stamp overrides to respect inline dynamic colors */
    .priority-stamp span.priority-stamp-meta {
        color: #718096 !important;
    }
    .priority-stamp h3.priority-stamp-title.critical {
        color: #9b2c2c !important;
    }
    .priority-stamp h3.priority-stamp-title.high {
        color: #9c4221 !important;
    }
    .priority-stamp h3.priority-stamp-title.medium {
        color: #2b6cb0 !important;
    }
    .priority-stamp h3.priority-stamp-title.low {
        color: #276749 !important;
    }
    .priority-stamp p.priority-stamp-body {
        color: #2d3748 !important;
    }
    
    /* Streamlit Alert/Notification box styling overrides */
    div[data-testid="stNotification"], div[data-testid="stAlert"], div[class*="stAlert"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e0 !important;
        border-left: 6px solid #0f294a !important;
        border-radius: 4px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    
    /* Force high-contrast text color inside all alert/notification boxes */
    div[data-testid="stNotification"] p,
    div[data-testid="stNotification"] li,
    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] li,
    div[class*="stAlert"] p,
    div[class*="stAlert"] li {
        color: #1a202c !important;
        font-weight: 500 !important;
    }
    
    /* Login page card styling */
    .login-card {
        max-width: 380px;
        margin: 30px auto;
        background: #ffffff;
        border-radius: 8px;
        border: 1px solid #cbd5e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        overflow: hidden;
    }
    .login-header {
        background: linear-gradient(135deg, #0f294a 0%, #1a365d 50%, #0f294a 100%);
        padding: 28px 24px;
        text-align: center;
        border-bottom: 4px solid #c49a2a;
    }
    .login-header h2 {
        color: #ffffff !important;
        margin: 0;
        font-size: 22px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        font-weight: 900;
    }
    .login-header .login-subtitle {
        color: #cbd5e0 !important;
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-top: 6px;
    }
    .login-header .login-emblem {
        font-size: 36px;
        margin-bottom: 8px;
    }
    .login-body {
        padding: 30px 28px;
    }
    .login-footer {
        background-color: #f7fafc;
        border-top: 1px solid #e2e8f0;
        padding: 16px 28px;
        font-size: 12px;
        color: #718096;
    }
    .login-footer table {
        width: 100%;
        font-size: 11.5px;
        border-collapse: collapse;
    }
    .login-footer table th {
        background-color: #eef2f6;
        color: #0f294a;
        padding: 6px 8px;
        text-align: left;
        border: 1px solid #e2e8f0;
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .login-footer table td {
        padding: 5px 8px;
        border: 1px solid #e2e8f0;
        color: #4a5568;
        font-family: monospace;
        font-size: 11px;
    }
    
    /* Number input styling */
    .stNumberInput input {
        border: 1px solid #cbd5e0 !important;
        border-radius: 4px !important;
        background-color: #ffffff !important;
        color: #2d3748 !important;
        font-size: 14px !important;
    }

    /* Remove default Streamlit top padding for cleaner header fit */
    div.block-container {
        padding-top: 2rem !important;
    }

    /* Full-width government header box */
    .gov-header-container {
        background-color: #0f294a;
        padding: 22px 30px;
        border-top: 6px solid #ff9933;
        border-bottom: 6px solid #138808;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 6px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 30px;
        width: 100%;
        box-sizing: border-box;
    }
    .gov-header-left {
        text-align: left;
    }
    .gov-header-left-title {
        margin: 0;
        font-size: 30px;
        font-weight: 900;
        letter-spacing: 1.5px;
        color: #ffffff !important;
        text-transform: uppercase;
        line-height: 1.1;
    }
    .gov-header-left-subtitle1 {
        font-size: 11px;
        color: #ff9933 !important;
        font-weight: bold;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .gov-header-left-subtitle2 {
        font-size: 13px;
        color: #cbd5e0 !important;
        font-weight: 500;
        letter-spacing: 0.8px;
        margin-top: 4px;
        text-transform: uppercase;
    }
    .gov-header-right {
        display: flex;
        gap: 12px;
        align-items: center;
    }
    .gov-nav-btn {
        padding: 10px 18px;
        font-size: 12.5px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-radius: 4px;
        text-decoration: none !important;
        transition: all 0.2s ease-in-out;
        display: inline-block;
        text-align: center;
        cursor: pointer;
    }
    .citizen-btn {
        background-color: #ff9933;
        color: white !important;
        border: 1.5px solid #ff9933;
    }
    .citizen-btn:hover {
        background-color: #e68a00;
        border-color: #e68a00;
        box-shadow: 0 4px 12px rgba(255, 153, 51, 0.4);
        transform: translateY(-1px);
    }
    .officer-btn {
        background-color: #138808;
        color: white !important;
        border: 1.5px solid #138808;
    }
    .officer-btn:hover {
        background-color: #0f6c06;
        border-color: #0f6c06;
        box-shadow: 0 4px 12px rgba(19, 136, 8, 0.4);
        transform: translateY(-1px);
    }
    .admin-btn {
        background-color: transparent;
        color: #ffffff !important;
        border: 1.5px solid #ffffff;
    }
    .admin-btn:hover {
        background-color: #ffffff;
        color: #0f294a !important;
        box-shadow: 0 4px 12px rgba(255, 255, 255, 0.25);
        transform: translateY(-1px);
    }
    
    /* Explanation elements */
    .landing-hero {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        padding: 40px;
        border-radius: 8px;
        border-left: 5px solid #0f294a;
        margin-bottom: 30px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .landing-hero h2 {
        color: #0f294a !important;
        font-weight: 800;
        margin-top: 0;
    }
    .landing-hero p {
        font-size: 16px;
        line-height: 1.6;
        color: #4a5568;
    }
    .info-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        height: 100%;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .info-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.05);
    }
    .info-card.accent-saffron {
        border-top: 4px solid #ff9933;
    }
    .info-card.accent-navy {
        border-top: 4px solid #0f294a;
    }
    .info-card.accent-green {
        border-top: 4px solid #138808;
    }
    .info-card h4 {
        color: #0f294a !important;
        font-weight: 700;
        margin-top: 0;
        margin-bottom: 12px;
        font-size: 18px;
    }
    .info-card p {
        font-size: 13.5px;
        color: #4a5568;
        line-height: 1.5;
        margin: 0;
    }
    
    /* Workflow step badges */
    .workflow-container {
        display: flex;
        flex-direction: column;
        gap: 20px;
        margin-top: 20px;
    }
    .workflow-step {
        display: flex;
        gap: 20px;
        background: #ffffff;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        align-items: flex-start;
    }
    .step-badge {
        background-color: #0f294a;
        color: white !important;
        font-weight: bold;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        font-size: 16px;
        box-shadow: 0 2px 4px rgba(15,41,74,0.2);
    }
    .step-content h5 {
        color: #0f294a !important;
        margin: 0 0 6px 0;
        font-weight: 700;
        font-size: 15px;
    }
    .step-content p {
        margin: 0;
        font-size: 13px;
        color: #4a5568;
        line-height: 1.45;
    }
    
    /* Style the second-to-last button in the sidebar as a profile card */
    section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button {
        background-color: #ffffff !important;
        border: 1.5px solid #cbd5e0 !important;
        border-radius: 8px !important;
        padding: 10px 12px 10px 60px !important; /* Space for avatar on left */
        min-height: 58px !important;
        width: 100% !important;
        position: relative !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04) !important;
        transition: background-color 0.2s ease, border-color 0.2s ease !important;
    }

    section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button:hover {
        background-color: #f7fafc !important;
        border-color: #a0aec0 !important;
    }

    /* Target the text inside the button to align left and style it */
    section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button div[data-testid="stMarkdownContainer"] {
        text-align: left !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button p {
        margin: 0 !important;
        line-height: 1.25 !important;
        font-family: Arial, sans-serif !important;
    }

    section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button p:first-child {
        font-size: 13px !important;
        font-weight: bold !important;
        color: #0f294a !important;
    }

    section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button p:last-child {
        font-size: 10.5px !important;
        color: #4a5568 !important;
        font-weight: normal !important;
        margin-top: 3px !important;
    }
    </style>
    <script>
    function applyPriorityColors() {
        const expanders = document.querySelectorAll('div[data-testid="stExpander"]');
        expanders.forEach(exp => {
            const header = exp.querySelector('summary') || exp;
            const headerText = header.textContent || header.innerText;
            
            // 1. Priority colors (controls left border)
            let leftBorderColor = "#718096"; // Default/Low
            if (headerText.includes("Level: CRITICAL") || headerText.includes("Level: HIGH")) {
                leftBorderColor = "#c53030";
            } else if (headerText.includes("Level: MEDIUM")) {
                leftBorderColor = "#d97706";
            }

            // 2. Status colors (controls background and text)
            let bgColor = "#ffffff";
            let borderColor = "#e2e8f0";
            let textColor = "#2d3748";

            if (headerText.includes("Status: SUBMITTED") || headerText.includes("Status: ASSIGNED")) {
                bgColor = "#ebf8ff"; // Light blue
                borderColor = "#90cdf4";
                textColor = "#2b6cb0";
            } else if (headerText.includes("Status: ACCEPTED") || headerText.includes("Status: IN PROGRESS") || headerText.includes("Status: FIELD INSPECTION")) {
                bgColor = "#faf5ff"; // Light purple
                borderColor = "#d6bcfa";
                textColor = "#553c9a";
            } else if (headerText.includes("Status: ESCALATED")) {
                bgColor = "#fff5f5"; // Light red
                borderColor = "#feb2b2";
                textColor = "#c53030";
            } else if (headerText.includes("Status: RESOLVED") || headerText.includes("Status: CLOSED")) {
                bgColor = "#f0fff4"; // Light green
                borderColor = "#9ae6b4";
                textColor = "#276749";
            } else if (headerText.includes("Status: REJECTED")) {
                bgColor = "#edf2f7"; // Light gray
                borderColor = "#cbd5e0";
                textColor = "#4a5568";
            }

            // Fallback: If priority is CRITICAL/HIGH but no status caught it, keep red tint
            if (bgColor === "#ffffff" && (headerText.includes("Level: CRITICAL") || headerText.includes("Level: HIGH"))) {
                bgColor = "#fff5f5";
                borderColor = "#feb2b2";
                textColor = "#9b2c2c";
            }
            
            exp.style.setProperty("background-color", bgColor, "important");
            exp.style.setProperty("border", `1px solid ${borderColor}`, "important");
            exp.style.setProperty("border-left", `8px solid ${leftBorderColor}`, "important");
            
            const titleText = exp.querySelector('p');
            if (titleText) {
                titleText.style.setProperty("color", textColor, "important");
                titleText.style.setProperty("font-weight", "bold", "important");
            }
        });
    }

    if (!window.priorityColorsInterval) {
        applyPriorityColors();
        window.priorityColorsInterval = setInterval(applyPriorityColors, 400);
    }
    </script>
    """
    st.markdown(css, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# REUSABLE UI COMPONENTS
# ════════════════════════════════════════════════════════════════════════════════

def get_notifications(user_id):
    try:
        r = requests.get(f"{API_URL}/notifications/{user_id}")
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

def mark_notification_read(notif_id):
    try:
        requests.post(f"{API_URL}/notifications/{notif_id}/read")
    except Exception:
        pass

def render_notifications_bell(user_id):
    notifs = get_notifications(user_id)
    unread = [n for n in notifs if not n.get("is_read")]
    
    col1, col2 = st.columns([10, 1])
    with col2:
        if hasattr(st, "popover"):
            with st.popover(f"🔔 ({len(unread)})"):
                st.markdown("### Notifications")
                if not notifs:
                    st.write("No notifications.")
                else:
                    for n in notifs:
                        icon = "🔴" if not n.get("is_read") else "⚪"
                        st.markdown(f"{icon} **{n.get('timestamp')}**\n{n.get('message')}")
                        if not n.get("is_read"):
                            if st.button("Mark Read", key=f"read_{n.get('id')}"):
                                mark_notification_read(n.get("id"))
                                st.rerun()
                        st.markdown("---")
        else:
            # Fallback for older Streamlit
            st.button(f"🔔 ({len(unread)})")

def render_government_banner():
    """Renders a formal government banner at the top of the main area"""
    logo_b64 = get_logo_base64()
    if logo_b64:
        html = f"""<div class="gov-banner" style="background-color: #0f294a; padding: 15px 22px; border-top: 5px solid #ff9933; border-bottom: 5px solid #138808; display: flex; align-items: center; gap: 20px; margin-bottom: 25px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
<img src="data:image/png;base64,{logo_b64}" style="height: 65px; width: auto; border-radius: 4px;" alt="Sahayak AI Logo">
<div style="text-align: left;">
<div style="font-size: 11px; color: #ff9933; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px;">Government of India Middleware Platform</div>
<h1 class="gov-banner-title" style="margin: 0; font-size: 28px; font-weight: 900; letter-spacing: 1.5px; color: #ffffff; text-transform: uppercase; line-height: 1.1;">SAHAYAK AI</h1>
<div style="font-size: 13px; color: #cbd5e0; font-weight: 500; letter-spacing: 0.8px; margin-top: 4px; text-transform: uppercase;">National Grievance Triage & Redressal Board</div>
</div>
</div>"""
    else:
        html = """<div class="gov-banner" style="background-color: #0f294a; padding: 22px; border-top: 5px solid #ff9933; border-bottom: 5px solid #138808; text-align: center; margin-bottom: 25px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
<div style="font-size: 11px; color: #ff9933; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px;">Government of India Middleware Platform</div>
<h1 class="gov-banner-title" style="margin: 0; font-size: 32px; font-weight: 900; letter-spacing: 1.5px; color: #ffffff; text-transform: uppercase;">SAHAYAK AI</h1>
<div style="font-size: 13px; color: #cbd5e0; font-weight: 500; letter-spacing: 0.8px; margin-top: 6px; text-transform: uppercase;">National Grievance Triage & Redressal Board</div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)


def render_priority_stamp(priority_label, priority_score, explanation):
    """Renders a formal triage stamp badge"""
    colors = {
        "Critical": {"border": "#c53030", "bg": "#fff5f5", "text": "#9b2c2c"},
        "High": {"border": "#dd6b20", "bg": "#fffaf0", "text": "#9c4221"},
        "Medium": {"border": "#3182ce", "bg": "#ebf8ff", "text": "#2b6cb0"},
        "Low": {"border": "#38a169", "bg": "#f0fff4", "text": "#276749"}
    }
    style = colors.get(priority_label, {"border": "#4a5568", "bg": "#f7fafc", "text": "#2d3748"})
    
    html = f"""
    <div class="priority-stamp" style="border: 2px solid {style['border']}; border-left: 8px solid {style['border']}; padding: 15px; margin-bottom: 20px; background-color: {style['bg']}; border-radius: 4px;">
        <span class="priority-stamp-meta" style="font-size: 11px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;">Official Grievance Triage Status</span>
        <h3 class="priority-stamp-title {priority_label.lower()}" style="margin: 5px 0; font-weight: bold; font-size: 18px; text-transform: uppercase;">Priority Tier: {priority_label} (Score: {priority_score:.3f})</h3>
        <p class="priority-stamp-body" style="margin: 0; font-size: 13px; line-height: 1.4;"><strong>Rationale:</strong> {explanation}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metrics_table(result):
    """Renders an official metrics details matrix table"""
    sev = result['severity_score']
    sev_reason = result['severity_reason']
    sev_level = result['severity_label']
    pi = result['public_impact_score']
    vul = result['vulnerability_score']
    urg = result['urgency_score']
    dup = result['duplicate_escalation_score']
    
    c_sev = sev * 0.30
    c_pi = pi * 0.25
    c_urg = urg * 0.20
    c_vul = vul * 0.15
    c_dup = dup * 0.10
    total = c_sev + c_pi + c_urg + c_vul + c_dup
    
    # Check if LLM reviewed
    is_llm = result.get('llm_reviewed', False)
    llm_adj = result.get('llm_adjustment', 0.0)
    final_score = result.get('final_priority_score', total)
    
    html = f"""
    <table style="width:100%; border-collapse: collapse; font-size: 13px; background-color: #ffffff; border: 1px solid #cbd5e0; margin-bottom: 20px;">
      <thead>
        <tr style="background-color: #eef2f6; border-bottom: 2px solid #0f294a; color: #0f294a; font-weight: bold;">
          <th style="padding: 10px; text-align: left; border: 1px solid #cbd5e0;">Triage Dimension</th>
          <th style="padding: 10px; text-align: center; border: 1px solid #cbd5e0; width: 110px;">Base Score (0.0-1.0)</th>
          <th style="padding: 10px; text-align: center; border: 1px solid #cbd5e0; width: 80px;">Weight</th>
          <th style="padding: 10px; text-align: center; border: 1px solid #cbd5e0; width: 110px;">Weighted Contrib.</th>
          <th style="padding: 10px; text-align: left; border: 1px solid #cbd5e0;">Governance Rules & Extracted Rationale</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; font-weight: bold; color: #0f294a;">Severity</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{sev:.2f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center;">30%</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{c_sev:.3f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; color: #2d3748;">Level: <strong>{sev_level.upper()}</strong> &bull; Reason: {sev_reason}</td>
        </tr>
        <tr>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; font-weight: bold; color: #0f294a;">Public Impact</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{pi:.2f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center;">25%</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{c_pi:.3f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; color: #2d3748;">Evaluates number of citizens and public structures affected.</td>
        </tr>
        <tr>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; font-weight: bold; color: #0f294a;">Urgency</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{urg:.2f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center;">20%</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{c_urg:.3f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; color: #2d3748;">Assesses emergency keyword indicators and response categories.</td>
        </tr>
        <tr>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; font-weight: bold; color: #0f294a;">Vulnerability</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{vul:.2f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center;">15%</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{c_vul:.3f}</td>
          <td style="padding: 8px 10px; border: 1px solid #cbd5e0; color: #2d3748;">Detects presence of schools, hospitals, seniors, or disaster-prone areas.</td>
        </tr>
<tr>
<td style="padding: 8px 10px; border: 1px solid #cbd5e0; font-weight: bold; color: #0f294a;">Duplicate Escalation</td>
<td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{dup:.2f}</td>
<td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center;">10%</td>
<td style="padding: 8px 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 14px;">{c_dup:.3f}</td>
<td style="padding: 8px 10px; border: 1px solid #cbd5e0; color: #2d3748;">Escalation factor matching frequency of repeat filings.</td>
</tr>
    """
    
    if is_llm:
        html += f"""
<tr style="background-color: #f7fafc; font-weight: bold; border-top: 2px solid #0f294a;">
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">BASE GOVERNANCE SCORE</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{total:.3f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center;">-</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{total:.3f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">Standard weighted baseline computed by deterministic rules.</td>
</tr>
<tr style="background-color: #ebf8ff; font-weight: bold; border-top: 1px solid #cbd5e0;">
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #2b6cb0;">LLM ADVISORY ADJUSTMENT</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #2b6cb0;">{llm_adj:+.2f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center;">-</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #2b6cb0;">{llm_adj:+.2f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #2b6cb0;">Reason: {result.get('llm_reasoning', 'Advisory adjustment applied.')}</td>
</tr>
<tr style="background-color: #f7fafc; font-weight: bold; border-top: 2px solid #0f294a;">
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">FINAL PRIORITY SCORE</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{final_score:.3f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center;">100%</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{final_score:.3f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">Computed Priority Level: {result['priority_label'].upper()}</td>
</tr>
        """
    else:
        html += f"""
<tr style="background-color: #f7fafc; font-weight: bold; border-top: 2px solid #0f294a;">
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">FINAL PRIORITY SCORE</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{total:.3f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center;">100%</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{total:.3f}</td>
<td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">Computed Priority Level: {result['priority_label'].upper()}</td>
</tr>
        """
        
    html += """
</tbody>
</table>
"""
    st.markdown(html, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# SHARED COMPLAINT RENDERING (used by both Officer and Admin dashboards)
# ════════════════════════════════════════════════════════════════════════════════

def render_complaint_expander(complaint, idx, show_actions=True, officer_id_for_override=None, is_admin=False):
    """
    Renders a single complaint inside an expander with all details,
    metrics, AI suggestions, RAG context, duplicates, SLA, and lifecycle actions.
    """
    display_label = complaint.get('officer_override') or complaint['priority_label']
    status = complaint.get('status', 'Submitted')
    sla_deadline = complaint.get('sla_deadline', 'N/A')
    sla_breached = complaint.get('sla_breached', False)
    
    # SLA formatting
    sla_warning = "[SLA BREACHED]" if sla_breached else f"SLA: {sla_deadline}"
    
    with st.expander(f"Ref: {complaint['id']} | Status: {status.upper()} | Priority: {display_label.upper()} | Category: {complaint['category']} | {sla_warning}", expanded=False):
        st.markdown("**Grievance Description:**")
        st.info(complaint['complaint_text'])
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Final Priority Level:** **{display_label}**")
            st.markdown(f"**Category:** `{complaint['category']}`")
            st.markdown(f"**Department:** `{complaint['department']}`")
            st.markdown(f"**Status:** `{status}`")
        with c2:
            st.markdown(f"**Registered:** `{complaint['timestamp']}`")
            st.markdown(f"**SLA Deadline:** `{sla_deadline}` {'(BREACHED)' if sla_breached else ''}")
            if complaint.get('officer_override'):
                st.markdown(f"*Priority overridden by officer from: {complaint['priority_label']}*")
            st.markdown(f"**Escalation Level:** `{complaint.get('escalation_level', 0)}`")
            
        if complaint.get('structured_json'):
            loc = complaint['structured_json'].get('location')
            infra = complaint['structured_json'].get('infrastructure')
            if loc or infra:
                st.markdown(f"**Location:** `{loc or 'N/A'}` &bull; **Infrastructure:** `{infra or 'N/A'}`")
                
        # Lifecycle Action Buttons
        if show_actions and officer_id_for_override:
            st.markdown("---")
            st.markdown("#### Lifecycle Actions")
            action_cols = st.columns(4)
            
            # Action states based on status
            if not is_admin:
                if status in ["Assigned", "Reassigned", "Submitted"]:
                    with action_cols[0]:
                        if st.button("Accept Assignment", key=f"btn_accept_{complaint['id']}"):
                            success, res = accept_complaint(complaint['id'], officer_id_for_override)
                            if success: st.success("Accepted!"); st.rerun()
                            else: st.error(res)
                
                if status in ["Accepted", "Field Inspection", "Escalated"]:
                    with action_cols[0]:
                        if st.button("Start Progress", key=f"btn_prog_{complaint['id']}"):
                            success, res = start_progress(complaint['id'], officer_id_for_override, "Action initiated.")
                            if success: st.success("In Progress!"); st.rerun()
                            else: st.error(res)
                
                if status in ["In Progress"]:
                    with action_cols[1]:
                        if st.button("Mark for Field Inspection", key=f"btn_field_{complaint['id']}"):
                            success, res = field_inspection(complaint['id'], officer_id_for_override, "Field team dispatched.")
                            if success: st.success("Field Inspection set!"); st.rerun()
                            else: st.error(res)
                            
                    with action_cols[2]:
                        if st.button("Resolve Issue", key=f"btn_res_{complaint['id']}"):
                            st.session_state[f"show_resolve_{complaint['id']}"] = True
                            
                if status in ["Accepted", "In Progress", "Field Inspection"]:
                    with action_cols[3]:
                        if st.button("Escalate to Higher Authority", key=f"btn_esc_{complaint['id']}"):
                            st.session_state[f"show_escalate_{complaint['id']}"] = True
            
            if is_admin and status == "Resolved":
                with action_cols[0]:
                    if st.button("Close Grievance (Admin)", key=f"btn_close_{complaint['id']}"):
                        success, res = close_complaint(complaint['id'], officer_id_for_override, "Verified and closed by Admin.")
                        if success: st.success("Closed!"); st.rerun()
                        else: st.error(res)
            
            if is_admin and status not in ["Resolved", "Closed"]:
                with action_cols[1]:
                    if st.button("Reassign Officer (Admin)", key=f"btn_reassign_{complaint['id']}"):
                        st.session_state[f"show_reassign_{complaint['id']}"] = True
            
            # Action forms
            if st.session_state.get(f"show_resolve_{complaint['id']}", False):
                with st.form(f"resolve_form_{complaint['id']}"):
                    notes = st.text_area("Resolution Notes:")
                    if st.form_submit_button("Submit Resolution"):
                        try:
                            r = requests.post(f"{API_URL}/complaints/{complaint['id']}/resolve", json={"notes": notes})
                            if r.status_code == 200:
                                st.success("Resolved successfully.")
                                st.session_state[f"show_resolve_{complaint['id']}"] = False
                                st.rerun()
                            else:
                                st.error(f"Error: {r.text}")
                        except Exception as e:
                            st.error(f"Failed to resolve: {e}")
                            
            if st.session_state.get(f"show_escalate_{complaint['id']}", False):
                with st.form(f"escalate_form_{complaint['id']}"):
                    reason = st.text_area("Reason for Escalation:")
                    if st.form_submit_button("Submit Escalation"):
                        success, res = escalate_complaint(complaint['id'], officer_id_for_override, reason)
                        if success:
                            st.success("Escalated successfully.")
                            st.session_state[f"show_escalate_{complaint['id']}"] = False
                            st.rerun()
                        else:
                            st.error(res)
                            
            if st.session_state.get(f"show_reassign_{complaint['id']}", False):
                with st.form(f"reassign_form_{complaint['id']}"):
                    new_off = st.text_input("New Officer ID:")
                    reason = st.text_area("Reason:")
                    if st.form_submit_button("Submit Reassignment"):
                        success, res = reassign_complaint(complaint['id'], officer_id_for_override, new_off, reason)
                        if success:
                            st.success("Reassigned successfully.")
                            st.session_state[f"show_reassign_{complaint['id']}"] = False
                            st.rerun()
                        else:
                            st.error(res)

        st.markdown("---")
        # Tabbed details for metrics, AI, duplicate, history
        t_metrics, t_ai, t_dup, t_hist = st.tabs(["Priority Metrics", "AI Advisory", "Duplicates & Similarity", "Audit & Lifecycle History"])
        
        with t_metrics:
            st.markdown("#### Formal Triage Computation Matrix")
            render_metrics_table(complaint)
            
            if show_actions and officer_id_for_override:
                st.markdown("#### Override Matrix Settings (Governance Only)")
                override_c1, override_c2 = st.columns(2)
                with override_c1:
                    with st.expander("Override Final Priority Level", expanded=False):
                        with st.form(f"override_form_{idx}_{complaint['id']}"):
                            st.markdown("Update final priority if algorithm missed external factors.")
                            new_label = st.selectbox("New Priority:", ["Critical", "High", "Medium", "Low"], index=["Critical", "High", "Medium", "Low"].index(display_label) if display_label in ["Critical", "High", "Medium", "Low"] else 0)
                            reason = st.text_area("Governance Reason for Override:")
                            if st.form_submit_button("Submit Override"):
                                payload = {"priority_label": new_label, "reason": reason}
                                try:
                                    r = requests.post(f"{API_URL}/complaints/{complaint['id']}/override", json=payload)
                                    if r.status_code == 200:
                                        if "officer_overrides" not in st.session_state:
                                            st.session_state.officer_overrides = []
                                        st.session_state.officer_overrides.append({
                                            "complaint_id": complaint['id'], "officer_id": officer_id_for_override,
                                            "original_priority": complaint['priority_label'], "new_priority": new_label,
                                            "reason": reason, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                        })
                                        st.success("Priority override applied.")
                                        st.rerun()
                                    else: st.error(f"Error: {r.text}")
                                except Exception as e: st.error(f"Failed to override: {e}")
                
                with override_c2:
                    with st.expander("Transfer Department", expanded=False):
                        with st.form(f"dept_form_{idx}_{complaint['id']}"):
                            st.markdown("Re-route to correct jurisdiction.")
                            depts = ["Public Works Department (PWD)", "Water & Sewerage Board", "Electricity Board", "Health Department", "Traffic Police", "Sanitation Department"]
                            new_dept = st.selectbox("New Department:", depts)
                            reason = st.text_area("Reason for Transfer:")
                            if st.form_submit_button("Submit Transfer"):
                                try:
                                    r = requests.post(f"{API_URL}/complaints/{complaint['id']}/override-department", json={"new_department": new_dept, "reason": reason, "officer_id": officer_id_for_override})
                                    if r.status_code == 200:
                                        st.success("Transferred successfully.")
                                        st.rerun()
                                    else: st.error(f"Error: {r.text}")
                                except Exception as e: st.error(f"Failed to transfer: {e}")

        with t_ai:
            if complaint.get('llm_reviewed'):
                st.markdown("#### LLM Risk Advisory & Suggested Response")
                st.info(f"**Advisory Reasoning:** {complaint.get('llm_reasoning')}")
                if complaint.get('llm_risk_summary'):
                    st.warning(f"**Risk Summary:** {complaint.get('llm_risk_summary')}")
                sj = complaint.get('structured_json', {})
                draft = complaint.get('suggested_response') or sj.get('suggested_response', 'None generated')
                handbook = complaint.get('officer_handbook') or sj.get('officer_handbook', complaint.get('suggested_action') or sj.get('suggested_action', 'None generated'))
                st.markdown(f"**Draft Response:** {draft}")
                st.markdown(f"**Officer Action Handbook:**\n\n{handbook}")
                st.download_button("Download Handbook (TXT)", handbook, file_name=f"Handbook_{complaint['id']}.txt", mime="text/plain", key=f"dl_hb1_{complaint['id']}")
            else:
                st.markdown("#### ML Dynamic Draft Generation")
                sj = complaint.get('structured_json', {})
                draft = complaint.get('suggested_response') or sj.get('suggested_response', 'None generated')
                handbook = complaint.get('officer_handbook') or sj.get('officer_handbook', complaint.get('suggested_action') or sj.get('suggested_action', 'None generated'))
                st.markdown(f"**Draft Response:** {draft}")
                st.markdown(f"**Officer Action Handbook:**\n\n{handbook}")
                st.download_button("Download Handbook (TXT)", handbook, file_name=f"Handbook_{complaint['id']}.txt", mime="text/plain", key=f"dl_hb2_{complaint['id']}")
        with t_dup:
            st.markdown("#### Duplicate Detection Details")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown(f"**Is Duplicate:** `{'Yes' if complaint.get('is_duplicate') else 'No'}`")
                if complaint.get('lead_id'):
                    st.markdown(f"**Lead Complaint ID:** `{complaint['lead_id']}`")
            with col_d2:
                st.markdown(f"**Duplicate Escalation Score:** `{complaint.get('duplicate_escalation_score', 0):.2f}`")
                
        with t_hist:
            st.markdown("#### Lifecycle Audit History")
            audit_logs = get_audit_logs(complaint['id'])
            if audit_logs:
                for log in audit_logs:
                    st.markdown(f"- **{log['timestamp']}** | `{log['action']}` by {log['performed_by']} ({log['performer_role']}): {log['from_value']} ➔ {log['to_value']} *(Notes: {log['notes']})*")
            else:
                st.info("No audit logs found.")
                
            st.markdown("#### Escalation History")
            esc = get_escalation_history(complaint['id'])
            esc_list = esc.get('escalation_history', [])
            if esc_list:
                for h in esc_list:
                    st.markdown(f"- **{h['date']}** | Level: {h['level']} | Reason: {h.get('reason', 'N/A')}")
            else:
                st.info("No escalations yet.")

def render_complaint_queue(complaints, resolved_complaints, rejected_complaints, show_actions=True, officer_id_for_override=None, key_prefix="", is_admin=False):
    """
    Shared complaint queue renderer with lifecycle status tabs.
    """
    status_groups = {
        "New Assignments": [c for c in complaints if c.get('status') in ["Submitted", "Assigned", "Reassigned", "Open"]],
        "In Progress": [c for c in complaints if c.get('status') in ["Accepted", "In Progress", "Field Inspection"]],
        "Escalated": [c for c in complaints if c.get('status') == "Escalated"]
    }
    st.markdown("---")
    tabs = st.tabs(["New Assignments", "In Progress", "Escalated", "Resolved/Closed", "Restricted"])
    
    # New Assignments
    with tabs[0]:
        if not status_groups["New Assignments"]: st.info("No new assignments.")
        else:
            for idx, c in enumerate(status_groups["New Assignments"], 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # In Progress
    with tabs[1]:
        if not status_groups["In Progress"]: st.info("No complaints currently in progress.")
        else:
            for idx, c in enumerate(status_groups["In Progress"], 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # Escalated
    with tabs[2]:
        if not status_groups["Escalated"]: st.info("No escalated complaints.")
        else:
            for idx, c in enumerate(status_groups["Escalated"], 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # Resolved
    with tabs[3]:
        if not resolved_complaints: st.info("No resolved complaints.")
        else:
            for idx, c in enumerate(resolved_complaints, 1):
                render_complaint_expander(c, idx, show_actions, officer_id_for_override, is_admin)
                
    # Restricted
    with tabs[4]:
        if not rejected_complaints: st.info("No restricted complaints.")
        else:
            for idx, c in enumerate(rejected_complaints, 1):
                with st.expander(f"Locked Ref: {c['id']} | Reason: {c.get('raw_predicted_category', 'Unknown')}", expanded=False):
                    st.warning(c['complaint_text'])
                    st.markdown(f"**Policy Violation Reason:** `{c.get('rejection_reason', 'N/A')}`")


def render_notification_center():
    user = st.session_state.user
    user_id = user.get("user_id") if user.get("role") == "admin" else user.get("officer_id")
    if not user_id:
        return
        
    try:
        r = requests.get(f"{API_URL}/notifications/{user_id}")
        if r.status_code == 200:
            notifs = r.json()
            unread = sum(1 for n in notifs if not n['is_read'])
            
            with st.sidebar.expander(f"🔔 Notifications ({unread})", expanded=unread > 0):
                if not notifs:
                    st.info("No notifications.")
                for n in notifs:
                    color = "red" if n['type'] == 'error' else "orange" if n['type'] == 'warning' else "blue"
                    st.markdown(f"<div style='border-left: 3px solid {color}; padding-left: 8px; margin-bottom: 8px;'>", unsafe_allow_html=True)
                    st.write(f"**{n['timestamp']}**")
                    st.write(n['message'])
                    if n.get('complaint_id'):
                        st.caption(f"Complaint: {n['complaint_id']} | Priority: {n.get('priority', 'N/A')}")
                    if not n['is_read']:
                        if st.button("Mark Read", key=f"read_{n['id']}", help="Mark this notification as read"):
                            requests.post(f"{API_URL}/notifications/{n['id']}/read")
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.sidebar.error("Failed to load notifications.")


def render_sidebar_header():
    """Renders the sidebar government header"""
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 40px; width: auto; margin-bottom: 8px;" alt="Logo">' if logo_b64 else ''
    st.sidebar.markdown(f"""<div class="sidebar-gov-header" style="background-color: #0f294a; padding: 12px; border-bottom: 3px solid #ff9933; text-align: center; margin-bottom: 20px; border-radius: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
{logo_html}
<h4 class="sidebar-gov-title" style="margin: 0; font-size: 13px; font-weight: bold; letter-spacing: 0.5px; text-transform: uppercase; color: #ffffff !important;">Portal Navigation</h4>
</div>""", unsafe_allow_html=True)


def render_sidebar_stats():
    """Renders portal registry stats in sidebar"""
    stats = get_stats()
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div style="border: 1px solid #cbd5e0; padding: 12px; background-color: #ffffff; border-radius: 4px; margin-bottom: 15px; font-family: Arial, sans-serif;">
        <span style="font-size: 10px; font-weight: bold; color: #718096; text-transform: uppercase; letter-spacing: 0.5px;">Portal Registry Stats</span>
        <div style="margin-top: 5px; font-size: 12.5px; color: #2d3748; line-height: 1.5;">
            &bull; <strong>Active Grievances:</strong> {stats['active_count']}<br>
            &bull; <strong>Restricted Logs:</strong> {stats['rejected_count']}<br>
            &bull; <strong>Officer Overrides:</strong> {stats['overrides_count']}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar_user_info():
    """Show currently logged-in user info in the sidebar"""
    user = st.session_state.user
    if not user:
        return
    
    role_colors = {
        "admin": "#c53030",
        "officer": "#2b6cb0",
        "citizen": "#38a169"
    }
    role_color = role_colors.get(user.get('role', ''), '#4a5568')
    role_display = user.get('role', 'unknown').upper()
    
    st.sidebar.markdown(f"""
    <div style="border: 1px solid #cbd5e0; padding: 12px; background-color: #ffffff; border-radius: 4px; margin-bottom: 15px; font-family: Arial, sans-serif;">
        <span style="font-size: 10px; font-weight: bold; color: #718096; text-transform: uppercase; letter-spacing: 0.5px;">Logged In As</span>
        <div style="margin-top: 8px; font-size: 13px; color: #2d3748; line-height: 1.6;">
            <strong>{user.get('name', user.get('username', 'User'))}</strong><br>
            Role: <span style="background-color: {role_color}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: bold;">{role_display}</span><br>
            Username: <code>{user.get('username', '')}</code>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Officer-specific info
    if user.get('role') == 'officer':
        officer_info = user.get('officer', {})
        if officer_info:
            profile_pic_b64 = officer_info.get('profile_pic')
            if profile_pic_b64:
                st.sidebar.markdown(f"""
                <div style="display: flex; justify-content: center; margin-top: 10px; margin-bottom: 10px;">
                    <img src="data:image/png;base64,{profile_pic_b64}" style="width: 100px; height: 100px; border-radius: 50%; border: 2px solid #cbd5e0; object-fit: cover;" alt="Officer Profile Picture">
                </div>
                """, unsafe_allow_html=True)
                
            st.sidebar.markdown(f"""
            <div style="border: 1px solid #cbd5e0; padding: 12px; background-color: #ffffff; border-radius: 4px; margin-bottom: 15px; font-family: Arial, sans-serif;">
                <span style="font-size: 10px; font-weight: bold; color: #718096; text-transform: uppercase; letter-spacing: 0.5px;">Officer Details</span>
                <div style="margin-top: 8px; font-size: 12.5px; color: #2d3748; line-height: 1.6;">
                    <strong>ID:</strong> {user.get('officer_id', 'N/A')}<br>
                    <strong>Department:</strong> {officer_info.get('department', 'N/A')}<br>
                    <strong>Zone:</strong> {officer_info.get('zone', 'N/A')}<br>
                    <strong>Ward:</strong> {officer_info.get('ward', 'N/A')}<br>
                    <strong>Designation:</strong> {officer_info.get('designation', 'N/A')}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_citizen_sidebar_layout():
    """Renders the entire sidebar content for the citizen: header, dashboard nav, profile photo + name nav, and logout at the bottom"""
    # 1. Header (this is render_sidebar_header)
    logo_b64 = get_logo_base64()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 40px; width: auto; margin-bottom: 8px;" alt="Logo">' if logo_b64 else ''
    st.sidebar.markdown(
        f'<div class="sidebar-gov-header" style="background-color: #0f294a; padding: 12px; border-bottom: 3px solid #ff9933; text-align: center; margin-bottom: 20px; border-radius: 4px; display: flex; flex-direction: column; align-items: center; justify-content: center;">'
        f'{logo_html}'
        f'<h4 class="sidebar-gov-title" style="margin: 0; font-size: 13px; font-weight: bold; letter-spacing: 0.5px; text-transform: uppercase; color: #ffffff !important;">Portal Navigation</h4>'
        f'</div>',
        unsafe_allow_html=True
    )
    
    # Initialize active view state if not set
    if 'citizen_view' not in st.session_state:
        st.session_state.citizen_view = "portal"
        
    # 2. Dashboard Navigation Button
    dashboard_label = "Dashboard Portal"
    if st.session_state.citizen_view == "portal":
        dashboard_label = "Dashboard Portal (Selected)"
        
    if st.sidebar.button(dashboard_label, key="nav_to_dashboard", use_container_width=True):
        st.session_state.citizen_view = "portal"
        if "view" in st.query_params:
            del st.query_params["view"]
        st.rerun()
        
    # 3. Add dynamic spacer so profile and logout sit at the bottom
    st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # Get user details
    user = st.session_state.user
    if not user:
        return
    username = user.get('username', 'Citizen')
    display_name = user.get('name', username)
    
    # Get sub text (email or role)
    profile_data = st.session_state.get('citizen_profile', {})
    sub_text = profile_data.get("email", "")
    if not sub_text:
        sub_text = "Citizen Portal"
        
    # Avatar base64 (for dynamic ::before CSS background injection)
    avatar_url = ""
    if 'citizen_profile_pic' in st.session_state and st.session_state.citizen_profile_pic:
        try:
            encoded_pic = base64.b64encode(st.session_state.citizen_profile_pic).decode('utf-8')
            avatar_url = f"data:image/png;base64,{encoded_pic}"
        except Exception:
            pass
            
    # Inject dynamic CSS rule for this button's avatar ::before pseudo-element
    avatar_style = ""
    if avatar_url:
        avatar_style = f"""
        <style>
        section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button::before {{
            content: "" !important;
            position: absolute !important;
            left: 12px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 38px !important;
            height: 38px !important;
            border-radius: 50% !important;
            background-image: url('{avatar_url}') !important;
            background-size: cover !important;
            background-position: center !important;
            border: 1.5px solid #cbd5e0 !important;
            z-index: 5 !important;
        }}
        </style>
        """
    else:
        first_letter = display_name[0].upper() if display_name else "C"
        avatar_style = f"""
        <style>
        section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button::before {{
            content: "{first_letter}" !important;
            position: absolute !important;
            left: 12px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 38px !important;
            height: 38px !important;
            border-radius: 50% !important;
            background-color: #38a169 !important;
            border: 1px solid #276749 !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 15px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: Arial, sans-serif !important;
            z-index: 5 !important;
        }}
        </style>
        """
        
    st.sidebar.markdown(avatar_style, unsafe_allow_html=True)
    
    # Spacing and active state styling injected dynamically
    is_active = (st.session_state.citizen_view == "profile")
    active_bg = "#e2e8f0" if is_active else "#ffffff"
    active_border = "#0f294a" if is_active else "#cbd5e0"
    
    sidebar_layout_css = f"""
    <style>
    section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button {{
        background-color: {active_bg} !important;
        border-color: {active_border} !important;
    }}
    /* Bring profile card right top of the logout button without a huge gap */
    section[data-testid="stSidebar"] div.element-container:nth-last-of-type(2) {{
        margin-bottom: 8px !important;
    }}
    section[data-testid="stSidebar"] div.element-container:nth-last-of-type(1) {{
        margin-top: 0px !important;
    }}
    </style>
    """
    st.sidebar.markdown(sidebar_layout_css, unsafe_allow_html=True)
        
    # Render the native Streamlit button formatted as the profile card
    profile_label = f"{display_name}\n\n{sub_text}"
    if st.sidebar.button(profile_label, key="nav_to_profile", use_container_width=True):
        st.session_state.citizen_view = "profile"
        if "view" in st.query_params:
            del st.query_params["view"]
        st.rerun()
        
    # 6. Logout Button at the very bottom down last (rendered immediately below the profile card)
    if st.sidebar.button("Logout", key="nav_logout_btn", use_container_width=True):
        st.session_state.user = None
        st.session_state.login_role = None
        st.session_state.login_error = None
        st.query_params.clear()
        st.rerun()


def citizen_profile_page():
    """Renders a dedicated full-page profile management workspace for the citizen"""
    render_government_banner()
    
    # Back to Dashboard button at the top
    if st.button("<- Back to Grievance Dashboard", key="profile_back_to_dash"):
        st.session_state.citizen_view = "portal"
        st.rerun()
        
    st.markdown("## Citizen Profile Management")
    st.markdown("Manage your personal contact details, residential location mapping, and profile photo.")
    st.markdown("---")
    
    # Initialize profile state if not set
    if 'citizen_profile' not in st.session_state:
        st.session_state.citizen_profile = {
            "email": "",
            "phone": "",
            "address": "",
            "zone": "",
            "ward": ""
        }
        
    # Divide the page layout: Left for Profile Picture, Right for Information Fields
    col_pic, col_fields = st.columns([1, 2])
    
    with col_pic:
        st.markdown("### Profile Photo")
        if 'citizen_profile_pic' in st.session_state and st.session_state.citizen_profile_pic:
            st.image(st.session_state.citizen_profile_pic, width=200, caption="Current Profile Photo")
            if st.button("Remove Photo", key="remove_profile_photo", type="secondary"):
                st.session_state.citizen_profile_pic = None
                st.rerun()
        else:
            # Placeholder circular avatar using custom HTML/CSS without emojis
            st.markdown("""
            <div style="width: 200px; height: 200px; border-radius: 50%; background-color: #cbd5e0; display: flex; align-items: center; justify-content: center; margin-bottom: 15px; border: 2px dashed #718096;">
                <div style="font-size: 14px; color: #4a5568; font-weight: bold; text-align: center;">No Photo Uploaded</div>
            </div>
            """, unsafe_allow_html=True)
            
        uploaded_pic = st.file_uploader(
            "Upload New Photo", 
            type=["png", "jpg", "jpeg"], 
            key="profile_pic_file_uploader",
            help="Select a PNG or JPG file"
        )
        if uploaded_pic is not None:
            new_bytes = uploaded_pic.getvalue()
            if st.session_state.get('citizen_profile_pic') != new_bytes:
                st.session_state.citizen_profile_pic = new_bytes
                st.rerun()
            
    with col_fields:
        st.markdown("### Account & Personal Details")
        
        user = st.session_state.user
        role_display = user.get('role', 'unknown').upper()
        
        st.markdown(f"""
        <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px 0; color: #718096; font-weight: bold; width: 150px;">Full Name</td>
                <td style="padding: 10px 0; color: #2d3748; font-weight: bold;">{user.get('name', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px 0; color: #718096; font-weight: bold;">Username</td>
                <td style="padding: 10px 0; color: #2d3748; font-family: monospace;">{user.get('username', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px 0; color: #718096; font-weight: bold;">Portal Role</td>
                <td style="padding: 10px 0;"><span style="background-color: #38a169; color: white; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{role_display}</span></td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        
        st.markdown("### Location & Routing Settings")
        st.info("Filling this out helps the AI automatically map and route your complaints to the correct local ward officer.")
        
        # Profile fields
        profile_email = st.text_input(
            "Email Address", 
            value=st.session_state.citizen_profile.get("email", ""),
            placeholder="e.g. email@domain.gov.in"
        )
        profile_phone = st.text_input(
            "Phone Number", 
            value=st.session_state.citizen_profile.get("phone", ""),
            placeholder="e.g. +91 99999 99999"
        )
        
        # Grid layout for location fields
        c_zone, c_ward = st.columns(2)
        with c_zone:
            zones = ["", "Anna Nagar", "T. Nagar", "Adyar", "Royapuram", "Velachery"]
            profile_zone = st.selectbox(
                "Primary Zone",
                options=zones,
                index=zones.index(st.session_state.citizen_profile.get("zone", "")) if st.session_state.citizen_profile.get("zone") in zones else 0
            )
        with c_ward:
            profile_ward = st.text_input(
                "Ward Number", 
                value=st.session_state.citizen_profile.get("ward", ""),
                placeholder="e.g. Ward 5"
            )
            
        profile_address = st.text_area(
            "Residential Address", 
            value=st.session_state.citizen_profile.get("address", ""),
            placeholder="Street, locality, area details...",
            height=100
        )
        
        if st.button("Save Profile Settings", key="profile_page_save_btn", type="primary", use_container_width=True):
            st.session_state.citizen_profile["email"] = profile_email
            st.session_state.citizen_profile["phone"] = profile_phone
            st.session_state.citizen_profile["address"] = profile_address
            st.session_state.citizen_profile["zone"] = profile_zone
            st.session_state.citizen_profile["ward"] = profile_ward
            st.success("Profile details updated successfully!")
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════════
# LANDING PAGE & LOGIN PORTALS
# ════════════════════════════════════════════════════════════════════════════════

def landing_page():
    """Renders the main government-themed landing page of Sahayak AI"""
    # 1. Full-width top header banner
    logo_b64 = get_logo_base64()
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="height: 60px; width: auto; border-radius: 4px;" alt="Sahayak AI Logo">'
        left_html = f"""<div class="gov-header-left" style="display: flex; align-items: center; gap: 15px;">
{logo_html}
<div>
<div class="gov-header-left-subtitle1">Government of India Middleware Platform</div>
<h1 class="gov-header-left-title" style="margin: 0; line-height: 1.1;">SAHAYAK AI</h1>
<div class="gov-header-left-subtitle2">National Grievance Triage & Redressal Board</div>
</div>
</div>"""
    else:
        left_html = """<div class="gov-header-left">
<div class="gov-header-left-subtitle1">Government of India Middleware Platform</div>
<h1 class="gov-header-left-title">SAHAYAK AI</h1>
<div class="gov-header-left-subtitle2">National Grievance Triage & Redressal Board</div>
</div>"""
        
    st.markdown(f"""<div class="gov-header-container">
{left_html}
<div class="gov-header-right">
<a href="?login=citizen" target="_self" class="gov-nav-btn citizen-btn">Citizen Login</a>
<a href="?login=officer" target="_self" class="gov-nav-btn officer-btn">Officer Login</a>
<a href="?login=admin" target="_self" class="gov-nav-btn admin-btn">Admin Login</a>
</div>
</div>""", unsafe_allow_html=True)
    
    # 2. Hero banner introduction
    st.markdown("""
    <div class="landing-hero">
        <h2>Revolutionizing Grievance Redressal with Intelligent AI Middleware</h2>
        <p>
            Sahayak AI is a state-of-the-art Natural Language Processing (NLP) and Machine Learning platform serving as the 
            official grievance triage board for the Government of India. By acting as an automated middleware layer 
            for portals like CPGRAMS, Sahayak AI ingests civic complaints, classifies them to correct departments, 
            identifies geographical jurisdictions (zones and wards), calculates multi-dimensional priorities, and 
            routes them directly to action officers—cutting resolution cycles from days to minutes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 3. Purpose and Use columns
    st.markdown("### Platform Purpose & Vision")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="info-card accent-saffron">
            <h4>Rapid Automated Triage</h4>
            <p>
                Civic issues submitted by citizens are parsed instantaneously. Advanced NLP classifiers determine whether 
                a grievance is admissible, assign it to a category (e.g. Sanitation, Roads, Water & Sewerage), and extract 
                crucial entity details like street names, landmarks, zones, and municipal wards.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
        <div class="info-card accent-navy">
            <h4>Multi-Dimensional Priority</h4>
            <p>
                Sahayak AI computes a detailed priority score using a 5-dimension weighted matrix: 
                <strong>Severity</strong>, <strong>Public Impact</strong> (detecting proximity to schools, hospitals, or transport hubs), 
                <strong>Urgency</strong>, <strong>Vulnerability</strong>, and <strong>Duplicate Clusters</strong>. 
                Scores are tailored to specific department policy weight profiles.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
        <div class="info-card accent-green">
            <h4>Officer Mapping & Trust</h4>
            <p>
                Complaints are dynamically assigned to the responsible Junior Inspector or action officer based on department 
                and location jurisdiction. Officer overrides are fed back to the learning engine, recalculating agreement rates 
                and trust scores for continuous improvement.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### End-to-End Workflow Flowchart")
    
    # 4. Use Case Workflow Steps
    st.markdown("""
    <div class="workflow-container">
        <div class="workflow-step">
            <div class="step-badge">1</div>
            <div class="step-content">
                <h5>Citizen Grievance Submission</h5>
                <p>Citizens lodge grievances in plain language through the Citizen Portal. The AI accepts unstructured text and tracks it with a unique Grievance ID.</p>
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-badge">2</div>
            <div class="step-content">
                <h5>AI Parsing, Categorization & NER Extraction</h5>
                <p>The NLP pipeline filters out spam/inadmissible text, identifies the civic category, and performs Named Entity Recognition (NER) to locate the exact ward and zone.</p>
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-badge">3</div>
            <div class="step-content">
                <h5>Smart Routing & Priority Scoring</h5>
                <p>The system computes default and department-specific priority levels. It checks for duplicates (RAG-based cluster matching) and escalates aged complaints automatically.</p>
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-badge">4</div>
            <div class="step-content">
                <h5>Officer Assignment & Resolution</h5>
                <p>The mapped Officer views their active queue, accesses similar historical resolutions, and takes corrective action, providing resolution details back to the middleware.</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 5. Live Portal Stats
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Live Middleware Statistics")
    stats = get_stats()
    resolved_count = 0
    try:
        resolved = get_resolved_complaints()
        resolved_count = len(resolved)
    except Exception:
        pass
        
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Active Grievances", stats.get("active_count", 0))
    with c2:
        st.metric("Resolved Cases", resolved_count)
    with c3:
        st.metric("Spam/Inadmissible Filtered", stats.get("rejected_count", 0))
    with c4:
        st.metric("AI Decisions Overridden", stats.get("overrides_count", 0))


def login_page(target_role):
    """Renders the login page with a premium government-themed card for a specific role"""
    
    # Inject card styling and role-specific submit button color
    if target_role == "citizen":
        btn_color = "#ff9933"
        hover_color = "#e68a00"
    elif target_role == "officer":
        btn_color = "#138808"
        hover_color = "#0f6c06"
    else:  # admin
        btn_color = "#0f294a"
        hover_color = "#1a3d66"
        
    st.markdown(f"""
    <style>
    /* Make the form container itself a visible, elegant card box */
    div[data-testid="stForm"] {{
        border: 1px solid #cbd5e0 !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08) !important;
        background-color: #ffffff !important;
        padding: 40px !important;
        box-sizing: border-box !important;
    }}
    /* Force white text on submit buttons and dynamic role-based color */
    div[data-testid="stForm"] button[type="submit"] {{
        background-color: {btn_color} !important;
        border-color: {btn_color} !important;
        color: white !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }}
    div[data-testid="stForm"] button[type="submit"]:hover {{
        background-color: {hover_color} !important;
        border-color: {hover_color} !important;
        color: white !important;
    }}
    div[data-testid="stFormSubmitButton"] button *,
    div[data-testid="stFormSubmitButton"] button p,
    div[data-testid="stFormSubmitButton"] button span,
    div[data-testid="stFormSubmitButton"] button div,
    button[type="submit"] *,
    button[type="submit"] p,
    button[type="submit"] span,
    button[type="submit"] div {{
        color: white !important;
    }}
    
    /* Header banner styling to override Streamlit markdown text coloring */
    .login-header-banner {{
        background-color: #0f294a !important;
        padding: 25px 35px !important;
        border-radius: 6px !important;
        text-align: center !important;
        margin-bottom: 25px !important;
        border-left: 5px solid #ff9933 !important;
        border-right: 5px solid #138808 !important;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.3) !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }}
    .login-header-banner h2 {{
        color: #ffffff !important;
        margin: 0 !important;
        font-size: 26px !important;
        font-weight: 900 !important;
        letter-spacing: 2px !important;
        text-transform: uppercase !important;
        line-height: 1.1 !important;
    }}
    .login-header-banner .subtitle-role {{
        font-size: 13px !important;
        color: #cbd5e0 !important;
        font-weight: 500 !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
        margin-top: 5px !important;
        margin-bottom: 0 !important;
    }}
    .login-header-banner .subtitle-gov {{
        font-size: 10px !important;
        color: #ff9933 !important;
        font-weight: bold !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        margin-top: 4px !important;
        margin-bottom: 0 !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # Back button to return to landing page
    if st.button("<- Back to Landing Page", key="back_to_home"):
        st.session_state.login_role = None
        st.session_state.login_error = None
        st.query_params.clear()
        st.rerun()
        
    # Center the login form inside a spacious, horizontal layout
    col_spacer_l, col_form, col_spacer_r = st.columns([1.0, 2.0, 1.0])
    
    with col_form:
        role_label = target_role.capitalize()
        
        # Check signup mode for citizen
        if target_role == "citizen" and st.session_state.get('citizen_signup_mode', False):
            with st.form("signup_form"):
                logo_b64 = get_logo_base64()
                if logo_b64:
                    banner_html = f"""<div class="login-header-banner" style="display: flex; align-items: center; justify-content: center; gap: 15px;">
<img src="data:image/png;base64,{logo_b64}" style="height: 50px; width: auto; border-radius: 4px;" alt="Sahayak AI Logo">
<div style="text-align: left;">
<h2 style="margin: 0; line-height: 1.1;">SAHAYAK AI</h2>
<div class="subtitle-role">Citizen Registration Portal</div>
<div class="subtitle-gov">Government of India Middleware Platform</div>
</div>
</div>"""
                else:
                    banner_html = f"""<div class="login-header-banner">
<h2>SAHAYAK AI</h2>
<div class="subtitle-role">Citizen Registration Portal</div>
<div class="subtitle-gov">Government of India Middleware Platform</div>
</div>"""
                st.markdown(banner_html, unsafe_allow_html=True)
                
                st.markdown("### Create Citizen Account")
                st.markdown("Register below to submit and track your civic grievances.")
                
                full_name = st.text_input("Full Name", placeholder="Enter your full name")
                username = st.text_input("Username / Email", placeholder="Choose a username")
                password = st.text_input("Password", type="password", placeholder="Choose a secure password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                
                signup_submitted = st.form_submit_button("Sign Up", type="primary", use_container_width=True)
                
                if signup_submitted:
                    if not full_name or not username or not password:
                        st.session_state.login_error = "All fields are required."
                    elif password != confirm_password:
                        st.session_state.login_error = "Passwords do not match."
                    else:
                        user_data, error = api_signup(username, password, full_name)
                        if user_data:
                            st.success("Registration successful! You can now log in.")
                            st.session_state.citizen_signup_mode = False
                            st.session_state.login_error = None
                            st.rerun()
                        else:
                            st.session_state.login_error = error or "Registration failed."
            
            if st.button("Already have an account? Log In", key="go_to_login"):
                st.session_state.citizen_signup_mode = False
                st.session_state.login_error = None
                st.rerun()
        else:
            # Login form containing both the horizontal header and form fields
            with st.form("login_form"):
                # Horizontal Sahayak AI header banner with css classes
                logo_b64 = get_logo_base64()
                if logo_b64:
                    banner_html = f"""<div class="login-header-banner" style="display: flex; align-items: center; justify-content: center; gap: 15px;">
<img src="data:image/png;base64,{logo_b64}" style="height: 50px; width: auto; border-radius: 4px;" alt="Sahayak AI Logo">
<div style="text-align: left;">
<h2 style="margin: 0; line-height: 1.1;">SAHAYAK AI</h2>
<div class="subtitle-role">{role_label} Access Portal</div>
<div class="subtitle-gov">Government of India Middleware Platform</div>
</div>
</div>"""
                else:
                    banner_html = f"""<div class="login-header-banner">
<h2>SAHAYAK AI</h2>
<div class="subtitle-role">{role_label} Access Portal</div>
<div class="subtitle-gov">Government of India Middleware Platform</div>
</div>"""
                st.markdown(banner_html, unsafe_allow_html=True)
                
                st.markdown(f"### {role_label} Authentication")
                st.markdown(f"Enter your credentials below to access the secure {role_label} workspace.")
                
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Login", type="primary", use_container_width=True)
                
                if submitted:
                    if not username or not password:
                        st.session_state.login_error = "Please enter both username and password."
                    else:
                        user_data, error = api_login(username, password)
                        if user_data:
                            # Enforce role restriction checks: citizen portal can't login officer etc.
                            user_role = user_data.get('role', '').lower()
                            # Allow commissioner to log in through officer portal
                            role_match = (user_role == target_role.lower()) or (user_role == 'commissioner' and target_role.lower() == 'officer')
                            if not role_match:
                                st.session_state.login_error = f"Access denied: You are attempting to log in as a {user_role.capitalize()} on the {role_label} Portal. Please use the appropriate portal."
                            else:
                                st.session_state.user = user_data
                                st.session_state.login_role = None
                                st.session_state.login_error = None
                                st.query_params.clear()
                                st.rerun()
                        else:
                            st.session_state.login_error = error or "Invalid credentials. Please try again."
        
        # Show error
        if st.session_state.login_error:
            st.error(st.session_state.login_error)
            
        if target_role == "citizen" and not st.session_state.get('citizen_signup_mode', False):
            if st.button("Don't have an account? Sign Up", key="go_to_signup"):
                st.session_state.citizen_signup_mode = True
                st.session_state.login_error = None
                st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# CITIZEN PORTAL
# ════════════════════════════════════════════════════════════════════════════════

def citizen_portal():
    """Citizen portal with timeline and SLA tracking"""
    render_government_banner()
    st.markdown("### Grievance Registration Portal")
    st.markdown("Submit and track your public service grievances.")
    st.markdown("---")
    
    tab_submit, tab_history = st.tabs(["Submit Grievance", "My Grievances & Tracking"])
    username = st.session_state.user.get('username')
    
    with tab_submit:
        complaint_text = st.text_area("Enter grievance description:", height=150)
        if st.button("Submit Grievance", type="primary"):
            if complaint_text.strip():
                with st.spinner("Processing..."):
                    result = predict_complaint(complaint_text.strip(), submitted_by=username)
                    if result:
                        if not result.get('admissible'):
                            st.error(f"Grievance Not Admissible: {result.get('rejection_reason')}")
                        else:
                            st.success(f"Filed successfully. Reference ID: {result['id']}")
            else:
                st.error("Enter a description.")
                
    with tab_history:
        st.markdown("#### Track Your Submitted Grievances")
        user_complaints = get_citizen_complaints(username)
        if not user_complaints:
            st.info("No grievances submitted.")
        else:
            # Status filter
            st_filter = st.selectbox("Filter by Status:", ["All", "Active", "Accepted", "Resolved/Closed", "Rejected"])
            filtered = []
            for c in user_complaints:
                s = c.get('status', 'Submitted')
                if st_filter == "Active" and s not in ["Resolved", "Closed", "Rejected"]: filtered.append(c)
                elif st_filter == "Accepted" and s in ["Accepted", "In Progress", "Field Inspection", "Escalated"]: filtered.append(c)
                elif st_filter == "Resolved/Closed" and s in ["Resolved", "Closed"]: filtered.append(c)
                elif st_filter == "Rejected" and s == "Rejected": filtered.append(c)
                elif st_filter == "All": filtered.append(c)
                
            for c in filtered:
                s = c.get('status', 'Submitted')
                with st.expander(f"Ref: {c['id']} | Status: {s.upper()} | Filed: {c['timestamp']}", expanded=False):
                    st.markdown(f"**Grievance:** {c['complaint_text']}")
                    st.markdown(f"**Department:** {c.get('department')} | **Category:** {c.get('category')}")
                    
                    if s not in ["Resolved", "Closed", "Rejected"]:
                        st.markdown(f"**Expected Resolution By (SLA):** `{c.get('sla_deadline', 'N/A')}`")
                        
                    off = c.get('assigned_officer_id')
                    if off:
                        st.markdown(f"**Handling Officer:** `{get_officer_display_name(off)}`")
                    
                    esc_level = c.get('escalation_level', 1)
                    if esc_level > 1:
                        st.markdown(f"🚨 **Escalated to Level {esc_level}** due to priority or SLA breach.")
                        
                    if s not in ["Submitted", "Assigned", "Reassigned", "Open", "Rejected"]:
                        draft = c.get('suggested_response') or (c.get('structured_json') or {}).get('suggested_response')
                        if draft:
                            st.info(f"**Official Message from Officer:** {draft}")
                            
                    st.markdown("**Tracking Timeline:**")
                    audit = get_audit_logs(c['id'])
                    if audit:
                        for log in audit:
                            st.markdown(f"- `{log['timestamp']}`: {log['from_value']} -> **{log['to_value']}** ({log['notes']})")
                    else:
                        st.info("Timeline is being updated.")

def officer_dashboard():
    """Officer dashboard with lifecycle tracking and performance panel at top"""
    render_government_banner()
    render_notifications_bell(st.session_state.user['officer_id'])
    user = st.session_state.user
    officer_id = user.get('officer_id', '')
    officer_name = user.get('name', user.get('username', 'Officer'))

    st.markdown(f"### Officer Triage Dashboard")
    st.markdown(f"Welcome, **{officer_name}** (`{officer_id}`). Monitor and process grievances assigned to you.")

    # ── My Performance Panel (always visible at top) ──
    perf_stats = get_officer_stats(officer_id)
    if perf_stats:
        st.markdown("---")
        st.markdown("#### My Performance")
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Total Assigned", perf_stats.get('total_assigned', 0))
        p2.metric("Resolved", perf_stats.get('total_resolved', 0))
        p3.metric("Active", perf_stats.get('current_active', 0))
        p4.metric("SLA Compliance", f"{perf_stats.get('sla_compliance_rate', 0)}%")
        p5.metric("Avg Resolution (hrs)", perf_stats.get('avg_resolution_hours', 0))
        # Resolution progress bar
        res_rate = perf_stats.get('resolution_rate', 0)
        st.markdown(f"Resolution Rate: **{res_rate}%**")
        st.progress(min(res_rate / 100.0, 1.0))

    st.markdown("---")

    # Fetch complaints filtered by this officer
    admissible_complaints = get_complaints(officer_id=officer_id)

    # We need resolved filtered by officer if we only want theirs, but get_resolved_complaints gets all.
    # We will filter locally.
    all_res = get_resolved_complaints()
    res = [c for c in all_res if c.get('assigned_officer_id') == officer_id]
    rej = [c for c in get_rejected_complaints() if c.get('assigned_officer_id') == officer_id]

    render_complaint_queue(
        complaints=admissible_complaints,
        resolved_complaints=res,
        rejected_complaints=rej,
        show_actions=True,
        officer_id_for_override=officer_id,
        key_prefix="officer",
        is_admin=False
    )


def render_commissioner_dashboard():
    st.header("🏢 Commissioner Dashboard")
    st.markdown("Monitor critical, disaster, and heavily escalated complaints across all departments.")
    
    col1, col2, col3 = st.columns(3)
    
    try:
        r = requests.get(f"{API_URL}/complaints?officer_id={st.session_state.user.get('officer_id')}")
        if r.status_code == 200:
            complaints = r.json()
            
            critical = [c for c in complaints if c.get('priority_score', 0) > 0.85]
            unresolved = [c for c in complaints if c.get('status') not in ['Resolved', 'Closed', 'Rejected']]
            
            col1.metric("Total L4 Escalations", len(complaints))
            col2.metric("Critical / High Impact", len(critical))
            col3.metric("Unresolved", len(unresolved))
            
            st.subheader("Actionable Escalations")
            for c in unresolved:
                with st.expander(f"{c['id']} - {c['category']} (Priority: {c.get('final_priority_score', 0)})"):
                    st.write(f"**Description:** {c['complaint_text']}")
                    st.write(f"**Status:** {c['status']}")
                    st.write(f"**Escalation Level:** {c.get('escalation_level', 4)}")
                    
                    if st.button("Close / Mark Resolved", key=f"comm_close_{c['id']}"):
                        requests.post(f"{API_URL}/complaints/{c['id']}/close", json={"admin_id": "COMM_1", "notes": "Commissioner resolved this critical issue."})
                        st.success("Complaint resolved successfully.")
                        st.rerun()
                    
                    if st.button("View Escalation History", key=f"comm_hist_{c['id']}"):
                        hr = requests.get(f"{API_URL}/complaints/{c['id']}/escalation-history")
                        if hr.status_code == 200:
                            st.json(hr.json())
        else:
            st.error("Failed to load commissioner data.")
    except Exception as e:
        st.error(f"Error: {e}")


def admin_dashboard(active_tab="Command Center (KPIs)"):
    """Admin dashboard with Command Center, Escalation Queue, Audit Trail Viewer + 5 Intelligence Modules"""
    render_government_banner()
    render_notifications_bell("admin")
    st.markdown("### Admin Control Panel")
    st.markdown("Full system access. Manage complaints, SLA escalations, and system analytics.")
    st.markdown("---")
    
    # Workload Alert Check
    all_comps = get_complaints()
    unassigned = [c for c in all_comps if c.get('status') == 'Submitted' and not c.get('assigned_officer_id')]
    if unassigned:
        from collections import Counter
        dept_counts = Counter([c.get('department', 'Unknown') for c in unassigned])
        alert_msg = "🚨 **Workload Alert:** "
        for dept, count in dept_counts.items():
            alert_msg += f"{count} complaints in {dept} are unassigned. "
        alert_msg += "All existing officers have reached their 10-complaint limit. Please add a new officer to automatically route them."
        st.error(alert_msg)
        st.markdown("---")
    
    # Removed tabs, using active_tab from sidebar
    
    stats = get_dashboard_stats()
    
    # ── Command Center ──
    if active_tab in ["Dashboard", "Command Center (KPIs)"]:
        st.markdown("#### System KPIs & Health")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Active", stats.get('total_active', 0))
        c2.metric("SLA Compliance Rate", f"{stats.get('sla_compliance_rate', 0)}%")
        c3.metric("SLA Breached", stats.get('sla_breached_count', 0))
        c4.metric("Avg Resolution Time (hrs)", stats.get('avg_resolution_hours', 0))
        
        st.markdown("#### Status Breakdown")
        status_counts = stats.get('status_counts', {})
        if status_counts:
            scols = st.columns(len(status_counts))
            for i, (k, v) in enumerate(status_counts.items()):
                scols[i].metric(k, v)
        else:
            st.info("No status data.")
        
    # ── System-Wide Queue ──
    if active_tab == "System-Wide Queue":
        admissible_complaints = get_complaints()
        resolved_complaints = get_resolved_complaints()
        rejected_complaints = get_rejected_complaints()
        render_complaint_queue(
            complaints=admissible_complaints,
            resolved_complaints=resolved_complaints,
            rejected_complaints=rejected_complaints,
            show_actions=True,
            officer_id_for_override="ADMIN",
            key_prefix="admin",
            is_admin=True
        )
        
    # ── Escalation Queue ──
    if active_tab == "Escalation & SLA Queue":
        st.markdown("#### SLA Breaches & Escalated Grievances")
        breached = get_sla_breached()
        if not breached:
            st.success("No SLA breaches currently active.")
        else:
            for idx, c in enumerate(breached, 1):
                render_complaint_expander(c, idx, True, "ADMIN", True)
                
    # ── Audit Trail Viewer ──
    if active_tab == "Audit Trail Viewer":
        st.markdown("#### Global Audit Logs")
        logs = get_audit_logs()
        if logs:
            df = pd.DataFrame(logs)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No audit logs available.")
            
    # ── Officer Management ──
    if active_tab == "Officer Management":
        st.markdown("#### Add New Officer")
        with st.form("add_officer_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                new_name = st.text_input("Name")
                new_email = st.text_input("Email/Username")
                new_password = st.text_input("Password", type="password")
                new_dept = st.text_input("Department")
            with col2:
                new_zone = st.text_input("Zone")
                new_ward = st.text_input("Ward")
                new_desig = st.text_input("Designation")
                new_escalation = st.selectbox("Escalation Level", options=[0, 1, 2, 3], format_func=lambda x: {0: "L1 - Junior", 1: "L2 - Senior", 2: "L3 - Dept Head", 3: "L4 - Ministry"}[x])
            submit_officer = st.form_submit_button("Add Officer")
            
            if submit_officer:
                if not new_name or not new_email or not new_password or not new_dept:
                    st.error("Please fill Name, Email, Password, and Department.")
                else:
                    payload = {
                        "name": new_name,
                        "email": new_email,
                        "password": new_password,
                        "department": new_dept,
                        "zone": new_zone,
                        "ward": new_ward,
                        "designation": new_desig,
                        "profile_pic": None,
                        "escalation_level": new_escalation
                    }
                    try:
                        r = requests.post(f"{API_URL}/officers", json=payload)
                        if r.status_code == 200:
                            st.success(f"Officer {new_name} added successfully!")
                        else:
                            st.error(f"Failed to add officer: {r.text}")
                    except Exception as e:
                        st.error("API Connection Error.")

        st.markdown("#### Current Officers by Department")
        officers = get_officers()
        if officers:
            from collections import defaultdict
            dept_officers = defaultdict(list)
            for off in officers:
                dept_officers[off.get('department', 'Unknown')].append(off)
            
            departments = list(dept_officers.keys())
            cols_per_row = 3
            for i in range(0, len(departments), cols_per_row):
                cols = st.columns(cols_per_row)
                for j in range(cols_per_row):
                    if i + j < len(departments):
                        dept = departments[i + j]
                        with cols[j]:
                            st.markdown(f"**{dept}**")
                            for off in sorted(dept_officers[dept], key=lambda x: x.get('escalation_level', 1)):
                                level = off.get('escalation_level', 1)
                                if level == 4: badge = "Commissioner"
                                else: badge = f"L{level}"
                                st.markdown(f"- 🔹 **{off.get('name', 'Unknown')}** (`{off.get('officer_id')}`) - *{badge}*")
                            st.markdown("---")
        
    # ── Department Policies ──
    if active_tab == "Department Policies":
        st.info("Department policies configuration. Adjust weights (must sum to 1.0) and click Save.")
        pols = get_department_policies()
        if pols: 
            df_pols = pd.DataFrame(pols)
            edited_df = st.data_editor(df_pols, num_rows="fixed", use_container_width=True, key="policy_editor")
            if st.button("Save Policy Changes"):
                success = True
                for index, row in edited_df.iterrows():
                    dept = row['department']
                    total = sum([row['severity_weight'], row['impact_weight'], row['urgency_weight'], row['vulnerability_weight'], row['duplicate_weight']])
                    if abs(total - 1.0) > 0.01:
                        st.error(f"Weights for {dept} must sum to 1.0. Got {total:.2f}.")
                        success = False
                        break
                    
                    payload = {
                        "severity_weight": row['severity_weight'],
                        "impact_weight": row['impact_weight'],
                        "urgency_weight": row['urgency_weight'],
                        "vulnerability_weight": row['vulnerability_weight'],
                        "duplicate_weight": row['duplicate_weight']
                    }
                    try:
                        r = requests.put(f"{API_URL}/department-policies/{dept}", json=payload)
                        if r.status_code != 200:
                            st.error(f"Failed to update {dept}: {r.text}")
                            success = False
                    except:
                        st.error("API Connection Error.")
                        success = False
                if success:
                    st.success("All policies updated successfully!")

    # ════════════════════════════════════════════════════════════════
    # Tab 7 ── HOTSPOT INTELLIGENCE DETECTION
    # ════════════════════════════════════════════════════════════════
    if active_tab == "Hotspot Intelligence":
        st.markdown("#### Hotspot Intelligence Detection")
        st.markdown("Clusters of complaints in the same location and issue category, within the past 7 days.")

        hotspots = get_hotspots()

        if not hotspots:
            st.info("No hotspots detected. This means no location+category cluster has 3 or more complaints in the last 7 days.")
        else:
            # Summary metrics row
            total_hotspots = len(hotspots)
            critical_hs = sum(1 for h in hotspots if h.get('severity_label') == 'Critical')
            high_hs = sum(1 for h in hotspots if h.get('severity_label') == 'High')
            needs_officer = sum(1 for h in hotspots if h.get('recommend_officer', False))

            hc1, hc2, hc3, hc4 = st.columns(4)
            hc1.metric("Total Hotspots", total_hotspots)
            hc2.metric("Critical Severity", critical_hs)
            hc3.metric("High Severity", high_hs)
            hc4.metric("Officer Reinforcement Needed", needs_officer)

            st.markdown("---")

            # Color map for severity
            sev_colors = {
                "Critical": ("#7f1d1d", "#fca5a5"),
                "High": ("#78350f", "#fcd34d"),
                "Medium": ("#1e3a5f", "#93c5fd"),
                "Low": ("#14532d", "#86efac"),
            }


            # Render each hotspot as a styled card
            for i, hs in enumerate(hotspots):
                sev = hs.get('severity_label', 'Low')
                bg_color, border_color = sev_colors.get(sev, ("#374151", "#9ca3af"))
                count = hs.get('complaints_count', 0)
                location = hs.get('location', 'Unknown').title()
                category = hs.get('category', 'Unknown')
                sev_score = hs.get('severity_score', 0)
                recommend = hs.get('recommend_officer', False)
                rec_reason = hs.get('recommendation_reason', '')
                officers_zone = hs.get('officers_in_zone', [])
                officers_zone_str = ', '.join(officers_zone) if officers_zone else 'None'
                first_rep = hs.get('first_reported', 'N/A')
                latest_rep = hs.get('latest_reported', 'N/A')

                # Build recommendation block separately to avoid nested f-string bug
                if recommend:
                    rec_block = f"""
                    <div style="margin-top:12px;background:#fef3c7;border-radius:6px;padding:10px 14px;">
                        <span style="font-weight:700;color:#92400e;">Officer Reinforcement Recommended</span>
                        <div style="color:#78350f;font-size:13px;margin-top:4px;">{rec_reason}</div>
                    </div>"""
                else:
                    rec_block = ""

                card_html = f"""
                <div style="background:{bg_color};border-left:5px solid {border_color};border-radius:8px;
                            padding:16px 20px;margin-bottom:14px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                        <div>
                            <span style="font-size:18px;font-weight:700;color:#fff;">{location}</span>
                            <span style="margin-left:12px;background:{border_color};color:#111;
                                        font-size:12px;font-weight:600;padding:2px 10px;
                                        border-radius:12px;">{sev} Severity</span>
                        </div>
                        <div style="display:flex;gap:16px;">
                            <div style="text-align:center;">
                                <div style="color:{border_color};font-size:24px;font-weight:800;">{count}</div>
                                <div style="color:#d1d5db;font-size:11px;">Complaints</div>
                            </div>
                            <div style="text-align:center;">
                                <div style="color:{border_color};font-size:24px;font-weight:800;">{sev_score:.2f}</div>
                                <div style="color:#d1d5db;font-size:11px;">Avg Priority</div>
                            </div>
                        </div>
                    </div>
                    <div style="margin-top:10px;display:flex;gap:20px;flex-wrap:wrap;">
                        <div style="color:#d1d5db;font-size:13px;">
                            <b style="color:#fff;">Issue Type:</b> {category}
                        </div>
                        <div style="color:#d1d5db;font-size:13px;">
                            <b style="color:#fff;">Officers in Zone:</b> {len(officers_zone)} ({officers_zone_str})
                        </div>
                        <div style="color:#d1d5db;font-size:13px;">
                            <b style="color:#fff;">First Reported:</b> {first_rep}
                        </div>
                        <div style="color:#d1d5db;font-size:13px;">
                            <b style="color:#fff;">Latest:</b> {latest_rep}
                        </div>
                    </div>
                    {rec_block}
                </div>
                """
                st.markdown(re.sub(r'^[ \t]+', '', card_html, flags=re.MULTILINE), unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Full Hotspot Data Table")
            hs_table = []
            for hs in hotspots:
                hs_table.append({
                    "Location": hs.get('location','').title(),
                    "Category": hs.get('category',''),
                    "Complaints": hs.get('complaints_count', 0),
                    "Severity Label": hs.get('severity_label', ''),
                    "Avg Priority Score": hs.get('severity_score', 0),
                    "Officers in Zone": len(hs.get('officers_in_zone', [])),
                    "Reinforcement Needed": "YES" if hs.get('recommend_officer') else "No",
                    "First Reported": hs.get('first_reported',''),
                    "Latest Reported": hs.get('latest_reported',''),
                })
            st.dataframe(pd.DataFrame(hs_table), use_container_width=True)

    # ════════════════════════════════════════════════════════════════
    # Tab 8 ── TRUST & FEEDBACK ANALYTICS
    # ════════════════════════════════════════════════════════════════
    if active_tab == "Trust & Feedback Analytics":
        st.markdown("#### Trust & Feedback Analytics")
        st.markdown("Officer override patterns and trust scores. High-trust officers' overrides drive dynamic weight learning.")

        fb_stats = get_feedback_stats()
        officers_data = fb_stats.get('officers', {})
        total_overrides = fb_stats.get('total_overrides', 0)

        # Summary
        fc1, fc2, fc3 = st.columns(3)
        fc1.metric("Total Overrides Logged", total_overrides)
        if officers_data:
            avg_trust = sum(v['trust_score'] for v in officers_data.values()) / len(officers_data)
            high_trust_count = sum(1 for v in officers_data.values() if v['trust_score'] >= 0.70)
        else:
            avg_trust = 0.0
            high_trust_count = 0
        fc2.metric("Avg Trust Score", f"{avg_trust:.2f}")
        fc3.metric("High-Trust Officers (>=0.70)", high_trust_count)

        st.markdown("---")

        # Apply Learning button
        st.markdown("#### Feedback-Driven Priority Learning")
        st.markdown(
            "Click **Apply Learning** to let the system automatically adjust department priority weights "
            "based on patterns from high-trust officers (trust >= 0.70). Weights shift by up to ±5%."
        )
        if st.button("Apply Learning to Priority Weights", key="apply_learning_btn"):
            result, err = apply_feedback_learning()
            if err:
                st.error(f"Learning failed: {err}")
            elif result:
                st.success(result.get('message', 'Learning applied.'))
                high_trust_officers = result.get('high_trust_officers', [])
                if high_trust_officers:
                    st.markdown(f"**High-trust officers used:** {', '.join(high_trust_officers)}")
                updated = result.get('updated', [])
                if updated:
                    st.markdown("**Weight changes applied:**")
                    for upd in updated:
                        old = upd['old_weights']
                        new = upd['new_weights']
                        st.markdown(f"**{upd['department']}** ({upd['feedback_count']} overrides)")
                        wc1, wc2 = st.columns(2)
                        wc1.markdown(
                            f"Old: Severity={old['severity']:.3f} | Impact={old['impact']:.3f} | "
                            f"Urgency={old['urgency']:.3f} | Vulnerability={old['vulnerability']:.3f} | Dup={old['duplicate']:.3f}"
                        )
                        wc2.markdown(
                            f"New: Severity={new['severity']:.3f} | Impact={new['impact']:.3f} | "
                            f"Urgency={new['urgency']:.3f} | Vulnerability={new['vulnerability']:.3f} | Dup={new['duplicate']:.3f}"
                        )
                else:
                    st.info("No department weights were updated (may need more reliable feedback data).")

        st.markdown("---")
        st.markdown("#### Officer Trust Score Leaderboard")

        if not officers_data:
            st.info("No feedback data yet. Trust scores will appear once officers start overriding priority/severity.")
        else:
            # Build sorted list
            sorted_officers = sorted(officers_data.items(), key=lambda x: x[1]['trust_score'], reverse=True)
            trust_rows = []
            for officer_id, data in sorted_officers:
                trust_rows.append({
                    "Officer ID": officer_id,
                    "Trust Score": data['trust_score'],
                    "Agreement Rate": data['agreement_rate'],
                    "Override Rate": data['override_rate'],
                    "Total Assigned": data['total_assigned'],
                    "Total Overrides": data['total_overrides'],
                    "Priority Overrides": data.get('priority_overrides', 0),
                    "Severity Overrides": data.get('severity_overrides', 0),
                    "Dept Overrides": data.get('department_overrides', 0),
                })
            trust_df = pd.DataFrame(trust_rows)
            st.dataframe(trust_df, use_container_width=True)

            # Visual trust bars using CSS
            st.markdown("#### Trust Score Visualization")
            trust_bar_html = "<div style='margin-top:8px;'>"
            for officer_id, data in sorted_officers:
                ts = data['trust_score']
                pct = int(ts * 100)
                if ts >= 0.80:
                    bar_color = "#16a34a"
                    label_color = "#14532d"
                elif ts >= 0.60:
                    bar_color = "#ca8a04"
                    label_color = "#78350f"
                else:
                    bar_color = "#dc2626"
                    label_color = "#7f1d1d"

                trust_bar_html += f"""
                <div style='display:flex;align-items:center;margin-bottom:10px;gap:12px;'>
                    <div style='min-width:90px;font-weight:600;font-size:13px;color:#1e3a5f;'>{officer_id}</div>
                    <div style='flex:1;background:#e5e7eb;border-radius:6px;height:22px;position:relative;'>
                        <div style='width:{pct}%;background:{bar_color};height:100%;border-radius:6px;
                                    display:flex;align-items:center;padding-left:8px;'>
                            <span style='color:#fff;font-size:12px;font-weight:700;'>{ts:.2f}</span>
                        </div>
                    </div>
                    <div style='min-width:80px;font-size:12px;color:{label_color};font-weight:600;'>
                        {"High Trust" if ts >= 0.70 else "Moderate" if ts >= 0.50 else "Low Trust"}
                    </div>
                </div>
                """
            trust_bar_html += "</div>"
            st.markdown(re.sub(r'^[ \t]+', '', trust_bar_html, flags=re.MULTILINE), unsafe_allow_html=True)

        # Feedback export
        st.markdown("---")
        st.markdown("#### Feedback Export")
        fb_export = get_feedback_export()
        if fb_export:
            fb_df = pd.DataFrame(fb_export)
            st.dataframe(fb_df, use_container_width=True)
            csv_data = fb_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download Feedback CSV",
                csv_data,
                "feedback_export.csv",
                "text/csv",
                key="download_feedback_csv"
            )
        else:
            st.info("No feedback records to export.")

    # ════════════════════════════════════════════════════════════════
    # Tab 9 ── OFFICER PERFORMANCE DASHBOARD
    # ════════════════════════════════════════════════════════════════
    if active_tab == "Officer Performance":
        st.markdown("#### Officer Performance Dashboard")
        st.markdown("Resolved count, active caseload, avg resolution time, and SLA compliance per officer.")

        all_officer_stats = get_all_officer_stats()

        if not all_officer_stats:
            st.info("No officer data available.")
        else:
            # Summary KPIs
            total_assigned_all = sum(o['total_assigned'] for o in all_officer_stats)
            total_resolved_all = sum(o['total_resolved'] for o in all_officer_stats)
            avg_resolution_all = (
                sum(o['avg_resolution_hours'] * o['total_resolved'] for o in all_officer_stats)
                / max(total_resolved_all, 1)
            )
            op1, op2, op3, op4 = st.columns(4)
            op1.metric("Total Officers", len(all_officer_stats))
            op2.metric("Total Assigned", total_assigned_all)
            op3.metric("Total Resolved", total_resolved_all)
            op4.metric("Avg Resolution (hrs)", f"{avg_resolution_all:.1f}")

            st.markdown("---")

            # Build performance table with color-coded rows
            perf_rows = []
            for o in all_officer_stats:
                perf_rows.append({
                    "Officer ID": o['officer_id'],
                    "Name": o['name'],
                    "Department": o['department'],
                    "Zone": o['zone'],
                    "Assigned": o['total_assigned'],
                    "Resolved": o['total_resolved'],
                    "Active": o['current_active'],
                    "Resolution Rate (%)": o['resolution_rate'],
                    "Avg Res. (hrs)": o['avg_resolution_hours'],
                    "SLA Rate (%)": o['sla_compliance_rate'],
                    "SLA Breached": o['sla_breached'],
                    "Overrides": o['overrides_count'],
                })
            perf_df = pd.DataFrame(perf_rows)
            st.dataframe(perf_df, use_container_width=True)

            st.markdown("---")
            st.markdown("#### Individual Officer Breakdown")

            for o in all_officer_stats:
                res_rate = o['resolution_rate']
                if res_rate >= 70:
                    header_color = "#14532d"
                    badge_bg = "#dcfce7"
                    badge_text = "#166534"
                    badge_label = "High Performer"
                elif res_rate >= 40:
                    header_color = "#78350f"
                    badge_bg = "#fef9c3"
                    badge_text = "#854d0e"
                    badge_label = "Moderate Performer"
                else:
                    header_color = "#7f1d1d"
                    badge_bg = "#fee2e2"
                    badge_text = "#991b1b"
                    badge_label = "Needs Improvement"

                with st.expander(f"{o['name']} ({o['officer_id']}) — {o['department']}"):
                    st.markdown(
                        f"<span style='background:{badge_bg};color:{badge_text};padding:3px 12px;"
                        f"border-radius:12px;font-weight:600;font-size:13px;'>{badge_label}</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown(f"**Zone:** {o['zone']} | **Ward:** {o['ward']} | **Designation:** {o['designation']}")
                    m1, m2, m3, m4, m5 = st.columns(5)
                    m1.metric("Assigned", o['total_assigned'])
                    m2.metric("Resolved", o['total_resolved'])
                    m3.metric("Active", o['current_active'])
                    m4.metric("Avg Res. (hrs)", o['avg_resolution_hours'])
                    m5.metric("SLA Rate", f"{o['sla_compliance_rate']}%")

                    if o.get('status_breakdown'):
                        st.markdown("**Status Breakdown:**")
                        sb_cols = st.columns(min(len(o['status_breakdown']), 5))
                        for idx_sb, (st_name, st_cnt) in enumerate(o['status_breakdown'].items()):
                            sb_cols[idx_sb % 5].metric(st_name, st_cnt)

                    # Progress bar for resolution rate
                    st.markdown(f"**Resolution Rate:** {res_rate}%")
                    st.progress(min(res_rate / 100, 1.0))

    # ════════════════════════════════════════════════════════════════
    # Tab 10 ── DEPARTMENT HEALTH DASHBOARD
    # ════════════════════════════════════════════════════════════════
    if active_tab == "Department Health":
        st.markdown("#### Department Health Dashboard")
        st.markdown("Per-department complaint volume, active cases, priority breakdown, and health index.")

        dept_counts = stats.get('department_counts', {})
        priority_counts = stats.get('priority_counts', {})

        # Fetch all complaints to compute per-dept breakdown
        all_comps = get_complaints()
        resolved_comps = get_resolved_complaints()

        # Aggregate per department
        dept_stats_map = {}
        for c in all_comps + resolved_comps:
            dept = c.get('department', 'Unknown')
            if dept not in dept_stats_map:
                dept_stats_map[dept] = {'total': 0, 'active': 0, 'resolved': 0, 'critical': 0, 'high': 0}
            dept_stats_map[dept]['total'] += 1
            status = c.get('status', '')
            if status in ['Resolved', 'Closed']:
                dept_stats_map[dept]['resolved'] += 1
            else:
                dept_stats_map[dept]['active'] += 1
            priority = c.get('officer_override') or c.get('priority_label', 'Low')
            if priority == 'Critical':
                dept_stats_map[dept]['critical'] += 1
            elif priority == 'High':
                dept_stats_map[dept]['high'] += 1

        if not dept_stats_map:
            st.info("No department data available.")
        else:
            # Summary
            dh1, dh2, dh3 = st.columns(3)
            dh1.metric("Total Departments", len(dept_stats_map))
            at_risk = sum(1 for d in dept_stats_map.values() if d['total'] > 0 and (d['critical'] / d['total']) > 0.30)
            dh2.metric("Departments At Risk (>30% Critical)", at_risk)
            total_all = sum(d['total'] for d in dept_stats_map.values())
            dh3.metric("Total Complaints Across All Depts", total_all)

            st.markdown("---")
            st.markdown("#### Department Health Overview")

            # Sort by total desc
            sorted_depts = sorted(dept_stats_map.items(), key=lambda x: x[1]['total'], reverse=True)
            max_total = max(d['total'] for _, d in sorted_depts) if sorted_depts else 1

            for dept_name, d in sorted_depts:
                total = d['total']
                active = d['active']
                resolved = d['resolved']
                critical = d['critical']
                high = d['high']

                # Health score: 1.0 = perfect, lower = worse
                if total > 0:
                    critical_ratio = critical / total
                    resolution_ratio = resolved / total
                    health_score = max(0.0, min(1.0, resolution_ratio - critical_ratio * 0.5))
                else:
                    health_score = 1.0
                    critical_ratio = 0.0

                if health_score >= 0.6:
                    bar_color = "#16a34a"
                    status_badge = ("Healthy", "#14532d", "#dcfce7")
                elif health_score >= 0.3:
                    bar_color = "#ca8a04"
                    status_badge = ("At Risk", "#78350f", "#fef9c3")
                else:
                    bar_color = "#dc2626"
                    status_badge = ("Critical", "#7f1d1d", "#fee2e2")

                pct = int(total / max_total * 100)
                health_pct = int(health_score * 100)

                st.markdown(f"""
                <div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                            padding:14px 18px;margin-bottom:12px;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div>
                            <span style='font-size:16px;font-weight:700;color:#1e3a5f;'>{dept_name}</span>
                            <span style='margin-left:10px;background:{status_badge[2]};color:{status_badge[1]};
                                         font-size:11px;font-weight:600;padding:2px 10px;border-radius:10px;'>
                                {status_badge[0]}
                            </span>
                        </div>
                        <div style='display:flex;gap:18px;text-align:center;'>
                            <div><b style='color:#374151;font-size:16px;'>{total}</b><br/><span style='font-size:11px;color:#6b7280;'>Total</span></div>
                            <div><b style='color:#1d4ed8;font-size:16px;'>{active}</b><br/><span style='font-size:11px;color:#6b7280;'>Active</span></div>
                            <div><b style='color:#16a34a;font-size:16px;'>{resolved}</b><br/><span style='font-size:11px;color:#6b7280;'>Resolved</span></div>
                            <div><b style='color:#dc2626;font-size:16px;'>{critical}</b><br/><span style='font-size:11px;color:#6b7280;'>Critical</span></div>
                            <div><b style='color:#f59e0b;font-size:16px;'>{high}</b><br/><span style='font-size:11px;color:#6b7280;'>High</span></div>
                        </div>
                    </div>
                    <div style='margin-top:10px;'>
                        <div style='font-size:12px;color:#4b5563;margin-bottom:4px;'>
                            Complaint Volume
                        </div>
                        <div style='background:#e5e7eb;border-radius:4px;height:8px;'>
                            <div style='width:{pct}%;background:#1e3a5f;height:100%;border-radius:4px;'></div>
                        </div>
                    </div>
                    <div style='margin-top:8px;'>
                        <div style='font-size:12px;color:#4b5563;margin-bottom:4px;'>
                            Health Score: {health_score:.0%}
                        </div>
                        <div style='background:#e5e7eb;border-radius:4px;height:8px;'>
                            <div style='width:{health_pct}%;background:{bar_color};height:100%;border-radius:4px;'></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            # Detailed table
            dept_table = []
            for dept_name, d in sorted_depts:
                total = d['total']
                health_score = max(0.0, min(1.0, (d['resolved'] / total) - (d['critical'] / total) * 0.5)) if total > 0 else 1.0
                dept_table.append({
                    "Department": dept_name,
                    "Total": total,
                    "Active": d['active'],
                    "Resolved": d['resolved'],
                    "Critical": d['critical'],
                    "High": d['high'],
                    "Health Score": f"{health_score:.0%}",
                    "Status": "Critical" if health_score < 0.3 else ("At Risk" if health_score < 0.6 else "Healthy"),
                })
            st.dataframe(pd.DataFrame(dept_table), use_container_width=True)

    # ════════════════════════════════════════════════════════════════
    # Tab 11 ── COMPLAINT ANALYTICS
    # ════════════════════════════════════════════════════════════════
    if active_tab == "Complaint Analytics":
        st.markdown("#### Complaint Analytics")
        st.markdown("Priority distribution, category breakdown, and status funnel across all complaints.")

        # Pull fresh stats
        dash_stats = stats  # already fetched at top
        category_counts = dash_stats.get('category_counts', {})
        priority_counts_ca = dash_stats.get('priority_counts', {})
        status_counts_ca = dash_stats.get('status_counts', {})
        dept_counts_ca = dash_stats.get('department_counts', {})

        # KPI Row
        ca1, ca2, ca3, ca4 = st.columns(4)
        ca1.metric("Total Complaints", dash_stats.get('total_complaints', 0))
        ca2.metric("Resolved", dash_stats.get('resolved_count', 0))
        ca3.metric("Active", dash_stats.get('total_active', 0))
        ca4.metric("Rejected", dash_stats.get('rejected_count', 0))

        st.markdown("---")

        col_a, col_b = st.columns(2)

        # Priority Distribution
        with col_a:
            st.markdown("##### Priority Distribution")
            priority_colors = {
                "Critical": ("#7f1d1d", "#fca5a5"),
                "High": ("#78350f", "#fcd34d"),
                "Medium": ("#1e3a5f", "#93c5fd"),
                "Low": ("#14532d", "#86efac"),
            }
            total_pri = sum(priority_counts_ca.values()) or 1
            pri_html = "<div>"
            for pri_label, pri_count in priority_counts_ca.items():
                pct = int(pri_count / total_pri * 100)
                bg, border = priority_colors.get(pri_label, ("#374151", "#9ca3af"))
                pri_html += f"""
                <div style='display:flex;align-items:center;margin-bottom:10px;gap:10px;'>
                    <div style='min-width:70px;font-size:13px;font-weight:600;color:{bg};'>{pri_label}</div>
                    <div style='flex:1;background:#f1f5f9;border-radius:6px;height:26px;position:relative;'>
                        <div style='width:{pct}%;background:{bg};height:100%;border-radius:6px;
                                    display:flex;align-items:center;padding-left:8px;min-width:2px;'>
                            <span style='color:#fff;font-size:12px;font-weight:700;'>{pri_count}</span>
                        </div>
                    </div>
                    <div style='min-width:40px;font-size:12px;color:#6b7280;'>{pct}%</div>
                </div>
                """
            pri_html += "</div>"
            st.markdown(re.sub(r'^[ \t]+', '', pri_html, flags=re.MULTILINE), unsafe_allow_html=True)

        # Status Funnel
        with col_b:
            st.markdown("##### Status Funnel")
            status_colors_map = {
                "Submitted": "#64748b",
                "Assigned": "#1d4ed8",
                "Accepted": "#7c3aed",
                "In Progress": "#0891b2",
                "Field Inspection": "#0369a1",
                "Escalated": "#b45309",
                "Resolved": "#16a34a",
                "Closed": "#166534",
                "Rejected": "#dc2626",
            }
            total_st = sum(status_counts_ca.values()) or 1
            st_html = "<div>"
            for st_name, st_count in sorted(status_counts_ca.items(), key=lambda x: x[1], reverse=True):
                pct = int(st_count / total_st * 100)
                color = status_colors_map.get(st_name, "#6b7280")
                st_html += f"""
                <div style='display:flex;align-items:center;margin-bottom:8px;gap:10px;'>
                    <div style='min-width:110px;font-size:12px;font-weight:600;color:{color};'>{st_name}</div>
                    <div style='flex:1;background:#f1f5f9;border-radius:6px;height:22px;'>
                        <div style='width:{max(pct,2)}%;background:{color};height:100%;border-radius:6px;
                                    display:flex;align-items:center;padding-left:6px;min-width:2px;'>
                            <span style='color:#fff;font-size:11px;font-weight:700;'>{st_count}</span>
                        </div>
                    </div>
                    <div style='min-width:36px;font-size:12px;color:#6b7280;'>{pct}%</div>
                </div>
                """
            st_html += "</div>"
            st.markdown(re.sub(r'^[ \t]+', '', st_html, flags=re.MULTILINE), unsafe_allow_html=True)

        st.markdown("---")

        col_c, col_d = st.columns(2)

        # Category Breakdown
        with col_c:
            st.markdown("##### Top Categories by Volume")
            if category_counts:
                sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                total_cat = sum(v for _, v in sorted_cats) or 1
                cat_html = "<div>"
                cat_palette = ["#1e3a5f", "#1d4ed8", "#7c3aed", "#0891b2", "#0369a1", "#059669", "#d97706", "#dc2626", "#be185d", "#6b7280"]
                for ci, (cat_name, cat_count) in enumerate(sorted_cats):
                    pct = int(cat_count / total_cat * 100)
                    color = cat_palette[ci % len(cat_palette)]
                    cat_html += f"""
                    <div style='display:flex;align-items:center;margin-bottom:8px;gap:10px;'>
                        <div style='min-width:120px;font-size:12px;font-weight:600;color:{color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{cat_name}</div>
                        <div style='flex:1;background:#f1f5f9;border-radius:6px;height:22px;'>
                            <div style='width:{max(pct,2)}%;background:{color};height:100%;border-radius:6px;
                                        display:flex;align-items:center;padding-left:6px;min-width:2px;'>
                                <span style='color:#fff;font-size:11px;font-weight:700;'>{cat_count}</span>
                            </div>
                        </div>
                        <div style='min-width:36px;font-size:12px;color:#6b7280;'>{pct}%</div>
                    </div>
                    """
                cat_html += "</div>"
                st.markdown(re.sub(r'^[ \t]+', '', cat_html, flags=re.MULTILINE), unsafe_allow_html=True)
            else:
                st.info("No category data available.")

        # Department Volume
        with col_d:
            st.markdown("##### Complaints by Department")
            if dept_counts_ca:
                sorted_depts_ca = sorted(dept_counts_ca.items(), key=lambda x: x[1], reverse=True)[:10]
                total_dept_ca = sum(v for _, v in sorted_depts_ca) or 1
                dept_html = "<div>"
                dept_palette = ["#0f766e", "#047857", "#0369a1", "#6d28d9", "#b45309", "#dc2626", "#1d4ed8", "#be185d", "#7c3aed", "#374151"]
                for di, (dept_name, dept_count) in enumerate(sorted_depts_ca):
                    pct = int(dept_count / total_dept_ca * 100)
                    color = dept_palette[di % len(dept_palette)]
                    dept_html += f"""
                    <div style='display:flex;align-items:center;margin-bottom:8px;gap:10px;'>
                        <div style='min-width:150px;font-size:12px;font-weight:600;color:{color};white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{dept_name}</div>
                        <div style='flex:1;background:#f1f5f9;border-radius:6px;height:22px;'>
                            <div style='width:{max(pct,2)}%;background:{color};height:100%;border-radius:6px;
                                        display:flex;align-items:center;padding-left:6px;min-width:2px;'>
                                <span style='color:#fff;font-size:11px;font-weight:700;'>{dept_count}</span>
                            </div>
                        </div>
                        <div style='min-width:36px;font-size:12px;color:#6b7280;'>{pct}%</div>
                    </div>
                    """
                dept_html += "</div>"
                st.markdown(re.sub(r'^[ \t]+', '', dept_html, flags=re.MULTILINE), unsafe_allow_html=True)
            else:
                st.info("No department data available.")

        st.markdown("---")

        # Meaningful analytics summary: 4 separate focused tables
        st.markdown("##### Detailed Analytics Breakdown")

        sum_col1, sum_col2 = st.columns(2)

        with sum_col1:
            st.markdown("**Priority Breakdown**")
            pri_rows = []
            total_pri_sum = sum(priority_counts_ca.values()) or 1
            pri_order = ["Critical", "High", "Medium", "Low"]
            for pl in pri_order:
                cnt = priority_counts_ca.get(pl, 0)
                pri_rows.append({
                    "Priority Level": pl,
                    "Complaints": cnt,
                    "Share (%)": f"{cnt/total_pri_sum*100:.1f}%",
                    "SLA Hours": {"Critical":"24h","High":"72h","Medium":"120h","Low":"168h"}.get(pl,"N/A")
                })
            st.dataframe(pd.DataFrame(pri_rows), use_container_width=True, hide_index=True)

            st.markdown("**Status Flow**")
            status_order_sum = ["Submitted","Assigned","Accepted","In Progress","Field Inspection","Escalated","Resolved","Closed","Rejected"]
            total_st_sum = sum(status_counts_ca.values()) or 1
            st_rows = []
            for sn in status_order_sum:
                sc = status_counts_ca.get(sn, 0)
                if sc > 0:
                    st_rows.append({
                        "Status": sn,
                        "Complaints": sc,
                        "Share (%)": f"{sc/total_st_sum*100:.1f}%",
                        "Stage": "Active" if sn in ["Submitted","Assigned","Accepted","In Progress","Field Inspection"] else ("Escalated" if sn == "Escalated" else "Closed")
                    })
            st.dataframe(pd.DataFrame(st_rows), use_container_width=True, hide_index=True)

        with sum_col2:
            st.markdown("**Category Breakdown**")
            total_cat_sum = sum(category_counts.values()) or 1
            cat_rows = []
            for cn, cc in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
                cat_rows.append({
                    "Category": cn,
                    "Complaints": cc,
                    "Share (%)": f"{cc/total_cat_sum*100:.1f}%"
                })
            st.dataframe(pd.DataFrame(cat_rows), use_container_width=True, hide_index=True)

            st.markdown("**Department Load**")
            total_dept_sum = sum(dept_counts_ca.values()) or 1
            dept_sum_rows = []
            for dn, dc in sorted(dept_counts_ca.items(), key=lambda x: x[1], reverse=True):
                dept_sum_rows.append({
                    "Department": dn,
                    "Complaints": dc,
                    "Share (%)": f"{dc/total_dept_sum*100:.1f}%"
                })
            st.dataframe(pd.DataFrame(dept_sum_rows), use_container_width=True, hide_index=True)



def officer_admin_profile_page(role):
    """Renders a profile page for officer or admin users"""
    render_government_banner()
    
    user = st.session_state.user
    view_key = f"{role}_view"
    
    # Back to Dashboard button at the top
    if st.button("Back to Dashboard", key="oa_profile_back_to_dash"):
        st.session_state[view_key] = "dashboard"
        st.rerun()
    
    title = "Officer Profile" if role == "officer" else "Admin Profile"
    st.markdown(f"## {title}")
    st.markdown("View your account details, role assignment, and portal information.")
    st.markdown("---")
    
    # Two-column layout
    col_info, col_details = st.columns([1, 1])
    
    with col_info:
        st.markdown("### Account Information")
        
        role_colors = {
            "admin": "#c53030",
            "officer": "#2b6cb0",
            "citizen": "#38a169"
        }
        role_color = role_colors.get(role, '#4a5568')
        role_display = role.upper()
        
        st.markdown(f"""
        <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px 0; color: #718096; font-weight: bold; width: 150px;">Full Name</td>
                <td style="padding: 10px 0; color: #2d3748; font-weight: bold;">{user.get('name', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px 0; color: #718096; font-weight: bold;">Username</td>
                <td style="padding: 10px 0; color: #2d3748; font-family: monospace;">{user.get('username', 'N/A')}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 10px 0; color: #718096; font-weight: bold;">Portal Role</td>
                <td style="padding: 10px 0;"><span style="background-color: {role_color}; color: white; padding: 3px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;">{role_display}</span></td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
    
    with col_details:
        if role == 'officer':
            st.markdown("### Officer Assignment Details")
            officer_info = user.get('officer', {})
            officer_id = user.get('officer_id', 'N/A')
            
            st.markdown(f"""
            <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold; width: 150px;">Officer ID</td>
                    <td style="padding: 10px 0; color: #2d3748; font-family: monospace;">{officer_id}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold;">Department</td>
                    <td style="padding: 10px 0; color: #2d3748;">{officer_info.get('department', 'N/A')}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold;">Zone</td>
                    <td style="padding: 10px 0; color: #2d3748;">{officer_info.get('zone', 'N/A')}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold;">Ward</td>
                    <td style="padding: 10px 0; color: #2d3748;">{officer_info.get('ward', 'N/A')}</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold;">Designation</td>
                    <td style="padding: 10px 0; color: #2d3748;">{officer_info.get('designation', 'N/A')}</td>
                </tr>
            </table>
            """, unsafe_allow_html=True)
        
        elif role == 'admin':
            st.markdown("### Admin Access Details")
            st.markdown(f"""
            <table style="width:100%; border-collapse: collapse; margin-bottom: 20px; font-size: 14px;">
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold; width: 150px;">Access Level</td>
                    <td style="padding: 10px 0; color: #2d3748; font-weight: bold;">Full System Access</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold;">Capabilities</td>
                    <td style="padding: 10px 0; color: #2d3748;">Manage Complaints, Officers, Policies, Analytics</td>
                </tr>
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 10px 0; color: #718096; font-weight: bold;">Override Authority</td>
                    <td style="padding: 10px 0; color: #2d3748;">Global Priority Override</td>
                </tr>
            </table>
            """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════


def main():
    inject_custom_css()
    
    # Synchronize query parameters to st.session_state.login_role
    qp = st.query_params
    if "login" in qp:
        login_role_qp = qp["login"]
        if login_role_qp in ["citizen", "officer", "admin"]:
            st.session_state.login_role = login_role_qp
        elif login_role_qp in ["none", ""]:
            st.session_state.login_role = None
            st.session_state.login_error = None
            
    # Synchronize view parameters for citizen portal profile card
    if "view" in qp:
        view_qp = qp["view"]
        if view_qp == "profile" and st.session_state.user and st.session_state.user.get('role') == 'citizen':
            st.session_state.citizen_view = "profile"
        elif view_qp == "portal" and st.session_state.user and st.session_state.user.get('role') == 'citizen':
            st.session_state.citizen_view = "portal"
    
    # ── Not Logged In → Show Landing Page or Login Portal ──
    if st.session_state.user is None:
        if st.session_state.get('login_role') is None:
            landing_page()
        else:
            login_page(st.session_state.login_role)
        return
    
    # ── Logged In → Show Role-Based Dashboard ──
    user = st.session_state.user
    role = user.get('role', 'citizen')
    
    # Initialize page variables for admin
    admin_page = "Dashboard"
    
    # Sidebar
    if role != 'citizen':
        render_sidebar_header()
        
        # Admin gets page navigation in sidebar at the top
        if role == 'commissioner' and st.session_state.get('commissioner_view') != 'profile':
            st.sidebar.markdown("**Role:** City Commissioner")
        elif role == 'admin' and st.session_state.get('admin_view') != 'profile':
            admin_page = st.sidebar.radio(
                "Admin Navigation:",
                [
                    "Dashboard",
                                        "System-Wide Queue",
                    "Escalation & SLA Queue",
                    "Audit Trail Viewer",
                    "SLA Configurations",
                    "Escalation Configurations",
                    "Officer Management",
                    "Department Policies",
                    "Hotspot Intelligence",
                    "Trust & Feedback Analytics",
                    "Officer Performance",
                    "Department Health",
                    "Complaint Analytics",
                    "Submit Grievance (Test)"
                ],
                label_visibility="collapsed"
            )

        if role == 'officer':
            user = st.session_state.user
            officer_id = user.get('officer_id', '')


        # Add spacer to push profile and logout to bottom
        st.sidebar.markdown("<br>", unsafe_allow_html=True)
        st.sidebar.markdown("---")
        
        # Profile button (styled as a card, similar to citizen sidebar)
        display_name = user.get('name', user.get('username', 'User'))
        role_display = role.upper()
        profile_label = f"{display_name}\n\n{role_display} Portal"
        
        # Initialize view state for officer/admin
        view_key = f"{role}_view"
        if view_key not in st.session_state:
            st.session_state[view_key] = "dashboard"
            
        # Inject dynamic CSS rule for this button's avatar ::before pseudo-element
        first_letter = display_name[0].upper() if display_name else "U"
        avatar_bg = "#2b6cb0" if role == "officer" else "#c53030"
        avatar_border = "#1a4e8a" if role == "officer" else "#9b2c2c"
        
        avatar_style = f"""
        <style>
        section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button::before {{
            content: "{first_letter}" !important;
            position: absolute !important;
            left: 12px !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
            width: 38px !important;
            height: 38px !important;
            border-radius: 50% !important;
            background-color: {avatar_bg} !important;
            border: 1px solid {avatar_border} !important;
            color: white !important;
            font-weight: bold !important;
            font-size: 15px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-family: Arial, sans-serif !important;
            z-index: 5 !important;
        }}
        </style>
        """
        st.sidebar.markdown(avatar_style, unsafe_allow_html=True)
        
        is_active = (st.session_state[view_key] == "profile")
        active_bg = "#e2e8f0" if is_active else "#ffffff"
        active_border = "#0f294a" if is_active else "#cbd5e0"
        
        sidebar_layout_css = f"""
        <style>
        section[data-testid="stSidebar"] div.stButton:nth-last-of-type(2) button {{
            background-color: {active_bg} !important;
            border-color: {active_border} !important;
        }}
        /* Bring profile card right top of the logout button without a huge gap */
        section[data-testid="stSidebar"] div.element-container:nth-last-of-type(2) {{
            margin-bottom: 8px !important;
        }}
        section[data-testid="stSidebar"] div.element-container:nth-last-of-type(1) {{
            margin-top: 0px !important;
        }}
        </style>
        """
        st.sidebar.markdown(sidebar_layout_css, unsafe_allow_html=True)
        

        if st.sidebar.button(profile_label, key="nav_to_oa_profile", use_container_width=True):
            st.session_state[view_key] = "profile"
            st.rerun()
        
        # Logout button
        if st.sidebar.button("Logout", key="nav_oa_logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.login_role = None
            st.session_state.login_error = None
            st.query_params.clear()
            st.rerun()
    else:
        render_citizen_sidebar_layout()
    
    # Role-based sidebar navigation
    raw_role = role
    role = raw_role.lower() if raw_role else ''
    
    if role == 'citizen':
        # Default citizen view
        if 'citizen_view' not in st.session_state:
            st.session_state.citizen_view = "portal"
            
        if st.session_state.citizen_view == "portal":
            citizen_portal()
        elif st.session_state.citizen_view == "profile":
            citizen_profile_page()
    
    elif role == 'officer':
        if st.session_state.get('officer_view') == "profile":
            officer_admin_profile_page(role)
        else:
            officer_dashboard()
    
    elif role == 'commissioner':
        if st.session_state.get('commissioner_view') == "profile":
            officer_admin_profile_page(role)
        else:
            render_commissioner_dashboard()

    elif role == 'admin':
        if st.session_state.get('admin_view') == "profile":
            officer_admin_profile_page(role)
        else:
            if admin_page == "Submit Grievance (Test)":
                citizen_portal()
            else:
                admin_dashboard(admin_page)
    
    else:
        st.error(f"Unknown role: {raw_role}")


if __name__ == "__main__":
    main()

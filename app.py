"""
Sahayak AI - Intelligent NLP-Driven Complaint Triage System
Streamlit Application with Role-Based Dashboards
  - Login Page (default entry point)
  - Citizen Portal (role=citizen)
  - Officer Dashboard (role=officer, filtered by officer_id)
  - Admin Dashboard (role=admin, full access)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import os
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
            
            if (headerText.includes("Level: CRITICAL") || headerText.includes("Level: HIGH")) {
                exp.style.setProperty("background-color", "#fff5f5", "important");
                exp.style.setProperty("border", "1px solid #feb2b2", "important");
                exp.style.setProperty("border-left", "8px solid #c53030", "important");
                
                const titleText = exp.querySelector('p');
                if (titleText) {
                    titleText.style.setProperty("color", "#9b2c2c", "important");
                    titleText.style.setProperty("font-weight", "bold", "important");
                }
            } else if (headerText.includes("Level: MEDIUM")) {
                exp.style.setProperty("background-color", "#fefbeb", "important");
                exp.style.setProperty("border", "1px solid #fef3c7", "important");
                exp.style.setProperty("border-left", "8px solid #d97706", "important");
                
                const titleText = exp.querySelector('p');
                if (titleText) {
                    titleText.style.setProperty("color", "#b45309", "important");
                    titleText.style.setProperty("font-weight", "bold", "important");
                }
            } else if (headerText.includes("Level: LOW")) {
                exp.style.setProperty("background-color", "#ffffff", "important");
                exp.style.setProperty("border", "1px solid #e2e8f0", "important");
                exp.style.setProperty("border-left", "8px solid #718096", "important");
                
                const titleText = exp.querySelector('p');
                if (titleText) {
                    titleText.style.setProperty("color", "#2d3748", "important");
                    titleText.style.setProperty("font-weight", "bold", "important");
                }
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

def render_complaint_expander(complaint, idx, show_actions=True, officer_id_for_override=None):
    """
    Renders a single complaint inside an expander with all details,
    metrics, AI suggestions, RAG context, duplicates, and officer actions.
    
    Args:
        complaint: complaint dict from API
        idx: display index (1-based)
        show_actions: whether to show resolve/override actions
        officer_id_for_override: officer_id to pass in severity/department override calls
    """
    has_override = complaint.get('officer_override') is not None
    display_label = complaint['officer_override'] if has_override else complaint['priority_label']
    
    dup_suffix = f" [Grouped: {complaint['duplicate_count'] + 1} Reports]" if complaint.get('duplicate_count', 0) > 0 else ""
    with st.expander(
        f"Ref: {complaint['id']}{dup_suffix} | Level: {display_label.upper()} (Score: {complaint['final_priority_score']:.3f}) | Category: {complaint['category']}",
        expanded=(idx <= 3)
    ):
        st.markdown("**Grievance Description:**")
        st.info(complaint['complaint_text'])
        
        rel_time_str = f" ({complaint['relative_time']})" if complaint.get('relative_time') else ""
        st.markdown(f"**Category:** `{complaint['category']}` | **Department:** `{complaint['department']}` | **Registered:** `{complaint['timestamp']}`{rel_time_str}")
        
        # Assigned officer info
        if complaint.get('assigned_officer'):
            officer = complaint['assigned_officer']
            officer_name = officer.get('name', 'Unknown')
            officer_dept = officer.get('department', '')
            st.markdown(f"**Assigned Officer:** `{officer_name}` | **Officer ID:** `{officer.get('officer_id', 'N/A')}` | **Dept:** `{officer_dept}`")
        
        # Metrics table (markdown)
        metrics_table = f"""
| Factor / Dimension | Score | Weight | Rationale / Info |
| :--- | :---: | :---: | :--- |
| **Severity (Tier: {complaint.get('severity_label', 'Low')})** | `{complaint.get('severity_score', 0.0):.2f}` | 30% | {complaint.get('severity_reason', 'N/A')} |
| **Public Impact** | `{complaint.get('public_impact_score', 0.0):.2f}` | 25% | Evaluates affected areas and infrastructure proximity |
| **Urgency** | `{complaint.get('urgency_score', 0.0):.2f}` | 20% | Derived from incident time & immediate hazards |
| **Vulnerability** | `{complaint.get('vulnerability_score', 0.0):.2f}` | 15% | School/hospital zones or public safety tags |
| **Duplicate Escalation** | `{complaint.get('duplicate_escalation_score', 0.0):.2f}` | 10% | Frequency of repeating reports in the area |
"""
        st.markdown(metrics_table)
        
        # AI Final Priority summary
        llm_note = f" (Adjusted {complaint['llm_adjustment']:+.2f} by AI Governance Advisory)" if complaint.get('llm_reviewed', False) else ""
        age_note = f" (Aging Escalation: +{complaint.get('aging_boost', 0.0):.2f} - registered {complaint.get('relative_time', 'some time ago')})" if complaint.get('aging_boost', 0.0) > 0 else ""
        st.markdown(f"**AI Final Priority:** **{display_label.upper()}** (Score: `{complaint.get('final_priority_score', 0.0):.3f}` = Base `{complaint.get('priority_score', 0.0):.3f}`{llm_note}{age_note})")
        
        # LLM Review details
        if complaint.get('llm_reviewed', False):
            triggers_str = ", ".join(complaint.get('llm_trigger_reasons', []))
            st.markdown(f"""
> **AI Governance Advisory Review**
> - **Trigger Flagged:** {triggers_str or 'None'}
> - **Risks:** Public Safety: `{complaint.get('llm_public_safety_risk', 'N/A')}` | Vulnerable Population: `{complaint.get('llm_vulnerable_population_risk', 'N/A')}` | Infrastructure: `{complaint.get('llm_infrastructure_risk', 'N/A')}`
> - **Advisory Rationale:** {complaint.get('llm_reasoning', 'N/A')} *(Summary: {complaint.get('llm_risk_summary', 'N/A')})*
""")

        # AI Feedback & Suggested Response/Action
        sj = complaint.get('structured_json', {})
        if isinstance(sj, dict) and (sj.get('suggested_response') or sj.get('suggested_action')):
            st.markdown("---")
            st.markdown("#### AI Feedback & Redressal Advice")
            adv_col1, adv_col2 = st.columns(2)
            with adv_col1:
                st.info(f"**Suggested Response (Copy/Paste):**  \n*\"{sj.get('suggested_response', 'N/A')}\"*")
            with adv_col2:
                st.success(f"**Suggested Actions for Officer:**  \n{sj.get('suggested_action', 'N/A')}")

        st.markdown("---")
        
        # RAG Similar Complaints & Duplicate Registry
        col_rag, col_dup = st.columns(2)
        with col_rag:
            st.markdown("**Historical Context (RAG)**")
            similar_cases = complaint.get('similar_cases')
            if similar_cases:
                for sc in similar_cases[:2]:
                    st.markdown(f"- **{sc['id']}** ({sc['category']}, Priority: **{sc['priority_label']}**) | Similarity: `{sc['similarity']*100:.1f}%`  \n"
                                 f"  *Text:* \"{sc['complaint_text'][:70]}...\"  \n"
                                 f"  *Status:* **{sc['resolution_history'][-1]['status'] if sc.get('resolution_history') else 'Submitted'}**")
            else:
                st.info("No past similar cases found in database.")
                
        with col_dup:
            st.markdown("**Duplicate Registry**")
            if complaint.get('duplicate_count', 0) > 0:
                st.warning(f"**Duplicate Count:** `{complaint['duplicate_count']}` recurring reports.")
                dup_ids = ", ".join([f"`{dc['id']}`" for dc in complaint.get('duplicate_reports', [])])
                st.markdown(f"**Duplicate IDs:** {dup_ids}")
            else:
                st.success("No duplicates detected in queue.")

        # Raw JSON data
        with st.expander("View Raw Technical Parser Data (JSON)", expanded=False):
            st.json(complaint.get('structured_json', {}))
        
        # Grouped duplicate reports
        if complaint.get('duplicate_count', 0) > 0:
            with st.expander(f"View Grouped Duplicate Reports ({complaint['duplicate_count']})", expanded=False):
                for d_idx, dc in enumerate(complaint.get('duplicate_reports', []), 1):
                    st.markdown(f"**Duplicate #{d_idx}:** Reference ID: `{dc['id']}` | Filed: `{dc['timestamp']}`")
                    st.markdown(f"*{dc['complaint_text']}*")
                    st.markdown("---")
        
        # ── Officer Actions ──
        if show_actions:
            st.markdown("---")
            st.markdown("**Officer Actions**")
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                st.markdown("**Resolve Grievance**")
                resolution_notes = st.text_input(
                    "Resolution Notes:",
                    key=f"resolve_notes_{complaint['id']}",
                    placeholder="Describe action taken to resolve..."
                )
                if st.button("Mark as Solved", key=f"solve_{complaint['id']}", type="primary", use_container_width=True):
                    notes = resolution_notes if resolution_notes.strip() else "Marked as resolved by officer."
                    try:
                        r = requests.post(f"{API_URL}/complaints/{complaint['id']}/resolve", json={"notes": notes})
                        if r.status_code == 200:
                            st.success(f"Grievance {complaint['id']} and its duplicates marked as solved!")
                            st.rerun()
                        else:
                            st.error(f"Failed to resolve complaint: {r.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to API server: {e}")
                    
            with action_col2:
                st.markdown("**Priority Override**")
                if has_override:
                    st.success(f"Priority overridden to: **{complaint['officer_override']}**")
                    if complaint.get('override_reason'):
                        st.markdown(f"*Reason:* {complaint['override_reason']}")
                else:
                    override_priority = st.selectbox(
                        "Override Priority Level:",
                        ["Critical", "High", "Medium", "Low"],
                        key=f"override_select_{complaint['id']}"
                    )
                    override_reason = st.text_input(
                        "Provide override justification:",
                        key=f"reason_{complaint['id']}",
                        placeholder="Why override this priority?"
                    )
                    if st.button("Submit Override", key=f"apply_{complaint['id']}", type="secondary", use_container_width=True):
                        o_reason = override_reason if override_reason else "No justification provided"
                        try:
                            r = requests.post(
                                f"{API_URL}/complaints/{complaint['id']}/override",
                                json={"priority_label": override_priority, "reason": o_reason}
                            )
                            if r.status_code == 200:
                                override_record = {
                                    'complaint_id': complaint['id'],
                                    'complaint_text': complaint['complaint_text'],
                                    'ai_priority': complaint['priority_label'],
                                    'officer_priority': override_priority,
                                    'reason': o_reason,
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                st.session_state.officer_overrides.append(override_record)
                                st.rerun()
                            else:
                                st.error(f"Failed to override priority: {r.text}")
                        except Exception as e:
                            st.error(f"Failed to connect to API server: {e}")
            
            # Additional override actions: Severity Override & Department Override
            ov_col1, ov_col2 = st.columns(2)
            with ov_col1:
                st.markdown("**Severity Override**")
                new_severity = st.number_input(
                    "New Severity Score (0.0-1.0):",
                    min_value=0.0, max_value=1.0, step=0.05, value=0.5,
                    key=f"sev_override_{complaint['id']}"
                )
                sev_reason = st.text_input(
                    "Severity override reason:",
                    key=f"sev_reason_{complaint['id']}",
                    placeholder="Justification for severity change..."
                )
                if st.button("Override Severity", key=f"sev_apply_{complaint['id']}", use_container_width=True):
                    oid = officer_id_for_override or "ADMIN"
                    try:
                        r = requests.post(
                            f"{API_URL}/complaints/{complaint['id']}/override-severity",
                            json={"severity_score": new_severity, "reason": sev_reason or "Manual override", "officer_id": oid}
                        )
                        if r.status_code == 200:
                            st.success("Severity overridden successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            
            with ov_col2:
                st.markdown("**Department Override**")
                new_dept = st.text_input(
                    "New Department:",
                    key=f"dept_override_{complaint['id']}",
                    placeholder="e.g. PWD, Health Dept..."
                )
                dept_reason = st.text_input(
                    "Department override reason:",
                    key=f"dept_reason_{complaint['id']}",
                    placeholder="Justification for re-routing..."
                )
                if st.button("Override Department", key=f"dept_apply_{complaint['id']}", use_container_width=True):
                    oid = officer_id_for_override or "ADMIN"
                    try:
                        r = requests.post(
                            f"{API_URL}/complaints/{complaint['id']}/override-department",
                            json={"new_department": new_dept, "reason": dept_reason or "Manual re-route", "officer_id": oid}
                        )
                        if r.status_code == 200:
                            st.success("Department overridden successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed: {r.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")


def render_complaint_queue(complaints, resolved_complaints, rejected_complaints,
                           show_actions=True, officer_id_for_override=None, key_prefix=""):
    """
    Shared complaint queue renderer with three tabs:
    Active Queue, Resolved, Restricted.
    Used by both Officer and Admin dashboards.
    """
    # Summary metrics
    total_admissible = len(complaints)
    total_rejected = len(rejected_complaints)
    critical_priority = len([c for c in complaints if c['priority_label'] == 'Critical'])
    high_priority = len([c for c in complaints if c['priority_label'] == 'High'])
    medium_priority = len([c for c in complaints if c['priority_label'] == 'Medium'])
    low_priority = len([c for c in complaints if c['priority_label'] == 'Low'])
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Active Groups", total_admissible)
    with col2:
        st.metric("Critical Priority", critical_priority)
    with col3:
        st.metric("High Priority", high_priority)
    with col4:
        st.metric("Medium Priority", medium_priority)
    with col5:
        st.metric("Low Priority", low_priority)
    with col6:
        st.metric("Restricted / Reject", total_rejected)
        
    st.markdown("---")
    tab_queue, tab_resolved, tab_rejected = st.tabs([
        "Active Triage Queue", 
        "Resolved Grievances", 
        "Restricted / Non-Admissible Logs"
    ])
    
    # ── Active Queue ──
    with tab_queue:
        if not complaints:
            st.info("No active complaints in the queue.")
        else:
            st.markdown("#### Active Grievance Queue (Ranked by Governance Priority)")
            for idx, complaint in enumerate(complaints, 1):
                render_complaint_expander(
                    complaint, idx,
                    show_actions=show_actions,
                    officer_id_for_override=officer_id_for_override
                )
    
    # ── Resolved ──
    with tab_resolved:
        if not resolved_complaints:
            st.info("No resolved grievances yet.")
        else:
            st.markdown("#### Resolved Grievances Log")
            for idx, complaint in enumerate(resolved_complaints, 1):
                display_label = complaint.get('officer_override') or complaint['priority_label']
                with st.expander(f"Ref: {complaint['id']} | Status: RESOLVED | Priority: {display_label.upper()} | Category: {complaint['category']}", expanded=False):
                    st.markdown("**Grievance Description:**")
                    st.info(complaint['complaint_text'])
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Final Priority Level:** **{display_label}**")
                        st.markdown(f"**Category:** `{complaint['category']}`")
                        st.markdown(f"**Department:** `{complaint['department']}`")
                    with c2:
                        st.markdown(f"**Registered:** `{complaint['timestamp']}`")
                        if complaint.get('officer_override'):
                            st.markdown(f"*Priority overridden by officer from: {complaint['priority_label']}*")
                        
                    st.markdown("**Resolution & Audit History:**")
                    for hist in complaint.get('resolution_history', []):
                        st.markdown(f"- **{hist['status']}** ({hist['date']}): {hist.get('notes', '')}")
                        
    # ── Restricted ──
    with tab_rejected:
        if not rejected_complaints:
            st.info("No restricted complaints logged in system.")
        else:
            st.markdown("#### Log of Non-Admissible / Restricted Issues")
            for idx, complaint in enumerate(rejected_complaints, 1):
                with st.expander(f"Locked Ref: {complaint['id']} | Reason: {complaint.get('raw_predicted_category', 'Unknown').replace('Prohibited_', '')}", expanded=True):
                    st.markdown("**Complaint Text:**")
                    st.warning(complaint['complaint_text'])
                    st.markdown(f"**Policy Violation Reason:** `{complaint.get('rejection_reason', 'N/A')}`")
                    st.markdown(f"**Timestamp:** `{complaint['timestamp']}`")
                    with st.expander("View Raw Technical Parser Data (JSON)", expanded=False):
                        st.json(complaint.get('structured_json', {}))
    
    # Export override feedback
    st.markdown("---")
    if st.session_state.officer_overrides:
        st.markdown(f"### Framework Training Data Log ({len(st.session_state.officer_overrides)} overrides)")
        if st.button("Compile & Export Override Log", key=f"{key_prefix}_export_btn"):
            override_df = pd.DataFrame(st.session_state.officer_overrides)
            csv = override_df.to_csv(index=False)
            st.download_button(
                label="Download Override Dataset (CSV)",
                data=csv,
                file_name=f"officer_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key=f"{key_prefix}_dl_btn"
            )
            st.success("Override feedback compiled. Dataset ready for download.")


# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR COMPONENTS
# ════════════════════════════════════════════════════════════════════════════════

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
    if st.button("← Back to Grievance Dashboard", key="profile_back_to_dash"):
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
        if uploaded_pic:
            st.session_state.citizen_profile_pic = uploaded_pic.read()
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
    if st.button("← Back to Landing Page", key="back_to_home"):
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
                            user_role = user_data.get('role')
                            if user_role != target_role:
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
    """Citizen-facing complaint submission and tracking portal"""
    render_government_banner()
    
    st.markdown("### Grievance Registration Portal")
    st.markdown("Use this portal to register public service or civic complaints. The Sahayak AI triage system will automatically classify, verify admissibility, and compute priority metrics.")
    st.markdown("---")
    
    tab_submit, tab_history, tab_track = st.tabs(["Submit Grievance", "My Submitted Grievances", "Track Grievance"])
    
    # ── Submit Tab ──
    with tab_submit:
        # Check profile settings
        profile = st.session_state.get('citizen_profile', {})
        location_parts = []
        if profile.get("address"):
            location_parts.append(profile["address"])
        if profile.get("zone"):
            location_parts.append(f"Zone: {profile['zone']}")
        if profile.get("ward"):
            location_parts.append(profile['ward'])
            
        if location_parts:
            st.info(f"Mapped location from profile: {', '.join(location_parts)}")

        complaint_text = st.text_area(
            "Enter grievance description:",
            height=150,
            placeholder="Provide a detailed description of the incident/issue...",
            help="Specify the location, what happened, and any public safety risks or affected populations."
        )
        
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            submit_button = st.button("Submit Grievance", type="primary", use_container_width=True)
        
        if submit_button:
            if not complaint_text.strip():
                st.error("Submission failed: Please enter a grievance description before submitting.")
            else:
                with st.spinner("Processing grievance..."):
                    # Enrich text with saved profile location details for NER routing
                    enriched_text = complaint_text.strip()
                    if location_parts:
                        enriched_text += f"\n\n[Citizen Profile Location: {', '.join(location_parts)}]"
                    
                    # Pass the logged-in citizen's username
                    username = st.session_state.user.get('username')
                    result = predict_complaint(enriched_text, submitted_by=username)
                    
                    if result is None:
                        st.stop()
                    
                    # Check admissibility
                    if not result['admissible']:
                        st.error(f"Grievance Not Admissible for Processing")
                        st.info(f"Reason for non-admissibility: {result['rejection_reason']}")
                        
                        with st.expander("View Technical Triage Data", expanded=False):
                            st.json(result['structured_json'])
                        
                        st.markdown("---")
                        st.warning("Notice: This complaint does not comply with public portal policies and has been locked from routing.")
                        return
                    
                    # Admissible - show details
                    complaint_id = result['id']
                    st.success(f"Grievance filed successfully. Reference ID: {complaint_id}")
                    
                    st.markdown("### Filed Grievance Record")
                    st.markdown(f"**Grievance Reference ID:** `{complaint_id}`")
                    st.markdown(f"**Grievance Category:** `{result['category']}`")
                    st.markdown(f"**Assigned Department:** `{result['department']}`")
                    
                    # Show assigned officer if available
                    assigned_officer_id = result.get('assigned_officer_id')
                    if assigned_officer_id:
                        off_disp = get_officer_display_name(assigned_officer_id)
                        st.markdown(f"**Complaint handling officer:** `{off_disp}`")
                    
                    st.markdown(f"**Identified Location:** `{result['structured_json'].get('location') or 'Not Detected'}`")
                    st.markdown(f"**Identified Infrastructure:** `{result['structured_json'].get('infrastructure') or 'Not Detected'}`")
                    st.markdown(f"**Filing Timestamp:** `{result['timestamp']}`")
                    
                    if result['structured_json'].get('risk_keywords'):
                        st.markdown("**Risk Keywords Flagged:**")
                        kw_badges = " ".join([f"`{kw}`" for kw in result['structured_json']['risk_keywords']])
                        st.markdown(kw_badges)
                    
                    st.markdown("---")
                    st.info("The grievance record has been synchronized. Triage analysis is complete. Save your Reference ID for tracking.")
    
    # ── History Tab ──
    with tab_history:
        st.markdown("#### My Submitted Grievances")
        st.markdown("Below is a history of all grievances you have registered on this platform.")
        
        username = st.session_state.user.get('username')
        user_complaints = get_citizen_complaints(username)
        
        if not user_complaints:
            st.info("You haven't submitted any grievances yet.")
        else:
            for c in user_complaints:
                status = c.get('status', 'Open')
                ref_id = c['id']
                timestamp = c['timestamp']
                
                status_emoji = "⏳"
                if status == "Resolved":
                    status_emoji = "✅"
                elif status == "Rejected":
                    status_emoji = "❌"
                    
                with st.expander(f"{status_emoji} {ref_id} — Registered: {timestamp} (Status: {status})", expanded=False):
                    st.markdown(f"**Grievance Text:**")
                    st.write(c['complaint_text'])
                    st.markdown(f"**Department:** `{c.get('department')}`")
                    st.markdown(f"**Category:** `{c.get('category')}`")
                    st.markdown(f"**Status:** `{status}`")
                    
                    # Show handling officer if assigned and not resolved/rejected
                    assigned_officer_id = c.get('assigned_officer_id')
                    if assigned_officer_id:
                        off_disp = get_officer_display_name(assigned_officer_id)
                        st.markdown(f"**Complaint handling officer:** `{off_disp}`")
                    
                    if status not in ["Resolved", "Rejected"]:
                        st.info(f"You can copy Reference ID `{ref_id}` to track further updates in the 'Track Grievance' tab.")
                    elif status == "Resolved":
                        st.success("This grievance has been resolved.")
                        if c.get("resolution_history"):
                            for h in c["resolution_history"]:
                                if h.get("status") == "Resolved":
                                    st.markdown(f"**Resolution Notes:** {h.get('notes', 'No notes provided.')}")
                    else:
                        st.warning(f"This grievance was rejected. Reason: {c.get('rejection_reason', 'N/A')}")

    # ── Track Tab ──
    with tab_track:
        st.markdown("#### Track Your Grievance")
        st.markdown("Enter your grievance reference ID to check current status.")
        
        track_id = st.text_input("Grievance Reference ID:", placeholder="e.g., GRV-20260617-XXXX")
        
        if st.button("Check Status", key="track_btn"):
            if not track_id.strip():
                st.error("Please enter a valid Reference ID.")
            else:
                with st.spinner("Looking up grievance..."):
                    found = False
                    
                    # Check active
                    all_complaints = get_complaints()
                    for c in all_complaints:
                        if c['id'] == track_id.strip():
                            st.success(f"**Status:** Active - In Triage Queue")
                            st.markdown(f"**Category:** `{c['category']}`")
                            st.markdown(f"**Department:** `{c['department']}`")
                            if c.get('assigned_officer_id'):
                                off_disp = get_officer_display_name(c['assigned_officer_id'])
                                st.markdown(f"**Complaint handling officer:** `{off_disp}`")
                            st.markdown(f"**Filed:** `{c['timestamp']}`")
                            found = True
                            break
                        # Check duplicate_reports
                        for dup in c.get('duplicate_reports', []):
                            if dup.get('id') == track_id.strip():
                                st.info(f"**Status:** Active - Grouped with primary complaint `{c['id']}`")
                                st.markdown(f"**Category:** `{c['category']}`")
                                st.markdown(f"**Department:** `{c['department']}`")
                                if c.get('assigned_officer_id'):
                                    off_disp = get_officer_display_name(c['assigned_officer_id'])
                                    st.markdown(f"**Complaint handling officer:** `{off_disp}`")
                                found = True
                                break
                        if found:
                            break
                    
                    if not found:
                        # Check resolved
                        resolved = get_resolved_complaints()
                        for c in resolved:
                            if c['id'] == track_id.strip():
                                st.success(f"**Status:** RESOLVED")
                                st.markdown(f"**Category:** `{c['category']}`")
                                st.markdown(f"**Department:** `{c['department']}`")
                                if c.get('assigned_officer_id'):
                                    off_disp = get_officer_display_name(c['assigned_officer_id'])
                                    st.markdown(f"**Complaint handling officer:** `{off_disp}`")
                                st.markdown("**Resolution History:**")
                                for hist in c.get('resolution_history', []):
                                    st.markdown(f"- **{hist['status']}** ({hist['date']}): {hist.get('notes', '')}")
                                found = True
                                break
                    
                    if not found:
                        # Check rejected
                        rejected = get_rejected_complaints()
                        for c in rejected:
                            if c['id'] == track_id.strip():
                                st.warning(f"**Status:** Restricted / Non-Admissible")
                                st.markdown(f"**Reason:** `{c.get('rejection_reason', 'N/A')}`")
                                found = True
                                break
                    
                    if not found:
                        st.warning("No grievance found with this Reference ID. Please verify and try again.")


# ════════════════════════════════════════════════════════════════════════════════
# OFFICER DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

def officer_dashboard():
    """Officer dashboard - shows only complaints assigned to this officer"""
    render_government_banner()
    
    user = st.session_state.user
    officer_id = user.get('officer_id', '')
    officer_name = user.get('name', user.get('username', 'Officer'))
    
    st.markdown(f"### Officer Triage Dashboard")
    st.markdown(f"Welcome, **{officer_name}** (`{officer_id}`). Monitor and process grievances assigned to you.")
    st.markdown("---")
    
    # Fetch complaints filtered by this officer
    admissible_complaints = get_complaints(officer_id=officer_id)
    resolved_complaints = get_resolved_complaints()
    rejected_complaints = get_rejected_complaints()
    
    # Render the shared complaint queue
    render_complaint_queue(
        complaints=admissible_complaints,
        resolved_complaints=resolved_complaints,
        rejected_complaints=rejected_complaints,
        show_actions=True,
        officer_id_for_override=officer_id,
        key_prefix="officer"
    )


# ════════════════════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

def admin_dashboard():
    """Admin dashboard with full system access, analytics, and management tools"""
    render_government_banner()
    
    st.markdown("### Admin Control Panel")
    st.markdown("Full system access. Manage complaints, officers, department policies, and system analytics.")
    st.markdown("---")
    
    # Admin navigation tabs
    admin_tab_complaints, admin_tab_analytics, admin_tab_officers, \
    admin_tab_policies, admin_tab_hotspots, admin_tab_feedback = st.tabs([
        "All Complaints",
        "Analytics Overview",
        "Officer Management",
        "Department Policies",
        "Hotspot Alerts",
        "Feedback & Trust Scores"
    ])
    
    # ── All Complaints Tab ──
    with admin_tab_complaints:
        st.markdown("#### System-Wide Complaint Queue")
        st.markdown("Viewing **all** complaints across all departments and officers.")
        
        admissible_complaints = get_complaints()  # No officer_id filter
        resolved_complaints = get_resolved_complaints()
        rejected_complaints = get_rejected_complaints()
        
        render_complaint_queue(
            complaints=admissible_complaints,
            resolved_complaints=resolved_complaints,
            rejected_complaints=rejected_complaints,
            show_actions=True,
            officer_id_for_override="ADMIN",
            key_prefix="admin"
        )
    
    # ── Analytics Overview Tab ──
    with admin_tab_analytics:
        st.markdown("#### Analytics Overview")
        
        admissible_complaints = get_complaints()
        resolved_complaints = get_resolved_complaints()
        rejected_complaints = get_rejected_complaints()
        stats = get_stats()
        
        # Summary metrics row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Active Complaints", stats.get('active_count', 0))
        with m2:
            st.metric("Resolved", len(resolved_complaints))
        with m3:
            st.metric("Rejected / Restricted", stats.get('rejected_count', 0))
        with m4:
            st.metric("Officer Overrides", stats.get('overrides_count', 0))
        
        st.markdown("---")
        
        if admissible_complaints:
            # Category distribution
            st.markdown("##### Complaints by Category")
            category_counts = {}
            for c in admissible_complaints:
                cat = c.get('category', 'Unknown')
                category_counts[cat] = category_counts.get(cat, 0) + 1
            
            cat_df = pd.DataFrame(list(category_counts.items()), columns=["Category", "Count"])
            cat_df = cat_df.sort_values("Count", ascending=False)
            st.bar_chart(cat_df.set_index("Category"))
            
            # Department distribution
            st.markdown("##### Complaints by Department")
            dept_counts = {}
            for c in admissible_complaints:
                dept = c.get('department', 'Unknown')
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
            
            dept_df = pd.DataFrame(list(dept_counts.items()), columns=["Department", "Count"])
            dept_df = dept_df.sort_values("Count", ascending=False)
            st.bar_chart(dept_df.set_index("Department"))
            
            # Priority distribution
            st.markdown("##### Complaints by Priority Level")
            priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
            for c in admissible_complaints:
                plabel = c.get('priority_label', 'Low')
                priority_counts[plabel] = priority_counts.get(plabel, 0) + 1
            
            pcol1, pcol2, pcol3, pcol4 = st.columns(4)
            with pcol1:
                st.metric("Critical", priority_counts["Critical"])
            with pcol2:
                st.metric("High", priority_counts["High"])
            with pcol3:
                st.metric("Medium", priority_counts["Medium"])
            with pcol4:
                st.metric("Low", priority_counts["Low"])
            
            priority_df = pd.DataFrame(list(priority_counts.items()), columns=["Priority", "Count"])
            st.bar_chart(priority_df.set_index("Priority"))
        else:
            st.info("No active complaints to analyze.")
    
    # ── Officer Management Tab ──
    with admin_tab_officers:
        st.markdown("#### Officer Management")
        
        officers = get_officers()
        
        if officers:
            st.markdown("##### Registered Officers")
            # Build a dataframe for display
            officer_rows = []
            for o in officers:
                officer_rows.append({
                    "Officer ID": o.get('officer_id', 'N/A'),
                    "Name": o.get('name', 'N/A'),
                    "Department": o.get('department', 'N/A'),
                    "Zone": o.get('zone', 'N/A'),
                    "Ward": o.get('ward', 'N/A'),
                    "Designation": o.get('designation', 'N/A'),
                    "Email": o.get('email', 'N/A')
                })
            officer_df = pd.DataFrame(officer_rows)
            st.dataframe(officer_df, use_container_width=True, hide_index=True)
        else:
            st.info("No officers registered in the system.")
        
        st.markdown("---")
        st.markdown("##### Add New Officer")
        
        st.markdown("""
        <style>
        div[data-testid="stFormSubmitButton"] button *,
        div[data-testid="stFormSubmitButton"] button p,
        div[data-testid="stFormSubmitButton"] button span,
        div[data-testid="stFormSubmitButton"] button div,
        button[type="submit"] *,
        button[type="submit"] p,
        button[type="submit"] span,
        button[type="submit"] div {
            color: white !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.form("add_officer_form"):
            aoc1, aoc2 = st.columns(2)
            with aoc1:
                new_name = st.text_input("Name", placeholder="Officer full name")
                new_department = st.text_input("Department", placeholder="e.g. Water & Sewerage Board")
                new_zone = st.text_input("Zone", placeholder="e.g. Anna Nagar")
            with aoc2:
                new_ward = st.text_input("Ward", placeholder="e.g. Ward 5")
                new_designation = st.text_input("Designation", placeholder="e.g. Junior Engineer")
                new_email = st.text_input("Email", placeholder="officer@gov.in")
            
            add_submitted = st.form_submit_button("Register Officer", type="primary", use_container_width=True)
            
            if add_submitted:
                if not new_name or not new_department:
                    st.error("Name and Department are required fields.")
                else:
                    result, error = add_officer({
                        "name": new_name,
                        "department": new_department,
                        "zone": new_zone,
                        "ward": new_ward,
                        "designation": new_designation,
                        "email": new_email
                    })
                    if result:
                        st.success(f"Officer `{result.get('officer_id', 'NEW')}` registered successfully!")
                        st.rerun()
                    else:
                        st.error(f"Failed to register officer: {error}")
    
    # ── Department Policies Tab ──
    with admin_tab_policies:
        st.markdown("#### Department Triage Weight Policies")
        st.markdown("Customize the triage formula weights per department. Weights should sum to 1.0.")
        
        policies = get_department_policies()
        
        if policies:
            for pidx, policy in enumerate(policies):
                dept_name = policy.get('department', f'Department {pidx + 1}')
                with st.expander(f"{dept_name}", expanded=False):
                    st.markdown(f"**Current Weights for {dept_name}:**")
                    
                    with st.form(f"policy_form_{pidx}"):
                        pw1, pw2, pw3 = st.columns(3)
                        with pw1:
                            sev_w = st.number_input(
                                "Severity Weight",
                                min_value=0.0, max_value=1.0, step=0.05,
                                value=float(policy.get('severity_weight', 0.30)),
                                key=f"sev_w_{pidx}"
                            )
                            impact_w = st.number_input(
                                "Impact Weight",
                                min_value=0.0, max_value=1.0, step=0.05,
                                value=float(policy.get('impact_weight', 0.25)),
                                key=f"impact_w_{pidx}"
                            )
                        with pw2:
                            urgency_w = st.number_input(
                                "Urgency Weight",
                                min_value=0.0, max_value=1.0, step=0.05,
                                value=float(policy.get('urgency_weight', 0.20)),
                                key=f"urgency_w_{pidx}"
                            )
                            vuln_w = st.number_input(
                                "Vulnerability Weight",
                                min_value=0.0, max_value=1.0, step=0.05,
                                value=float(policy.get('vulnerability_weight', 0.15)),
                                key=f"vuln_w_{pidx}"
                            )
                        with pw3:
                            dup_w = st.number_input(
                                "Duplicate Weight",
                                min_value=0.0, max_value=1.0, step=0.05,
                                value=float(policy.get('duplicate_weight', 0.10)),
                                key=f"dup_w_{pidx}"
                            )
                            total_w = sev_w + impact_w + urgency_w + vuln_w + dup_w
                            st.markdown(f"**Total:** `{total_w:.2f}`")
                            if abs(total_w - 1.0) > 0.01:
                                st.warning("Weights should sum to 1.0")
                        
                        update_btn = st.form_submit_button(f"Update {dept_name} Weights", type="primary", use_container_width=True)
                        
                        if update_btn:
                            result, error = update_department_policy(dept_name, {
                                "severity_weight": sev_w,
                                "impact_weight": impact_w,
                                "urgency_weight": urgency_w,
                                "vulnerability_weight": vuln_w,
                                "duplicate_weight": dup_w
                            })
                            if result:
                                st.success(f"Weights updated for {dept_name}!")
                                st.rerun()
                            else:
                                st.error(f"Failed to update: {error}")
        else:
            st.info("No department policies configured.")
    
    # ── Hotspot Alerts Tab ──
    with admin_tab_hotspots:
        st.markdown("#### Hotspot Alerts")
        st.markdown("Automatically detected geographic clusters of complaints indicating systemic issues.")
        
        hotspots = get_hotspots()
        
        if hotspots:
            for hidx, hotspot in enumerate(hotspots, 1):
                location = hotspot.get('location', hotspot.get('zone', f'Hotspot {hidx}'))
                count = hotspot.get('complaint_count', hotspot.get('count', 0))
                departments = hotspot.get('departments', [])
                
                dept_str = ", ".join(departments) if departments else "Multiple"
                severity = "[HIGH]" if count >= 5 else "[MED]" if count >= 3 else "[LOW]"
                
                with st.expander(f"{severity} {location} — {count} Complaints | Depts: {dept_str}", expanded=(hidx <= 3)):
                    st.markdown(f"**Location / Area:** `{location}`")
                    st.markdown(f"**Total Complaints:** `{count}`")
                    
                    if departments:
                        st.markdown("**Departments Involved:**")
                        for d in departments:
                            st.markdown(f"  - `{d}`")
                    
                    # Display additional hotspot info if available
                    if hotspot.get('categories'):
                        st.markdown("**Categories:**")
                        for cat in hotspot['categories']:
                            st.markdown(f"  - `{cat}`")
                    
                    if hotspot.get('avg_severity'):
                        st.markdown(f"**Average Severity:** `{hotspot['avg_severity']:.2f}`")
                    
                    if hotspot.get('complaint_ids'):
                        ids_str = ", ".join([f"`{cid}`" for cid in hotspot['complaint_ids'][:10]])
                        st.markdown(f"**Complaint IDs:** {ids_str}")
        else:
            st.info("No hotspot alerts detected at this time.")
    
    # ── Feedback & Trust Scores Tab ──
    with admin_tab_feedback:
        st.markdown("#### Officer Feedback & Trust Scores")
        st.markdown("Monitor officer override patterns, accuracy, and computed trust scores.")
        
        feedback_data = get_feedback_stats()
        
        if feedback_data and isinstance(feedback_data, dict):
            total_overrides = feedback_data.get('total_overrides', 0)
            officers_dict = feedback_data.get('officers', {})
            
            st.metric("Total System Overrides", total_overrides)
            st.markdown("---")
            
            if officers_dict:
                st.markdown("##### Override Statistics per Officer")
                
                fb_rows = []
                for officer_id, stats in officers_dict.items():
                    fb_rows.append({
                        "Officer ID": officer_id,
                        "Total Assigned": stats.get('total_assigned', 0),
                        "Total Overrides": stats.get('total_overrides', 0),
                        "Override Rate": f"{stats.get('override_rate', 0.0):.1%}",
                        "Agreement Rate": f"{stats.get('agreement_rate', 1.0):.1%}",
                        "Trust Score": f"{stats.get('trust_score', 1.0):.3f}",
                        "Severity": stats.get('severity_overrides', 0),
                        "Priority": stats.get('priority_overrides', 0),
                        "Department": stats.get('department_overrides', 0)
                    })
                
                fb_df = pd.DataFrame(fb_rows)
                st.dataframe(fb_df, use_container_width=True, hide_index=True)
                
                # Trust score visualization
                st.markdown("##### Trust Score Distribution")
                trust_data = []
                for officer_id, stats in officers_dict.items():
                    trust_data.append({
                        "Officer": officer_id,
                        "Trust Score": stats.get('trust_score', 1.0)
                    })
                trust_df = pd.DataFrame(trust_data)
                if not trust_df.empty:
                    st.bar_chart(trust_df.set_index("Officer"))
            else:
                st.info("No officer override data available yet.")
        else:
            st.info("No feedback statistics available.")
        
        st.markdown("---")
        st.markdown("##### Export Feedback Records")
        
        if st.button("Export All Feedback as CSV", key="admin_export_feedback"):
            feedback_records = get_feedback_export()
            if feedback_records:
                export_df = pd.DataFrame(feedback_records)
                csv_data = export_df.to_csv(index=False)
                st.download_button(
                    label="Download Feedback CSV",
                    data=csv_data,
                    file_name=f"feedback_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="admin_dl_feedback"
                )
                st.success(f"Exported {len(feedback_records)} feedback records.")
            else:
                st.info("No feedback records to export.")


# ════════════════════════════════════════════════════════════════════════════════
# OFFICER / ADMIN PROFILE PAGE
# ════════════════════════════════════════════════════════════════════════════════

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
        if role == 'admin' and st.session_state.get('admin_view') != 'profile':
            admin_page = st.sidebar.radio(
                "Admin Navigation:",
                ["Dashboard", "Submit Grievance (Test)"],
                label_visibility="collapsed"
            )
        
        # Add spacer to push profile and logout to bottom
        st.sidebar.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
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
    
    elif role == 'admin':
        if st.session_state.get('admin_view') == "profile":
            officer_admin_profile_page(role)
        else:
            if admin_page == "Dashboard":
                admin_dashboard()
            else:
                # Allow admin to test citizen portal
                citizen_portal()
    
    else:
        st.error(f"Unknown role: {role}")


if __name__ == "__main__":
    main()

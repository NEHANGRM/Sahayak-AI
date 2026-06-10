"""
Sahayak AI - Intelligent NLP-Driven Complaint Triage System
Streamlit Application with Citizen Portal and Officer Dashboard
"""

import streamlit as st
import pickle
import pandas as pd
from datetime import datetime
import utils

# Page configuration
st.set_page_config(
    page_title="Sahayak AI - Smart Complaint Triage",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load models
@st.cache_resource
def load_models():
    """Load trained ML models"""
    try:
        with open('tfidf_vectorizer.pkl', 'rb') as f:
            vectorizer = pickle.load(f)
        with open('category_classifier.pkl', 'rb') as f:
            category_model = pickle.load(f)
        with open('priority_classifier.pkl', 'rb') as f:
            priority_model = pickle.load(f)
        with open('severity_model.pkl', 'rb') as f:
            severity_model = pickle.load(f)
        return vectorizer, category_model, priority_model, severity_model
    except FileNotFoundError:
        st.error("⚠️ Models not found! Please run `python model_training.py` first.")
        st.stop()

vectorizer, category_model, priority_model, severity_model = load_models()

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
        border-left: 6px solid #0f294a !important; /* Left border accent */
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

def render_government_banner():
    """Renders a formal government banner at the top of the main area"""
    html = """
    <div class="gov-banner" style="background-color: #0f294a; padding: 18px; border-top: 5px solid #ff9933; border-bottom: 5px solid #138808; text-align: center; margin-bottom: 25px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
        <h1 class="gov-banner-title" style="margin: 0; font-size: 24px; font-weight: bold; letter-spacing: 1px; text-transform: uppercase;">National Grievance Redressal Portal</h1>
        <p class="gov-banner-subtitle" style="margin: 5px 0 0 0; font-size: 13px; letter-spacing: 0.5px; font-weight: 500;">
            SAHAYAK AI &bull; INTEGRATED CIVIC DECISION SUPPORT & TRIAGE MIDDLEWARE
        </p>
    </div>
    """
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
        <tr style="background-color: #f7fafc; font-weight: bold; border-top: 2px solid #0f294a;">
          <td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">FINAL PRIORITY SCORE</td>
          <td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{total:.3f}</td>
          <td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center;">100%</td>
          <td style="padding: 10px; border: 1px solid #cbd5e0; text-align: center; font-family: monospace; font-size: 15px; color: #0f294a;">{total:.3f}</td>
          <td style="padding: 10px; border: 1px solid #cbd5e0; color: #0f294a;">Computed Priority Level: {result['priority_label'].upper()}</td>
        </tr>
      </tbody>
    </table>
    """
    st.markdown(html, unsafe_allow_html=True)

# Initialize session state for storing complaints
if 'complaints' not in st.session_state:
    st.session_state.complaints = [
        {
            'id': 'CMP-2001',
            'complaint_text': "Water supply is completely cut off in Anna Nagar for the past 4 days. The local water board is not responding to calls.",
            'timestamp': "2026-06-05 09:12:00",
            'admissible': True,
            'rejection_reason': None,
            'category': "Water",
            'raw_predicted_category': "Water",
            'priority_label': "Medium",
            'priority_score': 0.385,
            'severity_score': 0.40,
            'severity_reason': "Infrastructure failure",
            'severity_label': "Medium",
            'public_impact_score': 0.50,
            'vulnerability_score': 0.20,
            'urgency_score': 0.35,
            'duplicate_escalation_score': 0.0,
            'sentiment_score': 0.75,
            'department': "Water & Sewerage Board",
            'explanation': "Marked MEDIUM based on governance factors.",
            'is_duplicate': False,
            'cluster_id': None,
            'similarity': 0.0,
            'structured_json': {"category": "Water", "location": "Anna Nagar", "infrastructure": "Water Pipeline", "risk_keywords": [], "entities": [], "severity": {"score": 0.40, "level": "Medium", "reason": "Infrastructure failure"}},
            'ner_breakdown': {"Locations": ["Anna Nagar"]},
            'officer_override': None,
            'override_reason': None,
            'resolution_history': [
                {"status": "Registered", "date": "2026-06-05 09:12:00", "notes": "Registered automatically."},
                {"status": "Assigned", "date": "2026-06-05 10:00:00", "notes": "Assigned to Water Board Engineer."},
                {"status": "In Progress", "date": "2026-06-06 14:00:00", "notes": "Leak detected in the main inlet pipeline."}
            ],
            'escalation_history': [
                {"level": "L1 - Junior Engineer", "date": "2026-06-05 10:00:00"},
                {"level": "L2 - Assistant Executive Engineer", "date": "2026-06-07 09:00:00"}
            ]
        },
        {
            'id': 'CMP-2002',
            'complaint_text': "Huge pothole on the main flyover near City General Hospital. Vehicles are swerving to avoid it, causing severe accident risk.",
            'timestamp': "2026-06-06 11:20:00",
            'admissible': True,
            'rejection_reason': None,
            'category': "Roads",
            'raw_predicted_category': "Roads",
            'priority_label': "Critical",
            'priority_score': 0.815,
            'severity_score': 0.85,
            'severity_reason': "Critical infrastructure + public safety risk",
            'severity_label': "Critical",
            'public_impact_score': 0.80,
            'vulnerability_score': 0.90,
            'urgency_score': 0.90,
            'duplicate_escalation_score': 0.0,
            'sentiment_score': 0.85,
            'department': "Public Works Department (PWD)",
            'explanation': "Marked CRITICAL based on governance factors.",
            'is_duplicate': False,
            'cluster_id': None,
            'similarity': 0.0,
            'structured_json': {"category": "Roads", "location": "City General Hospital", "infrastructure": "Bridge", "risk_keywords": ["accident", "danger"], "entities": [], "severity": {"score": 0.85, "level": "Critical", "reason": "Critical infrastructure + public safety risk"}},
            'ner_breakdown': {"Locations": ["City General Hospital"]},
            'officer_override': None,
            'override_reason': None,
            'resolution_history': [
                {"status": "Registered", "date": "2026-06-06 11:20:00", "notes": "Registered via portal."},
                {"status": "Assigned", "date": "2026-06-06 12:15:00", "notes": "Assigned to PWD Road Safety Division."},
                {"status": "Resolved", "date": "2026-06-07 17:30:00", "notes": "Pothole filled with cold mix asphalt. Temporary repair completed."}
            ],
            'escalation_history': [
                {"level": "L1 - PWD Engineer", "date": "2026-06-06 12:15:00"}
            ]
        },
        {
            'id': 'CMP-2003',
            'complaint_text': "Street lights are not functioning in T-Nagar near the girls high school, making the road unsafe for walking at night.",
            'timestamp': "2026-06-07 19:40:00",
            'admissible': True,
            'rejection_reason': None,
            'category': "Electricity",
            'raw_predicted_category': "Electricity",
            'priority_label': "High",
            'priority_score': 0.615,
            'severity_score': 0.60,
            'severity_reason': "Public safety risk + vulnerable setting",
            'severity_label': "High",
            'public_impact_score': 0.65,
            'vulnerability_score': 0.70,
            'urgency_score': 0.60,
            'duplicate_escalation_score': 0.0,
            'sentiment_score': 0.70,
            'department': "Electricity Utilities Board",
            'explanation': "Marked HIGH based on governance factors.",
            'is_duplicate': False,
            'cluster_id': None,
            'similarity': 0.0,
            'structured_json': {"category": "Electricity", "location": "T-Nagar", "infrastructure": "School", "risk_keywords": ["unsafe"], "entities": [], "severity": {"score": 0.60, "level": "High", "reason": "Public safety risk + vulnerable setting"}},
            'ner_breakdown': {"Locations": ["T-Nagar"]},
            'officer_override': None,
            'override_reason': None,
            'resolution_history': [
                {"status": "Registered", "date": "2026-06-07 19:40:00", "notes": "Registered via web app."},
                {"status": "Assigned", "date": "2026-06-08 08:30:00", "notes": "Assigned to Electricity Board Inspector."}
            ],
            'escalation_history': [
                {"level": "L1 - Line Inspector", "date": "2026-06-08 08:30:00"}
            ]
        },
        {
            'id': 'CMP-2004',
            'complaint_text': "Garbage has not been collected for two weeks in Sector 4, Chennai. The dumpster is overflowing onto the street, attracting stray dogs.",
            'timestamp': "2026-06-08 10:15:00",
            'admissible': True,
            'rejection_reason': None,
            'category': "Sanitation",
            'raw_predicted_category': "Sanitation",
            'priority_label': "Medium",
            'priority_score': 0.415,
            'severity_score': 0.45,
            'severity_reason': "Infrastructure failure",
            'severity_label': "Medium",
            'public_impact_score': 0.50,
            'vulnerability_score': 0.30,
            'urgency_score': 0.40,
            'duplicate_escalation_score': 0.0,
            'sentiment_score': 0.60,
            'department': "Municipal Sanitation Department",
            'explanation': "Marked MEDIUM based on governance factors.",
            'is_duplicate': False,
            'cluster_id': None,
            'similarity': 0.0,
            'structured_json': {"category": "Sanitation", "location": "Sector 4", "infrastructure": "Waste Bin", "risk_keywords": [], "entities": [], "severity": {"score": 0.45, "level": "Medium", "reason": "Infrastructure failure"}},
            'ner_breakdown': {"Locations": ["Sector 4", "Chennai"]},
            'officer_override': None,
            'override_reason': None,
            'resolution_history': [
                {"status": "Registered", "date": "2026-06-08 10:15:00", "notes": "Registered."},
                {"status": "Assigned", "date": "2026-06-08 11:30:00", "notes": "Assigned to Zonal Sanitation Officer."}
            ],
            'escalation_history': [
                {"level": "L1 - Sanitary Inspector", "date": "2026-06-08 11:30:00"}
            ]
        },
        {
            'id': 'CMP-2005',
            'complaint_text': "A local official is demanding a bribe of 5000 rupees to process my business license application at the Municipal Corporation Office.",
            'timestamp': "2026-06-09 14:30:00",
            'admissible': True,
            'rejection_reason': None,
            'category': "Corruption",
            'raw_predicted_category': "Corruption",
            'priority_label': "High",
            'priority_score': 0.595,
            'severity_score': 0.90,
            'severity_reason': "Integrity violation / corruption bribe",
            'severity_label': "High",
            'public_impact_score': 0.30,
            'vulnerability_score': 0.20,
            'urgency_score': 0.70,
            'duplicate_escalation_score': 0.0,
            'sentiment_score': 0.80,
            'department': "Vigilance Bureau",
            'explanation': "Marked HIGH based on governance factors.",
            'is_duplicate': False,
            'cluster_id': None,
            'similarity': 0.0,
            'structured_json': {"category": "Corruption", "location": "Municipal Corporation Office", "infrastructure": "Government Office", "risk_keywords": ["bribe", "corruption"], "entities": [], "severity": {"score": 0.90, "level": "High", "reason": "Integrity violation / corruption bribe"}},
            'ner_breakdown': {"Locations": ["Municipal Corporation Office"]},
            'officer_override': None,
            'override_reason': None,
            'resolution_history': [
                {"status": "Registered", "date": "2026-06-09 14:30:00", "notes": "Under review by anti-corruption cell."}
            ],
            'escalation_history': [
                {"level": "L1 - Vigilance Officer", "date": "2026-06-09 15:00:00"}
            ]
        }
    ]

if 'complaint_counter' not in st.session_state:
    st.session_state.complaint_counter = 6

# Initialize feedback storage
if 'officer_overrides' not in st.session_state:
    st.session_state.officer_overrides = []


def predict_complaint(complaint_text):
    """
    Process complaint through admissibility screening, classification, NER, severity, public impact, vulnerability, duplicate detection, urgency, and explainable priority scoring
    
    Returns:
        dict: Prediction results including admissibility, category, priority, JSON representation, etc.
    """
    # 1. Admissibility check
    is_admissible, rejection_reason, predicted_category = utils.check_admissibility(
        complaint_text, 
        category_model, 
        vectorizer
    )
    
    # 2. Extract NER details and risk keywords
    ner_details = utils.extract_entities_and_details(complaint_text, predicted_category)
    risk_kws = utils.extract_risk_keywords(complaint_text)
    
    # 3. Predict Severity, Public Impact, and Vulnerability (if admissible)
    if is_admissible:
        severity_details = utils.predict_severity(
            complaint_text, 
            predicted_category, 
            severity_model, 
            vectorizer
        )
        severity_score = severity_details["severity"]
        severity_reason = severity_details["reason"]
        severity_label = utils.get_severity_level(severity_score)
        
        # Temp structured JSON for impact calculators
        temp_json = {
            "location": ner_details["location"],
            "infrastructure": ner_details["infrastructure"]
        }
        public_impact_score = utils.calculate_public_impact(complaint_text, predicted_category, temp_json)
        vulnerability_score = utils.calculate_vulnerability(complaint_text, predicted_category, temp_json)
        
        # 4. Duplicate detection (run before priority calculation to get duplicate escalation score)
        existing_complaints = []
        try:
            if 'complaints' in st.session_state:
                existing_complaints = st.session_state.complaints
        except Exception:
            pass
            
        is_duplicate, cluster_id, similarity = utils.detect_duplicate(
            complaint_text, 
            existing_complaints, 
            vectorizer=vectorizer,
            threshold=0.7
        )
        duplicate_escalation_score = utils.calculate_duplicate_escalation(
            is_duplicate, 
            similarity, 
            cluster_id, 
            existing_complaints
        )
        
        # Phase 5: RAG Context Retrieval
        similar_cases = utils.search_similar_complaints(
            complaint_text,
            existing_complaints,
            vectorizer,
            k=3
        )
        
        # Phase 6: Duplicate detection API
        dup_info = utils.get_duplicate_info(
            complaint_text,
            existing_complaints,
            vectorizer,
            threshold=0.7
        )
        duplicate_count = dup_info["duplicate_count"]
        duplicate_ids = dup_info["duplicate_ids"]
        
        # 5. Urgency calculation
        urgency_score = utils.calculate_urgency(complaint_text, predicted_category, severity_score, temp_json)
        
        # 6. Calculate priority using the new governance weighted formula
        priority_score = utils.calculate_priority_score(
            severity_score, 
            public_impact_score, 
            urgency_score, 
            vulnerability_score, 
            duplicate_escalation_score
        )
        priority_label = utils.get_priority_label(priority_score)
        department = utils.route_to_department(predicted_category)
        explanation = utils.generate_explanation(
            severity_score,
            public_impact_score,
            urgency_score,
            vulnerability_score,
            duplicate_escalation_score,
            priority_label
        )
        sentiment_score = utils.get_sentiment_score(complaint_text)
    else:
        severity_score = 0.0
        severity_reason = "Not evaluated due to rejection policy."
        severity_label = "Low"
        public_impact_score = 0.0
        vulnerability_score = 0.0
        urgency_score = 0.0
        duplicate_escalation_score = 0.0
        sentiment_score = 0.0
        priority_score = 0.0
        priority_label = "Low"
        department = "Not Routed"
        explanation = f"Complaint rejected. Reason: {rejection_reason}"
        is_duplicate, cluster_id, similarity = False, None, 0.0
        duplicate_count = 0
        duplicate_ids = []
        similar_cases = []
        
    # 4. Create the final consolidated structured JSON response
    structured_json = {
        "category": predicted_category if is_admissible else "Other",
        "location": ner_details["location"],
        "infrastructure": ner_details["infrastructure"],
        "risk_keywords": risk_kws,
        "entities": ner_details["all_entities"],
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
            "score": priority_score,
            "level": priority_label
        }
    }
    
    return {
        'admissible': is_admissible,
        'rejection_reason': rejection_reason,
        'category': predicted_category if is_admissible else "Other",
        'raw_predicted_category': predicted_category,
        'severity_score': severity_score,
        'severity_reason': severity_reason,
        'severity_label': severity_label,
        'public_impact_score': public_impact_score,
        'vulnerability_score': vulnerability_score,
        'urgency_score': urgency_score,
        'duplicate_escalation_score': duplicate_escalation_score,
        'sentiment_score': sentiment_score,
        'priority_score': priority_score,
        'priority_label': priority_label,
        'department': department,
        'explanation': explanation,
        'is_duplicate': is_duplicate,
        'cluster_id': cluster_id,
        'similarity': similarity,
        'structured_json': structured_json,
        'ner_breakdown': ner_details['extracted_entities'],
        'duplicate_count': duplicate_count,
        'duplicate_ids': duplicate_ids,
        'similar_cases': similar_cases
    }


def citizen_portal():
    """Citizen-facing complaint submission portal"""
    render_government_banner()
    
    st.markdown("### Grievance Registration Portal")
    st.markdown("Use this portal to register public service or civic complaints. The Sahayak AI triage system will automatically classify, verify admissibility, and compute priority metrics.")
    st.markdown("---")
    
    # Complaint input
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
                # Get predictions
                result = predict_complaint(complaint_text)
                
                # Generate complaint ID
                complaint_id = f"CMP-{2000 + st.session_state.complaint_counter}"
                st.session_state.complaint_counter += 1
                
                # Store complaint
                complaint_record = {
                    'id': complaint_id,
                    'complaint_text': complaint_text,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'admissible': result['admissible'],
                    'rejection_reason': result['rejection_reason'],
                    'category': result['category'],
                    'raw_predicted_category': result['raw_predicted_category'],
                    'priority_label': result['priority_label'],
                    'priority_score': result['priority_score'],
                    'severity_score': result['severity_score'],
                    'severity_reason': result['severity_reason'],
                    'severity_label': result['severity_label'],
                    'public_impact_score': result['public_impact_score'],
                    'vulnerability_score': result['vulnerability_score'],
                    'urgency_score': result['urgency_score'],
                    'duplicate_escalation_score': result['duplicate_escalation_score'],
                    'sentiment_score': result['sentiment_score'],
                    'department': result['department'],
                    'explanation': result['explanation'],
                    'is_duplicate': result['is_duplicate'],
                    'cluster_id': result['cluster_id'],
                    'similarity': result['similarity'],
                    'structured_json': result['structured_json'],
                    'ner_breakdown': result['ner_breakdown'],
                    'officer_override': None,
                    'override_reason': None,
                    'duplicate_count': result.get('duplicate_count', 0),
                    'duplicate_ids': result.get('duplicate_ids', []),
                    'similar_cases': result.get('similar_cases', []),
                    'resolution_history': [
                        {"status": "Submitted", "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "notes": "Grievance received and registered."}
                    ],
                    'escalation_history': [
                        {"level": "L1 Officer", "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                    ]
                }
                
                st.session_state.complaints.append(complaint_record)
                
                # Check Admissibility for UI display
                if not result['admissible']:
                    st.error(f"🛑 Grievance Not Admissible for Processing")
                    st.info(f"Reason for non-admissibility: {result['rejection_reason']}")
                    
                    st.markdown("---")
                    st.markdown("### ⚙️ Parser Output (Structured JSON)")
                    st.json(result['structured_json'])
                    
                    st.markdown("---")
                    st.warning("Notice: This complaint does not comply with public portal policies and has been locked from routing.")
                    return
                
                # If Admissible:
                st.success(f"Grievance filed successfully. Reference ID: {complaint_id}")
                
                # Duplicate warning
                if result['is_duplicate']:
                    st.warning(f"Duplicate Alert: Similar grievance has already been filed ({result['similarity']*100:.1f}% match found, Cluster #{result['cluster_id']}). Duplicate escalation applied.")
                
                st.markdown("### Triage & Prioritization Report")
                
                # Render priority stamp
                render_priority_stamp(result['priority_label'], result['priority_score'], result['explanation'])
                
                # Render metrics table
                render_metrics_table(result)
                
                # Details & NER Entities
                st.markdown("---")
                col_det, col_ner = st.columns(2)
                
                with col_det:
                    st.markdown("#### 📂 Triage Metadata")
                    st.markdown(f"**Grievance Category:** `{result['category']}`")
                    st.markdown(f"**Assigned Department:** `{result['department']}`")
                    st.markdown(f"**Identified Location:** `{result['structured_json']['location'] or 'Not Detected'}`")
                    st.markdown(f"**Identified Infrastructure:** `{result['structured_json']['infrastructure'] or 'Not Detected'}`")
                    st.markdown(f"**Filing Timestamp:** `{complaint_record['timestamp']}`")
                    
                    if result['structured_json']['risk_keywords']:
                        st.markdown("**Risk Keywords Flagged:**")
                        kw_badges = " ".join([f"`{kw}`" for kw in result['structured_json']['risk_keywords']])
                        st.markdown(kw_badges)
                
                with col_ner:
                    st.markdown("#### 🔍 Named Entities Identified")
                    ner = result['ner_breakdown']
                    for ent_type, ent_list in ner.items():
                        if ent_list:
                            st.markdown(f"**{ent_type}:** {', '.join([f'`{e}`' for e in ent_list])}")
                    if not any(ner.values()):
                        st.markdown("*No specific named entities extracted.*")
                
                # Phase 5: RAG Context Retrieval & Phase 6: Duplicate Registry
                st.markdown("---")
                st.markdown("### 🔍 RAG Context & Similar Historical Grievances (Phase 5)")
                if result.get('similar_cases'):
                    for sc in result['similar_cases']:
                        with st.container():
                            st.markdown(f"**Grievance ID:** `{sc['id']}` (Category: `{sc['category']}`, Priority: `{sc['priority_label']}`) | **Similarity Score:** `{sc['similarity']*100:.1f}%`")
                            st.markdown(f"**Location:** `{sc['location']}`")
                            st.markdown(f"**Description:** *\"{sc['complaint_text']}\"*")
                            
                            col_res, col_esc = st.columns(2)
                            with col_res:
                                st.markdown("**Resolution History:**")
                                for r in sc.get('resolution_history', []):
                                    st.markdown(f"- `{r['date']}`: **{r['status']}** - *{r.get('notes', '')}*")
                            with col_esc:
                                st.markdown("**Escalation History:**")
                                for e in sc.get('escalation_history', []):
                                    st.markdown(f"- `{e['date']}`: **{e['level']}**")
                            st.markdown("<div style='border-bottom: 1px dashed #cbd5e0; margin: 10px 0;'></div>", unsafe_allow_html=True)
                else:
                    st.info("No past similar grievances found in context search.")

                st.markdown("---")
                st.markdown("### 📋 Duplicate Registry (Phase 6)")
                if result.get('duplicate_count', 0) > 0:
                    st.warning(f"**Duplicate Count:** `{result['duplicate_count']}` recurring reports detected.")
                    st.markdown(f"**Duplicate Complaint IDs:** {', '.join([f'`{did}`' for did in result['duplicate_ids']])}")
                else:
                    st.success("No recurring reports detected for this issue. This is a unique complaint.")

                # Structured JSON Box
                st.markdown("---")
                with st.expander("⚙️ View Structured Engine Output (JSON)", expanded=True):
                    st.json(result['structured_json'])
                
                st.markdown("---")
                st.info("The grievance record has been synchronized. Triage analysis is complete.")


def officer_dashboard():
    """Officer dashboard with triage queue, filter, and override functionality"""
    render_government_banner()
    
    st.markdown("### Officer Triage Dashboard")
    st.markdown("Monitor and process active grievances. Complaints are automatically prioritized using the 5-factor governance formula.")
    st.markdown("---")
    
    if not st.session_state.complaints:
        st.info("No complaints registered in the system yet. Active submissions will appear here.")
        return
    
    # Filter admissible vs rejected
    admissible_complaints = [c for c in st.session_state.complaints if c.get('admissible', True)]
    rejected_complaints = [c for c in st.session_state.complaints if not c.get('admissible', True)]
    
    total_admissible = len(admissible_complaints)
    total_rejected = len(rejected_complaints)
    critical_priority = len([c for c in admissible_complaints if c['priority_label'] == 'Critical'])
    high_priority = len([c for c in admissible_complaints if c['priority_label'] == 'High'])
    medium_priority = len([c for c in admissible_complaints if c['priority_label'] == 'Medium'])
    low_priority = len([c for c in admissible_complaints if c['priority_label'] == 'Low'])
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Active", total_admissible)
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
    
    tab_queue, tab_rejected = st.tabs(["Active Triage Queue", "Restricted / Non-Admissible Logs"])
    
    with tab_queue:
        if not admissible_complaints:
            st.info("No active complaints in the queue.")
        else:
            # Sort admissible complaints by priority score (descending)
            sorted_complaints = sorted(
                admissible_complaints, 
                key=lambda x: x['priority_score'], 
                reverse=True
            )
            
            st.markdown("#### Active Grievance Queue (Ranked by Governance Priority)")
            
            for idx, complaint in enumerate(sorted_complaints, 1):
                has_override = complaint.get('officer_override') is not None
                display_label = complaint['officer_override'] if has_override else complaint['priority_label']
                label_color = "red" if display_label in ["Critical", "High"] else "blue" if display_label == "Medium" else "green"
                
                with st.expander(
                    f"Ref: {complaint['id']} | Level: {display_label.upper()} (Score: {complaint['priority_score']:.3f}) | Category: {complaint['category']}",
                    expanded=(idx <= 3)
                ):
                    st.markdown("**Grievance Description:**")
                    st.info(complaint['complaint_text'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**🎯 AI Computed Priority:** **{complaint['priority_label']}** (Score: `{complaint['priority_score']:.3f}`)")
                        st.markdown(f"**📂 Grievance Category:** `{complaint['category']}`")
                        st.markdown(f"**🏢 Target Department:** `{complaint['department']}`")
                        st.markdown(f"**⏰ Registered Timestamp:** `{complaint['timestamp']}`")
                    with col2:
                        st.markdown(f"**⚠️ Severity Score:** `{complaint.get('severity_score', 0.0):.2f}` (Tier: **{complaint.get('severity_label', 'Low')}**)")
                        st.markdown(f"   *Rationale:* {complaint.get('severity_reason', 'N/A')}")
                        st.markdown(f"**📊 Public Impact Score:** `{complaint.get('public_impact_score', 0.0):.2f}`")
                        st.markdown(f"**😟 Vulnerability Score:** `{complaint.get('vulnerability_score', 0.0):.2f}`")
                        st.markdown(f"**⚡ Urgency Score:** `{complaint.get('urgency_score', 0.0):.2f}`")
                        st.markdown(f"**🔄 Duplicate Escalation Score:** `{complaint.get('duplicate_escalation_score', 0.0):.2f}`")
                    
                    st.markdown("**💡 System Explanation:**")
                    st.markdown(f"> {complaint['explanation']}")
                    
                    st.markdown("---")
                    col_rag, col_dup = st.columns(2)
                    with col_rag:
                        st.markdown("**🔍 RAG Context & Similar Grievances (Phase 5)**")
                        similar_cases = complaint.get('similar_cases')
                        if not similar_cases:
                            # Try to run it dynamically if not stored (e.g. for mock complaints)
                            similar_cases = utils.search_similar_complaints(
                                complaint['complaint_text'],
                                [c for c in st.session_state.complaints if c['id'] != complaint['id'] and c.get('admissible', True)],
                                vectorizer,
                                k=2
                            )
                        if similar_cases:
                            for sc in similar_cases[:2]:
                                st.markdown(f"- **{sc['id']}** ({sc['category']}, Priority: **{sc['priority_label']}**) | Score: `{sc['similarity']*100:.1f}%`\n"
                                            f"  *Text:* \"{sc['complaint_text'][:80]}...\"\n"
                                            f"  *Status:* **{sc['resolution_history'][-1]['status']}** ({sc['resolution_history'][-1]['date']})")
                        else:
                            st.info("No past similar cases found in database.")
                            
                    with col_dup:
                        st.markdown("**📋 Duplicate Registry (Phase 6)**")
                        dup_info = utils.get_duplicate_info(
                            complaint['complaint_text'],
                            [c for c in st.session_state.complaints if c['id'] != complaint['id'] and c.get('admissible', True)],
                            vectorizer,
                            threshold=0.7
                        )
                        if dup_info['duplicate_count'] > 0:
                            st.warning(f"**Duplicate Count:** `{dup_info['duplicate_count']}` recurring reports.")
                            st.markdown(f"**Duplicate IDs:** {', '.join([f'`{did}`' for did in dup_info['duplicate_ids']])}")
                        else:
                            st.success("No duplicates detected in queue.")

                    st.markdown("---")
                    st.markdown("**⚙️ Structured Parser Output (JSON)**")
                    st.json(complaint['structured_json'])
                    
                    st.markdown("---")
                    st.markdown("**👮 Officer Feedback & Priority Override**")
                    if has_override:
                        st.success(f"✅ Priority overridden by officer to: **{complaint['officer_override']}**")
                        if complaint.get('override_reason'):
                            st.markdown(f"*Override Reason:* {complaint['override_reason']}")
                    else:
                        st.markdown("*Override AI priority level (logged for framework refinement):*")
                        col_o1, col_o2, col_o3 = st.columns([2, 2, 3])
                        with col_o1:
                            override_priority = st.selectbox(
                                "Override Priority Level:",
                                ["Critical", "High", "Medium", "Low"],
                                key=f"override_select_{complaint['id']}"
                            )
                        with col_o2:
                            override_reason = st.text_input(
                                "Provide override justification:",
                                key=f"reason_{complaint['id']}",
                                placeholder="Why override this priority?"
                            )
                        with col_o3:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button("Submit Override", key=f"apply_{complaint['id']}", type="secondary"):
                                complaint['officer_override'] = override_priority
                                complaint['override_reason'] = override_reason if override_reason else "No justification provided"
                                
                                # Log override
                                override_record = {
                                    'complaint_id': complaint['id'],
                                    'complaint_text': complaint['complaint_text'],
                                    'ai_priority': complaint['priority_label'],
                                    'officer_priority': override_priority,
                                    'reason': complaint['override_reason'],
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                st.session_state.officer_overrides.append(override_record)
                                st.rerun()
                                
    with tab_rejected:
        if not rejected_complaints:
            st.info("No restricted complaints logged in system.")
        else:
            st.markdown("#### Log of Non-Admissible / Restricted Issues")
            
            for idx, complaint in enumerate(rejected_complaints, 1):
                with st.expander(f"Locked Ref: {complaint['id']} | Reason: {complaint['raw_predicted_category'].replace('Prohibited_', '')}", expanded=True):
                    st.markdown("**Complaint Text:**")
                    st.warning(complaint['complaint_text'])
                    
                    st.markdown(f"**Policy Violation Reason:** `{complaint['rejection_reason']}`")
                    st.markdown(f"**Timestamp:** `{complaint['timestamp']}`")
                    
                    st.markdown("---")
                    st.markdown("**⚙️ Parser Output (JSON)**")
                    st.json(complaint['structured_json'])
                    
    # Export override feedback
    st.markdown("---")
    if st.session_state.officer_overrides:
        st.markdown(f"### Framework Training Data Log ({len(st.session_state.officer_overrides)} overrides)")
        
        if st.button("Compile & Export Override Log"):
            override_df = pd.DataFrame(st.session_state.officer_overrides)
            csv = override_df.to_csv(index=False)
            
            st.download_button(
                label="Download Override Dataset (CSV)",
                data=csv,
                file_name=f"officer_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.success("Override feedback compiled. Dataset ready for download.")

# Main App
def main():
    inject_custom_css()
    
    # Sidebar navigation
    st.sidebar.markdown("""
    <div class="sidebar-gov-header" style="background-color: #0f294a; padding: 10px; border-bottom: 3px solid #ff9933; text-align: center; margin-bottom: 20px; border-radius: 4px;">
        <h4 class="sidebar-gov-title" style="margin: 0; font-size: 13px; font-weight: bold; letter-spacing: 0.5px; text-transform: uppercase;">Portal Navigation</h4>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.sidebar.radio(
        "Navigate:",
        ["Submit Grievance (Citizen Portal)", "Triage Queue (Officer Dashboard)"],
        label_visibility="collapsed"
    )
    
    admissible_count = len([c for c in st.session_state.complaints if c.get('admissible', True)])
    rejected_count = len([c for c in st.session_state.complaints if not c.get('admissible', True)])
    
    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div style="border: 1px solid #cbd5e0; padding: 12px; background-color: #ffffff; border-radius: 4px; margin-bottom: 15px; font-family: Arial, sans-serif;">
        <span style="font-size: 10px; font-weight: bold; color: #718096; text-transform: uppercase; letter-spacing: 0.5px;">Portal Registry Stats</span>
        <div style="margin-top: 5px; font-size: 12.5px; color: #2d3748; line-height: 1.5;">
            &bull; <strong>Active Grievances:</strong> {admissible_count}<br>
            &bull; <strong>Restricted Logs:</strong> {rejected_count}<br>
            &bull; <strong>Officer Overrides:</strong> {len(st.session_state.officer_overrides)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown(f"""
    <div style="border: 1px solid #cbd5e0; padding: 12px; background-color: #ffffff; border-radius: 4px; font-family: Arial, sans-serif;">
        <span style="font-size: 10px; font-weight: bold; color: #718096; text-transform: uppercase; letter-spacing: 0.5px;">Triage Formula Model</span>
        <div style="margin-top: 5px; font-size: 11px; font-family: monospace; color: #2d3748; line-height: 1.4;">
            Priority Score =<br>
            &nbsp;&nbsp;0.30 * Severity +<br>
            &nbsp;&nbsp;0.25 * Public Impact +<br>
            &nbsp;&nbsp;0.20 * Urgency +<br>
            &nbsp;&nbsp;0.15 * Vulnerability +<br>
            &nbsp;&nbsp;0.10 * Duplicates<br>
            <br>
            <strong>Tiers:</strong><br>
            &bull; Critical: >= 0.75<br>
            &bull; High: &nbsp;&nbsp;&nbsp;&nbsp;0.50 - 0.74<br>
            &bull; Medium: &nbsp;&nbsp;0.30 - 0.49<br>
            &bull; Low: &nbsp;&nbsp;&nbsp;&nbsp;< 0.30
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Route to page
    if page == "Submit Grievance (Citizen Portal)":
        citizen_portal()
    else:
        officer_dashboard()

if __name__ == "__main__":
    main()

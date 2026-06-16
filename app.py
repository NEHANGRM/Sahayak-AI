"""
Sahayak AI - Intelligent NLP-Driven Complaint Triage System
Streamlit Application with Citizen Portal and Officer Dashboard
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import requests

import os
API_URL = os.environ.get("SAHAYAK_API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="Sahayak AI - Smart Complaint Triage",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def get_stats():
    try:
        r = requests.get(f"{API_URL}/stats")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return {"active_count": 0, "rejected_count": 0, "overrides_count": 0}

def get_complaints():
    try:
        r = requests.get(f"{API_URL}/complaints")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        st.warning("⚠️ Cannot connect to backend server. Make sure api.py is running.")
    return []

def get_resolved_complaints():
    try:
        r = requests.get(f"{API_URL}/complaints/resolved")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return []

def get_rejected_complaints():
    try:
        r = requests.get(f"{API_URL}/complaints/rejected")
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        pass
    return []

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
    <div class="gov-banner" style="background-color: #0f294a; padding: 22px; border-top: 5px solid #ff9933; border-bottom: 5px solid #138808; text-align: center; margin-bottom: 25px; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.08);">
        <div style="font-size: 11px; color: #ff9933; font-weight: bold; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 6px;">Government of India Middleware Platform</div>
        <h1 class="gov-banner-title" style="margin: 0; font-size: 32px; font-weight: 900; letter-spacing: 1.5px; color: #ffffff; text-transform: uppercase;">SAHAYAK AI</h1>
        <div style="font-size: 13px; color: #cbd5e0; font-weight: 500; letter-spacing: 0.8px; margin-top: 6px; text-transform: uppercase;">National Grievance Triage & Redressal Board</div>
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

# Initialize feedback storage
if 'officer_overrides' not in st.session_state:
    st.session_state.officer_overrides = []


def predict_complaint(complaint_text):
    try:
        r = requests.post(f"{API_URL}/triage", json={"complaint_text": complaint_text})
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"Error processing grievance: {r.text}")
            return None
    except Exception as e:
        st.error(f"Failed to connect to triage API server: {e}")
        return None

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
                # Get predictions from API
                result = predict_complaint(complaint_text)
                
                if result is None:
                    st.stop()
                
                # Check Admissibility for UI display
                if not result['admissible']:
                    st.error(f"🛑 Grievance Not Admissible for Processing")
                    st.info(f"Reason for non-admissibility: {result['rejection_reason']}")
                    
                    with st.expander("⚙️ View Technical Triage Data", expanded=False):
                        st.json(result['structured_json'])
                    
                    st.markdown("---")
                    st.warning("Notice: This complaint does not comply with public portal policies and has been locked from routing.")
                    return
                
                # If Admissible:
                complaint_id = result['id']
                st.success(f"Grievance filed successfully. Reference ID: {complaint_id}")
                
                # Details
                st.markdown("### 📋 Filed Grievance Record")
                st.markdown(f"**Grievance Reference ID:** `{complaint_id}`")
                st.markdown(f"**Grievance Category:** `{result['category']}`")
                st.markdown(f"**Assigned Department:** `{result['department']}`")
                st.markdown(f"**Identified Location:** `{result['structured_json']['location'] or 'Not Detected'}`")
                st.markdown(f"**Identified Infrastructure:** `{result['structured_json']['infrastructure'] or 'Not Detected'}`")
                st.markdown(f"**Filing Timestamp:** `{result['timestamp']}`")
                
                if result['structured_json'].get('risk_keywords'):
                    st.markdown("**Risk Keywords Flagged:**")
                    kw_badges = " ".join([f"`{kw}`" for kw in result['structured_json']['risk_keywords']])
                    st.markdown(kw_badges)
                
                st.markdown("---")
                st.info("The grievance record has been synchronized. Triage analysis is complete.")


def officer_dashboard():
    """Officer dashboard with triage queue, filter, and override functionality"""
    render_government_banner()
    
    st.markdown("### Officer Triage Dashboard")
    st.markdown("Monitor and process active grievances. Complaints are automatically prioritized using the 5-factor governance formula.")
    st.markdown("---")
    
    # Filter admissible vs resolved vs rejected from API
    admissible_complaints = get_complaints()
    resolved_complaints = get_resolved_complaints()
    rejected_complaints = get_rejected_complaints()
    
    total_admissible = len(admissible_complaints)
    total_rejected = len(rejected_complaints)
    critical_priority = len([c for c in admissible_complaints if c['priority_label'] == 'Critical'])
    high_priority = len([c for c in admissible_complaints if c['priority_label'] == 'High'])
    medium_priority = len([c for c in admissible_complaints if c['priority_label'] == 'Medium'])
    low_priority = len([c for c in admissible_complaints if c['priority_label'] == 'Low'])
    
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
    
    with tab_queue:
        if not admissible_complaints:
            st.info("No active complaints in the queue.")
        else:
            sorted_complaints = admissible_complaints
            
            st.markdown("#### Active Grievance Queue (Ranked by Governance Priority)")
            
            for idx, complaint in enumerate(sorted_complaints, 1):
                has_override = complaint.get('officer_override') is not None
                display_label = complaint['officer_override'] if has_override else complaint['priority_label']
                label_color = "red" if display_label in ["Critical", "High"] else "blue" if display_label == "Medium" else "green"
                
                dup_suffix = f" [🔗 Grouped: {complaint['duplicate_count'] + 1} Reports]" if complaint.get('duplicate_count', 0) > 0 else ""
                with st.expander(
                    f"Ref: {complaint['id']}{dup_suffix} | Level: {display_label.upper()} (Score: {complaint['final_priority_score']:.3f}) | Category: {complaint['category']}",
                    expanded=(idx <= 3)
                ):
                    st.markdown("**Grievance Description:**")
                    st.info(complaint['complaint_text'])
                    
                    rel_time_str = f" ({complaint['relative_time']})" if complaint.get('relative_time') else ""
                    st.markdown(f"📂 **Category:** `{complaint['category']}` | 🏢 **Department:** `{complaint['department']}` | ⏰ **Registered:** `{complaint['timestamp']}`{rel_time_str}")
                    
                    # Markdown metrics table
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
                    
                    llm_note = f" (Adjusted {complaint['llm_adjustment']:+.2f} by AI Governance Advisory)" if complaint.get('llm_reviewed', False) else ""
                    age_note = f" (Aging Escalation: +{complaint.get('aging_boost', 0.0):.2f} - registered {complaint.get('relative_time', 'some time ago')})" if complaint.get('aging_boost', 0.0) > 0 else ""
                    st.markdown(f"🎯 **AI Final Priority:** **{display_label.upper()}** (Score: `{complaint.get('final_priority_score', 0.0):.3f}` = Base `{complaint.get('priority_score', 0.0):.3f}`{llm_note}{age_note})")
                    
                    # Display LLM reasoning details if available in a neat compact way
                    if complaint.get('llm_reviewed', False):
                        triggers_str = ", ".join(complaint.get('llm_trigger_reasons', []))
                        st.markdown(f"""
> 🤖 **AI Governance Advisory Review**
> - **Trigger Flagged:** {triggers_str or 'None'}
> - **Risks:** Public Safety: `{complaint['llm_public_safety_risk']}` | Vulnerable Population: `{complaint['llm_vulnerable_population_risk']}` | Infrastructure: `{complaint['llm_infrastructure_risk']}`
> - **Advisory Rationale:** {complaint['llm_reasoning']} *(Summary: {complaint['llm_risk_summary']})*
""")

                    st.markdown("---")
                    col_rag, col_dup = st.columns(2)
                    with col_rag:
                        st.markdown("**🔍 Historical Context (RAG)**")
                        similar_cases = complaint.get('similar_cases')
                        if similar_cases:
                            for sc in similar_cases[:2]:
                                st.markdown(f"- **{sc['id']}** ({sc['category']}, Priority: **{sc['priority_label']}**) | Similarity: `{sc['similarity']*100:.1f}%`  \n"
                                             f"  *Text:* \"{sc['complaint_text'][:70]}...\"  \n"
                                             f"  *Status:* **{sc['resolution_history'][-1]['status'] if sc.get('resolution_history') else 'Submitted'}**")
                        else:
                            st.info("No past similar cases found in database.")
                            
                    with col_dup:
                        st.markdown("**📋 Duplicate Registry**")
                        if complaint.get('duplicate_count', 0) > 0:
                            st.warning(f"**Duplicate Count:** `{complaint['duplicate_count']}` recurring reports.")
                            dup_ids = ", ".join([f"`{dc['id']}`" for dc in complaint['duplicate_reports']])
                            st.markdown(f"**Duplicate IDs:** {dup_ids}")
                        else:
                            st.success("No duplicates detected in queue.")
 
                    with st.expander("⚙️ View Raw Technical Parser Data (JSON)", expanded=False):
                        st.json(complaint['structured_json'])
                    
                    if complaint.get('duplicate_count', 0) > 0:
                        with st.expander(f"🔗 View Grouped Duplicate Reports ({complaint['duplicate_count']})", expanded=False):
                            for d_idx, dc in enumerate(complaint['duplicate_reports'], 1):
                                st.markdown(f"**Duplicate #{d_idx}:** Reference ID: `{dc['id']}` | Filed: `{dc['timestamp']}`")
                                st.markdown(f"*{dc['complaint_text']}*")
                                st.markdown("---")
                    
                    st.markdown("---")
                    st.markdown("**👮 Officer Actions**")
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
                            st.success(f"✅ Priority overridden to: **{complaint['officer_override']}**")
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
                                        # Log override locally for dataset export
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
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**🎯 Final Priority Level:** **{display_label}**")
                        st.markdown(f"**📂 Category:** `{complaint['category']}`")
                        st.markdown(f"**🏢 Department:** `{complaint['department']}`")
                    with col2:
                        st.markdown(f"**⏰ Registered:** `{complaint['timestamp']}`")
                        if complaint.get('officer_override'):
                            st.markdown(f"👮 *Priority overridden by officer from: {complaint['priority_label']}*")
                        
                    st.markdown("**📋 Resolution & Audit History:**")
                    for hist in complaint.get('resolution_history', []):
                        st.markdown(f"- **{hist['status']}** ({hist['date']}): {hist.get('notes', '')}")
                                
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
                    
                    with st.expander("⚙️ View Raw Technical Parser Data (JSON)", expanded=False):
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
    
    # Get stats from API
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

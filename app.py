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
        return vectorizer, category_model, priority_model
    except FileNotFoundError:
        st.error("⚠️ Models not found! Please run `python model_training.py` first.")
        st.stop()

vectorizer, category_model, priority_model = load_models()

# Initialize session state for storing complaints
if 'complaints' not in st.session_state:
    st.session_state.complaints = []

if 'complaint_counter' not in st.session_state:
    st.session_state.complaint_counter = 1

# Initialize feedback storage
if 'officer_overrides' not in st.session_state:
    st.session_state.officer_overrides = []


def predict_complaint(complaint_text):
    """
    Process complaint through AI pipeline and return predictions with XAI
    
    Returns:
        dict: Prediction results including category, priority, explanation, etc.
    """
    # Vectorize input
    complaint_vector = vectorizer.transform([complaint_text])
    
    # Predict category
    predicted_category = category_model.predict(complaint_vector)[0]
    
    # Get severity score
    severity_score = utils.get_severity_score(predicted_category)
    
    # Get sentiment score
    sentiment_score = utils.get_sentiment_score(complaint_text)
    
    # Calculate priority score using official formula
    priority_score = utils.calculate_priority_score(severity_score, sentiment_score)
    
    # Get priority label
    priority_label = utils.get_priority_label(priority_score)
    
    # Route to department
    department = utils.route_to_department(predicted_category)
    
    # Generate XAI explanation
    explanation = utils.generate_explanation(
        predicted_category, 
        severity_score, 
        sentiment_score, 
        priority_label
    )
    
    # Check for duplicates
    existing_texts = [c['complaint_text'] for c in st.session_state.complaints]
    is_duplicate, cluster_id, similarity = utils.detect_duplicate(
        complaint_text, 
        existing_texts, 
        threshold=0.7
    )
    
    return {
        'category': predicted_category,
        'severity_score': severity_score,
        'sentiment_score': sentiment_score,
        'priority_score': priority_score,
        'priority_label': priority_label,
        'department': department,
        'explanation': explanation,
        'is_duplicate': is_duplicate,
        'cluster_id': cluster_id,
        'similarity': similarity
    }


def citizen_portal():
    """Citizen-facing complaint submission portal"""
    st.title("🏛️ Sahayak AI - Smart Complaint Triage System")
    st.markdown("### 📝 Submit Your Grievance")
    st.markdown("---")
    
    # Complaint input
    complaint_text = st.text_area(
        "Enter your complaint below:",
        height=150,
        placeholder="Example: Patient not treated in emergency ward at Chennai. Urgent help needed.",
        help="Describe your grievance in detail. Our AI will automatically categorize and prioritize it."
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        submit_button = st.button("🚀 Submit Complaint", type="primary", use_container_width=True)
    
    if submit_button:
        if not complaint_text.strip():
            st.error("⚠️ Please enter a complaint before submitting!")
        else:
            with st.spinner("🔍 Analyzing complaint with AI..."):
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
                    'category': result['category'],
                    'priority_label': result['priority_label'],
                    'priority_score': result['priority_score'],
                    'severity_score': result['severity_score'],
                    'sentiment_score': result['sentiment_score'],
                    'department': result['department'],
                    'explanation': result['explanation'],
                    'is_duplicate': result['is_duplicate'],
                    'cluster_id': result['cluster_id'],
                    'similarity': result['similarity'],
                    'officer_override': None,
                    'override_reason': None
                }
                
                st.session_state.complaints.append(complaint_record)
                
                # Display results
                st.success(f"✅ Complaint submitted successfully! ID: **{complaint_id}**")
                
                st.markdown("### 🎯 AI Analysis Results")
                
                # Duplicate warning
                if result['is_duplicate']:
                    st.warning(f"⚠️ **Duplicate Detected!** This complaint is {result['similarity']*100:.1f}% similar to an existing complaint (Cluster #{result['cluster_id']})")
                
                # Priority badge
                emoji = utils.get_priority_emoji(result['priority_label'])
                st.markdown(f"## {emoji} Priority: **{result['priority_label'].upper()}**")
                
                # XAI Explanation
                st.info(f"💡 **Explanation:** {result['explanation']}")
                
                # Metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📊 Priority Score", f"{result['priority_score']:.2f}")
                    st.progress(result['priority_score'])
                
                with col2:
                    st.metric("⚠️ Severity Score", f"{result['severity_score']:.2f}")
                    st.progress(result['severity_score'])
                
                with col3:
                    st.metric("😟 Sentiment Score", f"{result['sentiment_score']:.2f}")
                    st.progress(result['sentiment_score'])
                
                # Details
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**📂 Category:** {result['category']}")
                    st.markdown(f"**🏢 Routed To:** {result['department']}")
                
                with col2:
                    st.markdown(f"**🆔 Complaint ID:** {complaint_id}")
                    st.markdown(f"**⏰ Submitted:** {complaint_record['timestamp']}")
                
                st.markdown("---")
                st.info("ℹ️ Your complaint has been routed to the appropriate department. Officers will review it based on priority.")


def officer_dashboard():
    """Officer dashboard with ranked complaints and override functionality"""
    st.title("👮 Officer Dashboard - Complaint Triage Queue")
    st.markdown("### 📋 View and manage complaints ranked by urgency")
    st.markdown("---")
    
    if not st.session_state.complaints:
        st.info("📭 No complaints submitted yet. Switch to Citizen Portal to submit test complaints.")
        return
    
    # Statistics
    total_complaints = len(st.session_state.complaints)
    high_priority = len([c for c in st.session_state.complaints if c['priority_label'] == 'High'])
    medium_priority = len([c for c in st.session_state.complaints if c['priority_label'] == 'Medium'])
    low_priority = len([c for c in st.session_state.complaints if c['priority_label'] == 'Low'])
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Complaints", total_complaints)
    with col2:
        st.metric("🔴 High Priority", high_priority)
    with col3:
        st.metric("🟡 Medium Priority", medium_priority)
    with col4:
        st.metric("🟢 Low Priority", low_priority)
    
    st.markdown("---")
    
    # Sort complaints by priority score (descending)
    sorted_complaints = sorted(
        st.session_state.complaints, 
        key=lambda x: x['priority_score'], 
        reverse=True
    )
    
    # Display complaints
    st.markdown("### 🎯 Complaint Queue (Sorted by Priority)")
    
    for idx, complaint in enumerate(sorted_complaints, 1):
        emoji = utils.get_priority_emoji(complaint['priority_label'])
        
        # Determine if override has been applied
        has_override = complaint.get('officer_override') is not None
        
        with st.expander(
            f"{emoji} #{idx} - {complaint['id']} | {complaint['priority_label']} Priority | {complaint['category']}",
            expanded=(idx <= 3)  # Expand top 3
        ):
            # Show complaint text
            st.markdown(f"**Complaint Text:**")
            st.info(complaint['complaint_text'])
            
            # Show AI analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**🎯 AI Priority:** {emoji} **{complaint['priority_label']}** (Score: {complaint['priority_score']:.2f})")
                st.markdown(f"**📂 Category:** {complaint['category']}")
                st.markdown(f"**🏢 Department:** {complaint['department']}")
                st.markdown(f"**⏰ Submitted:** {complaint['timestamp']}")
            
            with col2:
                st.markdown(f"**⚠️ Severity:** {complaint['severity_score']:.2f}")
                st.markdown(f"**😟 Sentiment:** {complaint['sentiment_score']:.2f}")
                if complaint['is_duplicate']:
                    st.warning(f"⚠️ Duplicate detected ({complaint['similarity']*100:.0f}% similar)")
            
            # XAI Explanation
            st.markdown("**💡 AI Explanation:**")
            st.markdown(f"> {complaint['explanation']}")
            
            st.markdown("---")
            
            # Officer Override Section
            st.markdown("**👮 Officer Override & Feedback**")
            
            if has_override:
                # Show existing override
                override_emoji = utils.get_priority_emoji(complaint['officer_override'])
                st.success(f"✅ **Officer Override Applied:** {override_emoji} **{complaint['officer_override']}**")
                if complaint.get('override_reason'):
                    st.markdown(f"*Reason:* {complaint['override_reason']}")
            else:
                # Allow officer to override
                st.markdown("*Override AI priority if needed (for model retraining):*")
                
                col1, col2, col3 = st.columns([2, 2, 3])
                
                with col1:
                    override_priority = st.selectbox(
                        "New Priority:",
                        ["High", "Medium", "Low"],
                        key=f"override_select_{complaint['id']}"
                    )
                
                with col2:
                    override_reason = st.text_input(
                        "Reason (optional):",
                        key=f"reason_{complaint['id']}",
                        placeholder="Why override?"
                    )
                
                with col3:
                    if st.button("Apply Override", key=f"apply_{complaint['id']}", type="secondary"):
                        # Store override
                        complaint['officer_override'] = override_priority
                        complaint['override_reason'] = override_reason if override_reason else "No reason provided"
                        
                        # Log for model retraining
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
    
    # Export override feedback
    st.markdown("---")
    if st.session_state.officer_overrides:
        st.markdown(f"### 📊 Officer Feedback Log ({len(st.session_state.officer_overrides)} overrides)")
        
        if st.button("💾 Export Feedback for Model Retraining"):
            override_df = pd.DataFrame(st.session_state.officer_overrides)
            csv = override_df.to_csv(index=False)
            
            st.download_button(
                label="⬇️ Download Override Feedback (CSV)",
                data=csv,
                file_name=f"officer_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            st.success("✅ Feedback ready for download! This can be used to retrain and improve the model.")


# Main App
def main():
    # Sidebar navigation
    st.sidebar.title("🏛️ Sahayak AI")
    st.sidebar.markdown("**Intelligent Complaint Triage**")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigate:",
        ["👤 Citizen Portal", "👮 Officer Dashboard"],
        label_visibility="collapsed"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 System Info")
    st.sidebar.info(f"""
    **Total Complaints:** {len(st.session_state.complaints)}  
    **Officer Overrides:** {len(st.session_state.officer_overrides)}
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Priority Formula")
    st.sidebar.code("""
Priority Score = 
  (Severity × 0.6) + 
  (Sentiment × 0.4)

High:   [0.8 - 1.0]
Medium: [0.4 - 0.79]
Low:    [0.0 - 0.39]
    """)
    
    # Route to appropriate page
    if page == "👤 Citizen Portal":
        citizen_portal()
    else:
        officer_dashboard()


if __name__ == "__main__":
    main()

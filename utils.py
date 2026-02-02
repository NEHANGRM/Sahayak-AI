"""
Utility functions for Sahayak AI Complaint Triage System
Includes sentiment analysis, severity scoring, priority calculation, XAI, and duplicate detection
"""

import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Initialize VADER sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()

# Category to severity mapping (0.0 to 1.0)
SEVERITY_MAP = {
    "Hospital Emergency": 1.0,
    "Women Safety": 1.0,
    "Corruption Bribe": 0.9,
    "Traffic Signal Failure": 0.6,
    "Electricity Outage": 0.5,
    "Road Damage": 0.5,
    "Water Supply": 0.3,
    "Garbage Disposal": 0.2
}

# Department routing map
DEPARTMENT_MAP = {
    "Hospital Emergency": "Health Department",
    "Women Safety": "Police & Disaster Response",
    "Corruption Bribe": "Vigilance Bureau",
    "Traffic Signal Failure": "Municipal Corporation",
    "Electricity Outage": "Utilities Board",
    "Road Damage": "Municipal Corporation",
    "Water Supply": "Utilities Board",
    "Garbage Disposal": "Municipal Corporation"
}


def get_sentiment_score(text):
    """
    Analyze sentiment and return distress polarity score [0-1]
    Higher score = more negative/distressed sentiment
    
    Args:
        text (str): Complaint text
        
    Returns:
        float: Sentiment score normalized to [0-1] range
    """
    scores = sentiment_analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # Convert compound score [-1, 1] to distress score [0, 1]
    # Negative sentiment (distress) gets higher scores
    if compound < 0:
        # Negative: map [-1, 0] to [0.5, 1.0]
        sentiment_score = 0.5 + abs(compound) * 0.5
    else:
        # Positive/Neutral: map [0, 1] to [0, 0.5]
        sentiment_score = (1 - compound) * 0.5
    
    return round(sentiment_score, 3)


def get_severity_score(category):
    """
    Get severity score based on complaint category
    
    Args:
        category (str): Predicted complaint category
        
    Returns:
        float: Severity score [0-1]
    """
    return SEVERITY_MAP.get(category, 0.3)  # Default to 0.3 if category unknown


def calculate_priority_score(severity_score, sentiment_score):
    """
    Calculate final priority score using official formula:
    PriorityScore = (SeverityScore × 0.6) + (SentimentScore × 0.4)
    
    Args:
        severity_score (float): Severity score [0-1]
        sentiment_score (float): Sentiment score [0-1]
        
    Returns:
        float: Final priority score [0-1]
    """
    priority_score = (severity_score * 0.6) + (sentiment_score * 0.4)
    return round(priority_score, 3)


def get_priority_label(priority_score):
    """
    Convert priority score to label (High/Medium/Low)
    
    Args:
        priority_score (float): Priority score [0-1]
        
    Returns:
        str: Priority label
    """
    if priority_score >= 0.8:
        return "High"
    elif priority_score >= 0.4:
        return "Medium"
    else:
        return "Low"


def route_to_department(category):
    """
    Route complaint to appropriate government department
    
    Args:
        category (str): Complaint category
        
    Returns:
        str: Department name
    """
    return DEPARTMENT_MAP.get(category, "General Affairs Department")


def generate_explanation(category, severity_score, sentiment_score, priority_label):
    """
    Generate XAI (Explainable AI) explanation for priority prediction
    
    Args:
        category (str): Predicted category
        severity_score (float): Severity score
        sentiment_score (float): Sentiment score
        priority_label (str): Final priority label
        
    Returns:
        str: Human-readable explanation
    """
    severity_level = "High" if severity_score >= 0.7 else "Medium" if severity_score >= 0.4 else "Low"
    sentiment_level = "Strong Negative" if sentiment_score >= 0.7 else "Moderate Negative" if sentiment_score >= 0.5 else "Neutral"
    
    explanation = f"Marked **{priority_label.upper()}** because: "
    
    reasons = []
    
    # Add category-based reason
    if severity_score >= 0.7:
        reasons.append(f"**{category}** category (Critical)")
    elif severity_score >= 0.4:
        reasons.append(f"**{category}** category (Important)")
    else:
        reasons.append(f"**{category}** category (Routine)")
    
    # Add sentiment-based reason
    if sentiment_score >= 0.7:
        reasons.append("**Strong Distress** detected in complaint")
    elif sentiment_score >= 0.5:
        reasons.append("**Moderate Distress** detected")
    else:
        reasons.append("Neutral sentiment")
    
    explanation += " + ".join(reasons)
    
    return explanation


def detect_duplicate(new_complaint_text, existing_complaints, threshold=0.7):
    """
    Detect if a complaint is duplicate using TF-IDF cosine similarity
    
    Args:
        new_complaint_text (str): New complaint text
        existing_complaints (list): List of existing complaint texts
        threshold (float): Similarity threshold (default 0.7)
        
    Returns:
        tuple: (is_duplicate: bool, cluster_id: int or None, similarity: float)
    """
    if not existing_complaints:
        return False, None, 0.0
    
    # Create TF-IDF vectors
    vectorizer = TfidfVectorizer(stop_words='english', max_features=100)
    
    try:
        # Combine new complaint with existing ones
        all_complaints = existing_complaints + [new_complaint_text]
        tfidf_matrix = vectorizer.fit_transform(all_complaints)
        
        # Calculate cosine similarity between new complaint and all existing
        new_vector = tfidf_matrix[-1]
        existing_vectors = tfidf_matrix[:-1]
        
        similarities = cosine_similarity(new_vector, existing_vectors).flatten()
        max_similarity = similarities.max()
        most_similar_idx = similarities.argmax()
        
        if max_similarity >= threshold:
            return True, most_similar_idx, round(float(max_similarity), 3)
        else:
            return False, None, round(float(max_similarity), 3)
            
    except Exception as e:
        # If vectorization fails (e.g., too few complaints), return no duplicate
        return False, None, 0.0


def get_priority_color(priority_label):
    """
    Get color code for priority badge
    
    Args:
        priority_label (str): Priority label
        
    Returns:
        str: Color name for Streamlit
    """
    colors = {
        "High": "red",
        "Medium": "orange",
        "Low": "green"
    }
    return colors.get(priority_label, "gray")


def get_priority_emoji(priority_label):
    """
    Get emoji for priority label
    
    Args:
        priority_label (str): Priority label
        
    Returns:
        str: Emoji
    """
    emojis = {
        "High": "🔴",
        "Medium": "🟡",
        "Low": "🟢"
    }
    return emojis.get(priority_label, "⚪")

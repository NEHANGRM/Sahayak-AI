# Sahayak AI - Intelligent NLP-Driven Complaint Triage System

**An AI-powered smart complaint prioritization and routing system for automated governance**

## 🎯 Project Overview

Sahayak AI addresses the challenge of handling lakhs of daily complaints on government grievance portals like CPGRAMS. Instead of FIFO/manual handling, our system uses NLP and ML to automatically:
- Classify complaint categories
- Predict urgency using severity and sentiment
- Route to appropriate departments
- Detect duplicate complaints
- Provide explainable AI reasoning
- Enable officer feedback for continuous improvement

---

## ✨ Key Features

### 🤖 AI-Powered Classification
- **NLP Model**: TF-IDF + Logistic Regression for complaint categorization
- **8 Categories**: Hospital Emergency, Women Safety, Corruption, Traffic, Electricity, Road Damage, Water Supply, Garbage
- **Automated Department Routing**: Maps categories to government departments

### 📊 Priority Scoring System
Uses **official formula**:
```
PriorityScore = (SeverityScore × 0.6) + (SentimentScore × 0.4)

Priority Labels:
• High:   [0.8 – 1.0]  🔴
• Medium: [0.4 – 0.79] 🟡
• Low:    [0.0 – 0.39] 🟢
```

### 💡 Explainable AI (XAI)
Provides transparent reasoning for every prediction:
> "Marked **HIGH** because: **Hospital Emergency** category (Critical) + **Strong Distress** detected in complaint"

### 🔍 Duplicate Detection
- TF-IDF cosine similarity analysis
- Automatic clustering of similar complaints
- Prevents redundant processing

### 👮 Officer Dashboard
- Complaints ranked by urgency (High priority first)
- **Officer Override System**: Manual priority adjustment with feedback storage
- Export feedback for model retraining

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone or navigate to the project directory**
```bash
cd /path/to/Sahayak-AI
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Train the ML models**
```bash
python model_training.py
```
This will:
- Load the synthetic dataset (`ai_priority_training_dataset.csv`)
- Train category and priority classifiers
- Save models as `.pkl` files
- Display accuracy metrics

4. **Run the Streamlit app**
```bash
streamlit run app.py
```

5. **Open your browser**
The app will automatically open at `http://localhost:8501`

---

## 📁 Project Structure

```
Sahayak-AI/
├── app.py                              # Main Streamlit application
├── utils.py                            # Core utility functions
├── model_training.py                   # ML model training script
├── data_generator.py                   # Dataset generation (existing)
├── requirements.txt                    # Python dependencies
├── ai_priority_training_dataset.csv    # Training dataset (1000 complaints)
├── tfidf_vectorizer.pkl               # Trained TF-IDF vectorizer (generated)
├── category_classifier.pkl            # Trained category model (generated)
└── priority_classifier.pkl            # Trained priority model (generated)
```

---

## 💻 Usage

### Citizen Portal (Submit Complaints)
1. Navigate to **"👤 Citizen Portal"** in the sidebar
2. Enter complaint text in the text area
3. Click **"🚀 Submit Complaint"**
4. View AI analysis results:
   - Priority label with color-coded badge
   - **XAI Explanation** of why this priority was assigned
   - Severity, sentiment, and priority scores
   - Predicted category and routed department
   - Duplicate warning (if applicable)

### Officer Dashboard (Manage Complaints)
1. Navigate to **"👮 Officer Dashboard"** in the sidebar
2. View complaints sorted by priority (High first)
3. See statistics: Total, High, Medium, Low counts
4. Expand complaints to view:
   - Full complaint text
   - AI analysis and explanation
   - **Override AI Priority** if needed
   - Provide feedback reason
5. Export officer override feedback for model retraining

---

## 🎓 Workflow (Matches Official Requirements)

1. ✅ **Citizen submits complaint** via portal/app
2. ✅ **NLP preprocessing** + cleaning
3. ✅ **AI model predicts** complaint category
4. ✅ **Sentiment and severity** signals extracted
5. ✅ **Urgency model assigns** priority score/label
6. ✅ **Complaint routed** to relevant department
7. ✅ **Officer dashboard** shows ranked complaints by urgency

**BONUS Features:**
- ✨ **XAI Explanations**: Transparent AI reasoning
- ✨ **Officer Feedback Loop**: Override system with export functionality

---

## 🧪 Testing the System

### Test High Priority Complaint
```
"Patient not treated in emergency ward at Chennai. Ambulance delayed, urgent help needed."
```
Expected: 🔴 High Priority (Health emergency + negative sentiment)

### Test Medium Priority Complaint
```
"Traffic signals not working at Mumbai for 2 days, risk of accidents."
```
Expected: 🟡 Medium Priority (Infrastructure issue)

### Test Low Priority Complaint
```
"Request for tree trimming permit in residential area."
```
Expected: 🟢 Low Priority (Routine service)

### Test Duplicate Detection
Submit the same complaint twice and verify duplicate warning appears.

---

## 🏆 Jury-Winning Features

### 1. **Explainable AI (XAI)**
Every prediction includes a human-readable explanation:
- **Why** this priority was assigned
- **Which factors** contributed (category severity + sentiment)
- Builds **trust** and **transparency**

### 2. **Officer Feedback Override**
- Officers can manually adjust AI predictions
- Feedback stored with reasons
- Exportable CSV for **model retraining**
- Creates **continuous improvement loop**

---

## 📊 Technical Details

### ML Models
- **Vectorizer**: TF-IDF with 500 max features, bigrams
- **Classifier**: Logistic Regression with balanced class weights
- **Training Split**: 80-20 train-test split
- **Accuracy**: Typically 85-95% on test set

### Priority Formula
```python
severity_score = CATEGORY_SEVERITY_MAP[category]  # 0.0 - 1.0
sentiment_score = get_distress_from_vader(text)   # 0.0 - 1.0
priority_score = (severity_score * 0.6) + (sentiment_score * 0.4)
```

### Duplicate Detection
- TF-IDF vectors with cosine similarity
- Threshold: 0.7 (70% similarity)
- Clusters similar complaints automatically

---

## 🔧 Dependencies

```
streamlit>=1.30.0        # Web UI framework
scikit-learn>=1.3.0      # ML models
pandas>=2.0.0            # Data handling
numpy>=1.24.0            # Numerical operations
vaderSentiment>=3.3.2    # Sentiment analysis
```

---

## 📈 Future Enhancements

- [ ] Integration with real CPGRAMS API
- [ ] Multi-language support (Hindi, regional languages)
- [ ] Real-time dashboard updates
- [ ] Advanced NLP models (BERT, transformers)
- [ ] Automated model retraining pipeline
- [ ] SMS/Email notifications to citizens
- [ ] Mobile app interface

---

## 👥 Team

**Project**: Sahayak AI - NIT Ideathon  
**Purpose**: Hackathon MVP Prototype

---

## 📄 License

This is a prototype demonstration system for educational and hackathon purposes.

---

## 🎯 Demo Instructions

For judges/reviewers:

1. **Run model training**: `python model_training.py` (30 seconds)
2. **Launch app**: `streamlit run app.py`
3. **Submit test complaints** in Citizen Portal (use examples above)
4. **Switch to Officer Dashboard** to see ranked queue
5. **Test override** on a complaint to see feedback system
6. **Export feedback CSV** to demonstrate retraining loop

**Key Highlights to Demonstrate:**
- ✅ AI priority scoring with official formula
- ✅ XAI explanations for transparency
- ✅ Officer override with feedback storage
- ✅ Duplicate detection
- ✅ Beautiful, intuitive UI
- ✅ End-to-end working prototype

---

**Built with ❤️ for better governance through AI**

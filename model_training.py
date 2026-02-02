"""
Model Training Script for Sahayak AI
Trains TF-IDF + Logistic Regression models for category and priority classification
"""

import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

def train_models():
    """Train and save category and priority classification models"""
    
    print("=" * 60)
    print("SAHAYAK AI - Model Training")
    print("=" * 60)
    
    # Load dataset
    print("\n[1/5] Loading dataset...")
    df = pd.read_csv('ai_priority_training_dataset.csv')
    print(f"✓ Loaded {len(df)} complaints")
    print(f"  Categories: {df['Category'].nunique()}")
    print(f"  Priority Labels: {df['Priority_Label'].nunique()}")
    
    # Prepare data
    X = df['Complaint_Text']
    y_category = df['Category']
    y_priority = df['Priority_Label']
    
    # Split data
    print("\n[2/5] Splitting data (80% train, 20% test)...")
    X_train, X_test, y_cat_train, y_cat_test, y_pri_train, y_pri_test = train_test_split(
        X, y_category, y_priority, test_size=0.2, random_state=42, stratify=y_category
    )
    print(f"✓ Training samples: {len(X_train)}")
    print(f"✓ Testing samples: {len(X_test)}")
    
    # Create TF-IDF vectorizer
    print("\n[3/5] Creating TF-IDF vectorizer...")
    vectorizer = TfidfVectorizer(
        max_features=500,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=2
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)
    print(f"✓ Vocabulary size: {len(vectorizer.vocabulary_)}")
    
    # Train Category Classifier
    print("\n[4/5] Training Category Classifier...")
    category_model = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
    category_model.fit(X_train_tfidf, y_cat_train)
    
    y_cat_pred = category_model.predict(X_test_tfidf)
    cat_accuracy = accuracy_score(y_cat_test, y_cat_pred)
    print(f"✓ Category Classification Accuracy: {cat_accuracy:.2%}")
    
    print("\nCategory Classification Report:")
    print(classification_report(y_cat_test, y_cat_pred, zero_division=0))
    
    # Train Priority Classifier
    print("\n[5/5] Training Priority Classifier...")
    priority_model = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
    priority_model.fit(X_train_tfidf, y_pri_train)
    
    y_pri_pred = priority_model.predict(X_test_tfidf)
    pri_accuracy = accuracy_score(y_pri_test, y_pri_pred)
    print(f"✓ Priority Classification Accuracy: {pri_accuracy:.2%}")
    
    print("\nPriority Classification Report:")
    print(classification_report(y_pri_test, y_pri_pred, zero_division=0))
    
    # Save models
    print("\n" + "=" * 60)
    print("Saving trained models...")
    print("=" * 60)
    
    with open('tfidf_vectorizer.pkl', 'wb') as f:
        pickle.dump(vectorizer, f)
    print("✓ Saved: tfidf_vectorizer.pkl")
    
    with open('category_classifier.pkl', 'wb') as f:
        pickle.dump(category_model, f)
    print("✓ Saved: category_classifier.pkl")
    
    with open('priority_classifier.pkl', 'wb') as f:
        pickle.dump(priority_model, f)
    print("✓ Saved: priority_classifier.pkl")
    
    print("\n" + "=" * 60)
    print("✅ MODEL TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\nFinal Results:")
    print(f"  → Category Accuracy: {cat_accuracy:.2%}")
    print(f"  → Priority Accuracy: {pri_accuracy:.2%}")
    print(f"\nModels are ready for deployment!")
    print(f"Run: streamlit run app.py")
    print("=" * 60)

if __name__ == "__main__":
    train_models()

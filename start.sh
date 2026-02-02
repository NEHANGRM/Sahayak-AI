#!/bin/bash

# Sahayak AI - Quick Start Script
# Run this script to install, train, and launch the application

echo "============================================================"
echo "🏛️  SAHAYAK AI - QUICK START"
echo "============================================================"
echo ""

# Step 1: Install dependencies
echo "[1/3] Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Installation failed. Please check your Python environment."
    exit 1
fi

echo "✅ Dependencies installed successfully"
echo ""

# Step 2: Train models
echo "[2/3] Training ML models..."
python model_training.py

if [ $? -ne 0 ]; then
    echo "❌ Model training failed. Please check the dataset."
    exit 1
fi

echo "✅ Models trained successfully"
echo ""

# Step 3: Launch application
echo "[3/3] Launching Streamlit application..."
echo ""
echo "============================================================"
echo "🚀 Starting Sahayak AI..."
echo "============================================================"
echo ""
echo "The app will open in your browser automatically."
echo "If not, navigate to: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

streamlit run app.py

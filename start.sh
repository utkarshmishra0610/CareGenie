#!/bin/bash
# ==============================================================================
# 🏥 Personalized AI Health Assistant - One-Command Launcher
# ==============================================================================

# Move to the script's directory (project root)
cd "$(dirname "$0")"

echo ""
echo "=================================================================="
echo "  🏥 HealthPulse AI - Personalized Disease Risk Assessment Assistant"
echo "  Theme: Customer.io Dark Spruce & Cream Paper | 9 Regional Languages"
echo "=================================================================="
echo ""

# Navigate into the backend directory
cd backend

# Locate and activate Python virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "  📦 Activating local virtual environment..."
    source venv/bin/activate
elif [ -f "$HOME/.gemini/antigravity/scratch/personalized-ai-health-assistant/backend/venv/bin/activate" ]; then
    echo "  📦 Activating workspace virtual environment..."
    source "$HOME/.gemini/antigravity/scratch/personalized-ai-health-assistant/backend/venv/bin/activate"
else
    echo "  ⚙️ Creating new Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    echo "  📥 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
fi

echo ""
echo "  🚀 Starting FastAPI Application Server on Port 8000..."
echo "  🌐 Web App:      http://localhost:8000/app"
echo "  📑 Swagger Docs: http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop the server."
echo "=================================================================="
echo ""

# Launch Uvicorn server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

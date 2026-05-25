#!/bin/bash

# One-Click Frictionless Startup Script for Mac/Linux

echo "🚀 Booting up Omni-Assistant..."

# Handle Ctrl+C to gracefully kill child processes
trap 'echo "🛑 Shutting down..."; kill 0; exit' SIGINT SIGTERM

# 1. Check & setup Python Virtual Environment
if [ ! -d ".venv" ]; then
    echo "🐍 No virtual environment found. Creating one..."
    python3 -m venv .venv
    echo "📦 Installing backend dependencies..."
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# 2. Check & setup Node Modules
if [ ! -d "frontend/node_modules" ]; then
    echo "🌐 No node_modules found. Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

# 3. Boot Backend
echo "🔥 Starting FastAPI Backend..."
python backend/main.py &

# 4. Boot Frontend
echo "✨ Starting React Frontend..."
cd frontend
npm run dev &
cd ..

echo "✅ All systems go! Press Ctrl+C to stop."
# Wait for child processes to prevent the script from exiting
wait

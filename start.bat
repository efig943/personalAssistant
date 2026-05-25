@echo off
title Omni-Assistant Starter
echo 🚀 Booting up Omni-Assistant...

:: 1. Check & setup Python Virtual Environment
if not exist ".venv\" (
    echo 🐍 No virtual environment found. Creating one...
    python -m venv .venv
    echo 📦 Installing backend dependencies...
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

:: 2. Check & setup Node Modules
if not exist "frontend\node_modules\" (
    echo 🌐 No node_modules found. Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

:: 3. Boot Backend in a new window
echo 🔥 Starting FastAPI Backend...
start "Omni-Assistant Backend" cmd /c "call .venv\Scripts\activate.bat && python backend\main.py"

:: 4. Boot Frontend in a new window
echo ✨ Starting React Frontend...
cd frontend
start "Omni-Assistant Frontend" cmd /c "npm run dev"
cd ..

echo ✅ All systems go! Two new windows have been opened for the Backend and Frontend.
echo To stop, simply close the new terminal windows.
pause

@echo off
echo ========================================================
echo   Intelligent AI Productivity Assistant Setup
echo ========================================================
echo.

echo [1/4] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/4] Installing requirements...
pip install -r requirements.txt

echo [3/4] Checking environment configuration...
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo IMPORTANT: Please edit .env and add your GEMINI_API_KEY.
) else (
    echo .env file already exists.
)

echo.
echo [4/4] Setup Complete!
echo.
echo To run the application, open two terminals and run:
echo Terminal 1 (API):
echo   venv\Scripts\activate
echo   python -m uvicorn app.main:app --reload
echo.
echo Terminal 2 (UI):
echo   venv\Scripts\activate
echo   streamlit run streamlit_app.py
echo.
pause

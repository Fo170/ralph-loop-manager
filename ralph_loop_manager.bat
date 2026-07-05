@echo off
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo Une erreur est survenue. Verifiez que Python est installe et que les dependances sont installees :
    echo   pip install -r requirements.txt
    pause
)

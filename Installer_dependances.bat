@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   Job Finder Pro - Installation des dependances
echo ================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
    py -m pip install --upgrade pip
    py -m pip install -r requirements.txt
) else (
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
)
if %errorlevel% neq 0 (
    echo.
    echo ERREUR : installation incomplete.
    echo Verifiez Internet et que Python est installe.
    pause
    exit /b 1
)
echo.
echo Installation terminee. Vous pouvez lancer Job_Finder.py.
pause

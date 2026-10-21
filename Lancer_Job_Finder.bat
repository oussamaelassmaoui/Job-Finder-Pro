@echo off
chcp 65001 >nul
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py Job_Finder.py
) else (
    python Job_Finder.py
)
if %errorlevel% neq 0 pause

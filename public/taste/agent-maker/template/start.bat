@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul || (echo 未找到 Python，请先安装 Python 3.9+ ^(安装时勾选 Add to PATH^) & pause & exit /b)
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
python run.py %*
pause

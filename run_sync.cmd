@echo off
chcp 65001 >nul
REM Запуск FolderSync в обычном режиме (с консолью)
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Venv не найден. Запустите setup_venv.cmd для создания окружения.
    pause
    exit /b 1
)

venv\Scripts\python.exe main.py
pause


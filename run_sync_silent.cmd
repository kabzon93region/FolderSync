@echo off
chcp 65001 >nul
REM Запуск FolderSync в режиме без консоли (pythonw)
cd /d "%~dp0"

if not exist "venv\Scripts\pythonw.exe" (
    echo Venv не найден. Запустите setup_venv.cmd для создания окружения.
    pause
    exit /b 1
)

start "" venv\Scripts\pythonw.exe main.py
exit


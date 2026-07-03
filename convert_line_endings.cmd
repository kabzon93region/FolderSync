@echo off
echo Конвертация окончаний строк из Unix (LF) в Windows (CRLF)
echo ========================================================

REM Проверяем наличие Python в venv
if not exist "venv\Scripts\python.exe" (
    echo ОШИБКА: Venv не найден. Запустите setup_venv.cmd для создания окружения.
    pause
    exit /b 1
)

REM Запускаем Python скрипт из venv
echo Запуск конвертации...
venv\Scripts\python.exe convert_line_endings.py

pause
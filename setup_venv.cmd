@echo off
chcp 65001 >nul
REM Создание виртуального окружения
cd /d "%~dp0"

echo Создаю виртуальное окружение в %~dp0venv ...
python -m venv venv

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: не удалось создать venv. Убедитесь, что Python установлен и доступен в PATH.
    pause
    exit /b 1
)

echo.
echo Готово! Venv создан.
echo Теперь можно запускать программу через run_sync.cmd или run_sync_silent.cmd
pause

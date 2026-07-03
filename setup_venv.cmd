@echo off
chcp 65001 >nul
REM Создание виртуального окружения и установка зависимостей
cd /d "%~dp0"

echo Создаю виртуальное окружение в %~dp0venv ...
python -m venv venv

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: не удалось создать venv. Убедитесь, что Python установлен и доступен в PATH.
    pause
    exit /b 1
)

echo.
echo Устанавливаю зависимости из requirements.txt ...
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\python.exe -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: не удалось установить зависимости.
    pause
    exit /b 1
)

echo.
echo Готово! Venv создан и зависимости установлены.
echo Теперь можно запускать программу через run_sync.cmd или run_sync_silent.cmd
pause

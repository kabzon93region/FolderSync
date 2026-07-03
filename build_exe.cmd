@echo off
chcp 65001 >nul
REM Сборка FolderSync в автономный exe через PyInstaller
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Venv не найден. Запустите setup_venv.cmd для создания окружения.
    pause
    exit /b 1
)

echo Устанавливаю PyInstaller...
venv\Scripts\python.exe -m pip install pyinstaller

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: не удалось установить PyInstaller.
    pause
    exit /b 1
)

echo.
echo Сборка exe...
venv\Scripts\python.exe -m PyInstaller ^
    --noconfirm ^
    --onefile ^
    --windowed ^
    --name "FolderSync" ^
    --icon "main.ico" ^
    --add-data "config.cfg;." ^
    --add-data "main.ico;." ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: сборка не удалась.
    pause
    exit /b 1
)

echo.
echo Готово! exe файл: dist\FolderSync.exe
echo.
echo Примечание: config.cfg будет создан рядом с exe при первом запуске.
pause

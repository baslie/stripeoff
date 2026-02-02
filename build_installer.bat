@echo off
chcp 65001 >nul
echo === Сборка StripeOff ===
echo.

echo Шаг 1: Сборка EXE через PyInstaller...
pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py
if errorlevel 1 (
    echo ОШИБКА: Сборка PyInstaller не удалась
    pause
    exit /b 1
)
echo.

echo Шаг 2: Сборка установщика через Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\StripeOff.iss
if errorlevel 1 (
    echo ОШИБКА: Сборка Inno Setup не удалась
    pause
    exit /b 1
)

echo.
echo === Готово! ===
echo Портативная версия: dist\StripeOff.exe
echo Установщик: dist\StripeOff_Setup_1.0.0.exe
pause

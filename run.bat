@echo off
title Mount & Blade 2D RPG
color 0A

echo ========================================
echo   Mount ^& Blade 2D RPG - MVP
echo ========================================
echo.
echo Starting the game...
echo.
echo Controls:
echo   WASD or Arrow Keys - Move
echo   Space - Attack (in battle)
echo   Close window - Exit
echo.

py -3.12 -B main.py

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to run the game!
    echo.
    echo Check if Pygame is installed:
    echo   Execute: install.bat
    echo.
    pause
)

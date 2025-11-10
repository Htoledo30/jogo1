@echo off
title Mount & Blade 2D RPG - Automatic Installation
color 0A

echo ========================================
echo   Mount ^& Blade 2D RPG - Installation
echo ========================================
echo.

echo [1/4] Checking for Python 3.12...
py -3.12 --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.12 not found!
    echo.
    echo Please install Python 3.12.x from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python 3.12 found:
py -3.12 --version
echo.

echo [2/4] Updating pip...
py -3.12 -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo [WARNING] Failed to update pip, but continuing...
) else (
    echo [OK] pip updated successfully
)
echo.

echo [3/4] Installing Pygame...
echo (This might take a few seconds...)
py -3.12 -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install Pygame!
    echo.
    echo Try manually: py -3.12 -m pip install pygame
    echo.
    pause
    exit /b 1
)
echo [OK] Pygame installed successfully!
echo.

echo [4/4] Verifying installation...
py -3.12 -c "import pygame; print('[OK] Pygame versao:', pygame.version.ver)"
if errorlevel 1 (
    echo [ERROR] Pygame could not be imported!
    pause
    exit /b 1
)
echo.

echo ========================================
echo   Installation Completed Successfully!
echo ========================================
echo.
echo To play, double-click on: run.bat
echo Or run: py -3.12 main.py
echo.
echo Controls:
echo   WASD or Arrow Keys - Move
echo   Space - Attack (in battle)
echo   ESC - Exit
echo.
pause

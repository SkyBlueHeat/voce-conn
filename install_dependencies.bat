@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Voice Assistant Dependency Installer
echo ===================================
echo.

REM Create logs directory
if not exist logs (
    mkdir logs
)

REM Check for Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Trying alternative commands...
    
    py --version > nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD=py
    ) else (
        echo ERROR: Python not found!
        echo Please install Python 3.10 or higher and add it to PATH
        echo or run this script from a Python environment.
        pause
        exit /b 1
    )
) else (
    set PYTHON_CMD=python
)

echo Found Python using: %PYTHON_CMD%

REM Install required packages
echo Installing required packages...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo Failed to install packages from requirements.txt
    echo Installing individual packages...
    
    echo Installing SpeechRecognition...
    %PYTHON_CMD% -m pip install SpeechRecognition
    
    echo Installing PyAudio...
    %PYTHON_CMD% -m pip install PyAudio
    
    echo Installing pyttsx3...
    %PYTHON_CMD% -m pip install pyttsx3
    
    echo Installing python-dotenv...
    %PYTHON_CMD% -m pip install python-dotenv
    
    echo Installing edge-tts...
    %PYTHON_CMD% -m pip install edge-tts
    
    echo Installing pygame...
    %PYTHON_CMD% -m pip install pygame
    
    echo Installing pyperclip...
    %PYTHON_CMD% -m pip install pyperclip
    
    if exist vosk (
        echo Installing vosk...
        %PYTHON_CMD% -m pip install vosk
    )
)

echo.
echo All dependencies installed successfully.
echo You can now run the voice assistant using run_voice_assistant.bat
echo.
pause
endlocal 
@echo off
setlocal enabledelayedexpansion

echo ===================================
echo Voice Assistant Launcher
echo ===================================
echo.

REM Check for Python
set PYTHON_CMD=python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Trying alternative commands...
    
    py --version > nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD=py
    ) else (
        echo ERROR: Python not found!
        echo Please install Python 3.10 or higher and add it to PATH
        echo or run install_dependencies.bat first.
        pause
        exit /b 1
    )
)

REM Get Python version
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VER=%%i
echo Found Python %PYTHON_VER% using: %PYTHON_CMD%

REM Check if logs directory exists
if not exist logs (
    mkdir logs
    echo Created logs directory.
)

REM Check if edge-tts is installed
%PYTHON_CMD% -c "import edge_tts" > nul 2>&1
if %errorlevel% neq 0 (
    echo Edge-TTS not found! Attempting to install...
    %PYTHON_CMD% -m pip install edge-tts
    
    if !errorlevel! neq 0 (
        echo Failed to install Edge-TTS.
        echo Please run install_dependencies.bat to set up all required packages.
        pause
        exit /b 1
    )
)

REM Check if pygame is installed
%PYTHON_CMD% -c "import pygame" > nul 2>&1
if %errorlevel% neq 0 (
    echo Pygame not found! Attempting to install...
    %PYTHON_CMD% -m pip install pygame
    
    if !errorlevel! neq 0 (
        echo Failed to install Pygame.
        echo Please run install_dependencies.bat to set up all required packages.
        pause
        exit /b 1
    )
)

REM Check if speech_recognition is installed
%PYTHON_CMD% -c "import speech_recognition" > nul 2>&1
if %errorlevel% neq 0 (
    echo Speech Recognition library not found! Attempting to install...
    %PYTHON_CMD% -m pip install SpeechRecognition
    
    if !errorlevel! neq 0 (
        echo Failed to install Speech Recognition.
        echo Please run install_dependencies.bat to set up all required packages.
        pause
        exit /b 1
    )
)

REM Check for command line argument
set MIC_INDEX=
if not "%~1"=="" (
    set MIC_INDEX=%~1
    goto runWithMic
)

echo.
echo ===================================
echo Mikrofon Seçimi
echo ===================================

:menu
echo.
echo Lütfen bir seçenek seçin:
echo 1 - Mikrofonları listele (detaylı liste)
echo 2 - Belirli bir mikrofon seç
echo 3 - Varsayılan mikrofon ile başlat
echo.
set /p choice="Seçiminizi girin (1-3): "

if "%choice%"=="1" (
    echo.
    echo Mikrofonlar listeleniyor...
    
    REM Check if list_microphones.py exists
    if exist list_microphones.py (
        %PYTHON_CMD% list_microphones.py
    ) else (
        echo list_microphones.py bulunamadı, alternatif listeleyici kullanılıyor...
        %PYTHON_CMD% -c "import speech_recognition as sr; print('\nKullanılabilir Mikrofonlar:'); [print(f'{i}: {name}') for i, name in enumerate(sr.Microphone.list_microphone_names())]"
    )
    goto menu
)

if "%choice%"=="2" (
    echo.
    set /p MIC_INDEX="Kullanmak istediğiniz mikrofonun numarasını girin: "
    goto runWithMic
)

if "%choice%"=="3" (
    echo.
    echo Varsayılan mikrofon kullanılıyor.
    echo Sesli asistan başlatılıyor...
    %PYTHON_CMD% main.py
    goto end
) else (
    echo.
    echo Geçersiz seçim. Lütfen tekrar deneyin.
    goto menu
)

:runWithMic
echo.
echo %MIC_INDEX% numaralı mikrofon seçildi.
echo Sesli asistan başlatılıyor...
%PYTHON_CMD% main.py --mic=%MIC_INDEX%
goto end

:end
if %errorlevel% neq 0 (
    echo An error occurred while running the voice assistant.
    echo Check the log files in the logs directory for more information.
    pause
)

endlocal 
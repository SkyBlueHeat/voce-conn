@echo off
echo Sesli Asistan .exe oluşturucu
echo Bu işlem gerekli paketlerin yuklu olmasini gerektirir

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller yuklu değil. Yukleniyor...
    pip install pyinstaller
)

echo .exe dosyasi oluşturuluyor...
pyinstaller --onefile --add-data="komutlar.json;." --add-data=".env;." --hidden-import=PIL._tkinter_finder main.py

echo İşlem tamamlandi! .exe dosyasi dist klasorunde oluşturuldu.
echo NOT: Vosk model dosyalarini dist klasorune taşimayi unutmayin.
pause 
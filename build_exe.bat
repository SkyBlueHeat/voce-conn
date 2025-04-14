@echo off
echo Sesli Asistan .exe oluşturucu
echo Bu işlem gerekli paketlerin yüklü olmasını gerektirir

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller yüklü değil. Yükleniyor...
    pip install pyinstaller
)

echo .exe dosyası oluşturuluyor...
pyinstaller --onefile --add-data="komutlar.json;." --add-data=".env;." --hidden-import=PIL._tkinter_finder main.py

echo İşlem tamamlandı! .exe dosyası dist klasöründe oluşturuldu.
echo NOT: Vosk model dosyalarını dist klasörüne taşımayı unutmayın.
pause 
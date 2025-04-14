#!/usr/bin/env python
"""
Voce Turkçe Sesli Asistan GUI Başlatici
"""

import os
import sys
import logging
import importlib.util

# Gunluk kaydini yapilandir
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/gui.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("Launcher")

def check_dependencies():
    """Gerekli bağimliliklari kontrol eder"""
    
    missing_packages = []
    required_packages = ["PyQt5", "python-dotenv"]
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_").split(">=")[0])
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Eksik bağimliliklari yuklemeyi dener"""
    import subprocess
    
    try:
        logger.info(f"Bağimliliklar yukleniyor: {', '.join(packages)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Bağimliliklar yuklenirken hata: {e}")
        return False

def run_gui():
    """Ana GUI uygulamasini başlatir"""
    try:
        # Logs dizininin varliğini kontrol et ve yoksa oluştur
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        # gui.main_window modulunu dinamik olarak içe aktar
        if os.path.isfile("gui/main_window.py"):
            print("GUI modulu bulundu.")
            
            # Python yoluna mevcut dizini ekle
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # GUI modulunu yukle
            from gui.main_window import main
            
            # GUI uygulamasini başlat
            main()
        else:
            logger.error("gui/main_window.py modulu bulunamadi!")
            print("GUI modulu bulunamadi: gui/main_window.py dosyasi mevcut değil.")
            print("Lutfen tum dosyalarin doğru şekilde kurulduğundan emin olun.")
            input("Çikmak için bir tuşa basin...")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Uygulama başlatilirken hata: {e}")
        print(f"Hata: {e}")
        input("Çikmak için bir tuşa basin...")
        sys.exit(1)

if __name__ == "__main__":
    print("Voce Turkçe Sesli Asistan GUI Başlatiliyor...")
    
    # Çalişma dizinini doğru yere ayarla
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Python surumunu kontrol et
    if sys.version_info < (3, 8):
        print("Hata: Python 3.8 veya daha yuksek bir surum gereklidir!")
        input("Çikmak için bir tuşa basin...")
        sys.exit(1)
    
    # Bağimliliklari kontrol et
    missing = check_dependencies()
    if missing:
        print(f"Eksik bağimliliklar tespit edildi: {', '.join(missing)}")
        install = input("Eksik bağimliliklari şimdi yuklemek ister misiniz? (e/h): ")
        
        if install.lower() in ('e', 'evet', 'y', 'yes'):
            if install_dependencies(missing):
                print("Bağimliliklar başariyla yuklendi.")
            else:
                print("Bağimliliklar yuklenemedi. Lutfen manuel olarak yukleyin.")
                print("Komut: pip install " + " ".join(missing))
                input("Çikmak için bir tuşa basin...")
                sys.exit(1)
        else:
            print("Bağimliliklar yuklenmedi. Uygulama duzgun çalişmayabilir.")
    
    # GUI'yi başlat
    run_gui() 
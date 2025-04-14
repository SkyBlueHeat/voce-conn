#!/usr/bin/env python
"""
Voce Türkçe Sesli Asistan GUI Başlatıcı
"""

import os
import sys
import logging
import importlib.util

# Günlük kaydını yapılandır
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
    """Gerekli bağımlılıkları kontrol eder"""
    
    missing_packages = []
    required_packages = ["PyQt5", "python-dotenv"]
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_").split(">=")[0])
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies(packages):
    """Eksik bağımlılıkları yüklemeyi dener"""
    import subprocess
    
    try:
        logger.info(f"Bağımlılıklar yükleniyor: {', '.join(packages)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Bağımlılıklar yüklenirken hata: {e}")
        return False

def run_gui():
    """Ana GUI uygulamasını başlatır"""
    try:
        # Logs dizininin varlığını kontrol et ve yoksa oluştur
        if not os.path.exists("logs"):
            os.makedirs("logs")
            
        # gui.main_window modülünü dinamik olarak içe aktar
        if os.path.isfile("gui/main_window.py"):
            print("GUI modülü bulundu.")
            
            # Python yoluna mevcut dizini ekle
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # GUI modülünü yükle
            from gui.main_window import main
            
            # GUI uygulamasını başlat
            main()
        else:
            logger.error("gui/main_window.py modülü bulunamadı!")
            print("GUI modülü bulunamadı: gui/main_window.py dosyası mevcut değil.")
            print("Lütfen tüm dosyaların doğru şekilde kurulduğundan emin olun.")
            input("Çıkmak için bir tuşa basın...")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Uygulama başlatılırken hata: {e}")
        print(f"Hata: {e}")
        input("Çıkmak için bir tuşa basın...")
        sys.exit(1)

if __name__ == "__main__":
    print("Voce Türkçe Sesli Asistan GUI Başlatılıyor...")
    
    # Çalışma dizinini doğru yere ayarla
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Python sürümünü kontrol et
    if sys.version_info < (3, 8):
        print("Hata: Python 3.8 veya daha yüksek bir sürüm gereklidir!")
        input("Çıkmak için bir tuşa basın...")
        sys.exit(1)
    
    # Bağımlılıkları kontrol et
    missing = check_dependencies()
    if missing:
        print(f"Eksik bağımlılıklar tespit edildi: {', '.join(missing)}")
        install = input("Eksik bağımlılıkları şimdi yüklemek ister misiniz? (e/h): ")
        
        if install.lower() in ('e', 'evet', 'y', 'yes'):
            if install_dependencies(missing):
                print("Bağımlılıklar başarıyla yüklendi.")
            else:
                print("Bağımlılıklar yüklenemedi. Lütfen manuel olarak yükleyin.")
                print("Komut: pip install " + " ".join(missing))
                input("Çıkmak için bir tuşa basın...")
                sys.exit(1)
        else:
            print("Bağımlılıklar yüklenmedi. Uygulama düzgün çalışmayabilir.")
    
    # GUI'yi başlat
    run_gui() 
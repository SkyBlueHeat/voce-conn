import os
import sys
import subprocess
import platform
from download_model import download_vosk_model

def check_python_version():
    """Check if Python version is compatible"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print(f"Hata: Python {required_version[0]}.{required_version[1]} veya üstü gerekli.")
        print(f"Şu anda kullanılan sürüm: Python {current_version[0]}.{current_version[1]}")
        return False
        
    return True

def install_requirements():
    """Install required packages"""
    try:
        print("Gerekli paketler yükleniyor...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Paketler başarıyla yüklendi.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Hata: Paketler yüklenirken bir sorun oluştu - {e}")
        return False
    except Exception as e:
        print(f"Beklenmeyen hata: {e}")
        return False

def check_os_compatibility():
    """Check if operating system is compatible"""
    os_name = platform.system()
    
    if os_name != "Windows":
        print(f"Uyarı: Bu uygulama Windows için tasarlanmıştır, ancak şu an {os_name} üzerinde çalıştırılıyor.")
        print("Bazı özellikler düzgün çalışmayabilir.")
        return False
        
    return True

def check_microphone_access():
    """Check if microphone access is available"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if not input_devices:
            print("Uyarı: Kullanılabilir mikrofon bulunamadı.")
            return False
            
        print(f"{len(input_devices)} adet mikrofon bulundu.")
        return True
    except:
        print("Uyarı: Mikrofonlar kontrol edilirken bir sorun oluştu.")
        return False

def setup():
    """Run the setup process"""
    print("Kişisel Sesli Asistan Kurulum Aracı")
    print("=" * 40)
    
    if not check_python_version():
        return False
    
    if not check_os_compatibility():
        proceed = input("Devam etmek istiyor musunuz? (e/h): ").lower()
        if proceed != 'e':
            return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Download Vosk model
    if not download_vosk_model():
        return False
    
    # Check microphone access
    check_microphone_access()
    
    print("\nKurulum tamamlandı!")
    print("Uygulamayı başlatmak için: python main.py")
    
    return True

if __name__ == "__main__":
    setup() 
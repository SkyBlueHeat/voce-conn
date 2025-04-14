import os
import sys
import requests
import zipfile
import shutil
import time

# tqdm kütüphanesini yüklü olma kontrolü
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Not: tqdm kütüphanesi bulunamadı, basit ilerleme çubuğu kullanılacak.")
    print("Gelişmiş ilerleme çubuğu için: pip install tqdm")

def simple_progress_bar(current, total, bar_length=40):
    """Basit bir ilerleme çubuğu"""
    percent = float(current) * 100 / total
    arrow = '-' * int(percent / 100 * bar_length - 1) + '>'
    spaces = ' ' * (bar_length - len(arrow))
    
    sys.stdout.write('\r[%s%s] %d%%' % (arrow, spaces, percent))
    sys.stdout.flush()
    
    if current == total:
        sys.stdout.write('\n')

def download_file(url, filename):
    """Dosya indirme fonksiyonu"""
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        
        print(f"Dosya indirilmeye başlanıyor: {filename}")
        print(f"Toplam boyut: {total_size / (1024*1024):.2f} MB")
        
        if HAS_TQDM:
            # tqdm ile ilerleme çubuğu
            with open(filename, 'wb') as f, tqdm(
                desc="İndiriliyor",
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(block_size):
                    f.write(data)
                    pbar.update(len(data))
        else:
            # Basit ilerleme çubuğu
            downloaded = 0
            start_time = time.time()
            with open(filename, 'wb') as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded += len(data)
                    
                    # Her 100KB'da bir güncelle
                    if downloaded % (block_size * 100) == 0:
                        simple_progress_bar(downloaded, total_size)
                        
                        # İndirme hızı hesapla
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            speed = downloaded / (1024 * 1024 * elapsed)
                            sys.stdout.write(f' {speed:.2f} MB/s')
                
                # Son durum
                simple_progress_bar(total_size, total_size)
                
        return True
    except Exception as e:
        print(f"İndirme hatası: {e}")
        return False

def download_vosk_model():
    """Download Vosk Turkish model"""
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-tr-0.3.zip"
    model_zip = "vosk-model-tr.zip"
    model_parent_dir = "model"
    model_dir = os.path.join(model_parent_dir, "vosk-model-small-tr")
    
    # Ensure model parent directory exists
    if not os.path.exists(model_parent_dir):
        os.makedirs(model_parent_dir)
    
    # Check if model already exists
    if os.path.exists(model_dir):
        print(f"Model klasörü '{model_dir}' zaten mevcut. İndirme işlemi atlanıyor.")
        return True
    
    print(f"Vosk Türkçe modeli indiriliyor: {model_url}")
    print("Bu işlem dosya boyutuna bağlı olarak birkaç dakika sürebilir...")
    
    try:
        # İndirme işlemi
        if not download_file(model_url, model_zip):
            return False
        
        # Extract the model
        print(f"ZIP dosyası çıkartılıyor: {model_zip}")
        with zipfile.ZipFile(model_zip, 'r') as zip_ref:
            # Get the name of the folder inside the zip
            folder_name = zip_ref.namelist()[0].split('/')[0]
            zip_ref.extractall()
        
        # Move the extracted folder to model directory
        temp_dir = folder_name
        if os.path.exists(model_dir):
            shutil.rmtree(model_dir)
        
        # Move extracted folder to model directory with correct name
        shutil.move(temp_dir, model_dir)
        
        # Remove the zip file
        os.remove(model_zip)
        
        print(f"Vosk Türkçe modeli başarıyla indirildi ve çıkartıldı: {model_dir}")
        return True
    except Exception as e:
        print(f"Hata: {e}")
        return False

if __name__ == "__main__":
    print("Vosk Türkçe Model İndirme Aracı")
    print("-" * 40)
    
    # Requests kütüphanesini kontrol et
    try:
        import requests
    except ImportError:
        print("Requests kütüphanesi bulunamadı. Yükleniyor...")
        try:
            import pip
            if hasattr(pip, 'main'):
                pip.main(['install', 'requests'])
            else:
                import pip._internal
                pip._internal.main(['install', 'requests'])
                
            # Modül yeniden yükleniyor
            import requests
            print("Requests kütüphanesi yüklendi.")
        except Exception as e:
            print(f"Requests kütüphanesi yüklenemedi: {e}")
            print("Lütfen manuel olarak yükleyin: pip install requests")
            sys.exit(1)
    
    success = download_vosk_model()
    
    if success:
        print("Model başarıyla indirildi ve kuruldu.")
    else:
        print("Model indirme işlemi başarısız oldu.")
        
    input("Devam etmek için bir tuşa basın...") 
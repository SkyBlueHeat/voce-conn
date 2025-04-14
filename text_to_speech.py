"""
Text-to-speech utilities for voice assistant with enhanced natural sounding voice using Edge TTS
"""
import os
import threading
import asyncio
import time
import random
import tempfile
import subprocess
from pathlib import Path
from dotenv import load_dotenv
import re
from threading import Thread, Event

# Edge TTS için import
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("Edge TTS kutuphanesi bulunamadi, pyttsx3 kullanilacak")

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

# Load environment variables
load_dotenv()

# Voice feedback setting
VOICE_FEEDBACK = os.getenv('VOICE_FEEDBACK', 'true').lower() == 'true'

# TTS Configuration - DuZELTME: TTS_RATE değerini guvenli bir şekilde dönuştur
try:
    rate_str = os.getenv('TTS_RATE', '0')
    # + ve % karakterlerini temizle
    rate_str = rate_str.replace('%', '').replace('+', '')
    TTS_RATE = int(rate_str)
except (ValueError, TypeError):
    print(f"TTS_RATE değeri ({os.getenv('TTS_RATE')}) int'e çevrilemedi, varsayilan değer kullaniliyor")
    TTS_RATE = 0

# Diğer TTS ayarlari
try:
    volume_str = os.getenv('TTS_VOLUME', '1.0')
    # % ve + karakterlerini kaldir
    volume_str = volume_str.replace('%', '').replace('+', '')
    volume_float = float(volume_str) / 100.0 if '%' in os.getenv('TTS_VOLUME', '') else float(volume_str)
    # 0.0 ile 1.0 arasinda olduğundan emin ol
    TTS_VOLUME = max(0.0, min(1.0, volume_float))
except (ValueError, TypeError):
    TTS_VOLUME = 1.0
    print(f"TTS_VOLUME değeri ({os.getenv('TTS_VOLUME')}) float'a çevrilemedi, varsayilan değer kullaniliyor")

TTS_ENGINE = os.getenv('TTS_ENGINE', 'edge-tts').lower()  # 'edge-tts' veya 'pyttsx3'
EDGE_TTS_VOICE = os.getenv('EDGE_TTS_VOICE', 'tr-TR-EmelNeural')  # Edge TTS için ses
EDGE_TTS_RATE = os.getenv('EDGE_TTS_RATE', '+0%')  # Normal hiz (değişim yok)
EDGE_TTS_VOLUME = os.getenv('EDGE_TTS_VOLUME', '+0%')  # Normal ses seviyesi

# Temporary directory for audio files
TEMP_DIR = os.path.join(tempfile.gettempdir(), "voce_tts_temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# Global engine and lock for thread safety
_tts_engine = None
_tts_lock = threading.RLock()
_tts_busy = False
_edge_communicate = None

# Global flag to enable detailed logging
DEBUG_TTS = False

# Doğal konuşma için rastgele konuşma kaliplari
GREETING_PHRASES = [
    "Merhaba, size nasil yardimci olabilirim?",
    "Merhaba, ne yapmak istersiniz?",
    "Dinliyorum, nasil yardimci olabilirim?",
    "Size nasil yardimci olabilirim?",
    "Sizi dinliyorum."
]

ACKNOWLEDGEMENT_PHRASES = [
    "Tamam",
    "Hemen yapiyorum",
    "Anlaşildi",
    "Hemen hallediyorum",
    "Peki",
    "Tabii"
]

COMPLETION_PHRASES = [
    "İşlem tamamlandi",
    "Hazir",
    "Tamamlandi",
    "İşlemi tamamladim",
    "Tamamdir"
]

ERROR_PHRASES = [
    "uzgunum, bunu yapamadim",
    "Maalesef bir hata oluştu",
    "Bu komutu anlamadim",
    "uzgunum, şu anda bunu yapamiyorum"
]

THINKING_PHRASES = [
    "Duşunuyorum...",
    "Bir saniye...",
    "Bakiyorum..."
]

# Temizlenecek dosya listesi
_pending_cleanup_files = []
_cleanup_thread_active = False

# Gunun saatine göre selamlama mesajlari
MORNING_GREETINGS = [
    "Gunaydin! Size nasil yardimci olabilirim?",
    "Gunaydin! Bugun size nasil yardimci olabilirim?",
    "Gunaydin! Sesli asistaniniz hizmetinizde."
]

AFTERNOON_GREETINGS = [
    "İyi gunler! Size nasil yardimci olabilirim?",
    "İyi gunler! Bugun size nasil yardimci olabilirim?",
    "İyi gunler! Sesli asistaniniz hizmetinizde."
]

EVENING_GREETINGS = [
    "İyi akşamlar! Size nasil yardimci olabilirim?",
    "İyi akşamlar! Bugun size nasil yardimci olabilirim?",
    "İyi akşamlar! Sesli asistaniniz hizmetinizde."
]

NIGHT_GREETINGS = [
    "İyi geceler! Size nasil yardimci olabilirim?",
    "Geç saatte çalişiyorsunuz! Size nasil yardimci olabilirim?",
    "İyi geceler! Sesli asistaniniz hizmetinizde."
]

# TTS motorlari için öğeler
tts_engine = None
tts_voice = None
pygame_initialized = False
temp_dir = None
shutdown_event = Event()
is_speaking = Event()

# TTS Buffer sistemi
tts_buffer = []
tts_buffer_lock = threading.Lock()
tts_buffer_thread = None
tts_buffer_running = False

def get_tts_engine():
    """
    Initialize and return TTS engine (singleton pattern)
    Edge TTS kullanilacaksa None döndurur çunku her çağrida ayri iletişim kurulur
    """
    global _tts_engine
    
    # Edge TTS için engine başlatmaya gerek yok
    if TTS_ENGINE == 'edge-tts' and EDGE_TTS_AVAILABLE:
        return None
    
    # Pyttsx3 için normal akiş
    with _tts_lock:
        if _tts_engine is None:
            try:
                import pyttsx3
                
                # Windows'ta önce SAPI5 motorunu dene (daha iyi Turkçe destek olabilir)
                if os.name == 'nt':  # Windows işletim sistemi kontrolu
                    try:
                        print("Windows SAPI5 TTS motoru deneniyor...")
                        _tts_engine = pyttsx3.init(driverName='sapi5')
                    except:
                        print("SAPI5 başlatilamadi, varsayilan motor kullaniliyor...")
                        _tts_engine = pyttsx3.init()
                else:
                    _tts_engine = pyttsx3.init()
                
                # Konuşma hizi (duşuk değer daha yavaş konuşma)
                _tts_engine.setProperty('rate', TTS_RATE)
                
                # Ses seviyesi (0.0 - 1.0)
                _tts_engine.setProperty('volume', TTS_VOLUME)
                
                # Mevcut sesleri al
                try:
                    voices = _tts_engine.getProperty('voices')
                except Exception as e:
                    print(f"Sesler alinamadi: {e}")
                    voices = []
                
                # Uygun bir ses bulup uygulamak için farkli yöntemler dene
                turkish_voice = None
                microsoft_voice = None
                female_voice = None
                best_voice = None
                
                if voices:
                    print("Mevcut TTS sesleri:")
                    for idx, voice in enumerate(voices):
                        try:
                            voice_id = getattr(voice, 'id', 'unknown_id')
                            voice_name = getattr(voice, 'name', 'unknown_name')
                            
                            voice_info = f"  {idx}: {voice_name} ({voice_id})"
                            if hasattr(voice, 'languages') and voice.languages:
                                voice_info += f" - {voice.languages}"
                            print(voice_info)
                            
                            # Varsayilan sesi en azindan kaydet
                            if best_voice is None:
                                best_voice = voice
                            
                            # Önce direkt Turkçe ses ara
                            if ('turkish' in voice_name.lower() or 
                                'turk' in voice_name.lower() or 
                                'tr-' in voice_id.lower() or 
                                'tr_' in voice_id.lower()):
                                turkish_voice = voice
                                print(f"  [Turkçe ses bulundu: {voice_name}]")
                            
                            # Sonra Microsoft sesleri için kontrol et
                            if 'microsoft' in voice_id.lower() and not microsoft_voice:
                                microsoft_voice = voice
                                if not turkish_voice:  # Turkçe ses bulunmadiysa bilgilendirme yap
                                    print(f"  [Microsoft sesi bulundu: {voice_name}]")
                            
                            # Kadin sesi ara
                            if ('female' in voice_name.lower() and 
                                not 'male' in voice_name.lower()):
                                female_voice = voice
                                
                        except Exception as ve:
                            print(f"Ses bilgisi alinamadi {idx}: {ve}")
                    
                    # Ses seçimini öncelik sirasina göre yap
                    selected_voice = turkish_voice or female_voice or microsoft_voice or best_voice
                    
                    if selected_voice:
                        try:
                            voice_id = getattr(selected_voice, 'id', None)
                            if voice_id:
                                print(f"Seçilen TTS sesi: {getattr(selected_voice, 'name', 'Bilinmeyen ses')}")
                                _tts_engine.setProperty('voice', voice_id)
                            else:
                                print(f"Seçilen sesin ID'si bulunamadi")
                        except Exception as se:
                            print(f"Ses ayarlanirken hata: {se}")
                    else:
                        print("Uygun ses bulunamadi, varsayilan ses kullaniliyor")
                else:
                    print("Mevcut sesler alinamadi, varsayilan kullanilacak")
                
                print("Sesli geri bildirim sistemi hazir.")
                
            except Exception as e:
                print(f"TTS motoru başlatilirken hata: {e}")
                _tts_engine = None
                
        return _tts_engine

async def _speak_with_edge_tts(text):
    """
    Edge TTS ile sesli konuşma gerçekleştirir
    """
    global _tts_busy
    
    try:
        # Thread guvenliği için kilitleme
        _tts_busy = True
        
        # Benzersiz bir geçici dosya adi oluştur
        temp_file = os.path.join(TEMP_DIR, f"tts_{int(time.time() * 1000)}.mp3")
        
        # Edge TTS iletişimi (communicate) ve ses dosyasi oluştur
        communicate = edge_tts.Communicate(
            text, 
            EDGE_TTS_VOICE,
            rate=EDGE_TTS_RATE,
            volume=EDGE_TTS_VOLUME
        )
        
        # Ses dosyasini oluştur
        await communicate.save(temp_file)
        print(f"Ses dosyasi oluşturuldu: {temp_file}")
        
        if DEBUG_TTS:
            print(f"[TTS] Metin: {text}")
        
        # Pygame ile ses çal - daha hizli yanit için
        try:
            if DEBUG_TTS:
                print("[TTS] Pygame ile ses çaliniyor...")
            
            # Pygame başlatilmamişsa başlat
            if not pygame.get_init():
                pygame.init()
                
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, buffer=1024, channels=1)  # Daha duşuk buffer boyutu
            
            # Ses dosyasini yukle ve çal - daha hizli yanit için
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Daha kisa bir bekleme döngusu
            max_wait = 3.0  # En fazla 3 saniye bekle
            start_time = time.time()
            
            # Sesin çalmasini bekle - daha verimli döngu
            while pygame.mixer.music.get_busy() and (time.time() - start_time < max_wait):
                await asyncio.sleep(0.05)  # Daha kisa bekleme araliği
                
            # Ses çalmayi durdur
            pygame.mixer.music.stop()
            
            if DEBUG_TTS:
                print("[TTS] Pygame ses çalma tamamlandi")
                
        except Exception as e:
            print(f"Pygame ses çalma hatasi: {e}")
            
            # Son çare - ses çalmayi atla, sadece debug göster
            print(f"[TTS] ATLANMIŞ SES: {text}")
        
        # Temizlik - daha kisa bekleme
        try:
            await asyncio.sleep(0.2)  # Çok daha kisa bekleme
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    if DEBUG_TTS:
                        print(f"[TTS] Dosya temizlendi: {temp_file}")
                except Exception as e:
                    if DEBUG_TTS:
                        print(f"[TTS] Dosya silinemiyor: {temp_file}")
                    # Dosyayi gecikmiş temizlemeye ekle
                    _schedule_cleanup(temp_file)
        except Exception as e:
            if DEBUG_TTS:
                print(f"[TTS] Dosya temizleme hatasi: {e}")
            
    except Exception as e:
        print(f"Edge TTS hatasi: {e}")
        _fallback_to_pyttsx3(text)
    finally:
        _tts_busy = False  # Kilidi kaldir - çok önemli

def _fallback_to_pyttsx3(text):
    """
    Edge TTS başarisiz olursa pyttsx3 ile konuşma yaptir
    """
    engine = get_tts_engine()
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"Pyttsx3 hatasi: {e}")

def speak_text(text, async_mode=True):
    """
    Convert text to speech
    
    Args:
        text (str): Text to speak
        async_mode (bool): If True, speech runs in a separate thread
    """
    global _tts_engine, _tts_busy
    
    # Eğer TTS meşgulse, hemen çik
    if _tts_busy:
        if DEBUG_TTS:
            print(f"[TTS] TTS meşgul olduğu için atlaniyor: {text}")
        return
    
    if not VOICE_FEEDBACK:
        print(f"[TTS] {text}")
        return
    
    # Metin ön işleme
    if not text or not isinstance(text, str):
        print(f"[TTS] Geçersiz metin: {text}")
        return
    
    # ChatGPT tarzi daha doğal cumleler kullanma
    text = add_natural_language_elements(text)
        
    # Çok uzun metinleri kisalt veya parçala
    if len(text) > 200:
        # Uzun metni cumlelere ayir
        sentences = split_into_sentences(text)
        # Her cumleyi ayri ayri söyle
        for sentence in sentences:
            # Son cumle değilse async_mode=True, son cumle ise orijinal async_mode kullan
            speak_single_text(sentence, async_mode=(async_mode if sentence == sentences[-1] else True))
        return
    else:
        # Normal uzunlukta metni doğrudan söyle
        speak_single_text(text, async_mode)
        
def speak_single_text(text, async_mode=True):
    """
    Tek bir metin parçasini TTS ile söyle
    """
    global _tts_engine, _tts_busy
    
    # Eğer TTS meşgulse, hemen çik
    if _tts_busy:
        if DEBUG_TTS:
            print(f"[TTS] TTS meşgul olduğu için atlaniyor: {text}")
        return
    
    # Turkçe karakter ve sözcuk duzeltmeleri yap
    processed_text = _normalize_turkish_text(text)
    
    # Edge TTS kullan
    if TTS_ENGINE == 'edge-tts' and EDGE_TTS_AVAILABLE:
        if async_mode:
            # Async thread oluştur
            def run_edge_tts():
                asyncio.run(_speak_with_edge_tts(processed_text))
                
            thread = threading.Thread(target=run_edge_tts)
            thread.daemon = True
            thread.start()
        else:
            # Blocking mode - sync çaliştirir
            asyncio.run(_speak_with_edge_tts(processed_text))
        return
    
    # Pyttsx3 kullan (varsayilan)
    # TTS motoru başlatilmamişsa tekrar dene
    if _tts_engine is None:
        get_tts_engine()
        
    # Hala başlatilamadiysa sadece yazdir ve çik
    if _tts_engine is None:
        print(f"[TTS Error] TTS motoru başlatilamadi: {text}")
        return
    
    # TTS motorunu kullan
    if async_mode:
        # Run in a separate thread to avoid blocking
        def speak_async():
            global _tts_busy
            try:
                # Thread-safe operation with TTS engine
                with _tts_lock:
                    # If TTS engine is busy, wait a moment or just print
                    if _tts_busy:
                        print(f"[TTS Skipped - Engine Busy] {text}")
                        return
                        
                    _tts_busy = True
                    try:
                        _tts_engine.say(processed_text)
                        _tts_engine.runAndWait()
                    except Exception as inner_e:
                        print(f"[TTS Error in engine.say/runAndWait] {inner_e}")
                        # Tekrar başlatmayi dene
                        shutdown_tts()
                        time.sleep(0.2)
                        get_tts_engine()
                    finally:
                        _tts_busy = False
            except Exception as e:
                print(f"[TTS Error in speak_async] {e}")
                
        thread = threading.Thread(target=speak_async)
        thread.daemon = True
        thread.start()
    else:
        # Blocking mode - only use this at startup or shutdown
        try:
            with _tts_lock:
                # Safe blocking call
                _tts_engine.say(processed_text)
                _tts_engine.runAndWait()
        except Exception as e:
            print(f"[TTS Error in blocking mode] {e}")
            # Tekrar başlatmayi dene
            shutdown_tts()
            time.sleep(0.2)
            get_tts_engine()

def add_natural_language_elements(text):
    """
    Metni daha doğal dil kullanimiyla zenginleştir - ChatGPT tarzi
    """
    text = text.strip()
    
    # Komut bulunamadi
    if "komut bulunamadi" in text.lower():
        return random.choice([
            "uzgunum, bu komutu taniyamadim. Başka bir şekilde ifade edebilir misiniz?",
            "Bu komutu anlayamadim. Farkli bir komut deneyin.",
            "Maalesef ne demek istediğinizi anlayamadim. Yardim için 'yardim' diyebilirsiniz."
        ])
    
    # Komut çaliştirildi
    if "komutu çaliştirildi" in text.lower():
        base_command = text.split("komutu çaliştirildi")[0].strip()
        return random.choice([
            f"{base_command} işlemi tamamlandi.",
            f"{base_command} için istediğiniz işlemi gerçekleştirdim.",
            f"{base_command} isteğiniz yerine getirildi."
        ])
    
    # Asistan kapatiliyor
    if "asistan kapatiliyor" in text.lower():
        return random.choice([
            "Göruşmek uzere, iyi gunler dilerim.",
            "Asistan kapatiliyor. Tekrar göruşmek uzere.",
            "Hoşça kalin, tekrar ihtiyaciniz olduğunda buradayim."
        ])
    
    # Asistan hazir
    if "asistan hazir" in text.lower() or "sizi dinliyorum" in text.lower():
        return random.choice(GREETING_PHRASES)
    
    # Media kontrolu
    if "muzik" in text.lower() or "video" in text.lower() or "ses" in text.lower():
        if "başlat" in text.lower() or "oynat" in text.lower():
            return random.choice([
                "Muziği başlatiyorum.",
                "Medya oynatiliyor.",
                "Tamam, başlatiyorum."
            ])
        elif "durdur" in text.lower() or "duraklat" in text.lower():
            return random.choice([
                "Muziği durdurdum.",
                "Medya duraklatildi.",
                "Tamam, durdurdum."
            ])
    
    # Standart komutu olduğu gibi birak
    return text

def split_into_sentences(text):
    """
    Uzun metni daha kisa cumlelere böl
    """
    # Noktalama işaretleriyle böl
    parts = []
    current_text = ""
    
    for sentence in text.replace('!', '.').replace('?', '?|').replace('.', '.|').split('|'):
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Cumle uzunluğu kontrolu
        if len(current_text) + len(sentence) < 150:
            if current_text:
                current_text += " " + sentence
            else:
                current_text = sentence
        else:
            parts.append(current_text)
            current_text = sentence
    
    # Son kismi ekle
    if current_text:
        parts.append(current_text)
    
    # Çok kisa bir metin varsa direkt tek parça olarak döndur
    if len(parts) == 0:
        return [text]
        
    return parts

def _normalize_turkish_text(text):
    """
    Turkçe karakterlerin doğru telaffuz edilmesi için metni duzenle
    """
    # Orijinal metni sakla
    original_text = text
    
    # Turkçe karakterlerin daha iyi telaffuzu için değişiklikler
    # Bazi karakterleri daha iyi telaffuz için başkalariyla değiştir
    replacements = {
        'ğ': 'g',        # yumuşak g -> g sesi (daha doğal)
        'Ğ': 'G',
        'ş': 'sh',       # ş -> sh sesi
        'Ş': 'Sh',
        'ç': 'ch',       # ç -> ch sesi
        'Ç': 'Ch',
        'i': 'i',        # kapali i için orijinali koruyalim
        'İ': 'i',        # buyuk i
        'ö': 'ö',        # ö sesi için orijinali koruyalim, Edge-TTS daha iyi telaffuz ediyor
        'Ö': 'Ö',
        'u': 'u',        # u sesi için orijinali koruyalim
        'u': 'u',
    }
    
    # Bazi Turkçe kelime ve ifadelerin telaffuzu iyileştirme
    # Özel kayitli cumleler - tam eşleşmeler için
    phrase_replacements = {
        "komut anlaşilamadi": "komut anlaşilamadi",
        "komut bulunamadi": "komut bulunamadi",
        "sizi dinliyorum": "sizi dinliyorum",
        "komut başariyla çaliştirildi": "komut başariyla çaliştirildi",
        "asistan kapatiliyor": "asistan kapatiliyor",
        "asistan hazir": "asistan hazir",
        "konuşma modu kapatiliyor": "konuşma modu kapatiliyor",
        "başka bir komut söyleyebilirsiniz": "başka bir komut söyleyebilirsiniz",
        "wake word moduna geçiliyor": "wake word moduna geçiliyor",
    }
    
    # Tam cumle eşleşmelerini kontrol et
    cleaned_text = text.lower().strip()
    if cleaned_text in phrase_replacements:
        return phrase_replacements[cleaned_text]
    
    # Yaygin komutlar ve kelimeler için duzeltmeler - Edge-TTS için daha az değişiklik gerekiyor,
    # sadece problemli olanlari ekleyelim
    word_replacements = {
        # Problemli sayilar
        "sifir": "sifir",
        "uç": "uç",
        "dört": "dört",
        "beş": "beş",
        "alti": "alti",
        "kirk": "kirk",
        "yuz": "yuz",
        
        # Problemli komutlar
        "başariyla": "başariyla",
        "çaliştirildi": "çaliştirildi",
        "muzik": "muzik",
        "durdur": "durdur",
        "başlat": "başlat",
        "aç": "aç",
        "artir": "artir",
        "altyazi": "altyazi"
    }
    
    # TTS motorunun kelimeler arasina boşluk koymasini sağla
    text = ' '.join(text.split())
    
    # Noktalama işaretlerinden sonra duraklatma ekle (virgul ekleyerek)
    # Bu virguller TTS motorunun daha doğal konuşmasini sağlar
    for punct in ['.', '!', '?', ';', ':']:
        text = text.replace(punct, f"{punct}, ")
    
    # Doğal konuşma için sesler arasi kuçuk boşluklar ekle
    text = insert_breathing_pauses(text)
    
    # Debug amaçli
    if os.getenv('DEBUG_MODE', 'false').lower() == 'true':
        print(f"[TTS DEBUG] Orijinal: '{original_text}' -> Duzeltilmiş: '{text}'")
        
    return text

def insert_breathing_pauses(text):
    """
    Daha doğal konuşma için nefes alma efekti olarak duraklama işaretleri ekle
    """
    # Çok kisa metinler için işlem yapma
    if len(text) < 20:
        return text
        
    # Cumleleri bölmek için noktalama işaretlerini kullan
    sentences = text.split(',')
    
    # Her 3-5 kelimeden sonra kuçuk bir duraklama ekle
    for i in range(len(sentences)):
        if i == 0:
            continue
        
        words = sentences[i].split()
        if len(words) > 4:
            # Cumle içinde uygun bir yere duraklama ekle
            insert_position = len(words) // 2
            words.insert(insert_position, ", ")
            sentences[i] = " ".join(words)
    
    return ", ".join(sentences)

def greet():
    """
    Karşilama mesaji söyle
    """
    hour = time.localtime().tm_hour
    
    if 5 <= hour < 12:
        return random.choice(MORNING_GREETINGS)
    elif 12 <= hour < 18:
        return random.choice(AFTERNOON_GREETINGS)
    elif 18 <= hour < 22:
        return random.choice(EVENING_GREETINGS)
    else: # 22-5
        return random.choice(NIGHT_GREETINGS)

def acknowledge():
    """
    Onaylama mesaji söyle
    """
    return random.choice(ACKNOWLEDGEMENT_PHRASES)

def complete():
    """
    Tamamlama mesaji söyle
    """
    return random.choice(COMPLETION_PHRASES)
    
def error():
    """
    Hata mesaji söyle
    """
    return random.choice(ERROR_PHRASES)

def thinking():
    """
    Duşunme mesaji söyle
    """
    return random.choice(THINKING_PHRASES)

def shutdown_tts():
    """Clean up TTS engine resources"""
    global _tts_engine, _tts_busy
    
    print("TTS sistemi kapatiliyor...")
    
    # TTS meşgul bayrağini temizle
    _tts_busy = False
    
    # Pygame'i kapat
    try:
        if pygame.get_init():
            try:
                if pygame.mixer.get_init():
                    try:
                        pygame.mixer.music.stop()
                    except:
                        pass
                    pygame.mixer.quit()
            except:
                pass
            pygame.quit()
    except:
        pass
    
    # Bekle
    time.sleep(0.5)
    
    # Temp dizinindeki tum geçici dosyalari temizle
    try:
        temp_files = []
        for file in os.listdir(TEMP_DIR):
            if file.startswith("tts_") and file.endswith(".mp3"):
                full_path = os.path.join(TEMP_DIR, file)
                temp_files.append(full_path)
        
        # İlk temizleme denemesi
        for file_path in temp_files:
            try:
                os.remove(file_path)
                if DEBUG_TTS:
                    print(f"[TTS] Dosya kapatilirken silindi: {file_path}")
            except:
                pass
                
        # Kisa bekleme
        time.sleep(0.2)
        
        # İkinci temizleme denemesi (daha agresif)
        for file_path in temp_files:
            if os.path.exists(file_path):
                try:
                    # Windows'ta dosya kilidini zorla kaldirmaya çaliş
                    if os.name == 'nt':
                        import subprocess
                        try:
                            subprocess.run(["taskkill", "/F", "/IM", "wmplayer.exe"], 
                                        stdout=subprocess.DEVNULL, 
                                        stderr=subprocess.DEVNULL)
                        except:
                            pass
                    
                    # Tekrar silmeyi dene
                    os.remove(file_path)
                    if DEBUG_TTS:
                        print(f"[TTS] Dosya ikinci denemede silindi: {file_path}")
                except:
                    if DEBUG_TTS:
                        print(f"[TTS] Temp dosyasi kapatma sirasinda silinemedi: {file_path}")
    except Exception as e:
        if DEBUG_TTS:
            print(f"[TTS] Temp dizini temizleme hatasi: {e}")
    
    # Pyttsx3 motorunu kapat
    with _tts_lock:
        if _tts_engine is not None:
            try:
                _tts_engine.stop()
            except:
                pass
            _tts_engine = None
    
    print("TTS sistemi kapatildi.")

def list_available_voices():
    """
    Mevcut Edge TTS seslerini listeler
    """
    if not EDGE_TTS_AVAILABLE:
        print("Edge TTS kullanilamiyor. Lutfen 'pip install edge-tts' komutu ile yukleyin.")
        return []
    
    # Edge TTS seslerini asenkron olarak listele
    async def _list_voices():
        try:
            voices = await edge_tts.list_voices()
            turkish_voices = [v for v in voices if v["Locale"].startswith("tr")]
            
            # Tum sesleri göster
            print("\nTum Edge TTS Turkçe sesleri:")
            print("-" * 50)
            for idx, voice in enumerate(turkish_voices):
                print(f"{idx+1}. {voice['ShortName']} - {voice['Gender']}")
                
            return turkish_voices
        except Exception as e:
            print(f"Edge TTS sesleri listelenirken hata: {e}")
            return []
            
    # Asenkron fonksiyonu çağir
    return asyncio.run(_list_voices())

def _schedule_cleanup(filename):
    """Daha sonra temizlenecek dosyalari planlar"""
    global _pending_cleanup_files, _cleanup_thread_active
    
    if filename not in _pending_cleanup_files:
        _pending_cleanup_files.append(filename)
    
    # Temizleme thread'i yoksa başlat
    if not _cleanup_thread_active:
        _cleanup_thread_active = True
        cleanup_thread = threading.Thread(target=_delayed_cleanup)
        cleanup_thread.daemon = True
        cleanup_thread.start()

def _delayed_cleanup():
    """Arka planda periyodik olarak geçici dosyalari temizler"""
    global _pending_cleanup_files, _cleanup_thread_active
    
    try:
        # İlk 5 saniye bekle
        time.sleep(5)
        
        # Şimdi dosyalari temizlemeyi dene
        files_to_clean = _pending_cleanup_files.copy()
        success_count = 0
        
        for file in files_to_clean:
            try:
                if os.path.exists(file):
                    os.remove(file)
                    _pending_cleanup_files.remove(file)
                    success_count += 1
                    if DEBUG_TTS:
                        print(f"[TTS] Gecikmiş temizleme: {file}")
            except:
                # Silinemeyen dosyalari listede tut
                pass
        
        # Başarisiz temizleme sayisi
        failed_count = len(_pending_cleanup_files)
        
        # Hala silinemeyen dosya varsa, biraz daha bekleyip tekrar dene
        if failed_count > 0:
            if DEBUG_TTS:
                print(f"[TTS] {success_count} dosya temizlendi, {failed_count} dosya kaldi. Tekrar deneniyor...")
            
            # Daha uzun bekle
            time.sleep(15)
            
            # İkinci deneme
            remaining_files = _pending_cleanup_files.copy()
            for file in remaining_files:
                try:
                    if os.path.exists(file):
                        os.remove(file)
                        _pending_cleanup_files.remove(file)
                        if DEBUG_TTS:
                            print(f"[TTS] Gecikmiş temizleme (2. deneme): {file}")
                except:
                    # Hala silinemeyen dosyalari logla
                    if DEBUG_TTS:
                        print(f"[TTS] Dosya israrla silinemiyor: {file}")
    except Exception as e:
        if DEBUG_TTS:
            print(f"[TTS] Gecikmiş temizleme hatasi: {e}")
    finally:
        _cleanup_thread_active = False
        
        # Hala dosya varsa, tekrar planla (ama çok sik değil)
        if _pending_cleanup_files:
            # En az 5 dosya birikirse veya 30 saniye geçtiyse tekrar temizlemeyi dene
            if len(_pending_cleanup_files) >= 5:
                _cleanup_thread_active = True
                cleanup_thread = threading.Thread(target=_delayed_cleanup)
                cleanup_thread.daemon = True
                cleanup_thread.start()
            else:
                # Az sayida dosya kaldiysa birak, programdan çikinca temizlenecek
                pass
        
        # TEMP_DIR içindeki tum eski dosyalari da temizle (10 dakikadan eski)
        try:
            current_time = time.time()
            for file in os.listdir(TEMP_DIR):
                if file.startswith("tts_") and file.endswith(".mp3"):
                    file_path = os.path.join(TEMP_DIR, file)
                    file_age = current_time - os.path.getmtime(file_path)
                    # 10 dakikadan eski dosyalari temizle
                    if file_age > 600:  # 10 dakika = 600 saniye
                        try:
                            os.remove(file_path)
                            if DEBUG_TTS:
                                print(f"[TTS] Eski dosya temizlendi: {file}")
                        except:
                            pass
        except:
            pass

if __name__ == "__main__":
    # Test TTS
    print("Testing TTS...")
    print(f"TTS_ENGINE ayari: {TTS_ENGINE}")
    print(f"EDGE_TTS_AVAILABLE: {EDGE_TTS_AVAILABLE}")
    print(f"VOICE_FEEDBACK: {VOICE_FEEDBACK}")
    print(f"EDGE_TTS_VOICE: {EDGE_TTS_VOICE}")
    
    # Turkçe Edge TTS seslerini listele
    if EDGE_TTS_AVAILABLE:
        print("\nEdge TTS kullanilabilir sesleri listeleniyor...")
        list_available_voices()
        
        # Edge TTS test
        print("\nEdge TTS test ediliyor...")
        print("Test için kisa cumle söyleniyor...")
        try:
            print("Async modda çaliştiriliyor...")
            speak_text("Merhaba, ben Edge TTS ile çalişan bir test cumlesiyim.", async_mode=True)
            print("Async mod başarili, 2 saniye bekleniyor...")
            time.sleep(2)
            
            print("Blocking modda çaliştiriliyor...")
            speak_text("Bu cumle ise blocking modda çalişiyor. Bu şekilde çalişiyor mu kontrol ediyoruz.", async_mode=False)
            print("Blocking mod başarili!")
        except Exception as e:
            print(f"Edge TTS test hatasi: {e}")
    else:
        # Pyttsx3 test
        print("\nPyttsx3 test ediliyor...")
        try:
            speak_text("Merhaba, sesli asistaniniz test ediliyor.", async_mode=False)
            print("Pyttsx3 test başarili!")
        except Exception as e:
            print(f"Pyttsx3 test hatasi: {e}")
    
    print("Test tamamlandi.")
    
    # Geçici dosyalari listele
    print("\nGeçici dosyalari kontrol ediyorum...")
    try:
        temp_files = [f for f in os.listdir(TEMP_DIR) if f.startswith("tts_")]
        print(f"Geçici dosya sayisi: {len(temp_files)}")
        if temp_files:
            print(f"Örnek geçici dosya: {temp_files[0]}")
    except Exception as e:
        print(f"Geçici dosya kontrolu hatasi: {e}")
    
    # Clean up
    print("\nKaynaklari temizliyorum...")
    shutdown_tts() 
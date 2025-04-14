import os
import json
import subprocess
import threading
import ctypes
import time
from dotenv import load_dotenv
from text_to_speech import get_tts_engine, speak_text
import win32api
import re

# Windows specific media key control
try:
    import ctypes
    SendInput = ctypes.windll.user32.SendInput
    KEYBOARD_EVENT = 1
    
    # Key code constants
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    VK_MEDIA_PLAY_PAUSE = 0xB3
    VK_MEDIA_NEXT_TRACK = 0xB0
    VK_MEDIA_PREV_TRACK = 0xB1
    
    # Windows key event flags
    KEYEVENTF_KEYUP = 0x0002
    KEYEVENTF_EXTENDEDKEY = 0x0001
    
    # Extended key codes
    VK_LEFT = 0x25
    VK_UP = 0x26
    VK_RIGHT = 0x27
    VK_DOWN = 0x28
    VK_SHIFT = 0x10
    
    # Define key mapping for letters and numbers
    KEY_MAPPING = {
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
        'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
        'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
        'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
        'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
        'z': 0x5A, '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33,
        '4': 0x34, '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38,
        '9': 0x39, '>': 0xBE, '<': 0xBC, 'tab': 0x09, 'space': 0x20,
        'enter': 0x0D, 'backspace': 0x08, 'delete': 0x2E, 'escape': 0x1B,
        'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22
    }
    
    # Türkçe karakter mappings
    TURKISH_KEY_MAPPING = {
        'ç': 0xBA,  # ç için virtual key code
        'ğ': 0xDE,  # ğ için virtual key code
        'ı': 0xDB,  # ı için virtual key code
        'ö': 0xC0,  # ö için virtual key code
        'ş': 0xDC,  # ş için virtual key code
        'ü': 0xDD,  # ü için virtual key code
        'İ': 0xDB,  # İ (büyük ı) için virtual key code - SHIFT ile kullanılır
    }
    
    # Genişletilmiş tuş haritası - daha fazla sembol ve karakter
    EXTENDED_KEY_MAPPING = {
        # Noktalama işaretleri
        '.': 0xBE,  # Nokta
        ',': 0xBC,  # Virgül
        ';': 0xBA,  # Noktalı virgül (bazı klavyelerde)
        ':': 0xBA,  # İki nokta üst üste (SHIFT + ;)
        "'": 0xDE,  # Tek tırnak
        '"': 0xDE,  # Çift tırnak (SHIFT + ')
        '/': 0xBF,  # Bölü
        '\\': 0xDC,  # Ters slash
        '[': 0xDB,  # Köşeli parantez aç
        ']': 0xDD,  # Köşeli parantez kapat
        '{': 0xDB,  # Süslü parantez aç (SHIFT + [)
        '}': 0xDD,  # Süslü parantez kapat (SHIFT + ])
        '(': 0x39,  # Parantez aç (SHIFT + 9)
        ')': 0x30,  # Parantez kapat (SHIFT + 0)
        '-': 0xBD,  # Eksi
        '_': 0xBD,  # Alt çizgi (SHIFT + -)
        '+': 0xBB,  # Artı (SHIFT + =)
        '=': 0xBB,  # Eşittir
        '`': 0xC0,  # Backtick
        '~': 0xC0,  # Tilde (SHIFT + `)
        '!': 0x31,  # Ünlem (SHIFT + 1)
        '@': 0x32,  # At işareti (SHIFT + 2)
        '#': 0x33,  # Diyez (SHIFT + 3)
        '$': 0x34,  # Dolar (SHIFT + 4)
        '%': 0x35,  # Yüzde (SHIFT + 5)
        '^': 0x36,  # Şapka (SHIFT + 6)
        '&': 0x37,  # Ve işareti (SHIFT + 7)
        '*': 0x38,  # Yıldız (SHIFT + 8)
        '?': 0xBF,  # Soru işareti (SHIFT + /)
        
        # Fonksiyon tuşları
        'f1': 0x70,
        'f2': 0x71,
        'f3': 0x72,
        'f4': 0x73,
        'f5': 0x74,
        'f6': 0x75,
        'f7': 0x76,
        'f8': 0x77,
        'f9': 0x78,
        'f10': 0x79,
        'f11': 0x7A,
        'f12': 0x7B,
        
        # Medya ve kontrol tuşları
        'volumeup': VK_VOLUME_UP,
        'volumedown': VK_VOLUME_DOWN,
        'mute': VK_VOLUME_MUTE,
        'playpause': VK_MEDIA_PLAY_PAUSE,
        'nexttrack': VK_MEDIA_NEXT_TRACK,
        'prevtrack': VK_MEDIA_PREV_TRACK,
        
        # Alt, Ctrl, Win tuşları
        'alt': 0x12,
        'ctrl': 0x11,
        'control': 0x11,
        'win': 0x5B,
        'windows': 0x5B,
        'shift': VK_SHIFT,
        
        # Diğer özel tuşlar
        'printscrn': 0x2C,
        'scrolllock': 0x91,
        'pause': 0x13,
        'break': 0x13,
        'insert': 0x2D,
        'capslock': 0x14,
        'numlock': 0x90,
    }
    
    # KEY_MAPPING'i Türkçe karakterlerle ve genişletilmiş tuşlarla birleştir
    KEY_MAPPING.update(TURKISH_KEY_MAPPING)
    KEY_MAPPING.update(EXTENDED_KEY_MAPPING)
    
    # Input structure for SendInput
    class KeyboardInput(ctypes.Structure):
        _fields_ = [
            ("wVk", ctypes.c_ushort),
            ("wScan", ctypes.c_ushort),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
        ]

    class HardwareInput(ctypes.Structure):
        _fields_ = [
            ("uMsg", ctypes.c_ulong),
            ("wParamL", ctypes.c_short),
            ("wParamH", ctypes.c_ushort)
        ]

    class MouseInput(ctypes.Structure):
        _fields_ = [
            ("dx", ctypes.c_long),
            ("dy", ctypes.c_long),
            ("mouseData", ctypes.c_ulong),
            ("dwFlags", ctypes.c_ulong),
            ("time", ctypes.c_ulong),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
        ]

    class InputUnion(ctypes.Union):
        _fields_ = [
            ("ki", KeyboardInput),
            ("mi", MouseInput),
            ("hi", HardwareInput)
        ]

    class Input(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.c_ulong),
            ("ii", InputUnion)
        ]
        
    def press_key(key_code):
        extra = ctypes.c_ulong(0)
        ii_ = InputUnion()
        ii_.ki = KeyboardInput(key_code, 0, 0, 0, ctypes.pointer(extra))
        x = Input(KEYBOARD_EVENT, ii_)
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
        
        ii_.ki = KeyboardInput(key_code, 0, 2, 0, ctypes.pointer(extra))
        x = Input(KEYBOARD_EVENT, ii_)
        SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
    
    def press_key_combination(keys):
        """Press a combination of keys in sequence or together"""
        if not keys:
            return
            
        # Split by commas to handle sequences
        key_sequences = keys.split(',')
        
        for seq in key_sequences:
            # Split by + to handle combinations
            combo = seq.strip().split('+')
            
            # Prepare keys to press down
            pressed_keys = []
            
            # Press all keys in combination
            for key_name in combo:
                key_name = key_name.strip().lower()
                if key_name in KEY_MAPPING:
                    key_code = KEY_MAPPING[key_name]
                elif key_name == 'left':
                    key_code = VK_LEFT
                elif key_name == 'right':
                    key_code = VK_RIGHT
                elif key_name == 'up':
                    key_code = VK_UP
                elif key_name == 'down':
                    key_code = VK_DOWN
                elif key_name == 'shift':
                    key_code = VK_SHIFT
                else:
                    print(f"Unknown key: {key_name}")
                    continue
                
                # Press key down
                extra = ctypes.c_ulong(0)
                ii_ = InputUnion()
                ii_.ki = KeyboardInput(key_code, 0, 0, 0, ctypes.pointer(extra))
                x = Input(KEYBOARD_EVENT, ii_)
                SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                
                pressed_keys.append(key_code)
            
            # Small delay to ensure keys are registered
            time.sleep(0.05)
            
            # Release keys in reverse order
            for key_code in reversed(pressed_keys):
                extra = ctypes.c_ulong(0)
                ii_ = InputUnion()
                ii_.ki = KeyboardInput(key_code, 0, 2, 0, ctypes.pointer(extra))
                x = Input(KEYBOARD_EVENT, ii_)
                SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
            
            # Small delay between sequences
            time.sleep(0.1)
    
    # Yeni fonksiyon: Konuşulan herhangi bir metni yazdırma
    def type_text(text):
        """Metni harf harf yazdır"""
        if not text:
            return
            
        print(f"Yazılacak metin: {text}")
        
        # Metin içindeki her karakter için
        for char in text:
            # Karakter boşluk ise space tuşuna bas
            if char == ' ':
                press_key_combination('space')
                continue
            
            # Yeni özel semboller ve özel işaretler için daha akıllı işleme
            needs_shift = False
            key_char = char.lower()
            
            # Büyük harf kontrolü
            if char.isupper():
                needs_shift = True
                
            # Shift gerektiren özel semboller kontrolü
            if char in ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '_', '+', '{', '}', '|', ':', '"', '<', '>', '?', '~']:
                needs_shift = True
                
                # Shift ile basılması gereken sembollerin alt tuşlarını bul
                if char == '!': key_char = '1'
                elif char == '@': key_char = '2'
                elif char == '#': key_char = '3'
                elif char == '$': key_char = '4'
                elif char == '%': key_char = '5'
                elif char == '^': key_char = '6'
                elif char == '&': key_char = '7'
                elif char == '*': key_char = '8'
                elif char == '(': key_char = '9'
                elif char == ')': key_char = '0'
                elif char == '_': key_char = '-'
                elif char == '+': key_char = '='
                elif char == '{': key_char = '['
                elif char == '}': key_char = ']'
                elif char == '|': key_char = '\\'
                elif char == ':': key_char = ';'
                elif char == '"': key_char = "'"
                elif char == '<': key_char = ','
                elif char == '>': key_char = '.'
                elif char == '?': key_char = '/'
                elif char == '~': key_char = '`'
            
            # Karakter KEY_MAPPING'de var mı kontrol et
            if key_char in KEY_MAPPING:
                key_code = KEY_MAPPING[key_char]
                
                if needs_shift:
                    # SHIFT tuşunu basılı tut
                    extra = ctypes.c_ulong(0)
                    ii_ = InputUnion()
                    ii_.ki = KeyboardInput(VK_SHIFT, 0, 0, 0, ctypes.pointer(extra))
                    x = Input(KEYBOARD_EVENT, ii_)
                    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                    
                    # Karakteri yaz
                    press_key(key_code)
                    
                    # SHIFT tuşunu bırak
                    ii_.ki = KeyboardInput(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
                    x = Input(KEYBOARD_EVENT, ii_)
                    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                else:
                    # Karakteri doğrudan yaz
                    press_key(key_code)
            else:
                # Önceden tanımlanmamış bir karakter, unicode değerini kullanarak yazmayı dene
                try:
                    # Alt tuşunu basılı tut
                    extra = ctypes.c_ulong(0)
                    ii_ = InputUnion()
                    ii_.ki = KeyboardInput(0x12, 0, 0, 0, ctypes.pointer(extra))  # 0x12 = ALT
                    x = Input(KEYBOARD_EVENT, ii_)
                    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                    
                    # Unicode değerine göre Alt+Numpad kombinasyonu bas
                    unicode_value = ord(char)
                    numpad_sequence = str(unicode_value)
                    
                    for digit in numpad_sequence:
                        # Numpad tuşları için keycodes: 0x60-0x69 (Numpad 0-9)
                        numpad_key = 0x60 + int(digit)
                        press_key(numpad_key)
                    
                    # Alt tuşunu bırak
                    ii_.ki = KeyboardInput(0x12, 0, KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
                    x = Input(KEYBOARD_EVENT, ii_)
                    SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))
                except Exception as e:
                    print(f"Bilinmeyen karakter yazılırken hata: {char} - {e}")
            
            # Karakterler arası kısa bir bekleme ekle
            time.sleep(0.05)
    
    HAS_MEDIA_KEYS = True
except:
    HAS_MEDIA_KEYS = False
    def press_key_combination(keys):
        print(f"Tuş simülasyonu yapılamadı: {keys}")
    
    def type_text(text):
        print(f"Metin yazdırma simülasyonu yapılamadı: {text}")

# Text to speech is handled by imported module

class CommandExecutor:
    """Command processor that responds to voice commands"""
    
    def __init__(self, debug_mode=False, execution_callback=None):
        """Initialize command executor"""
        self.debug_mode = debug_mode
        self.commands = {}
        self.categories = {}
        self.command_cache = {}  # Komut önbelleği
        self.cache_hits = 0
        self.cache_misses = 0
        self.execution_callback = execution_callback
        self.exit_requested = False
        self.use_voice_feedback = os.getenv('VOICE_FEEDBACK', 'true').lower() == 'true'
        
        # Bağlam farkındalığı için ekler
        self.current_context = {
            "active_app": None,  # Şu anda aktif olan uygulama
            "previous_command": None,  # Son çalıştırılan komut
            "last_category": None,  # Son komut kategorisi
            "last_action": None,  # Son yapılan eylem
            "fullscreen_active": False,  # Tam ekran durumu
            "media_playing": False,  # Medya oynatma durumu
            "browser_tabs": {},  # Tarayıcı sekmeleri ve içerikleri
            "command_history": []  # Son 5 komutu saklayacak liste
        }
        
        # Komutları yükle
        self._load_commands()
        
        # Initialize TTS engine if voice feedback is enabled
        if self.use_voice_feedback:
            try:
                self.tts_engine = get_tts_engine()
                if not self.tts_engine:
                    print("Warning: TTS engine initialization failed. Voice feedback disabled.")
                    self.use_voice_feedback = False
            except Exception as e:
                print(f"Error initializing TTS engine: {e}")
                self.use_voice_feedback = False
        
    def _load_commands(self):
        """Load commands from komutlar.json file"""
        try:
            with open('komutlar.json', 'r', encoding='utf-8') as f:
                self.commands = json.load(f)
            print("Commands loaded successfully")
        except Exception as e:
            print(f"Error loading commands: {e}")
            # Default empty command structure
            self.commands = {
                "uygulamalar": {},
                "sistem": {},
                "medya": {},
                "asistan": {}
            }
    
    def _find_similar_commands(self, text):
        """Benzer komutları bulan yardımcı fonksiyon"""
        similar_commands = []
        
        # Metni küçük harflere çevir ve Türkçe karakterleri standartlaştır
        normalized_text = self._normalize_turkish_text(text.lower())
        words = normalized_text.split()
        
        # Hem komut anahtarından hem de kategoriden aramak için tüm kategorileri döngüye al
        for category, commands in self.commands.items():
            for cmd_key in commands:
                normalized_cmd = self._normalize_turkish_text(cmd_key.lower())
                
                # Kelime bazlı eşleşme puanı hesapla
                score = 0
                cmd_words = normalized_cmd.split()
                
                # Her kelime için puan ver
                for word in words:
                    if word in normalized_cmd:
                        score += 1
                    # Kelime benzerliği için kısmi eşleşme
                    else:
                        for cmd_word in cmd_words:
                            if len(word) > 3 and len(cmd_word) > 3:
                                # En az 3 karakter benzerliği aranıyor
                                if word[:3] == cmd_word[:3]:
                                    score += 0.5
                                    break
                
                # Puanı kelime sayısına göre normalize et
                if len(words) > 0:
                    normalized_score = score / len(words)
                    
                    # Belirli bir eşik değerini geçen komutları ekle
                    if normalized_score > 0.5:
                        similar_commands.append((normalized_score, f"{category}: {cmd_key}"))
        
        # Puanlara göre sırala ve sadece komut metinlerini döndür
        return [cmd for _, cmd in sorted(similar_commands, key=lambda x: x[0], reverse=True)]
    
    def _normalize_turkish_text(self, text):
        """Türkçe metni normalleştir - arama için karakterleri standartlaştır"""
        text = text.lower()
        # Türkçe karakterleri İngilizce karşılıklarına dönüştür (arama için)
        replace_map = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'â': 'a', 'î': 'i', 'û': 'u'
        }
        for tr_char, en_char in replace_map.items():
            text = text.replace(tr_char, en_char)
        return text
        
    def find_matching_command(self, text):
        """Find a matching command for the given text"""
        # Önce tam komut eşleşmesi ara
        for category, commands in self.commands.items():
            for cmd_key, cmd_action in commands.items():
                if cmd_key.lower() == text.lower():
                    return category, cmd_key, cmd_action
        
        # Komut içerisinde arama yap
        best_match = None
        best_match_len = 0
        best_match_category = None
        best_match_action = None
        
        text_lower = text.lower()
        
        # Özel durum: "X için arama yap" formülündeki komutlar
        search_markers = ["ara", "arama yap", "bul", "göster"]
        search_command = None
        search_category = None
        search_query = None
        
        for marker in search_markers:
            if marker in text_lower:
                # Metni parçalara ayırarak arama sorgusunu ve komut kısmını tespit et
                parts = text_lower.split(marker, 1)
                if len(parts) == 2:
                    before_marker = parts[0].strip()
                    after_marker = parts[1].strip()
                    
                    # Arama komutunu belirle
                    for category, commands in self.commands.items():
                        if category == "web":
                            for cmd_key, cmd_action in commands.items():
                                if marker in cmd_key:
                                    # Arama kategorisini ve ne aramalı belirlemeye çalış
                                    if before_marker:
                                        if before_marker in cmd_key:
                                            search_command = cmd_key
                                            search_category = category
                                            search_query = after_marker
                                            break
                                    else:
                                        # Genel arama komutu
                                        if "google" in cmd_key or "internette" in cmd_key:
                                            search_command = cmd_key
                                            search_category = category
                                            search_query = after_marker
                                            break
                            
                            if search_command:
                                break
        
        # Eğer arama komutu tespit edildiyse, onu kullan
        if search_command and search_category and search_query:
            cmd_action = self.commands[search_category][search_command]
            # Özel arama URL'sini oluştur
            import urllib.parse
            search_encoded = urllib.parse.quote(search_query)
            
            # URL sonunda "?q=" varsa oraya ekle, yoksa "?q=" ekleyip öyle ekle
            if "?q=" in cmd_action:
                new_action = cmd_action.split("?q=")[0] + "?q=" + search_encoded
            else:
                new_action = cmd_action + search_encoded
                
            return search_category, search_command, new_action
        
        # Normal komut eşleşmesi için devam et
        for category, commands in self.commands.items():
            for cmd_key, cmd_action in commands.items():
                cmd_key_lower = cmd_key.lower()
                
                # Check if command key is in the text
                if cmd_key_lower in text_lower:
                    # Find the longest matching command
                    if len(cmd_key) > best_match_len:
                        best_match = cmd_key
                        best_match_len = len(cmd_key)
                        best_match_category = category
                        best_match_action = cmd_action
                
                # Medya komutları için özel eşleşme: "filmi duraklat" -> "duraklat"
                elif category in ["medya", "netflix", "youtube"]:
                    # Ekstraktif eşleşme yap, metinde komutun her kelimesi varsa eşleştir
                    cmd_words = cmd_key_lower.split()
                    # Kelimelerin büyük çoğunluğu varsa eşleşme kabul et
                    matches = sum(1 for word in cmd_words if word in text_lower)
                    match_ratio = matches / len(cmd_words) if cmd_words else 0
                    
                    # Eğer komutun çoğu kelimesi varsa ve mevcut en iyi eşleşmeden daha uzunsa
                    if match_ratio > 0.7 and len(cmd_key) > best_match_len:
                        best_match = cmd_key
                        best_match_len = len(cmd_key)
                        best_match_category = category
                        best_match_action = cmd_action
        
        # Eğer eşleşme bulunamazsa, kelime benzerliğini dene
        if not best_match:
            # Metnin kelimelerini al
            text_words = text_lower.split()
            
            for category, commands in self.commands.items():
                for cmd_key, cmd_action in commands.items():
                    cmd_key_lower = cmd_key.lower()
                    cmd_words = cmd_key_lower.split()
                    
                    # Ortak kelime sayısı
                    common_words = len(set(text_words) & set(cmd_words))
                    
                    # Metindeki ve komuttaki kelime sayısına göre oran
                    if common_words > 0:
                        match_ratio = common_words / len(cmd_words)
                        
                        # En az %50 oranda kelime eşleşmesi olmalı
                        if match_ratio >= 0.5 and len(cmd_key) > best_match_len:
                            best_match = cmd_key
                            best_match_len = len(cmd_key)
                            best_match_category = category
                            best_match_action = cmd_action
        
        # Return the best match if found
        if best_match:
            return best_match_category, best_match, best_match_action
        else:
        return None, None, None
    
    def execute(self, recognized_text):
        """Execute a recognized command"""
        if not recognized_text:
            return False
            
        # Komut geçmişine ekle (en fazla 5 komut saklansın)
        self.current_context["command_history"].insert(0, recognized_text)
        if len(self.current_context["command_history"]) > 5:
            self.current_context["command_history"].pop()
            
        # Çıkış komutları kontrolü
        exit_commands = ["çık", "kapat", "programı kapat", "asistanı kapat", "uygulamayı kapat", "exit", "quit"]
        for cmd in exit_commands:
            if cmd in recognized_text.lower():
                print("Çıkış komutu algılandı. Program kapatılıyor...")
            if self.use_voice_feedback:
                    speak_text("Asistan kapatılıyor")
                self.exit_requested = True
                return True
        
        # Özel kontroller
        if "konuşma modu" in recognized_text.lower() and "kapat" in recognized_text.lower():
            print("Konuşma modu kapatılıyor...")
            return True
            
        # Önce önbellekte komut var mı kontrol et
        if recognized_text in self.command_cache:
            self.cache_hits += 1
            if self.debug_mode:
                print(f"Önbellek kullanılıyor: {recognized_text}")
            category, cmd_key, cmd_action = self.command_cache[recognized_text]
            return self._execute_command(category, cmd_key, cmd_action, recognized_text)
            
        self.cache_misses += 1
            
        # Komutu bul ve yürüt
        category, cmd_key, cmd_action = self.find_matching_command(recognized_text)
                
        if not category or not cmd_key or not cmd_action:
            # Bağlam tabanlı akıllı karar verme
            if self._try_context_based_execution(recognized_text):
            return True
            
            # Benzer komutları bul
            similar_commands = self._find_similar_commands(recognized_text)
            if similar_commands and self.debug_mode:
                print("Benzer komutlar bulundu:")
                for sim_cmd in similar_commands[:3]:
                    print(f" - {sim_cmd}")
                    
                if self.use_voice_feedback:
                speak_text("Bu komutu anlamadım")
            return False
            
        # Önbelleğe ekle
        self.command_cache[recognized_text] = (category, cmd_key, cmd_action)
        
        # Komutu yürüt
        return self._execute_command(category, cmd_key, cmd_action, recognized_text)
    
    def _execute_command(self, category, cmd_key, cmd_action, original_text):
        """Execute a command with the given parameters and update context"""
        try:
            # Bağlam bilgisini güncelle
            self.current_context["previous_command"] = original_text
            self.current_context["last_category"] = category
            self.current_context["last_action"] = cmd_action
            
            # Komut gerçekleştirme kategoriye göre farklılaşabilir
            result = False
            
            # Tarayıcı sekmesi komutu ise bağlam güncellemesi yap
            if category == "chrome" and "sekme" in cmd_key.lower():
                # Tab numarasını belirle
                tab_match = re.search(r'(\d+)', cmd_key)
                if tab_match:
                    tab_number = int(tab_match.group(1))
                    self.current_context["browser_tabs"]["active_tab"] = tab_number
                
            # Medya tuşu ve tam ekran takibi
            if cmd_action == "mediaplaypause":
                self.current_context["media_playing"] = not self.current_context["media_playing"]
            elif "simulateKey:f" in cmd_action:
                self.current_context["fullscreen_active"] = not self.current_context["fullscreen_active"]
                
            # Uygulama başlatma durumunda aktif uygulamayı güncelle
            if category == "uygulamalar" and "aç" in cmd_key:
                app_name = cmd_key.replace(" aç", "")
                self.current_context["active_app"] = app_name
                
            # Medya key komutları için
            if category == "medya" or cmd_action in ["volumeup", "volumedown", "volumemute"]:
                result = self._handle_media_command(cmd_action)
                time.sleep(0.7)  # Medya komutları sonrası bekle
                        if self.use_voice_feedback:
                    speak_text(f"{cmd_key} komutu çalıştırıldı")
                        return result
            
            # Chrome sekme komutları
            if category == "chrome" and cmd_action.startswith("noop+simulateKey:"):
                keys = cmd_action.replace("noop+simulateKey:", "")
                if self.debug_mode:
                    print(f"Chrome sekme komutunu çalıştırıyorum: {keys}")
                
                        press_key_combination(keys)
                        time.sleep(0.5)
                
                if self.execution_callback:
                    self.execution_callback(True, "Sekme değiştirildi")
                
                if self.use_voice_feedback:
                    speak_text(f"{cmd_key} komutu uygulandı")
                
                return True
                
            # Normal sistem komutları
            result = self._execute_system_command(cmd_action)
            time.sleep(0.5)
            
            if self.use_voice_feedback:
                speak_text(f"{cmd_key} komutu çalıştırıldı")
            return result
                
        except Exception as e:
            print(f"Komut çalıştırılırken hata: {e}")
            if self.execution_callback:
                self.execution_callback(False, f"Hata: {str(e)}")
            if self.use_voice_feedback:
                speak_text("Komut çalıştırılırken bir hata oluştu")
            return False
    
    def _try_context_based_execution(self, text):
        """Bağlam bilgisine göre komutları akıllıca yorumla"""
        try:
            # Tam ekran ile ilgili komutlar
            if "tam ekran" in text.lower():
                if "çık" in text.lower() or "kapat" in text.lower():
                    if self.current_context["fullscreen_active"]:
                        # Tam ekrandan çıkma işlemi - 'f' tuşu ile
                        press_key_combination("f")
                        self.current_context["fullscreen_active"] = False
                        speak_text("Tam ekrandan çıkıldı")
                        return True
                elif self.current_context["active_app"] in ["chrome", "netflix", "youtube"]:
                    # Tam ekran yapma işlemi
                    press_key_combination("f")
                    self.current_context["fullscreen_active"] = True
                    speak_text("Tam ekran yapıldı")
                    return True
            
            # Sekme ile ilgili komutlar
            if "sekme" in text.lower():
                tab_match = re.search(r'(\d+)', text)
                if tab_match:
                    tab_number = int(tab_match.group(1))
                    if 0 < tab_number < 10:  # 1-9 arası sekmelere geçiş
                        press_key_combination(f"ctrl+{tab_number}")
                        self.current_context["browser_tabs"]["active_tab"] = tab_number
                        speak_text(f"Sekme {tab_number}'e geçildi")
                        return True
            
            # "Filmi/videoyu başlat" gibi medya komutları
            if any(word in text.lower() for word in ["film", "video", "dizi"]) and any(word in text.lower() for word in ["başlat", "oynat", "devam"]):
                press_key_combination("space")  # Space tuşu genellikle oynat/duraklat işlevi görür
                self.current_context["media_playing"] = True
                speak_text("Medya başlatıldı")
                return True
                
            # "Filmi/videoyu durdur" gibi medya komutları
            if any(word in text.lower() for word in ["film", "video", "dizi"]) and any(word in text.lower() for word in ["durdur", "duraklat", "dur"]):
                press_key_combination("space")
                self.current_context["media_playing"] = False
                speak_text("Medya duraklatıldı")
                return True
                
            # Önceki komut bağlamını kullan
            if self.current_context["last_category"] and "tekrar" in text.lower():
                # Önceki komutu tekrar çalıştır
                prev_cmd = self.current_context["previous_command"]
                if prev_cmd:
                    speak_text(f"Son komutu tekrarlıyorum: {prev_cmd}")
                    return self.execute(prev_cmd)
                    
            return False
            
        except Exception as e:
            print(f"Bağlam tabanlı yürütme hatası: {e}")
            return False
    
    def _handle_media_command(self, cmd_action):
        """Handle media key commands with more reliable execution"""
        try:
            if cmd_action == "volumeup":
                for _ in range(3):  # 3 kez basarak daha belirgin artış sağla
                    win32api.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                    time.sleep(0.05)
                    win32api.keybd_event(VK_VOLUME_UP, 0, KEYEVENTF_KEYUP, 0)
                    time.sleep(0.1)
            elif cmd_action == "volumedown":
                for _ in range(3):  # 3 kez basarak daha belirgin azalış sağla
                    win32api.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                    time.sleep(0.05)
                    win32api.keybd_event(VK_VOLUME_DOWN, 0, KEYEVENTF_KEYUP, 0)
                    time.sleep(0.1)
            elif cmd_action == "volumemute":
                win32api.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(VK_VOLUME_MUTE, 0, KEYEVENTF_KEYUP, 0)
            elif cmd_action == "mediaplaypause":
                # Sadece medya tuşunu kullanarak play/pause fonksiyonu
                win32api.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(VK_MEDIA_PLAY_PAUSE, 0, KEYEVENTF_KEYUP, 0)
                # Space tuşu kullanımı kaldırıldı - soruna neden oluyordu
            elif cmd_action == "medianext":
                win32api.keybd_event(VK_MEDIA_NEXT_TRACK, 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(VK_MEDIA_NEXT_TRACK, 0, KEYEVENTF_KEYUP, 0)
            elif cmd_action == "mediaprevious":
                win32api.keybd_event(VK_MEDIA_PREV_TRACK, 0, 0, 0)
                time.sleep(0.05)
                win32api.keybd_event(VK_MEDIA_PREV_TRACK, 0, KEYEVENTF_KEYUP, 0)
            
            if self.execution_callback:
                self.execution_callback(True, "Medya komutu uygulandı")
            
            # Medya komutları sonrası biraz daha bekleyerek uygulamaların yanıt vermesine izin ver
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"Medya komutu işlenirken hata: {e}")
            if self.execution_callback:
                self.execution_callback(False, f"Hata: {str(e)}")
            return False
    
    def _execute_system_command(self, command):
        """Execute a system command using subprocess"""
        try:
            # Run the command in a separate thread to avoid blocking
            def run_command():
                # Platform-specific settings to hide console window
                if os.name == 'nt':  # Windows
                    try:
                        # Windows-specific: Hide console window
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                        startupinfo.wShowWindow = 0  # SW_HIDE
                        
                        subprocess.Popen(
                            command, 
                            shell=True,
                            startupinfo=startupinfo,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                    except Exception as e:
                        print(f"Windows-specific Popen failed: {e}")
                        # Fallback to normal Popen
                        subprocess.Popen(command, shell=True)
                else:
                    # For other platforms
                    subprocess.Popen(command, shell=True)
                
            threading.Thread(target=run_command, daemon=True).start()
            
            if self.execution_callback:
                self.execution_callback(True, "Komut çalıştırıldı")
            return True
        except Exception as e:
            print(f"Sistem komutu çalıştırılırken hata: {e}")
            return False
    
    def print_cache_stats(self):
        """Print cache statistics"""
        total = self.cache_hits + self.cache_misses
        if total > 0:
            hit_rate = (self.cache_hits / total) * 100
            print(f"Önbellek istatistikleri: {self.cache_hits} hit, {self.cache_misses} miss, {hit_rate:.1f}% hit rate")
            print(f"Önbellek boyutu: {len(self.command_cache)} komut")
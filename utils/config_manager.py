"""
Konfigürasyon Yöneticisi
"""
import os
import json
from dotenv import load_dotenv, set_key

class ConfigManager:
    """
    Sesli asistan için ayarları yöneten sınıf
    .env dosyasıyla etkileşim kurar
    """
    def __init__(self, env_file=".env", commands_file="komutlar.json"):
        """
        Konfigürasyon yöneticisini başlatır
        
        Args:
            env_file: .env dosya yolu
            commands_file: komutlar.json dosya yolu
        """
        self.env_file = env_file
        self.commands_file = commands_file
        
        # Varsayılan ayarları yükle
        load_dotenv(self.env_file)
        
        # Komutları yükle
        self.commands = self._load_commands()
        
    def get_setting(self, key, default=None):
        """
        .env'den bir ayar değeri alır
        
        Args:
            key: Ayar anahtarı
            default: Değer bulunamazsa dönecek varsayılan değer
        
        Returns:
            Ayar değeri veya default değeri
        """
        value = os.getenv(key, default)
        return value
        
    def save_setting(self, key, value):
        """
        .env dosyasına bir ayar değeri kaydeder
        
        Args:
            key: Ayar anahtarı
            value: Ayar değeri
            
        Returns:
            bool: İşlem başarılı mı?
        """
        try:
            # .env dosyasına yaz
            set_key(self.env_file, key, str(value))
            return True
        except Exception as e:
            print(f"Ayar kaydedilemedi: {e}")
            return False
    
    def get_all_settings(self):
        """
        Tüm ayarları sözlük olarak döndürür
        
        Returns:
            dict: Tüm ayar anahtar-değer çiftleri
        """
        settings = {}
        for key in ["WAKE_WORD", "VOICE_FEEDBACK", "TTS_ENGINE", 
                    "EDGE_TTS_VOICE", "EDGE_TTS_RATE", "EDGE_TTS_VOLUME", 
                    "DEBUG_MODE", "CONVERSATION_TIMEOUT"]:
            settings[key] = self.get_setting(key)
        return settings
    
    def _load_commands(self):
        """
        Komutlar dosyasını yükler
        
        Returns:
            dict: Komutlar sözlüğü
        """
        try:
            with open(self.commands_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Komutlar yüklenemedi: {e}")
            return {
                "uygulamalar": {},
                "sistem": {},
                "medya": {},
                "asistan": {}
            }
            
    def get_all_commands(self):
        """
        Tüm komutları kategorilere göre döndürür
        
        Returns:
            dict: Komutlar
        """
        return self.commands
        
    def get_commands_by_category(self, category):
        """
        Belirli kategorideki komutları döndürür
        
        Args:
            category: Komut kategorisi (uygulamalar, sistem, medya, asistan)
        
        Returns:
            dict: Kategorideki komutlar
        """
        if category in self.commands:
            return self.commands[category]
        return {} 
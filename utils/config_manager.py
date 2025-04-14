"""
Konfigurasyon Yöneticisi
"""
import os
import json
from dotenv import load_dotenv, set_key

class ConfigManager:
    """
    Sesli asistan için ayarlari yöneten sinif
    .env dosyasiyla etkileşim kurar
    """
    def __init__(self, env_file=".env", commands_file="komutlar.json"):
        """
        Konfigurasyon yöneticisini başlatir
        
        Args:
            env_file: .env dosya yolu
            commands_file: komutlar.json dosya yolu
        """
        self.env_file = env_file
        self.commands_file = commands_file
        
        # Varsayilan ayarlari yukle
        load_dotenv(self.env_file)
        
        # Komutlari yukle
        self.commands = self._load_commands()
        
    def get_setting(self, key, default=None):
        """
        .env'den bir ayar değeri alir
        
        Args:
            key: Ayar anahtari
            default: Değer bulunamazsa dönecek varsayilan değer
        
        Returns:
            Ayar değeri veya default değeri
        """
        value = os.getenv(key, default)
        return value
        
    def save_setting(self, key, value):
        """
        .env dosyasina bir ayar değeri kaydeder
        
        Args:
            key: Ayar anahtari
            value: Ayar değeri
            
        Returns:
            bool: İşlem başarili mi?
        """
        try:
            # .env dosyasina yaz
            set_key(self.env_file, key, str(value))
            return True
        except Exception as e:
            print(f"Ayar kaydedilemedi: {e}")
            return False
    
    def get_all_settings(self):
        """
        Tum ayarlari sözluk olarak döndurur
        
        Returns:
            dict: Tum ayar anahtar-değer çiftleri
        """
        settings = {}
        for key in ["WAKE_WORD", "VOICE_FEEDBACK", "TTS_ENGINE", 
                    "EDGE_TTS_VOICE", "EDGE_TTS_RATE", "EDGE_TTS_VOLUME", 
                    "DEBUG_MODE", "CONVERSATION_TIMEOUT"]:
            settings[key] = self.get_setting(key)
        return settings
    
    def _load_commands(self):
        """
        Komutlar dosyasini yukler
        
        Returns:
            dict: Komutlar sözluğu
        """
        try:
            with open(self.commands_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Komutlar yuklenemedi: {e}")
            return {
                "uygulamalar": {},
                "sistem": {},
                "medya": {},
                "asistan": {}
            }
            
    def get_all_commands(self):
        """
        Tum komutlari kategorilere göre döndurur
        
        Returns:
            dict: Komutlar
        """
        return self.commands
        
    def get_commands_by_category(self, category):
        """
        Belirli kategorideki komutlari döndurur
        
        Args:
            category: Komut kategorisi (uygulamalar, sistem, medya, asistan)
        
        Returns:
            dict: Kategorideki komutlar
        """
        if category in self.commands:
            return self.commands[category]
        return {} 
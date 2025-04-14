import os
import struct
import wave
import pvporcupine
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv

class WakeWordListener:
    def __init__(self, wake_detected_callback):
        load_dotenv()
        
        self.wake_word = os.getenv('WAKE_WORD', 'jarvis')
        self.sensitivity = float(os.getenv('SENSITIVITY', '0.5'))
        self.access_key = os.getenv('PORCUPINE_ACCESS_KEY', '')
        self.wake_detected_callback = wake_detected_callback
        self.is_listening = False
        self.porcupine = None
        self.audio_stream = None
        
    def initialize(self):
        """Initialize Porcupine wake word detection engine"""
        try:
            if not self.access_key:
                print("Erişim anahtarı bulunamadı. Lütfen .env dosyasında PORCUPINE_ACCESS_KEY ayarını yapın.")
                print("Ücretsiz bir anahtar almak için: https://console.picovoice.ai/")
                return False
            
            print(f"Porcupine başlatılıyor: keyword={self.wake_word}, access_key={self.access_key[:5]}...")
            
            # Try to create Porcupine with the provided keyword
            try:
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=[self.wake_word],
                    sensitivities=[self.sensitivity]
                )
                print("Porcupine başarıyla oluşturuldu.")
            except Exception as e:
                # If that fails, try with known keywords
                print(f"Standart wake word ile denenirken hata: {e}")
                print("Alternatif anahtar kelimeleri deneniyor...")
                
                # List all available keywords
                available_keywords = pvporcupine.KEYWORDS
                print(f"Kullanılabilir anahtar kelimeler: {available_keywords}")
                
                if self.wake_word not in available_keywords:
                    print(f"'{self.wake_word}' mevcut anahtar kelimeler arasında değil.")
                    print(f"'picovoice' anahtar kelimesini kullanılıyor...")
                    self.wake_word = 'picovoice'
                
                self.porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=[self.wake_word],
                    sensitivities=[self.sensitivity]
                )
                print(f"Porcupine '{self.wake_word}' anahtar kelimesi ile oluşturuldu.")
            
            # Audio stream parameters
            self.sample_rate = self.porcupine.sample_rate
            self.frame_length = self.porcupine.frame_length
            
            return True
        except Exception as e:
            print(f"Porcupine initialization error: {e}")
            print("Detaylı hata bilgisi:", repr(e))
            return False
            
    def start_listening(self):
        """Start listening for wake words in the background"""
        if self.porcupine is None and not self.initialize():
            return False
            
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio stream status: {status}")
                return
                
            # Convert audio data to the format Porcupine expects
            pcm = np.frombuffer(indata, dtype=np.int16)
            
            # Process audio frame with Porcupine
            keyword_index = self.porcupine.process(pcm)
            
            # If wake word detected
            if keyword_index >= 0:
                print(f"Wake word detected! ('{self.wake_word}')")
                self.wake_detected_callback()
        
        try:
            self.audio_stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                blocksize=self.frame_length,
                callback=audio_callback
            )
            
            self.audio_stream.start()
            self.is_listening = True
            print(f"Anahtar kelime dinleniyor: '{self.wake_word}'...")
            return True
        except Exception as e:
            print(f"Error starting audio stream: {e}")
            self.cleanup()
            return False
            
    def stop_listening(self):
        """Stop listening for wake words"""
        self.is_listening = False
        self.cleanup()
        
    def cleanup(self):
        """Clean up resources"""
        if self.audio_stream is not None:
            self.audio_stream.stop()
            self.audio_stream.close()
            self.audio_stream = None
            
        if self.porcupine is not None:
            self.porcupine.delete()
            self.porcupine = None 
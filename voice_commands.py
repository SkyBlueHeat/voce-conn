import os
import sys
import time
import logging
from datetime import datetime
import speech_recognition as sr
from command_executor import CommandExecutor

class VoiceCommandListener:
    """Listens for voice commands and executes them"""
    
    def __init__(self, debug_mode=False, microphone_index=None):
        """Initialize voice recognition with fallback options"""
        # Setup logging
        self._setup_logging()
        
        self.debug_mode = debug_mode
        self.recognizer = sr.Recognizer()
        self.command_executor = CommandExecutor(debug_mode)
        self.is_running = False
        self.recognizer.dynamic_energy_threshold = True
        self.microphone_index = microphone_index
        
        # Read settings from environment
        self.language = os.getenv('LISTEN_LANGUAGE', 'tr-TR')
        self.energy_threshold = int(os.getenv('ENERGY_THRESHOLD', '300'))
        self.pause_threshold = float(os.getenv('PAUSE_THRESHOLD', '0.8'))
        self.recognizer.energy_threshold = self.energy_threshold 
        self.recognizer.pause_threshold = self.pause_threshold
        self.dictation_mode = False

        # Log initialization
        self.logger.info("Voice Command Listener initialized")
        self.logger.info(f"Language: {self.language}")
        self.logger.info(f"Energy threshold: {self.energy_threshold}")
        self.logger.info(f"Pause threshold: {self.pause_threshold}")
        
    def _setup_logging(self):
        """Setup logging to file and console"""
        self.logger = logging.getLogger('voice_commands')
        self.logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Log file with timestamp
        log_filename = f"logs/voice_commands_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Format for log messages
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    @staticmethod
    def list_microphones():
        """List all available microphones with their indices"""
        mics = []
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            mics.append((index, name))
            print(f"Mikrofon {index}: {name}")
        return mics
        
    def select_microphone(self, index=None):
        """Select a specific microphone by index"""
        try:
            self.microphone_index = index
            if index is not None:
                mic = sr.Microphone(device_index=index)
                print(f"Mikrofon seçildi: {sr.Microphone.list_microphone_names()[index]}")
                self.logger.info(f"Selected microphone index {index}: {sr.Microphone.list_microphone_names()[index]}")
                return mic
            else:
                print("Varsayilan mikrofon kullaniliyor")
                self.logger.info("Using default microphone")
                return sr.Microphone()
        except Exception as e:
            print(f"Mikrofon seçilirken hata oluştu: {e}")
            self.logger.error(f"Error selecting microphone: {e}")
            print("Varsayilan mikrofon kullaniliyor")
            self.logger.info("Falling back to default microphone")
            self.microphone_index = None
            return sr.Microphone()
    
    def toggle_dictation_mode(self):
        """Toggle dictation mode for longer text input"""
        self.dictation_mode = not self.dictation_mode
        mode_str = "enabled" if self.dictation_mode else "disabled"
        self.logger.info(f"Dictation mode {mode_str}")
        print(f"Dictation mode {mode_str}")
        # Dictation mode açikken daha uzun duraklamalara izin ver
        if self.dictation_mode:
            self.recognizer.pause_threshold = 1.5  # Dictation için daha uzun duraklama
        else:
            self.recognizer.pause_threshold = self.pause_threshold  # Normal moda dön
        return True
        
    def write_dictation(self):
        """Handle the 'Write what I say' command for dictating long texts at once"""
        print("Söylediğinizi yaziyorum. Lutfen konuşmaya başlayin...")
        self.logger.info("Starting 'Write what I say' dictation mode")
        
        try:
            with self.select_microphone(self.microphone_index) as source:
                print("Dinliyorum... (Bitirmek için en az 2 saniye sessiz kalin)")
                # Dictation için daha uzun bir dinleme suresi ve duraklama
                orig_pause = self.recognizer.pause_threshold
                self.recognizer.pause_threshold = 2.0  # Longer pause for dictation end detection
                
                audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=None)
                
                # Pause threshold'i geri al
                self.recognizer.pause_threshold = orig_pause
                
                try:
                    # Recognize the dictated text
                    recognized_text = self.recognizer.recognize_google(audio, language=self.language)
                    print(f"Yazdirilacak metin: {recognized_text}")
                    self.logger.info(f"Dictating full text: {recognized_text}")
                    
                    # Type the recognized text
                    from command_executor import type_text
                    type_text(recognized_text)
                    return True
                except sr.UnknownValueError:
                    print("Söylediğinizi anlayamadim.")
                    self.logger.warning("Could not understand dictation")
                    return False
                except sr.RequestError as e:
                    print(f"Ses tanima servisi şu anda kullanilamiyor: {e}")
                    self.logger.error(f"Dictation request error: {e}")
                    return False
        except Exception as e:
            print(f"Dictation error: {e}")
            self.logger.error(f"Dictation error: {e}")
            return False

    def speak_typed_text(self):
        """Reads back text that has been typed or copied to the clipboard"""
        try:
            import pyperclip
            from text_to_speech import speak_text
            
            print("Yazdiğiniz/kopyaladiğiniz metni okuyorum...")
            self.logger.info("Starting 'Speak what I type' functionality")
            
            # Get text from clipboard
            clipboard_text = pyperclip.paste()
            
            if not clipboard_text or clipboard_text.strip() == "":
                print("Clipboard'da okunacak metin bulunamadi.")
                self.logger.warning("No text found in clipboard to speak")
                return False
                
            print(f"Okunan metin: {clipboard_text}")
            self.logger.info(f"Speaking text from clipboard: {clipboard_text}")
            
            # Kullanilan projenin kendi TTS modulunu kullanalim - daha uyumlu olacaktir
            speak_text(clipboard_text)
            
            return True
        except ImportError as e:
            print(f"Gerekli moduller yuklu değil: {e}")
            self.logger.error(f"Required modules not installed: {e}")
            print("pyperclip modulunu yuklemek için: pip install pyperclip")
            return False
        except Exception as e:
            print(f"Metin okuma hatasi: {e}")
            self.logger.error(f"Text-to-speech error: {e}")
            return False
        
    def listen(self):
        """Main loop to listen for voice commands"""
        self.is_running = True
        self.logger.info("Starting voice command listener")
        
        # Hata sayisi ve bekletme surelerini izlemek için değişkenler
        consecutive_errors = 0
        max_consecutive_errors = 5  # Bu sayidan fazla arka arkaya hata olursa yeniden başlat
        error_backoff_time = 0.1    # Başlangiç bekleme suresi
        max_backoff_time = 5.0      # Maksimum bekleme suresi
        
        try:
            # Use selected or default microphone
            with self.select_microphone(self.microphone_index) as source:
                print("Adjusting for ambient noise... Please wait.")
                self.logger.info("Adjusting for ambient noise")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print(f"Ambient energy threshold: {self.recognizer.energy_threshold}")
                print("Listening for commands...")
                
                while self.is_running:
                    try:
                        # Önce mikrofonun hazir olduğundan emin olalim
                        if source is None:
                            self.logger.error("Microphone source is None. Recreating microphone.")
                            source = self.select_microphone(self.microphone_index)
                            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        
                        # İyileştirilmiş dinleme
                        try:
                            audio = self.recognizer.listen(source, timeout=None)
                        except Exception as listen_error:
                            self.logger.error(f"Error during listening: {listen_error}")
                            consecutive_errors += 1
                            time.sleep(min(error_backoff_time * consecutive_errors, max_backoff_time))
                            continue
                        
                        # Google Speech Recognition
                        recognized_text = self.recognizer.recognize_google(audio, language=self.language)
                        
                        # Başarili tanima, hata sayacini sifirla
                        consecutive_errors = 0
                        
                        if self.debug_mode:
                            print(f"Recognized: {recognized_text}")
                        self.logger.info(f"Recognized: {recognized_text}")
                        
                        # Check for dictation mode toggle command
                        if "dikte moduna geç" in recognized_text.lower() or "dikte modu başlat" in recognized_text.lower():
                            self.toggle_dictation_mode()
                            continue
                            
                        if "dikte modunu kapat" in recognized_text.lower() or "dikte bitir" in recognized_text.lower():
                            if self.dictation_mode:
                                self.toggle_dictation_mode()
                            continue
                        
                        # Check for "Write what I say" command
                        if "söylediğimi yaz" in recognized_text.lower() or "ne dersem yaz" in recognized_text.lower() or "yazdir" in recognized_text.lower():
                            self.write_dictation()
                            continue
                            
                        # Check for "Speak what I type" command
                        if "yazdiğimi oku" in recognized_text.lower() or "metni oku" in recognized_text.lower() or "yazdiklarimi seslendir" in recognized_text.lower():
                            self.speak_typed_text()
                            continue
                            
                        # If in dictation mode, handle continuous text input
                        if self.dictation_mode:
                            print(f"Yazdirilacak metin: {recognized_text}")
                            self.logger.info(f"Dictating: {recognized_text}")
                            # Burada metni CommandExecutor uzerinden yazdirma işlemi yapiliyor
                            # CommandExecutor'daki type_text fonksiyonunu doğrudan çağiriyoruz
                            # Bu, klavye simulasyonu ile metni yazacak
                            try:
                                from command_executor import type_text
                                type_text(recognized_text)
                                time.sleep(0.5)  # Biraz bekleme
                            except Exception as e:
                                self.logger.error(f"Error in dictation typing: {e}")
                                print(f"Metin yazilirken hata: {e}")
                            continue
                        
                        # Process regular commands
                        try:
                            result = self.command_executor.execute(recognized_text)
                            
                            # Check if exit was requested
                            if self.command_executor.exit_requested:
                                print("Exiting voice command listener...")
                                self.logger.info("Exit requested by command")
                                self.is_running = False
                                break
                        except Exception as cmd_error:
                            self.logger.error(f"Command execution error: {cmd_error}")
                            print(f"Komut çaliştirilirken hata: {cmd_error}")
                            consecutive_errors += 1
                            
                    except sr.UnknownValueError:
                        if self.debug_mode:
                            print("Could not understand audio")
                        continue
                    except sr.RequestError as e:
                        self.logger.error(f"Request error: {e}")
                        print(f"Could not request results; {e}")
                        consecutive_errors += 1
                        # Kademeli bekleme
                        time.sleep(min(error_backoff_time * consecutive_errors, max_backoff_time))
                        continue
                    except Exception as e:
                        self.logger.error(f"Error processing command: {e}")
                        print(f"Error processing command: {e}")
                        consecutive_errors += 1
                        # Kademeli bekleme
                        time.sleep(min(error_backoff_time * consecutive_errors, max_backoff_time))
                        continue
                    
                    # Arka arkaya çok fazla hata olursa yeniden başlat
                    if consecutive_errors >= max_consecutive_errors:
                        self.logger.warning(f"Too many consecutive errors ({consecutive_errors}). Reinitializing...")
                        print(f"Çok fazla arka arkaya hata oluştu. Mikrofon yeniden başlatiliyor...")
                        # Mikrofonla ilgili sorun olabilir, yeniden başlat
                        break
        
        except KeyboardInterrupt:
            print("\nStopping voice command listener...")
            self.logger.info("Stopped by user (KeyboardInterrupt)")
            self.is_running = False
        except Exception as e:
            print(f"Error in voice command listener: {e}")
            self.logger.error(f"Fatal error: {e}")
            self.is_running = False
        
        # Aşiri hata durumunda recursive olarak yeniden başlatma
        if consecutive_errors >= max_consecutive_errors and self.is_running:
            print("Yeniden başlatiliyor...")
            self.logger.info("Restarting voice command listener after errors")
            time.sleep(1)  # Kisa bir bekleme
            return self.listen()  # Recursive olarak yeniden başlat
            
        return 0
        
    def stop(self):
        """Stop the voice command listener"""
        self.is_running = False
        self.logger.info("Voice command listener stopped")

# Run standalone
if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    
    # Check if user wants to list microphones
    if "--list-mics" in sys.argv:
        VoiceCommandListener.list_microphones()
        sys.exit(0)
    
    # Check if a specific microphone is requested
    mic_index = None
    for arg in sys.argv:
        if arg.startswith("--mic="):
            try:
                mic_index = int(arg.split("=")[1])
                print(f"Using microphone with index: {mic_index}")
            except (ValueError, IndexError):
                print("Invalid microphone index format. Use --mic=NUMBER")
                sys.exit(1)
    
    listener = VoiceCommandListener(debug_mode, mic_index)
    sys.exit(listener.listen()) 
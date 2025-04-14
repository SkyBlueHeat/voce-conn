import os
import sys
import threading
import time
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY_ICON = True
except ImportError:
    print("Tray icon support not available - pystray or PIL is missing")
    HAS_TRAY_ICON = False

from command_executor import CommandExecutor
from command_listener import CommandListener
from dotenv import load_dotenv
from text_to_speech import speak_text, get_tts_engine, shutdown_tts, acknowledge, thinking, complete, error, greet
from wake_word_detector import PicoWakeWordDetector

# Load environment variables
load_dotenv()

class VoiceAssistant:
    def __init__(self, microphone_index=None):
        # Configuration from environment
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.wake_word = os.getenv('WAKE_WORD', 'picovoice')
        self.conversation_timeout = int(os.getenv('CONVERSATION_TIMEOUT', '60'))
        self.voice_feedback = os.getenv('VOICE_FEEDBACK', 'true').lower() == 'true'
        
        # Microphone selection
        self.microphone_index = microphone_index
        if self.microphone_index is not None:
            try:
                self.microphone_index = int(self.microphone_index)
                print(f"Using microphone index: {self.microphone_index}")
            except ValueError:
                print(f"Invalid microphone index: {self.microphone_index}. Using default.")
                self.microphone_index = None
        
        # State variables
        self.running = False
        self.conversation_active = False
        self.conversation_end_time = None
        self.timer_thread = None
        self.timer_running = False
        self.exit_requested = False
        
        # Components
        self.command_executor = None
        self.command_listener = None
        self.wake_detector = None
        self.icon = None
        self.icon_thread = None
        
        # Initialize TTS
        if self.voice_feedback:
            try:
                engine = get_tts_engine()
                if engine:
                    print("Sesli geri bildirim sistemi hazir.")
                    speak_text("Sesli asistan başlatiliyor", async_mode=False)
            except Exception as e:
                print(f"TTS initialization error: {e}")
                
    def _on_wake_word_detected(self):
        """Called when wake word is detected"""
        print(f"UYANDIRMA KELİMESİ ALGILANDI: '{self.wake_word}'")
        if self.wake_detector:
            self.wake_detector.stop()
        
        # Visual feedback
        print("Dinleme başlatiliyor...")
        
        # Create custom greeting message - SADECE BİR KEZ
        if not self.conversation_active:
            speak_text(greet())
        
        # Start conversation mode
        self.conversation_active = True
        
        # Start command listener
        self._restart_command_listener()
        
        # Start timer for conversation mode
        self._reset_conversation_timer()
    
    def _reset_conversation_timer(self):
        """Reset the conversation timer"""
        self.conversation_end_time = time.time() + self.conversation_timeout
        
        # Start timer display thread if not running
        if not self.timer_running:
            self.timer_running = True
            if self.timer_thread and self.timer_thread.is_alive():
                return
                
            self.timer_thread = threading.Thread(target=self._display_timer)
            self.timer_thread.daemon = True
            self.timer_thread.start()
    
    def _display_timer(self):
        """Display the remaining time in the conversation mode"""
        try:
            while self.timer_running and self.conversation_active:
                if not self.conversation_end_time:
                    time.sleep(0.5)
                    continue
                    
                remaining = max(0, int(self.conversation_end_time - time.time()))
                
                # Display time at intervals
                if remaining in [45, 30, 15, 10, 5]:
                    print(f"Konuşma modu: {remaining} saniye kaldi")
                
                # Check if timer expired
                if remaining <= 0:
                    print("\nKonuşma suresi doldu. Wake word moduna geçiliyor...")
                    speak_text("Konuşma modu kapatiliyor")
                    self._conversation_timeout()
                    break
                    
                time.sleep(1)
                
            self.timer_running = False
        except Exception as e:
            print(f"Timer error: {e}")
            self.timer_running = False
            
    def _conversation_timeout(self):
        """Called when conversation mode times out"""
        if not self.conversation_active:
            return
            
        # Önce durumu değiştir
        self.conversation_active = False
        self.timer_running = False
        
        # Konuşma modunun bittiğini bildir
        print("\nKonuşma suresi doldu. Wake word moduna geçiliyor...")
        speak_text("Konuşma modu kapatiliyor")
        
        # Stop command listener if active
        if self.command_listener and self.command_listener.is_listening:
            self.command_listener.stop_listening()
            time.sleep(0.5)  # Dinleyici kapanmasi için bekle
        
        # Wake word dedektörunu durdur ve tekrar başlat (sifirlama için)
        if self.wake_detector:
            # Önce tamamen kapat
            if hasattr(self.wake_detector, 'running') and self.wake_detector.running:
                self.wake_detector.stop()
                time.sleep(1)  # Dedektörun tamamen durmasi için bekle
                
            # Sonra tekrar başlat
            if self.running:
                self.wake_detector.start()
                
                # Asistanin hazir olduğunu bildir
                print("\n========== Asistan Hazir ==========")
                print(f">> '{self.wake_word}' diyerek asistani aktifleştirebilirsiniz.")
    
    def _start_command_listener(self):
        """Start the command listener"""
        # Mevcut dinleyiciyi durdur
        if self.command_listener and self.command_listener.is_listening:
            self.command_listener.stop_listening()
            time.sleep(0.5)  # Bekle ve mevcut işlemin durmasini sağla
        
        # Command listener'i sifirla, yeni bir tane oluştur
        from command_listener import CommandListener
        self.command_listener = CommandListener(self._on_command_detected, microphone_index=self.microphone_index)
        
        print("Konuşma modu aktif! Komutlarinizi söyleyebilirsiniz...")
        self.command_listener.start_listening()
    
    def _restart_command_listener(self):
        """Restart command listener with a small delay"""
        # Daha uzun bekle
        time.sleep(0.5)  # Önceki komutun tamamen işlenmesi için daha kisa bekle
        
        if self.conversation_active:
            # Arka arkaya konuşma sorunu için sadece bir kez 'sizi dinliyorum' de
            speak_text("Sizi dinliyorum")
            self._start_command_listener()
    
    def _on_command_detected(self, text):
        """Called when a command is detected"""
        # Process command in a separate thread to avoid UI blocking
        if not text:
            return
        
        # Detected command
        detected_command = text.strip()
        print(f"Algilanan komut: '{detected_command}'")
        
        # Create a new thread for processing the command
        def process_command():
            # Mevcut dinleyiciyi durdur
            if self.command_listener and self.command_listener.is_listening:
                self.command_listener.stop_listening()
            
            try:
                # Daha doğal bir yanit ver - rastgele onaylama kalibi söyle (sadece bir kez)
                speak_text(acknowledge())
                
                if self.debug_mode:
                    print(f"Komut işleniyor: {detected_command}")
                
                # Try to execute the command
                result = self.command_executor.execute(detected_command)
                
                # Check if a command was recognized and executed
                category, cmd_key, _ = self.command_executor.find_matching_command(detected_command)
                
                if self.command_executor.exit_requested:
                    self.stop()
                    return
                
                # If a command was found and executed
                if category and cmd_key:
                    print(f"Komut başariyla çaliştirildi: {cmd_key}")
                    
                    # Check if the command is to exit conversation mode
                    if category == "asistan" and "konuşma modu" in cmd_key:
                        speak_text("Konuşma modu kapatiliyor. Wake word bekleniyor...")
                        print("Konuşma modu kapatiliyor. Wake word bekleniyor...")
                        self.conversation_active = False
                        self.timer_running = False
                        
                        # Stop command listener if active
                        if self.command_listener and self.command_listener.is_listening:
                            self.command_listener.stop_listening()
                            time.sleep(0.5)  # Dinleyici kapanmasi için bekle
                        
                        # Wake word dedektörunu durdur ve tekrar başlat (sifirlama için)
                        if self.wake_detector:
                            # Önce tamamen kapat
                            if hasattr(self.wake_detector, 'running') and self.wake_detector.running:
                                self.wake_detector.stop()
                                time.sleep(1)  # Dedektörun tamamen durmasi için bekle
                                
                            # Sonra tekrar başlat
                            if self.running:
                                self.wake_detector.start()
                                
                                # Asistanin hazir olduğunu bildir
                                print("\n========== Asistan Hazir ==========")
                                print(f">> '{self.wake_word}' diyerek asistani aktifleştirebilirsiniz.")
                        return
                    
                    # Çok kisa bir bekleme - daha hizli yanit için
                    if category == "medya":
                        time.sleep(0.3)  # Medya komutlari için kisa bekle
                    elif category == "chrome":
                        # Chrome sekme geçişleri için biraz daha uzun bekle
                        # Bu sayede sekme değiştirdikten sonra komutlar çalişacak
                        time.sleep(1.0)  # Sekme geçişleri için daha uzun bekleme
                        print("Sekme değiştirildi, hazirlaniyor...")
                
                # Reset timer and restart command listener
                if self.conversation_active:
                    self._reset_conversation_timer()
                    
                    # Başka bir komut için dinlemeyi başlat
                    self._restart_command_listener()
                
            except Exception as e:
                print(f"Command execution error: {e}")
                # Konuşma dinleme tekrar aktif edilsin
                if self.conversation_active:
                    self._restart_command_listener()
        
        # Thread çaliştir
        command_thread = threading.Thread(target=process_command)
        command_thread.daemon = True
        command_thread.start()
        
        return True
    
    def _on_execution_callback(self, success, message):
        """Called after command execution"""
        if self.debug_mode:
            print(f"Command execution: {'Success' if success else 'Failed'} - {message}")
    
    def create_tray_icon(self):
        """Create system tray icon"""
        if not HAS_TRAY_ICON:
            print("Tray icon not available - running without system tray icon")
            return False
            
        try:
            # Create a simple icon
            icon_image = self._create_icon_image()
            
            # Create menu
            menu = (
                pystray.MenuItem(f"Listening for: {self.wake_word}", lambda: None, enabled=False),
                pystray.MenuItem('Exit', self.stop)
            )
            
            # Create icon
            self.icon = pystray.Icon("voice_assistant", icon_image, "Ses Asistani", menu)
            
            # Run icon in a separate thread
            self.icon_thread = threading.Thread(target=self.icon.run)
            self.icon_thread.daemon = True
            self.icon_thread.start()
            return True
        except Exception as e:
            print(f"Error creating tray icon: {e}")
            return False
    
    def _create_icon_image(self):
        """Create a simple icon image"""
        if not HAS_TRAY_ICON:
            return None
            
        width = 64
        height = 64
        color1 = (34, 177, 76)  # green
        color2 = (0, 162, 232)  # blue
        
        image = Image.new('RGB', (width, height), (0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Draw a simple microphone-like icon
        dc.rectangle((16, 8, 48, 24), fill=color1)
        dc.rectangle((26, 24, 38, 48), fill=color1)
        dc.ellipse((20, 48, 44, 56), fill=color2)
        
        return image
    
    def start(self):
        """Start the voice assistant"""
        self.running = True
        print("============================================================")
        print("Kişisel Sesli Asistan - Uzaktan Kontrol Versiyonu")
        print("============================================================")
        print(f"Mikrofonunuz: {'Varsayilan' if self.microphone_index is None else f'Index {self.microphone_index}'}")
        print(f"1. Asistani aktifleştirmek için '{self.wake_word}' deyin (buyuk/kuçuk harf önemli değil)")
        print(f"2. Komutlarinizi söyleyin. Aktif dinleme suresi: {self.conversation_timeout} saniye")
        print("   Bazi örnek komutlar:")
        print("   - Chrome aç")
        print("   - YouTube aç")
        print("   - Ses seviyesini artir")
        print("   - Muziği durdur/başlat")
        print("   - Netflix'te diziyi durdur")
        print("   - 10 saniye ileri sar")
        print("   - Altyazilari göster")
        print("3. Her komuttan sonra 60 saniyelik sure yeniden başlar")
        print("4. Konuşma modundan çikmak için 'konuşma modunu kapat' deyin")
        print("5. Uygulamadan çikmak için 'çik' veya 'kapat' deyin")
        print()
        
        print("Sesli asistan başlatiliyor...")
        
        # Ses sistemini test et
        if self.voice_feedback:
            print("TTS sistemini test ediyorum...")
            try:
                speak_text("Merhaba, Komutlarinizi dinlemeye hazirim.", async_mode=False)
                time.sleep(1)
                print("TTS sistemi çalişiyor.")
            except Exception as e:
                print(f"TTS sistemi test edilirken hata: {e}")
                print("TTS sistemi devre dişi birakiliyor...")
                self.voice_feedback = False
        
        # Initialize command executor
        self.command_executor = CommandExecutor(
            debug_mode=self.debug_mode,
            execution_callback=self._on_execution_callback
        )
        
        # Create wake word detector
        self.wake_detector = PicoWakeWordDetector(self._on_wake_word_detected)
        
        # Start tray icon if available
        if HAS_TRAY_ICON:
            self.create_tray_icon()
        
        # Start wake word detector
        self.wake_detector.start()
        
        # Wait for exit request
        try:
            print("\n========== Asistan Hazir ==========")
            print(f">> '{self.wake_word}' diyerek asistani aktifleştirebilirsiniz.")
            print(">> Çikmak için Ctrl+C tuşlarina basin.\n")
            
            while not self.exit_requested:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nKullanici tarafindan kapatiliyor...")
        finally:
            self.stop()
            
        return 0
    
    def stop(self):
        """Stop voice assistant"""
        print("Sesli asistan durduruluyor...")
        self.running = False
        self.exit_requested = True
        self.conversation_active = False
        self.timer_running = False
        
        # Stop wake word detector
        if self.wake_detector:
            self.wake_detector.stop()
            
        # Stop command listener if active
        if self.command_listener and self.command_listener.is_listening:
            self.command_listener.stop_listening()
            
        # Stop system tray icon
        if self.icon:
            try:
                self.icon.stop()
            except:
                pass
            
        print("Sesli asistan durduruldu")
        speak_text("Sesli asistan kapatiliyor", async_mode=False)
        
        # Clean up TTS resources
        shutdown_tts()

if __name__ == "__main__":
    # Parse command line arguments
    microphone_index = None
    for arg in sys.argv:
        if arg.startswith("--mic="):
            microphone_index = arg.replace("--mic=", "")
            break
    
    # List microphones if requested
    if "--list-mics" in sys.argv:
        try:
            import speech_recognition as sr
            print("\nKullanilabilir Mikrofonlar:")
            for idx, name in enumerate(sr.Microphone.list_microphone_names()):
                print(f"{idx}: {name}")
            sys.exit(0)
        except Exception as e:
            print(f"Mikrofonlar listelenirken hata oluştu: {e}")
            sys.exit(1)
    
    # Create and start the voice assistant
    assistant = VoiceAssistant(microphone_index)
    sys.exit(assistant.start()) 
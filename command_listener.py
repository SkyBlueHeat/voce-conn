"""
Command listener module for voice assistant
"""
import os
import time
import threading
try:
    import speech_recognition as sr
    HAS_SPEECH_RECOGNITION = True
except ImportError as e:
    print(f"Error importing speech_recognition: {e}")
    print("\nÖNEMLİ: Ses tanıma modülünü yüklemek için lütfen:")
    print("install_dependencies.bat dosyasını tekrar çalıştırın.\n")
    HAS_SPEECH_RECOGNITION = False

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CommandListener:
    """
    Listen for voice commands
    """
    def __init__(self, callback=None, lang="tr-TR", microphone_index=None):
        """
        Initialize command listener
        
        Args:
            callback: Function to call when a command is detected
            lang: Language for speech recognition
            microphone_index: Index of the microphone to use
        """
        self.callback = callback
        self.lang = lang
        self.is_listening = False
        self.thread = None
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.microphone_index = microphone_index
        
        # Try to convert microphone_index to int if it's a string
        if self.microphone_index is not None:
            try:
                self.microphone_index = int(self.microphone_index)
                if self.debug_mode:
                    print(f"Command listener using microphone index: {self.microphone_index}")
            except ValueError:
                print(f"Invalid microphone index: {self.microphone_index}. Using default.")
                self.microphone_index = None
        
        # Fallback mode
        self.use_fallback_mode = not HAS_SPEECH_RECOGNITION
        
        if not self.use_fallback_mode:
            # Initialize recognizer
            try:
                self.recognizer = sr.Recognizer()
                self.recognizer.energy_threshold = int(os.getenv('ENERGY_THRESHOLD', '300'))
                self.recognizer.dynamic_energy_threshold = True
                self.recognizer.pause_threshold = 0.8
                
                # Adjust for ambient noise to improve recognition
                try:
                    with sr.Microphone(device_index=self.microphone_index) as source:
                        if self.debug_mode:
                            print("Adjusting for ambient noise...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                        if self.debug_mode:
                            print(f"Energy threshold: {self.recognizer.energy_threshold}")
                except Exception as e:
                    print(f"Error adjusting for ambient noise: {e}")
                    self.use_fallback_mode = True
            except Exception as e:
                print(f"Error initializing speech recognition: {e}")
                self.use_fallback_mode = True
        
        if self.use_fallback_mode:
            print("\n!!! FALLBACK MODE ACTIVE: Using text input instead of speech recognition !!!")
            print("Type your commands in the console when prompted.")
            print("To fix speech recognition, run install_dependencies.bat again.\n")
    
    def start_listening(self):
        """Start listening for commands"""
        if self.is_listening:
            print("Already listening for commands")
            return False
            
        self.is_listening = True
        self.thread = threading.Thread(target=self._listen_thread)
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def stop_listening(self):
        """Stop listening for commands"""
        if not self.is_listening:
            return True
            
        self.is_listening = False
        
        # Thread'in durmasını bekle
        if self.thread and self.thread.is_alive():
            self.thread.join(1.0)  # En fazla 1 saniye bekle
            
        # Thread'i sıfırla
        self.thread = None
        
        if self.debug_mode:
            print("Command listening stopped")
            
        return True
    
    def _listen_thread(self):
        """Thread function to listen for commands"""
        if self.use_fallback_mode:
            self._fallback_listen_thread()
            return
        
        # Dinleme işlemi başlamadan önce biraz bekle
        time.sleep(0.5)
            
        while self.is_listening:
            try:
                # Use microphone as source with the specified index
                with sr.Microphone(device_index=self.microphone_index) as source:
                    if self.debug_mode:
                        print("Listening for command...")
                        
                    # Listen for speech
                    audio = self.recognizer.listen(source, 
                                                  timeout=5, 
                                                  phrase_time_limit=10)
                    
                    # Dinleme durmuşsa hemen çık
                    if not self.is_listening:
                        break
                        
                    if self.debug_mode:
                        print("Processing speech...")
                    
                    # Try to recognize speech
                    try:
                        # Google Speech Recognition
                        text = self.recognizer.recognize_google(audio, language=self.lang)
                        
                        if self.debug_mode:
                            print(f"Recognized: {text}")
                        
                        # Dinleme durmuşsa komut çağrılmasın
                        if not self.is_listening:
                            break
                            
                        # Call callback with recognized text
                        if self.callback and text:
                            # Callback fonksiyonunu farklı bir thread'de çağır
                            def safe_callback():
                                try:
                                    self.callback(text)
                                except Exception as cb_error:
                                    print(f"Error in command callback: {cb_error}")
                            
                            callback_thread = threading.Thread(target=safe_callback, daemon=True)
                            callback_thread.start()
                            
                    except sr.UnknownValueError:
                        if self.debug_mode:
                            print("Could not understand audio")
                    except sr.RequestError as e:
                        print(f"Google Speech Recognition service error: {e}")
                
            except Exception as e:
                print(f"Error in command listening: {e}")
                time.sleep(0.5)  # Short delay to prevent tight loop on error
                
            # Small delay to prevent CPU usage spikes
            time.sleep(0.1)
        
        if self.debug_mode:
            print("Command listening thread exiting")
            
    def _fallback_listen_thread(self):
        """Fallback method that uses console input instead of speech recognition"""
        print("\nFALLBACK MODE: Please type your commands")
        print("Type 'exit' to quit listening mode\n")
        
        while self.is_listening:
            try:
                text = input("Command > ")
                
                if text.lower() in ["exit", "quit", "çık", "çıkış"]:
                    if self.callback:
                        self.callback("exit")
                    break
                
                # Call callback with entered text
                if self.callback and text:
                    self.callback(text)
                    
            except Exception as e:
                print(f"Error in fallback command input: {e}")
                
            time.sleep(0.1)
        
        print("Fallback listening mode stopped")
            
if __name__ == "__main__":
    # Test the command listener
    def on_command(text):
        print(f"Command detected: {text}")
        if text.lower() == "exit":
            listener.stop_listening()
    
    listener = CommandListener(on_command)
    if listener.use_fallback_mode:
        print("Starting command listener test in FALLBACK mode. Type your commands...")
    else:
        print("Starting command listener test. Say something...")
    listener.start_listening()
    
    try:
        while listener.is_listening:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping...")
        listener.stop_listening() 
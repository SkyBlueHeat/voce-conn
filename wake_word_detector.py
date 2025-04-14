"""
Wake word detection module using Porcupine
"""
import os
import time
import threading
try:
    import struct
    import pyaudio
    HAS_AUDIO_SUPPORT = True
except ImportError as e:
    print(f"Error importing audio support: {e}")
    HAS_AUDIO_SUPPORT = False

try:
    import pvporcupine
    HAS_PORCUPINE = True
    print(f"Available wake words: {pvporcupine.KEYWORDS}")
except ImportError as e:
    print(f"Error importing pvporcupine: {e}")
    print("\nÖNEMLİ: Wake word detection modulunu yuklemek için lutfen:")
    print("install_dependencies.bat dosyasini tekrar çaliştirin.\n")
    HAS_PORCUPINE = False

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PicoWakeWordDetector:
    """
    Detects wake words using Picovoice Porcupine
    """
    def __init__(self, detection_callback=None):
        """
        Initialize the wake word detector
        
        Args:
            detection_callback: Function to call when wake word is detected
        """
        self.detection_callback = detection_callback
        self.running = False
        self.thread = None
        self.audio_stream = None
        self.audio_interface = None
        
        # Configuration from environment
        self.wake_word = os.getenv('WAKE_WORD', 'jarvis').lower()
        self.sensitivity = float(os.getenv('SENSITIVITY', '0.75'))
        self.access_key = os.getenv('PORCUPINE_ACCESS_KEY', 'Tawvv+6qt9lBeAKKK4TM2wMqzw2oirKK+0rX5J4e7ykyZJ54FoAk4Q==')
        
        # Fallback mode
        self.use_fallback_mode = not (HAS_AUDIO_SUPPORT and HAS_PORCUPINE)
        
        # Initialize Porcupine
        self.porcupine = None
        if not self.use_fallback_mode:
            self._check_porcupine()
        
        if self.use_fallback_mode:
            print("\n!!! FALLBACK MODE ACTIVE: Using text input for wake word !!!")
            print("Type your wake word in the console when prompted.")
            print("To fix wake word detection, run install_dependencies.bat again.\n")
        
    def _check_porcupine(self):
        """Check if Porcupine is available and initialize it"""
        try:
            # Verify wake word is in available keywords
            if self.wake_word not in pvporcupine.KEYWORDS:
                print(f"Warning: '{self.wake_word}' is not in Porcupine's built-in keywords.")
                print(f"Available keywords: {pvporcupine.KEYWORDS}")
                print(f"Defaulting to 'jarvis' as wake word")
                self.wake_word = 'jarvis'
            
            # Try pvporcupine new API style first (v3+)
            print(f"Initializing Porcupine v3+ with wake word: '{self.wake_word}', sensitivity: {self.sensitivity}")
            self.porcupine = pvporcupine.create(
                access_key=self.access_key,
                keywords=[self.wake_word],
                sensitivities=[self.sensitivity]
            )
            print(f"Porcupine v3+ initialized successfully")
            return True
        except Exception as e1:
            print(f"Error initializing Porcupine v3+: {e1}")
            try:
                # Try older API style as fallback (v2)
                print("Trying Porcupine v2 as fallback...")
                from pvporcupine import create
                self.porcupine = create(
                    access_key=self.access_key,
                    keywords=[self.wake_word],
                    sensitivities=[self.sensitivity]
                )
                print(f"Porcupine v2 initialized with wake word: '{self.wake_word}'")
                return True
            except Exception as e2:
                print(f"Error initializing Porcupine v2: {e2}")
                print("Could not initialize Porcupine. Using fallback mode.")
                self.use_fallback_mode = True
                return False
        
    def start(self):
        """Start wake word detection"""
        # Önceki çalişan bir instance varsa temizle
        if self.running:
            self.stop()
            time.sleep(0.5)  # Dedektörun tam olarak kapanmasi için bekle
        
        # Porcupine engine'i tekrar başlat
        if not self.use_fallback_mode and not self.porcupine:
            self._check_porcupine()
        
        self.running = True
        
        # Start detection in a separate thread
        self.thread = threading.Thread(target=self._detection_thread)
        self.thread.daemon = True
        self.thread.start()
        
        if self.use_fallback_mode:
            print(f"Wake word detector started in FALLBACK MODE - type '{self.wake_word}' to activate")
        else:
            print(f"Wake word detector started, listening for '{self.wake_word}'")
        return True
        
    def stop(self):
        """Stop wake word detection"""
        if not self.running:
            return False
            
        # Önce durum değişkenini guncelle
        self.running = False
        
        # Thread'i bekle
        if self.thread and self.thread.is_alive():
            try:
                # Thread'e join at ama bloke etme
                self.thread.join(timeout=1.0)
            except:
                pass
        
        # Kaynaklari temizle
        if not self.use_fallback_mode:
            if self.audio_stream:
                try:
                    self.audio_stream.stop_stream()
                    self.audio_stream.close()
                except:
                    pass
                self.audio_stream = None
                
            if self.audio_interface:
                try:
                    self.audio_interface.terminate()
                except:
                    pass
                self.audio_interface = None
                
            if self.porcupine:
                try:
                    self.porcupine.delete()
                except:
                    pass
                self.porcupine = None
            
        print("Wake word detector stopped")
        return True
        
    def _detection_thread(self):
        """Thread for wake word detection"""
        if self.use_fallback_mode:
            self._fallback_detection_thread()
            return
            
        try:
            # Initialize audio
            self.audio_interface = pyaudio.PyAudio()
            
            # Get sample rate and frame length from porcupine
            sample_rate = getattr(self.porcupine, 'sample_rate', 16000)
            frame_length = getattr(self.porcupine, 'frame_length', 512)
            
            self.audio_stream = self.audio_interface.open(
                rate=sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=frame_length,
                stream_callback=self._audio_callback
            )
            
            self.audio_stream.start_stream()
            
            # Keep thread alive while running
            while self.running:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error in detection thread: {e}")
            print("Switching to fallback mode...")
            self.use_fallback_mode = True
            self._fallback_detection_thread()
            
    def _fallback_detection_thread(self):
        """Fallback method using console input instead of audio detection"""
        print("\nFALLBACK MODE ACTIVE: Using text input for wake word detection")
        print(f"Type '{self.wake_word}' to activate the assistant")
        print("Type 'exit' to quit\n")
        
        while self.running:
            try:
                text = input("> ")
                
                if text.lower() == "exit":
                    print("Exiting wake word detection...")
                    self.running = False
                    break
                    
                if text.lower() == self.wake_word.lower():
                    print(f"Wake word '{self.wake_word}' detected!")
                    
                    # Call detection callback
                    if self.detection_callback:
                        threading.Thread(target=self.detection_callback).start()
                        
            except Exception as e:
                print(f"Error in fallback detection: {e}")
                time.sleep(0.5)
                
            time.sleep(0.1)
            
    def _audio_callback(self, in_data, frame_count, time_info, status_flags):
        """Handle audio data from stream"""
        if not self.running or not self.porcupine:
            return (b'', pyaudio.paContinue)
            
        try:
            pcm = struct.unpack_from("h" * self.porcupine.frame_length, in_data)
            
            # Different versions of Porcupine have different method names
            if hasattr(self.porcupine, 'process'):
                # v2+
                result = self.porcupine.process(pcm)
            elif hasattr(self.porcupine, 'process_frame'):
                # v1
                result = self.porcupine.process_frame(pcm)
            else:
                print("Unknown Porcupine API - can't process audio")
                return (b'', pyaudio.paContinue)
            
            # If wake word detected (result is the index of detected keyword or -1)
            if result >= 0:
                print(f"Wake word '{self.wake_word}' detected with confidence index: {result}")
                
                if self.detection_callback:
                    # Call detection callback in a new thread to avoid blocking
                    threading.Thread(target=self.detection_callback).start()
                
        except Exception as e:
            print(f"Error processing audio: {e}")
            
        # Return empty data to continue stream
        return (b'', pyaudio.paContinue) 
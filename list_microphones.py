import speech_recognition as sr
import sys
import pyaudio

def list_microphones_detailed():
    """
    List all available microphones with detailed information
    """
    p = pyaudio.PyAudio()
    recognizer = sr.Recognizer()
    
    print("\n=== KULLANILABILIR MIKROFONLAR ===")
    print("-" * 50)
    
    device_info = []
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:  # Only input devices
            device_info.append({
                'index': i,
                'name': info['name'],
                'channels': info['maxInputChannels'],
                'sample_rate': int(info['defaultSampleRate']),
                'is_default': info.get('isDefaultInputDevice', False)
            })
    
    # Get the list from speech_recognition for cross-reference
    sr_mic_names = sr.Microphone.list_microphone_names()
    
    for i, device in enumerate(device_info):
        is_default = "✓" if device['is_default'] else " "
        sr_index = -1
        
        # Find corresponding index in speech_recognition list
        for j, name in enumerate(sr_mic_names):
            if device['name'] in name or name in device['name']:
                sr_index = j
                break
        
        print(f"{device['index']} [{is_default}] {device['name']}")
        print(f"    Kanallar: {device['channels']}, Örnekleme hızı: {device['sample_rate']} Hz")
        
        if sr_index >= 0:
            print(f"    Speech Recognition indeksi: {sr_index}")
        else:
            print(f"    Speech Recognition indeksi bulunamadı")
        
        print("-" * 50)
    
    print("\nNot: [✓] işareti varsayılan mikrofonu gösterir")
    print("Sesli asistanı belirli bir mikrofonla başlatmak için:")
    print("  run_voice_assistant.bat <mikrofon_indeksi>")
    print("  veya menüden '2 - Belirli bir mikrofon seç' seçeneğini kullanın")
    
    p.terminate()

if __name__ == "__main__":
    try:
        list_microphones_detailed()
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        print("\nAlternatif basit liste:")
        try:
            mic_names = sr.Microphone.list_microphone_names()
            for i, name in enumerate(mic_names):
                print(f"{i}: {name}")
        except Exception as e2:
            print(f"Mikrofonlar listelenirken ikinci bir hata oluştu: {str(e2)}")
            sys.exit(1) 
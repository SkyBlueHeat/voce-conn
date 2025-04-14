# Voce-Con: Turkçe Sesli Asistan Kurulum ve Kullanim Kilavuzu

Bu proje, Windows ortaminda çalişan, Turkçe sesli komutlarla bilgisayarinizi kontrol etmenizi sağlayan bir sesli asistan uygulamasidir. "Jarvis" gibi bir aktivasyon sozcuğu ile uyandirilabilen asistan, web tarayici kontrolu, medya oynatici kontrolu, sistem sesi ayarlari, uygulama açma ve daha birçok işlevi sesli komutlarla gerçekleştirebilir.

## Başlangiç

Bu projeyi çaliştirmak için aşağidaki adimlari takip edin:

### Sistem Gereksinimleri

- Windows 10 veya daha yeni bir Windows surumu
- Python 3.10 veya daha yeni bir surum
- Çalişan bir mikrofon
- İnternet bağlantisi (bazi modeller için)

### Kurulum Adimlari

1. **Projeyi klonlayin:**

2. **Bağimliliklari yukleyin:**

Projeyi indirdikten sonra, `install_dependencies.bat` dosyasini çaliştirarak gerekli tum bağimliliklari otomatik olarak yukleyebilirsiniz:

```bash
install_dependencies.bat
```

Bu komut aşağidaki Python paketlerini yukleyecektir:
- speech_recognition
- pyttsx3
- pyaudio
- pvporcupine (uyandirma sozcuğu algilama için)
- edge-tts (doğal konuşma sentezi için)
- python-dotenv (konfigurasyon için)
- pygame (ses çalma için)
- ctypes, win32api (Windows API ile etkileşim için)

3. **Modelleri indirin:**

Eğer `download_model.py` dosyasi mevcutsa, bu dosyayi çaliştirarak konuşma tanima veya TTS (Text-to-Speech) için gereken modelleri indirin:

```bash
python download_model.py
```

4. **Konfigurasyon:**

Proje kok dizinindeki `.env` dosyasini duzenleyerek temel ayarlari yapilandirabilirsiniz:

```
WAKE_WORD=jarvis
SENSITIVITY=0.7
VOICE_FEEDBACK=true
TTS_ENGINE=edge-tts
EDGE_TTS_VOICE=tr-TR-EmelNeural
DEBUG_MODE=false
CONVERSATION_TIMEOUT=60
```

Bu ayarlar:
- **WAKE_WORD**: Asistani aktifleştirmek için kullanilan sozcuk ("jarvis", "alexa", "hey google" vb.)
- **SENSITIVITY**: Uyandirma sozcuğu duyarliliği (0.0 - 1.0)
- **VOICE_FEEDBACK**: Sesli geri bildirim (true/false)
- **TTS_ENGINE**: Metin-konuşma motoru (edge-tts veya pyttsx3)
- **EDGE_TTS_VOICE**: Edge TTS ses modeli
- **DEBUG_MODE**: Detayli hata ayiklama bilgileri (true/false)
- **CONVERSATION_TIMEOUT**: Konuşma modunun zaman aşimi suresi (saniye)

## Asistani Çaliştirma

Asistani çaliştirmak için iki yontem mevcuttur:

### 1. Doğrudan Python ile çaliştirma:

```bash
python main.py
```

### 2. Hazir bat dosyasi ile çaliştirma:

```bash
run_voice_assistant.bat
```

İlk çaliştirmada, mikrofon seçim menusu goruntulenecektir:

```
Voice Assistant Launcher
===================================
Mikrofon Seçimi
===================================
Lutfen bir seçenek seçin:
1 - Mikrofonlari listele (detayli liste)
2 - Belirli bir mikrofon seç
3 - Varsayilan mikrofon ile başlat
```

Eğer birden fazla mikrofonunuz varsa, "1" seçeneği ile mikrofonlari listeleyebilir ve ardindan "2" seçeneği ile belirli bir mikrofon seçebilirsiniz.

## Sesli Asistani Kullanma

Asistan başladiktan sonra şu adimlari izleyin:

1. **Asistani uyandirma:** 
   - "Jarvis" (veya ayarladiğiniz uyandirma sozcuğunu) soyleyin
   - Asistan "Sizi dinliyorum" diyerek yanit verecektir

2. **Komut verme:**
   - Asistan aktifleştikten sonra, komutunuzu soyleyin (orn. "Chrome aç", "YouTube aç", "sesi artir")
   - Asistan komutu tanidiğinda uygulayacak ve sesli geri bildirim verecektir

3. **Konuşma modu:**
   - Asistan, varsayilan olarak 60 saniye boyunca aktif kalir ve bu sure içinde uyandirma sozcuğunu tekrar soylemeden komut verebilirsiniz
   - "Konuşma modunu kapat" diyerek manuel olarak uyandirma sozcuğu moduna donebilirsiniz

4. **Asistani kapatma:**
   - "Çik" veya "Kapat" komutlarini soyleyerek asistani kapatabilirsiniz
   - Veya komut satirinda Ctrl+C tuşlarina basabilirsiniz

## Komut Kategorileri

Asistan aşağidaki kategorilerde komutlari destekler:

### Uygulama Açma Komutlari
- "Chrome aç", "YouTube aç", "Netflix aç", "Spotify aç"
- "Not defteri aç", "Hesap makinesi aç", "Dosya gezgini aç"
- "Word aç", "Excel aç", "PowerPoint aç"

### Sistem Kontrol Komutlari
- "Sesi artir", "Sesi azalt", "Sesi kapat"
- "Screenshot" (ekran goruntusu alma)

### Medya Kontrol Komutlari
- "Oynat", "Duraklat", "Durdur"
- "Sonraki parça", "onceki parça"
- "Tam ekran yap", "Tam ekrandan çik"
- "10 saniye ileri sar", "30 saniye geri sar"

### Tarayici Kontrol Komutlari
- "Sekme bir", "Sekme iki", "uçuncu sekme" (1-9 arasi sekmeler)
- "Sonraki sekme", "onceki sekme"
- "Yeni sekme", "Sekmeyi kapat"
- "Sayfayi yenile", "Tarayici geçmişi", "İndirilenler"

### Web Arama Komutlari
- "Google'da ara [arama terimi]"
- "YouTube'da ara [arama terimi]"
- "Wikipedia'da ara [arama terimi]"
- "Hava durumu goster", "Haberleri goster"

### Netflix ozel Komutlari
- "Altyazilari goster/gizle"
- "Jeneriği atla", "Bolum atla"
- "Bolum bilgilerini goster"

### Asistan Kontrol Komutlari
- "Konuşma modunu kapat"
- "Yardim", "Komutlari goster"
- "Çik", "Kapat"

## Komutlari ozelleştirme

Tum komutlar `komutlar.json` dosyasinda tanimlanmiştir. Bu dosyayi duzenleyerek mevcut komutlari değiştirebilir veya yeni komutlar ekleyebilirsiniz.

Her komut, kategori altinda bir anahtar-değer çifti olarak tanimlanir:
```json
"kategori": {
    "komut ifadesi": "eylem"
}
```

Eylem tipleri:
- Doğrudan sistem komutu: `"start chrome"`
- Medya tuşu: `"mediaplaypause"`, `"volumeup"`, `"medianext"`
- Tuş simulasyonu: `"noop+simulateKey:ctrl+1"`, `"noop+simulateKey:f"`

ornek: Yeni bir komut eklemek için `komutlar.json` dosyasini açin ve ilgili kategoriye komutunuzu ekleyin:
```json
"uygulamalar": {
    "hesap makinesi aç": "start calc",
    "yeni uygulama aç": "start yeniuygulama.exe"
}
```

## Sorun Giderme

### Asistan çalişmiyor veya "Hata" mesaji veriyor:
1. Python surumunuzun 3.10 veya daha yeni olduğundan emin olun
2. Tum bağimliliklarin kurulu olduğunu kontrol edin (`install_dependencies.bat` tekrar çaliştirin)
3. Mikrofonunuzun çaliştiğindan emin olun
4. Konsolda gorunen hata mesajlarini kontrol edin

### Asistan uyandirma sozcuğunu algilamiyor:
1. `.env` dosyasinda `SENSITIVITY` değerini artirin (orn. 0.8 gibi)
2. Farkli bir mikrofonla deneyin
3. Gurultulu ortamlardan uzaklaşin

### Asistan komutlari algilamiyor veya yanliş algiliyor:
1. Daha net ve yuksek sesle konuşun
2. Komutlarin tam olarak `komutlar.json` dosyasinda tanimlandiği şekilde olduğunu kontrol edin
3. İnternet bağlantinizin olduğundan emin olun (komut tanima için Google Speech API kullaniliyor)

### TTS (metin-konuşma) çalişmiyor:
1. `.env` dosyasinda `TTS_ENGINE=pyttsx3` olarak değiştirip tekrar deneyin
2. Edge TTS için internet bağlantinizin olduğundan emin olun

## İleri Seviye ozellikler

### Bağlam Farkindaliği
Asistan, son komutlari ve hangi uygulamanin aktif olduğunu hatirlayarak daha doğal etkileşimler sağlar. orneğin, bir film izlerken "tam ekran yap" ve "tam ekrandan çik" komutlari akillica işlenir.

### ozel Tuş Kombinasyonlari
Karmaşik tuş kombinasyonlarini "noop+simulateKey:" onekiyle tanimlayabilirsiniz:
```json
"komudum": "noop+simulateKey:ctrl+shift+t"
```

### Doğal Dil İşleme
Asistan, tam eşleşme yerine benzer komutlari taniyabilecek ve bağlamsal ipuçlarini kullanabilecek şekilde tasarlanmiştir. Bu sayede doğal konuşma ile etkileşime geçebilirsiniz.

## Teknik Detaylar

- **Uyandirma Sozcuğu Algilama**: Picovoice Porcupine kutuphanesi
- **Konuşma Tanima**: Google Speech Recognition API
- **Metin-Konuşma**: Edge TTS veya pyttsx3
- **Tuş Simulasyonu**: Windows API (ctypes ve win32api)
- **Komut Yurutme**: Subprocess ve bağlam farkindaliği ile geliştirilmiş komut yurutucu
- **Konfigurasyon**: Python-dotenv ile .env dosyasindan

## Lisans ve Katkida Bulunma

Bu proje açik kaynaklidir. Hata raporlari, ozellik istekleri ve katkilar memnuniyetle karşilanir.

---

Sesli asistaninizi keyifle kullanin! Herhangi bir sorunuz veya geri bildiriminiz varsa, lutfen GitHub uzerinden iletişime geçin.

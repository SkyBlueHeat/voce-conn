"""
Voce Sesli Asistan - Ana Pencere
GUI arayuzu için ana pencere bileşeni.
"""

import os
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QComboBox, 
                            QSlider, QCheckBox, QTabWidget, QGroupBox, 
                            QFormLayout, QLineEdit, QMessageBox, QFileDialog)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap
import logging

from gui.assistant_controller import AssistantController
from utils.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Sesli asistan için ana pencere sinifi"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.controller = AssistantController(self.config_manager)
        
        # Ana pencere ayarlari
        self.setWindowTitle("Voce - Turkçe Sesli Asistan")
        self.setMinimumSize(800, 600)
        
        # UI bileşenlerini oluştur
        self.init_ui()
        
        # Kontrol bağlantilarini kur
        self.connect_signals()
        
        # Config'ten ayarlari yukle
        self.load_settings()
    
    def init_ui(self):
        """UI bileşenlerini oluşturur"""
        # Ana widget ve yerleşim
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget oluştur
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Ana kontrol sekmesi
        control_tab = QWidget()
        control_layout = QVBoxLayout(control_tab)
        
        # Başlik ve logo (eğer varsa)
        title_layout = QHBoxLayout()
        
        logo_file = os.path.join("resources", "logo.png")
        if os.path.exists(logo_file):
            logo_label = QLabel()
            logo_label.setPixmap(QPixmap(logo_file).scaled(
                64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            title_layout.addWidget(logo_label)
        
        title_label = QLabel("Voce Turkçe Sesli Asistan")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        control_layout.addLayout(title_layout)
        
        # Durum grubu
        status_group = QGroupBox("Asistan Durumu")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("Hazir")
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        control_layout.addWidget(status_group)
        
        # Komut kontrolu grupi
        command_group = QGroupBox("Asistan Kontrolu")
        command_layout = QHBoxLayout(command_group)
        
        self.start_button = QPushButton("Başlat")
        self.start_button.setMinimumHeight(50)
        self.start_button.setFont(QFont("Arial", 12))
        command_layout.addWidget(self.start_button)
        
        self.stop_button = QPushButton("Durdur")
        self.stop_button.setMinimumHeight(50)
        self.stop_button.setFont(QFont("Arial", 12))
        self.stop_button.setEnabled(False)
        command_layout.addWidget(self.stop_button)
        
        self.test_button = QPushButton("Ses Testi")
        self.test_button.setMinimumHeight(50)
        self.test_button.setFont(QFont("Arial", 12))
        command_layout.addWidget(self.test_button)
        
        control_layout.addWidget(command_group)
        
        # Hizli Komutlar
        commands_group = QGroupBox("Hizli Komutlar")
        commands_layout = QVBoxLayout(commands_group)
        
        self.command_examples = [
            "Saat kaç", 
            "Bugun hava nasil", 
            "Tarayiciyi aç", 
            "Muziği çal",
            "Sesli oku"
        ]
        
        for cmd in self.command_examples:
            cmd_button = QPushButton(cmd)
            cmd_button.setFont(QFont("Arial", 11))
            cmd_button.clicked.connect(lambda checked, c=cmd: self.controller.execute_direct_command(c))
            commands_layout.addWidget(cmd_button)
        
        control_layout.addWidget(commands_group)
        control_layout.addStretch()
        
        # Ayarlar sekmesi
        settings_tab = QWidget()
        settings_layout = QVBoxLayout(settings_tab)
        
        # Genel ayarlar grubu
        general_group = QGroupBox("Genel Ayarlar")
        general_layout = QFormLayout(general_group)
        
        # Uyandirma kelimesi
        self.wake_word_input = QLineEdit()
        general_layout.addRow("Uyandirma Kelimesi:", self.wake_word_input)
        
        # Debug modu
        self.debug_checkbox = QCheckBox("Debug Modu")
        general_layout.addRow("", self.debug_checkbox)
        
        # Ses geri bildirimi
        self.voice_feedback_checkbox = QCheckBox("Sesli Geri Bildirim")
        general_layout.addRow("", self.voice_feedback_checkbox)
        
        settings_layout.addWidget(general_group)
        
        # TTS ayarlari grubu
        tts_group = QGroupBox("Ses Sentezi Ayarlari")
        tts_layout = QFormLayout(tts_group)
        
        # TTS motoru
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems(["Edge TTS", "pyttsx3"])
        tts_layout.addRow("TTS Motoru:", self.tts_engine_combo)
        
        # Ses
        self.voice_combo = QComboBox()
        tts_layout.addRow("Ses:", self.voice_combo)
        
        # Hiz
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setRange(50, 200)
        self.rate_slider.setValue(100)
        self.rate_value_label = QLabel("100%")
        rate_layout = QHBoxLayout()
        rate_layout.addWidget(self.rate_slider)
        rate_layout.addWidget(self.rate_value_label)
        tts_layout.addRow("Konuşma Hizi:", rate_layout)
        
        # Ses yuksekliği
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(75)
        self.volume_value_label = QLabel("75%")
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_value_label)
        tts_layout.addRow("Ses Seviyesi:", volume_layout)
        
        settings_layout.addWidget(tts_group)
        settings_layout.addStretch()
        
        # Kaydet butonu
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_button = QPushButton("Ayarlari Kaydet")
        self.save_button.setMinimumSize(150, 40)
        self.save_button.setFont(QFont("Arial", 12))
        save_layout.addWidget(self.save_button)
        
        settings_layout.addLayout(save_layout)
        
        # Sekmeleri ekle
        self.tabs.addTab(control_tab, "Kontrol")
        self.tabs.addTab(settings_tab, "Ayarlar")
        
        # Durum çubuğu
        self.statusBar().showMessage("Hazir")
    
    def connect_signals(self):
        """Sinyal bağlantilarini kurar"""
        # Buton bağlantilari
        self.start_button.clicked.connect(self.start_assistant)
        self.stop_button.clicked.connect(self.stop_assistant)
        self.test_button.clicked.connect(self.test_tts)
        self.save_button.clicked.connect(self.save_settings)
        
        # Ayar değişiklikleri
        self.tts_engine_combo.currentIndexChanged.connect(self.update_voice_options)
        self.rate_slider.valueChanged.connect(self.update_rate_label)
        self.volume_slider.valueChanged.connect(self.update_volume_label)
        
        # Controller sinyalleri
        self.controller.status_changed.connect(self.update_status)
    
    def load_settings(self):
        """Config'ten ayarlari yukler"""
        try:
            # Genel ayarlar
            self.wake_word_input.setText(self.config_manager.get('WAKE_WORD', 'hey asistan'))
            self.debug_checkbox.setChecked(self.config_manager.get('DEBUG_MODE', 'false').lower() == 'true')
            self.voice_feedback_checkbox.setChecked(self.config_manager.get('VOICE_FEEDBACK', 'true').lower() == 'true')
            
            # TTS ayarlari
            tts_engine = self.config_manager.get('TTS_ENGINE', 'edge-tts')
            self.tts_engine_combo.setCurrentIndex(0 if tts_engine.lower() == 'edge-tts' else 1)
            
            # Slider değerleri
            self.rate_slider.setValue(int(float(self.config_manager.get('TTS_RATE', '100'))))
            self.volume_slider.setValue(int(float(self.config_manager.get('TTS_VOLUME', '75'))))
            
            # Ses seçeneklerini guncelle
            self.update_voice_options()
            
            # Seçili ses
            voice = self.config_manager.get('TTS_VOICE', '')
            if voice:
                index = self.voice_combo.findText(voice)
                if index >= 0:
                    self.voice_combo.setCurrentIndex(index)
            
        except Exception as e:
            logger.error(f"Ayarlar yuklenirken hata: {e}")
            QMessageBox.warning(self, "Ayarlar Hatasi", 
                               f"Ayarlar yuklenirken bir hata oluştu: {e}")
    
    def update_voice_options(self):
        """Seçili TTS motoru için ses seçeneklerini gunceller"""
        self.voice_combo.clear()
        
        if self.tts_engine_combo.currentIndex() == 0:  # Edge TTS
            try:
                # Edge TTS sesleri (anlik olarak alamiyoruz, ama statik olarak ekleyebiliriz)
                turkish_voices = ["tr-TR-AhmetNeural (Erkek)", "tr-TR-EmelNeural (Kadin)"]
                self.voice_combo.addItems(turkish_voices)
            except Exception as e:
                logger.error(f"Edge TTS sesleri alinirken hata: {e}")
                self.voice_combo.addItem("Varsayilan")
        else:  # pyttsx3
            try:
                self.voice_combo.addItem("Varsayilan")
                # Burada pyttsx3 seslerini listeleyebilirsiniz, ancak şu an için sadece varsayilan
                # ses ekleniyor çunku pyttsx3 seslerine erişim biraz karmaşik
            except Exception as e:
                logger.error(f"pyttsx3 sesleri alinirken hata: {e}")
                self.voice_combo.addItem("Varsayilan")
    
    def update_rate_label(self, value):
        """Konuşma hizi etiketini gunceller"""
        self.rate_value_label.setText(f"{value}%")
    
    def update_volume_label(self, value):
        """Ses seviyesi etiketini gunceller"""
        self.volume_value_label.setText(f"{value}%")
    
    def save_settings(self):
        """Ayarlari kaydeder"""
        try:
            # Genel ayarlar
            self.config_manager.set('WAKE_WORD', self.wake_word_input.text())
            self.config_manager.set('DEBUG_MODE', str(self.debug_checkbox.isChecked()).lower())
            self.config_manager.set('VOICE_FEEDBACK', str(self.voice_feedback_checkbox.isChecked()).lower())
            
            # TTS ayarlari
            tts_engine = "edge-tts" if self.tts_engine_combo.currentIndex() == 0 else "pyttsx3"
            self.config_manager.set('TTS_ENGINE', tts_engine)
            
            # Ses seçimi
            voice_text = self.voice_combo.currentText()
            if '(' in voice_text:
                voice_text = voice_text.split('(')[0].strip()  # Sadece ses adini al, açiklamayi çikar
            self.config_manager.set('TTS_VOICE', voice_text)
            
            # Hiz ve ses seviyesi
            self.config_manager.set('TTS_RATE', str(self.rate_slider.value()))
            self.config_manager.set('TTS_VOLUME', str(self.volume_slider.value()))
            
            # Ayarlari kaydet
            self.config_manager.save_config()
            
            # Controller'a bildirmek için ayarlari yeniden yukle
            self.controller.reload_config()
            
            QMessageBox.information(self, "Ayarlar", "Ayarlar başariyla kaydedildi.")
            
        except Exception as e:
            logger.error(f"Ayarlar kaydedilirken hata: {e}")
            QMessageBox.warning(self, "Ayarlar Hatasi", 
                               f"Ayarlar kaydedilirken bir hata oluştu: {e}")
    
    def start_assistant(self):
        """Asistani başlatir"""
        try:
            self.controller.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.test_button.setEnabled(False)
            self.tabs.setTabEnabled(1, False)  # Ayarlar sekmesini devre dişi birak
        except Exception as e:
            logger.error(f"Asistan başlatilirken hata: {e}")
            QMessageBox.critical(self, "Başlatma Hatasi", 
                                f"Asistan başlatilirken bir hata oluştu: {e}")
    
    def stop_assistant(self):
        """Asistani durdurur"""
        try:
            self.controller.stop()
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.test_button.setEnabled(True)
            self.tabs.setTabEnabled(1, True)  # Ayarlar sekmesini etkinleştir
        except Exception as e:
            logger.error(f"Asistan durdurulurken hata: {e}")
            QMessageBox.critical(self, "Durdurma Hatasi", 
                                f"Asistan durdurulurken bir hata oluştu: {e}")
    
    def test_tts(self):
        """TTS test fonksiyonu"""
        try:
            self.controller.test_speech("Merhaba! Ben Voce Turkçe Sesli Asistan. Şu anda sesli sentez testi yapiyorum.")
        except Exception as e:
            logger.error(f"Ses testi sirasinda hata: {e}")
            QMessageBox.warning(self, "Ses Testi Hatasi", 
                               f"Ses testi sirasinda bir hata oluştu: {e}")
    
    def update_status(self, status):
        """Asistan durumunu gunceller"""
        self.status_label.setText(status)
        self.statusBar().showMessage(status)
    
    def closeEvent(self, event):
        """Uygulama kapatildiğinda çağrilir"""
        try:
            # Asistani duzgun şekilde kapatalim
            if self.controller.is_running:
                reply = QMessageBox.question(self, 'Çikiş', 
                                           "Asistan çalişiyor. Kapatmak istediğinize emin misiniz?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                
                if reply == QMessageBox.Yes:
                    self.controller.stop()
                else:
                    event.ignore()
                    return
            
            self.controller.shutdown()
            event.accept()
        except Exception as e:
            logger.error(f"Uygulama kapatilirken hata: {e}")
            event.accept()  # Yine de kapatalim

def main():
    """Ana uygulama başlatici fonksiyonu"""
    app = QApplication(sys.argv)
    
    # Stil ayarlari
    app.setStyle("Fusion")
    
    # Ana pencereyi oluştur ve göster
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
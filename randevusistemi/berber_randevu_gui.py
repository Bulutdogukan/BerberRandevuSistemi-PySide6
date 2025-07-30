import sqlite3
from datetime import datetime
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton, QMessageBox, QTabWidget,
                               QTableWidget, QTableWidgetItem, QHeaderView)
from PySide6.QtCore import Qt

# --- Mevcut Veritabanı Fonksiyonlarınız ---
DATABASE_NAME = 'berber_randevu.db'

def connect_db():
    conn = sqlite3.connect(DATABASE_NAME)
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS randevular (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_adi TEXT NOT NULL,
            tarih TEXT NOT NULL,
            saat TEXT NOT NULL,
            berber_adi TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Randevular tablosu oluşturuldu veya zaten mevcut.")

def convert_date_to_db_format(date_str):
    try:
        dt_object = datetime.strptime(date_str, '%d-%m-%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return None

def convert_date_from_db_format(date_str):
    try:
        dt_object = datetime.strptime(date_str, '%Y-%m-%d')
        return dt_object.strftime('%d-%m-%Y')
    except ValueError:
        return None

def add_appointment(musteri_adi, tarih_gg_aa_yyyy, saat, berber_adi=None):
    tarih_db_format = convert_date_to_db_format(tarih_gg_aa_yyyy)
    if not tarih_db_format:
        return "Hata: Geçersiz tarih formatı. Lütfen GG-AA-YYYY formatında girin."

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO randevular (musteri_adi, tarih, saat, berber_adi) VALUES (?, ?, ?, ?)",
                       (musteri_adi, tarih_db_format, saat, berber_adi))
        conn.commit()
        return f"{musteri_adi} için {tarih_gg_aa_yyyy} {saat} tarihine randevu başarıyla eklendi."
    except sqlite3.Error as e:
        return f"Randevu eklenirken bir hata oluştu: {e}"
    finally:
        conn.close()

def get_all_appointments():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, musteri_adi, tarih, saat, berber_adi FROM randevular ORDER BY tarih ASC, saat ASC")
    appointments = cursor.fetchall()
    conn.close()
    
    formatted_appointments = []
    for app in appointments:
        formatted_date = convert_date_from_db_format(app[2])
        formatted_appointments.append((app[0], app[1], formatted_date, app[3], app[4]))
    return formatted_appointments

def get_appointments_by_date(tarih_gg_aa_yyyy):
    tarih_db_format = convert_date_to_db_format(tarih_gg_aa_yyyy)
    if not tarih_db_format:
        return "Hata: Geçersiz tarih formatı. Lütfen GG-AA-YYYY formatında girin.", []

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, musteri_adi, tarih, saat, berber_adi FROM randevular WHERE tarih = ? ORDER BY saat ASC", (tarih_db_format,))
    appointments = cursor.fetchall()
    conn.close()

    formatted_appointments = []
    for app in appointments:
        formatted_date = convert_date_from_db_format(app[2])
        formatted_appointments.append((app[0], app[1], formatted_date, app[3], app[4]))
    return None, formatted_appointments

def update_appointment(appointment_id, new_musteri_adi=None, new_tarih_gg_aa_yyyy=None, new_saat=None, new_berber_adi=None):
    conn = connect_db()
    cursor = conn.cursor()
    update_fields = []
    update_values = []

    if new_musteri_adi:
        update_fields.append("musteri_adi = ?")
        update_values.append(new_musteri_adi)
    
    if new_tarih_gg_aa_yyyy:
        new_tarih_db_format = convert_date_to_db_format(new_tarih_gg_aa_yyyy)
        if not new_tarih_db_format:
            conn.close()
            return "Hata: Güncellenecek tarih için geçersiz format. Lütfen GG-AA-YYYY formatında girin."
        update_fields.append("tarih = ?")
        update_values.append(new_tarih_db_format)
    
    if new_saat:
        update_fields.append("saat = ?")
        update_values.append(new_saat)
    if new_berber_adi:
        update_fields.append("berber_adi = ?")
        update_values.append(new_berber_adi)

    if not update_fields:
        conn.close()
        return "Güncellenecek alan bulunamadı."

    update_query = f"UPDATE randevular SET {', '.join(update_fields)} WHERE id = ?"
    update_values.append(appointment_id)

    try:
        cursor.execute(update_query, tuple(update_values))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Randevu ID {appointment_id} başarıyla güncellendi."
        else:
            return f"Randevu ID {appointment_id} bulunamadı."
    except sqlite3.Error as e:
        return f"Randevu güncellenirken bir hata oluştu: {e}"
    finally:
        conn.close()

# delete_appointment fonksiyonu geri eklendi
def delete_appointment(appointment_id):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM randevular WHERE id = ?", (appointment_id,))
        conn.commit()
        if cursor.rowcount > 0:
            return f"Randevu ID {appointment_id} başarıyla silindi."
        else:
            return f"Randevu ID {appointment_id} bulunamadı."
    except sqlite3.Error as e:
        return f"Randevu silinirken bir hata oluştu: {e}"
    finally:
        conn.close()

# --- PySide6 GUI Sınıfı ---
class BarberAppointmentApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Berber Randevu Sistemi (PySide6)")
        self.setGeometry(100, 100, 900, 700) # Pencere boyutu ve konumu

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.create_add_appointment_tab()
        self.create_list_appointments_tab()
        self.create_update_delete_appointment_tab() # Sekme adı eski haline getirildi
        self.create_search_appointment_tab()

        self.load_appointments_to_table() # Başlangıçta randevuları yükle

    def create_add_appointment_tab(self):
        self.add_tab = QWidget()
        self.tab_widget.addTab(self.add_tab, "Randevu Ekle")
        layout = QVBoxLayout(self.add_tab)

        form_layout = QVBoxLayout()

        # Müşteri Adı
        self.musteri_adi_input = self._create_labeled_input("Müşteri Adı:", form_layout)
        # Randevu Tarihi
        self.tarih_input = self._create_labeled_input("Randevu Tarihi (GG-AA-YYYY):", form_layout)
        # Randevu Saati
        self.saat_input = self._create_labeled_input("Randevu Saati (SS:DD):", form_layout)
        # Berber Adı
        self.berber_adi_input = self._create_labeled_input("Berber Adı (isteğe bağlı):", form_layout)

        add_button = QPushButton("Randevu Ekle")
        add_button.clicked.connect(self.add_appointment_gui)
        form_layout.addWidget(add_button)

        layout.addLayout(form_layout)
        layout.addStretch() # İçeriği üste yaslar

    def _create_labeled_input(self, label_text, layout):
        h_layout = QHBoxLayout()
        label = QLabel(label_text)
        text_input = QLineEdit()
        h_layout.addWidget(label)
        h_layout.addWidget(text_input)
        layout.addLayout(h_layout)
        return text_input

    def add_appointment_gui(self):
        musteri_adi = self.musteri_adi_input.text().strip()
        tarih = self.tarih_input.text().strip()
        saat = self.saat_input.text().strip()
        berber_adi = self.berber_adi_input.text().strip()
        
        if not berber_adi:
            berber_adi = None

        if not musteri_adi or not tarih or not saat:
            QMessageBox.warning(self, "Eksik Bilgi", "Müşteri Adı, Tarih ve Saat alanları boş bırakılamaz.")
            return

        result = add_appointment(musteri_adi, tarih, saat, berber_adi)
        QMessageBox.information(self, "Randevu Ekle", result)
        
        # Alanları temizle
        self.musteri_adi_input.clear()
        self.tarih_input.clear()
        self.saat_input.clear()
        self.berber_adi_input.clear()
        self.load_appointments_to_table() # Randevu listesini güncelle

    def create_list_appointments_tab(self):
        self.list_tab = QWidget()
        self.tab_widget.addTab(self.list_tab, "Tüm Randevular")
        layout = QVBoxLayout(self.list_tab)

        self.appointment_table = QTableWidget()
        self.appointment_table.setColumnCount(5)
        self.appointment_table.setHorizontalHeaderLabels(["ID", "Müşteri Adı", "Tarih", "Saat", "Berber Adı"])
        self.appointment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # Sütunları yay
        
        layout.addWidget(self.appointment_table)

        refresh_button = QPushButton("Randevuları Yenile")
        refresh_button.clicked.connect(self.load_appointments_to_table)
        layout.addWidget(refresh_button)

    # create_update_delete_appointment_tab fonksiyonu geri getirildi ve güncellendi
    def create_update_delete_appointment_tab(self):
        self.update_delete_tab = QWidget()
        self.tab_widget.addTab(self.update_delete_tab, "Randevu Güncelle/Sil")
        layout = QVBoxLayout(self.update_delete_tab)

        # Randevu ID Girişi
        self.id_update_delete_input = self._create_labeled_input("Randevu ID:", layout)

        # Güncelleme Alanları
        update_form_layout = QVBoxLayout()
        self.new_musteri_adi_input = self._create_labeled_input("Yeni Müşteri Adı:", update_form_layout)
        self.new_tarih_input = self._create_labeled_input("Yeni Tarih (GG-AA-YYYY):", update_form_layout)
        self.new_saat_input = self._create_labeled_input("Yeni Saat (SS:DD):", update_form_layout)
        self.new_berber_adi_input = self._create_labeled_input("Yeni Berber Adı:", update_form_layout)

        layout.addLayout(update_form_layout)

        # Butonlar
        button_layout = QHBoxLayout()
        update_button = QPushButton("Randevu Güncelle")
        update_button.clicked.connect(self.update_appointment_gui)
        button_layout.addWidget(update_button)

        delete_button = QPushButton("Randevu Sil") # Sil butonu geri eklendi
        delete_button.clicked.connect(self.delete_appointment_gui) # Sinyal bağlandı
        button_layout.addWidget(delete_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()

    def update_appointment_gui(self):
        app_id_str = self.id_update_delete_input.text().strip()
        try:
            app_id = int(app_id_str)
        except ValueError:
            QMessageBox.warning(self, "Geçersiz ID", "Lütfen geçerli bir Randevu ID girin.")
            return

        new_musteri_adi = self.new_musteri_adi_input.text().strip()
        new_tarih = self.new_tarih_input.text().strip()
        new_saat = self.new_saat_input.text().strip()
        new_berber_adi = self.new_berber_adi_input.text().strip()

        result = update_appointment(
            app_id,
            new_musteri_adi if new_musteri_adi else None,
            new_tarih if new_tarih else None,
            new_saat if new_saat else None,
            new_berber_adi if new_berber_adi else None
        )
        QMessageBox.information(self, "Randevu Güncelleme", result)
        self.load_appointments_to_table() # Listeyi güncelle
        self.clear_update_fields()

    # delete_appointment_gui fonksiyonu geri eklendi
    def delete_appointment_gui(self):
        app_id_str = self.id_update_delete_input.text().strip()
        try:
            app_id = int(app_id_str)
        except ValueError:
            QMessageBox.warning(self, "Geçersiz ID", "Lütfen geçerli bir Randevu ID girin.")
            return

        confirm = QMessageBox.question(self, "Randevu Sil", f"Randevu ID {app_id} silmek istediğinize emin misiniz?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            result = delete_appointment(app_id)
            QMessageBox.information(self, "Randevu Silme", result)
            self.load_appointments_to_table() # Listeyi güncelle
            self.clear_update_fields()

    def clear_update_fields(self):
        self.id_update_delete_input.clear()
        self.new_musteri_adi_input.clear()
        self.new_tarih_input.clear()
        self.new_saat_input.clear()
        self.new_berber_adi_input.clear()

    def create_search_appointment_tab(self):
        self.search_tab = QWidget()
        self.tab_widget.addTab(self.search_tab, "Randevu Ara")
        layout = QVBoxLayout(self.search_tab)

        # Arama Kriterleri
        self.search_criteria_input = QLineEdit()
        self.search_criteria_input.setPlaceholderText("Müşteri Adı veya Randevu ID ile ara...")
        layout.addWidget(self.search_criteria_input)

        search_button = QPushButton("Ara")
        search_button.clicked.connect(self.search_appointment_gui)
        layout.addWidget(search_button)

        # Sonuç Tablosu
        self.search_result_table = QTableWidget()
        self.search_result_table.setColumnCount(5)
        self.search_result_table.setHorizontalHeaderLabels(["ID", "Müşteri Adı", "Tarih", "Saat", "Berber Adı"])
        self.search_result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.search_result_table)

    def search_appointment_gui(self):
        criteria = self.search_criteria_input.text().strip()
        if not criteria:
            QMessageBox.warning(self, "Boş Arama Kriteri", "Lütfen arama yapmak için bir kriter girin.")
            return

        # Kriterin sayı mı yoksa metin mi olduğunu kontrol et
        try:
            # Eğer sayı ise, doğrudan ID ile ara
            appointment_id = int(criteria)
            _, appointments = get_appointments_by_date(criteria) # Tarih ile arama fonksiyonunu kullanıyoruz
            if appointments:
                self.show_search_results(appointments)
            else:
                QMessageBox.information(self, "Sonuç", "Hiçbir randevu bulunamadı.")
        except ValueError:
            # Eğer metin ise, müşteri adı ile ara
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, musteri_adi, tarih, saat, berber_adi FROM randevular WHERE musteri_adi LIKE ?",
                           ('%' + criteria + '%',))
            appointments = cursor.fetchall()
            conn.close()

            if appointments:
                self.show_search_results(appointments)
            else:
                QMessageBox.information(self, "Sonuç", "Hiçbir randevu bulunamadı.")

    def show_search_results(self, appointments):
        self.search_result_table.setRowCount(0) # Önceki sonuçları temizle
        for app in appointments:
            row_position = self.search_result_table.rowCount()
            self.search_result_table.insertRow(row_position)
            for col, value in enumerate(app):
                self.search_result_table.setItem(row_position, col, QTableWidgetItem(str(value)))

    def load_appointments_to_table(self):
        all_appointments = get_all_appointments()
        self.appointment_table.setRowCount(0)  # Temizle mevcut satırlar
        for app in all_appointments:
            row_position = self.appointment_table.rowCount()
            self.appointment_table.insertRow(row_position)
            for col, value in enumerate(app):
                self.appointment_table.setItem(row_position, col, QTableWidgetItem(str(value)))

if __name__ == "__main__":
    create_table()  # Uygulama her başladığında tabloyu oluştur
    app = QApplication(sys.argv)
    window = BarberAppointmentApp()
    window.show()
    sys.exit(app.exec())
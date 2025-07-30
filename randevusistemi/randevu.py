import sqlite3
from datetime import datetime

DATABASE_NAME = 'berber_randevu.db'

def connect_db():
    """Veritabanına bağlanır ve bağlantı nesnesini döndürür."""
    conn = sqlite3.connect(DATABASE_NAME)
    # Satırları dict olarak döndürmek için:
    # conn.row_factory = sqlite3.Row
    return conn

def create_table():
    """Randevular tablosunu oluşturur."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS randevular (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            musteri_adi TEXT NOT NULL,
            tarih TEXT NOT NULL, -- YYYY-MM-DD formatında saklanacak
            saat TEXT NOT NULL, -- HH:MM formatında saklanacak
            berber_adi TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Randevular tablosu oluşturuldu veya zaten mevcut.")

def convert_date_to_db_format(date_str):
    """GG-AA-YYYY formatındaki tarihi YYYY-MM-DD formatına dönüştürür."""
    try:
        dt_object = datetime.strptime(date_str, '%d-%m-%Y')
        return dt_object.strftime('%Y-%m-%d')
    except ValueError:
        return None # Hata durumunda None dönebiliriz veya hata fırlatabiliriz

def convert_date_from_db_format(date_str):
    """YYYY-MM-DD formatındaki tarihi GG-AA-YYYY formatına dönüştürür."""
    try:
        dt_object = datetime.strptime(date_str, '%Y-%m-%d')
        return dt_object.strftime('%d-%m-%Y')
    except ValueError:
        return None

def add_appointment(musteri_adi, tarih_gg_aa_yyyy, saat, berber_adi=None):
    """Yeni bir randevu ekler."""
    tarih_db_format = convert_date_to_db_format(tarih_gg_aa_yyyy)
    if not tarih_db_format:
        print("Hata: Geçersiz tarih formatı. Lütfen GG-AA-YYYY formatında girin.")
        return

    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO randevular (musteri_adi, tarih, saat, berber_adi) VALUES (?, ?, ?, ?)",
                       (musteri_adi, tarih_db_format, saat, berber_adi))
        conn.commit()
        print(f"{musteri_adi} için {tarih_gg_aa_yyyy} {saat} tarihine randevu başarıyla eklendi.")
    except sqlite3.Error as e:
        print(f"Randevu eklenirken bir hata oluştu: {e}")
    finally:
        conn.close()

def get_all_appointments():
    """Tüm randevuları listeler."""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, musteri_adi, tarih, saat, berber_adi FROM randevular ORDER BY tarih ASC, saat ASC")
    appointments = cursor.fetchall()
    conn.close()
    
    # Kullanıcıya göstermek için tarihi GG-AA-YYYY formatına dönüştür
    formatted_appointments = []
    for app in appointments:
        formatted_date = convert_date_from_db_format(app[2])
        formatted_appointments.append((app[0], app[1], formatted_date, app[3], app[4]))
    return formatted_appointments

def get_appointments_by_date(tarih_gg_aa_yyyy):
    """Belirli bir tarihteki randevuları listeler."""
    tarih_db_format = convert_date_to_db_format(tarih_gg_aa_yyyy)
    if not tarih_db_format:
        print("Hata: Geçersiz tarih formatı. Lütfen GG-AA-YYYY formatında girin.")
        return []

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, musteri_adi, tarih, saat, berber_adi FROM randevular WHERE tarih = ? ORDER BY saat ASC", (tarih_db_format,))
    appointments = cursor.fetchall()
    conn.close()

    # Kullanıcıya göstermek için tarihi GG-AA-YYYY formatına dönüştür
    formatted_appointments = []
    for app in appointments:
        formatted_date = convert_date_from_db_format(app[2])
        formatted_appointments.append((app[0], app[1], formatted_date, app[3], app[4]))
    return formatted_appointments

def update_appointment(appointment_id, new_musteri_adi=None, new_tarih_gg_aa_yyyy=None, new_saat=None, new_berber_adi=None):
    """Mevcut bir randevuyu günceller."""
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
            print("Hata: Güncellenecek tarih için geçersiz format. Lütfen GG-AA-YYYY formatında girin.")
            conn.close()
            return
        update_fields.append("tarih = ?")
        update_values.append(new_tarih_db_format)
    
    if new_saat:
        update_fields.append("saat = ?")
        update_values.append(new_saat)
    if new_berber_adi:
        update_fields.append("berber_adi = ?")
        update_values.append(new_berber_adi)

    if not update_fields:
        print("Güncellenecek alan bulunamadı.")
        conn.close()
        return

    update_query = f"UPDATE randevular SET {', '.join(update_fields)} WHERE id = ?"
    update_values.append(appointment_id)

    try:
        cursor.execute(update_query, tuple(update_values))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Randevu ID {appointment_id} başarıyla güncellendi.")
        else:
            print(f"Randevu ID {appointment_id} bulunamadı.")
    except sqlite3.Error as e:
        print(f"Randevu güncellenirken bir hata oluştu: {e}")
    finally:
        conn.close()

def delete_appointment(appointment_id):
    """Belirli bir randevuyu siler."""
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM randevular WHERE id = ?", (appointment_id,))
        conn.commit()
        if cursor.rowcount > 0:
            print(f"Randevu ID {appointment_id} başarıyla silindi.")
        else:
            print(f"Randevu ID {appointment_id} bulunamadı.")
    except sqlite3.Error as e:
        print(f"Randevu silinirken bir hata oluştu: {e}")
    finally:
        conn.close()

def main_menu():
    """Ana menüyü gösterir ve kullanıcıdan seçim alır."""
    while True:
        print("\n--- Berber Randevu Sistemi ---")
        print("1. Randevu Ekle")
        print("2. Tüm Randevuları Listele")
        print("3. Tarihe Göre Randevu Listele")
        print("4. Randevu Güncelle")
        print("5. Randevu Sil")
        print("0. Çıkış")

        choice = input("Seçiminizi yapın: ")

        if choice == '1':
            musteri_adi = input("Müşteri Adı: ")
            tarih = input("Randevu Tarihi (GG-AA-YYYY): ")
            saat = input("Randevu Saati (SS:DD): ")
            berber_adi = input("Berber Adı (isteğe bağlı): ")
            add_appointment(musteri_adi, tarih, saat, berber_adi if berber_adi else None)
        elif choice == '2':
            appointments = get_all_appointments()
            if appointments:
                print("\n--- Tüm Randevular ---")
                for app in appointments:
                    print(f"ID: {app[0]}, Müşteri: {app[1]}, Tarih: {app[2]}, Saat: {app[3]}, Berber: {app[4] if app[4] else 'Belirtilmemiş'}")
            else:
                print("Henüz hiç randevu yok.")
        elif choice == '3':
            tarih = input("Listelemek istediğiniz tarihi girin (GG-AA-YYYY): ")
            appointments = get_appointments_by_date(tarih)
            if appointments:
                print(f"\n--- {tarih} Tarihli Randevular ---")
                for app in appointments:
                    print(f"ID: {app[0]}, Müşteri: {app[1]}, Saat: {app[3]}, Berber: {app[4] if app[4] else 'Belirtilmemiş'}")
            else:
                print(f"{tarih} tarihinde randevu bulunamadı.")
        elif choice == '4':
            app_id = input("Güncellenecek randevunun ID'sini girin: ")
            try:
                app_id = int(app_id)
            except ValueError:
                print("Geçersiz ID. Lütfen sayısal bir değer girin.")
                continue

            new_musteri_adi = input("Yeni müşteri adı (değiştirmek istemiyorsanız boş bırakın): ")
            new_tarih = input("Yeni tarih (GG-AA-YYYY) (değiştirmek istemiyorsanız boş bırakın): ")
            new_saat = input("Yeni saat (SS:DD) (değiştirmek istemiyorsanız boş bırakın): ")
            new_berber_adi = input("Yeni berber adı (değiştirmek istemiyorsanız boş bırakın): ")

            update_appointment(app_id,
                               new_musteri_adi if new_musteri_adi else None,
                               new_tarih if new_tarih else None,
                               new_saat if new_saat else None,
                               new_berber_adi if new_berber_adi else None)
        elif choice == '5':
            app_id = input("Silinecek randevunun ID'sini girin: ")
            try:
                app_id = int(app_id)
                delete_appointment(app_id)
            except ValueError:
                print("Geçersiz ID. Lütfen sayısal bir değer girin.")
        elif choice == '0':
            print("Çıkılıyor...")
            break
        else:
            print("Geçersiz seçim. Lütfen tekrar deneyin.")

if __name__ == "__main__":
    create_table()
    main_menu()
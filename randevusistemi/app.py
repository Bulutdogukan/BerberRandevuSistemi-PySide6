from randevu import connect_db, create_tables
import sqlite3

def musteri_ekle(kullanici_adi, sifre, eposta=None, telefon=None):
    conn, cursor = connect_db()
    try:
        cursor.execute('''
            INSERT INTO musteriler (kullanici_adi, sifre, eposta, telefon)
            VALUES (?, ?, ?, ?)
        ''', (kullanici_adi, sifre, eposta, telefon))
        conn.commit()
        print(f"Müşteri '{kullanici_adi}' başarıyla eklendi.")
    except sqlite3.IntegrityError:
        print(f"Hata: Kullanıcı adı '{kullanici_adi}' zaten mevcut.")
    finally:
        conn.close()

def kuafor_ekle(ad_soyad, uzmanlik_alani):
    conn, cursor = connect_db()
    try:
        cursor.execute('''
            INSERT INTO kuaforler (ad_soyad, uzmanlik_alani)
            VALUES (?, ?)
        ''', (ad_soyad, uzmanlik_alani))
        conn.commit()
        print(f"Kuaför '{ad_soyad}' başarıyla eklendi.")
    except Exception as e:
        print(f"Kuaför eklenirken bir hata oluştu: {e}")
    finally:
        conn.close()

def hizmet_ekle(hizmet_adi, fiyat, tahmini_sure_dk):
    conn, cursor = connect_db()
    try:
        cursor.execute('''
            INSERT INTO hizmetler (hizmet_adi, fiyat, tahmini_sure_dk)
            VALUES (?, ?, ?)
        ''', (hizmet_adi, fiyat, tahmini_sure_dk))
        conn.commit()
        print(f"Hizmet '{hizmet_adi}' başarıyla eklendi.")
    except sqlite3.IntegrityError:
        print(f"Hata: Hizmet adı '{hizmet_adi}' zaten mevcut.")
    finally:
        conn.close()

def randevu_olustur(musteri_id, kuafor_id, hizmet_id, tarih, saat):
    conn, cursor = connect_db()
    try:
        cursor.execute('''
            INSERT INTO randevular (musteri_id, kuafor_id, hizmet_id, randevu_tarihi, randevu_saati)
            VALUES (?, ?, ?, ?, ?)
        ''', (musteri_id, kuafor_id, hizmet_id, tarih, saat))
        conn.commit()
        print(f"Randevu başarıyla oluşturuldu: Müşteri ID: {musteri_id}, Kuaför ID: {kuafor_id}, Tarih: {tarih} {saat}")
    except Exception as e:
        print(f"Randevu oluşturulurken bir hata oluştu: {e}")
    finally:
        conn.close()

def randevulari_goruntule():
    conn, cursor = connect_db()
    cursor.execute('''
        SELECT
            r.id AS randevu_id,
            m.kullanici_adi AS musteri_adi,
            k.ad_soyad AS kuafor_adi,
            h.hizmet_adi,
            h.fiyat,
            h.tahmini_sure_dk,
            r.randevu_tarihi,
            r.randevu_saati,
            r.durum
        FROM randevular r
        JOIN musteriler m ON r.musteri_id = m.id
        JOIN kuaforler k ON r.kuafor_id = k.id
        JOIN hizmetler h ON r.hizmet_id = h.id
        ORDER BY r.randevu_tarihi, r.randevu_saati
    ''')
    randevular = cursor.fetchall()
    conn.close()

    if not randevular:
        print("Henüz hiç randevu bulunmamaktadır.")
        return

    print("\nTüm Randevular:")
    for randevu in randevular:
        print(f"ID: {randevu['randevu_id']}, Müşteri: {randevu['musteri_adi']}, Kuaför: {randevu['kuafor_adi']}, "
              f"Hizmet: {randevu['hizmet_adi']} ({randevu['fiyat']} TL, {randevu['tahmini_sure_dk']} dk), "
              f"Tarih: {randevu['randevu_tarihi']} {randevu['randevu_saati']}, Durum: {randevu['durum']}")

if __name__ == '__main__':
    create_tables()

    print("\n--- Uygulama Başladı ---")

    print("\n--- Uygulama Bitti ---")

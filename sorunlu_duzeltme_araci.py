#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sorunlu Sözcükleri Düzeltme Aracı
"""

import os
import sys
import sqlite3
import argparse
import time
import json
from typing import List, Dict, Tuple, Optional

def veritabanini_baglat(veritabani_yolu: str) -> sqlite3.Connection:
    """Veritabanına bağlanır"""
    if not os.path.exists(veritabani_yolu):
        print(f"Hata: Veritabanı bulunamadı: {veritabani_yolu}")
        sys.exit(1)
    
    try:
        conn = sqlite3.connect(veritabani_yolu)
        return conn
    except sqlite3.Error as e:
        print(f"Veritabanı bağlantı hatası: {e}")
        sys.exit(1)

def sorunlu_sozcukleri_getir(conn: sqlite3.Connection, limit: int = 50, sirala: str = 'frekans') -> List[Dict]:
    """Sorunlu sözcükleri getirir"""
    cursor = conn.cursor()
    
    # Önce sorunlu_sozcukler_detay tablosunun var olup olmadığını kontrol et
    cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name='sorunlu_sozcukler_detay'
    """)
    
    detay_tablo_var = cursor.fetchone() is not None
    
    if detay_tablo_var:
        # Detaylı tabloyu kullan (daha fazla bilgi içerir)
        if sirala == 'frekans':
            siralama = "ORDER BY frekans DESC"
        elif sirala == 'alfabe':
            siralama = "ORDER BY sozcuk ASC"
        else:
            siralama = "ORDER BY belge_frekansi DESC, frekans DESC"
            
        cursor.execute(f"""
        SELECT id, sozcuk, frekans, belge_frekansi, kaynak, belgeler, durum, eklenme_tarihi
        FROM sorunlu_sozcukler_detay
        WHERE durum = 'beklemede' OR durum = 'çözülemedi'
        {siralama}
        LIMIT ?
        """, (limit,))
    else:
        # Eski tabloyu kullan
        cursor.execute("""
        SELECT id, sozcuk, durum, not_metni as belgeler, deneme_sayisi as frekans
        FROM sorunlu_sozcukler
        WHERE durum = 'beklemede' OR durum = 'çözülemedi'
        ORDER BY deneme_sayisi DESC
        LIMIT ?
        """, (limit,))
    
    sonuclar = []
    for row in cursor.fetchall():
        sonuc = {}
        for i, column in enumerate(cursor.description):
            sonuc[column[0]] = row[i]
        sonuclar.append(sonuc)
    
    return sonuclar

def dosyalarda_bul(sozcuk: str, belgeler_str: str) -> List[Tuple[str, int, List[str]]]:
    """Sözcüğün geçtiği satırları dosyalarda bulur"""
    if not belgeler_str:
        return []
    
    dosya_bilgileri = []
    for belge_info in belgeler_str.split(";"):
        if not belge_info.strip():
            continue
            
        try:
            dosya_yolu, sayi_str = belge_info.strip().split(":")
            dosya_yolu = dosya_yolu.strip()
            sayi = int(sayi_str)
            
            # Dosyayı oku
            if os.path.exists(dosya_yolu):
                with open(dosya_yolu, 'r', encoding='utf-8', errors='ignore') as f:
                    satirlar = f.readlines()
                
                # Sözcüğü içeren satırları bul
                bulunan_satirlar = []
                for i, satir in enumerate(satirlar):
                    if sozcuk.lower() in satir.lower():
                        bulunan_satirlar.append(f"{i+1}: {satir.strip()}")
                
                if bulunan_satirlar:
                    dosya_bilgileri.append((dosya_yolu, sayi, bulunan_satirlar))
            else:
                print(f"Dosya bulunamadı: {dosya_yolu}")
        except Exception as e:
            print(f"Dosya okuma hatası: {belge_info} - {e}")
    
    return dosya_bilgileri

def kok_ve_ek_tahmini_yap(sozcuk: str, conn: sqlite3.Connection) -> List[Tuple[str, str]]:
    """Sözcük için olası kök ve ek tahminleri yapar"""
    cursor = conn.cursor()
    
    # Kökler tablosundan olası kökler
    cursor.execute("""
    SELECT kok, tur
    FROM kokler
    WHERE ? LIKE kok || '%'
    ORDER BY LENGTH(kok) DESC
    LIMIT 5
    """, (sozcuk,))
    
    olasi_kokler = cursor.fetchall()
    
    # Ekler tablosundan olası ekler (en sık kullanılanlar)
    cursor.execute("""
    SELECT ek, kategori
    FROM ekler
    ORDER BY frekans DESC
    LIMIT 10
    """)
    
    olasi_ekler = cursor.fetchall()
    
    # Kökler ve eklerden tahminler oluştur
    tahminler = []
    
    if olasi_kokler:
        # En uzun köklerle başla (greedy yaklaşım)
        for kok, tur in olasi_kokler:
            if sozcuk.startswith(kok):
                ek_kismi = sozcuk[len(kok):]
                if not ek_kismi:
                    tahminler.append((kok, ""))
                else:
                    # Ek kısmı için uygun ekler bul
                    for ek, kategori in olasi_ekler:
                        if ek_kismi == ek or ek_kismi.endswith(ek):
                            tahminler.append((kok, ek))
                    
                    # Hiç uygun ek bulunamadıysa, ek kısmını olduğu gibi ekle
                    if not any(tahmin[0] == kok for tahmin in tahminler):
                        tahminler.append((kok, ek_kismi))
    
    return tahminler

def sozcuk_duzenle(conn: sqlite3.Connection, sozcuk_id: int, kok: str, tur: str, ek: str = "") -> bool:
    """Sözcüğü düzenler ve veritabanına kaydeder"""
    cursor = conn.cursor()
    
    # Sorunlu sözcüğü getir
    cursor.execute("SELECT sozcuk FROM sorunlu_sozcukler WHERE id = ?", (sozcuk_id,))
    row = cursor.fetchone()
    if not row:
        print(f"Hata: {sozcuk_id} ID'li sorunlu sözcük bulunamadı.")
        return False
    
    sozcuk = row[0]
    
    try:
        # Kök ekle/güncelle
        cursor.execute("""
        INSERT INTO kokler (kok, tur, kaynak) 
        VALUES (?, ?, 'manuel_duzeltme')
        ON CONFLICT(kok) DO UPDATE SET frekans = frekans + 1
        """, (kok, tur))
        
        # Kök ID'sini al
        cursor.execute("SELECT id FROM kokler WHERE kok = ?", (kok,))
        kok_id = cursor.fetchone()[0]
        
        # Analiz sonucunu oluştur
        analiz_sonuc = {
            'kok': kok,
            'ekler': [(ek, 'manuel_duzeltme')] if ek else [],
            'source': 'manuel_duzeltme'
        }
        
        # Sorunlu sözcük analizini kaydet
        cursor.execute("""
        INSERT INTO sozcuk_analizleri (sozcuk, kok_id, analiz_json)
        VALUES (?, ?, ?)
        ON CONFLICT(sozcuk) DO UPDATE SET 
        kok_id = ?, analiz_json = ?, frekans = frekans + 1
        """, (sozcuk, kok_id, json.dumps(analiz_sonuc), kok_id, json.dumps(analiz_sonuc)))
        
        # Sorunlu sözcük durumunu güncelle
        cursor.execute("""
        UPDATE sorunlu_sozcukler 
        SET durum = 'çözüldü', not_metni = ? 
        WHERE id = ?
        """, (f"Kök: {kok}, Ek: {ek}, Tür: {tur}", sozcuk_id))
        
        # Detay tablosunu güncelle (varsa)
        try:
            cursor.execute("""
            UPDATE sorunlu_sozcukler_detay 
            SET durum = 'çözüldü' 
            WHERE sozcuk = ?
            """, (sozcuk,))
        except sqlite3.Error:
            pass  # Tablo yoksa hata verme
        
        conn.commit()
        return True
        
    except sqlite3.Error as e:
        print(f"Veritabanı güncelleme hatası: {e}")
        conn.rollback()
        return False

def interaktif_menu(conn: sqlite3.Connection):
    """Sorunlu sözcükleri düzeltmek için interaktif menü"""
    while True:
        print("\n=== SORUNLU SÖZCÜK DÜZELTME ARACI ===")
        print("1. En sık kullanılan sorunlu sözcükleri göster")
        print("2. Alfabetik sırayla sorunlu sözcükleri göster")
        print("3. En çok belgede geçen sorunlu sözcükleri göster")
        print("4. Bir sözcüğü düzelt")
        print("5. Toplu düzeltme (ID listesi ile)")
        print("0. Çıkış")
        
        secim = input("\nSeçiminiz: ")
        
        if secim == "0":
            break
            
        elif secim in ("1", "2", "3"):
            limit = int(input("Kaç sözcük listelensin? (varsayılan: 20): ") or "20")
            
            if secim == "1":
                sorunlu_sozckler = sorunlu_sozcukleri_getir(conn, limit, 'frekans')
            elif secim == "2":
                sorunlu_sozckler = sorunlu_sozcukleri_getir(conn, limit, 'alfabe')
            else:
                sorunlu_sozckler = sorunlu_sozcukleri_getir(conn, limit, 'belge')
            
            if not sorunlu_sozckler:
                print("Hiç sorunlu sözcük bulunamadı.")
                continue
                
            print("\nID  | Sözcük       | Frekans | Belge Sayısı | Kaynak")
            print("-" * 60)
            
            for s in sorunlu_sozckler:
                belge_frekansi = s.get('belge_frekansi', 0)
                kaynak = s.get('kaynak', 'N/A')
                print(f"{s['id']:<4}| {s['sozcuk']:<13}| {s['frekans']:<8}| {belge_frekansi:<13}| {kaynak}")
        
        elif secim == "4":
            sozcuk_id = int(input("\nDüzeltilecek sözcüğün ID'si: "))
            
            # Sözcük bilgilerini al
            cursor = conn.cursor()
            cursor.execute("""
            SELECT sozcuk, belgeler, durum
            FROM sorunlu_sozcukler_detay
            WHERE id = ?
            """, (sozcuk_id,))
            
            row = cursor.fetchone()
            if not row:
                cursor.execute("""
                SELECT sozcuk, not_metni as belgeler, durum
                FROM sorunlu_sozcukler
                WHERE id = ?
                """, (sozcuk_id,))
                row = cursor.fetchone()
                
            if not row:
                print(f"Hata: {sozcuk_id} ID'li sözcük bulunamadı.")
                continue
                
            sozcuk, belgeler, durum = row
            
            print(f"\nSeçilen sözcük: {sozcuk}")
            print(f"Durum: {durum}")
            
            # Sözcüğün geçtiği dosyaları ve satırları bul
            dosya_bilgileri = dosyalarda_bul(sozcuk, belgeler)
            
            if dosya_bilgileri:
                print("\nSözcüğün geçtiği dosyalar:")
                for i, (dosya, sayi, satirlar) in enumerate(dosya_bilgileri):
                    print(f"\n{i+1}. {dosya} ({sayi} kez):")
                    for j, satir in enumerate(satirlar[:5]):  # İlk 5 satırı göster
                        print(f"   {satir}")
                    if len(satirlar) > 5:
                        print(f"   ... ve {len(satirlar)-5} satır daha")
            
            # Olası kök ve ek tahminleri
            tahminler = kok_ve_ek_tahmini_yap(sozcuk, conn)
            
            if tahminler:
                print("\nOlası kök-ek kombinasyonları:")
                for i, (kok, ek) in enumerate(tahminler):
                    print(f"{i+1}. Kök: '{kok}', Ek: '{ek}'")
            
            # Düzeltme bilgilerini al
            print("\nDüzeltme bilgilerini girin (veya 'iptal' yazın):")
            
            if tahminler:
                tahmin_secimi = input("Tahmini seçin (numara) veya manuel giriş için boş bırakın: ")
                if tahmin_secimi.lower() == 'iptal':
                    continue
                    
                if tahmin_secimi.isdigit() and 1 <= int(tahmin_secimi) <= len(tahminler):
                    secilen_tahmin = tahminler[int(tahmin_secimi) - 1]
                    kok, ek = secilen_tahmin
                    tur = input(f"Kök türü [isim/fiil/sıfat/zarf/zamir] (varsayılan: isim): ") or "isim"
                else:
                    kok = input("Kök: ")
                    if not kok:
                        print("Kök boş olamaz.")
                        continue
                    if kok.lower() == 'iptal':
                        continue
                        
                    ek = input("Ek (yoksa boş bırakın): ")
                    tur = input("Kök türü [isim/fiil/sıfat/zarf/zamir] (varsayılan: isim): ") or "isim"
            else:
                kok = input("Kök: ")
                if not kok:
                    print("Kök boş olamaz.")
                    continue
                if kok.lower() == 'iptal':
                    continue
                    
                ek = input("Ek (yoksa boş bırakın): ")
                tur = input("Kök türü [isim/fiil/sıfat/zarf/zamir] (varsayılan: isim): ") or "isim"
            
            # Düzeltmeyi uygula
            if sozcuk_duzenle(conn, sozcuk_id, kok, tur, ek):
                print(f"\n'{sozcuk}' sözcüğü başarıyla düzeltildi: Kök='{kok}', Ek='{ek}', Tür='{tur}'")
            else:
                print("Düzeltme başarısız oldu.")
        
        elif secim == "5":
            id_listesi_str = input("\nDüzeltilecek sözcüklerin ID'lerini virgülle ayırarak girin: ")
            id_listesi = [int(id_str.strip()) for id_str in id_listesi_str.split(",") if id_str.strip().isdigit()]
            
            if not id_listesi:
                print("Geçerli bir ID listesi girilmedi.")
                continue
                
            print(f"\nToplu düzeltme için {len(id_listesi)} sözcük seçildi.")
            print("Her sözcük için kök ve tür bilgisi girmeniz gerekecek.")
            
            basarili = 0
            basarisiz = 0
            
            for sozcuk_id in id_listesi:
                # Sözcük bilgilerini al
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT sozcuk FROM sorunlu_sozcukler WHERE id = ?", (sozcuk_id,))
                    row = cursor.fetchone()
                    if not row:
                        print(f"Hata: {sozcuk_id} ID'li sözcük bulunamadı.")
                        basarisiz += 1
                        continue
                        
                    sozcuk = row[0]
                    print(f"\nSözcük: {sozcuk} (ID: {sozcuk_id})")
                    
                    tahminler = kok_ve_ek_tahmini_yap(sozcuk, conn)
                    if tahminler:
                        print("Olası kök-ek kombinasyonları:")
                        for i, (kok, ek) in enumerate(tahminler):
                            print(f"{i+1}. Kök: '{kok}', Ek: '{ek}'")
                    
                    tahmin_secimi = input("Tahmini seçin (numara) veya manuel giriş için boş bırakın: ")
                    if tahmin_secimi.lower() == 'atla':
                        print(f"'{sozcuk}' sözcüğü atlandı.")
                        continue
                        
                    if tahminler and tahmin_secimi.isdigit() and 1 <= int(tahmin_secimi) <= len(tahminler):
                        secilen_tahmin = tahminler[int(tahmin_secimi) - 1]
                        kok, ek = secilen_tahmin
                        tur = input(f"Kök türü [isim/fiil/sıfat/zarf/zamir] (varsayılan: isim): ") or "isim"
                    else:
                        kok = input("Kök: ")
                        if not kok:
                            print("Kök boş olamaz, sözcük atlandı.")
                            basarisiz += 1
                            continue
                        if kok.lower() == 'atla':
                            print(f"'{sozcuk}' sözcüğü atlandı.")
                            continue
                            
                        ek = input("Ek (yoksa boş bırakın): ")
                        tur = input("Kök türü [isim/fiil/sıfat/zarf/zamir] (varsayılan: isim): ") or "isim"
                    
                    # Düzeltmeyi uygula
                    if sozcuk_duzenle(conn, sozcuk_id, kok, tur, ek):
                        print(f"'{sozcuk}' sözcüğü başarıyla düzeltildi: Kök='{kok}', Ek='{ek}', Tür='{tur}'")
                        basarili += 1
                    else:
                        print(f"'{sozcuk}' sözcüğü düzeltme başarısız oldu.")
                        basarisiz += 1
                        
                except Exception as e:
                    print(f"İşlem sırasında hata: {e}")
                    basarisiz += 1
            
            print(f"\nToplu düzeltme tamamlandı. Başarılı: {basarili}, Başarısız: {basarisiz}")
        
        else:
            print("Geçersiz seçim, tekrar deneyin.")
    
    print("Program kapatılıyor...")

def main():
    """Ana program fonksiyonu"""
    parser = argparse.ArgumentParser(description='Sorunlu Sözcükleri Düzeltme Aracı')
    parser.add_argument('--veritabani', '-db', default='turkce_morfoloji.db', help='Veritabanı dosya yolu')
    
    args = parser.parse_args()
    
    # Veritabanına bağlan
    conn = veritabanini_baglat(args.veritabani)
    
    try:
        # İnteraktif menüyü başlat
        interaktif_menu(conn)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
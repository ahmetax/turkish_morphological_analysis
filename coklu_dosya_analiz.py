#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Morfolojik Analiz - Toplu Dosya İşleme Aracı
Klasör veya tek dosya analizi yapabilir
"""

import os
import re
import argparse
import time
import glob
from typing import Dict, Set, List, Tuple

def temizle_ve_parcala(metin: str, sayilari_atla: bool = True) -> Set[str]:
    """Metni temizler ve tekil sözcüklere ayırır"""
    # Noktalama işaretlerini temizle
    temiz_metin = re.sub(r'[^\w\s]', ' ', metin)
    
    # Sözcüklere ayır ve küçük harfe çevir
    if sayilari_atla:
        # Sayı içermeyen sözcükleri seç
        sozcukler = {s.lower() for s in temiz_metin.split() 
                    if s and len(s) > 1 and not s.isdigit() and not re.match(r'^\d+[a-zA-Z]*$', s)}
    else:
        # Tüm sözcükleri seç
        sozcukler = {s.lower() for s in temiz_metin.split() if s and len(s) > 1}
    
    return sozcukler

def dosya_oku(dosya_yolu: str) -> str:
    """Metin dosyasını okur, farklı kodlamaları dener"""
    kodlamalar = ['utf-8', 'latin-1', 'windows-1254', 'iso-8859-9']
    
    for kodlama in kodlamalar:
        try:
            with open(dosya_yolu, 'r', encoding=kodlama) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # Hiçbir kodlama çalışmazsa, binary olarak oku ve decode edebileceğimiz karakterleri al
    try:
        with open(dosya_yolu, 'rb') as f:
            return f.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"HATA: {dosya_yolu} dosyası okunamadı: {e}")
        return ""

def analiz_et(sozcukler: Set[str], veritabani_yolu: str, zemberek_aktif: bool = False) -> Dict:
    """Sözcükleri analiz et"""
    from turkce_morfologik_analiz import TurkceMorfologikAnaliz
    
    print(f"Toplam {len(sozcukler)} benzersiz sözcük analiz edilecek.")
    
    # Analizci oluştur
    analizci = TurkceMorfologikAnaliz(
        veritabani_path=veritabani_yolu,
        zemberek_jar_path="zemberek-full.jar" if zemberek_aktif else "non-existent.jar",
        interaktif=False,
        zemberek_oncelikli=zemberek_aktif
    )
    
    sonuclar = {}
    islenecek_toplam = len(sozcukler)
    
    baslangic = time.time()
    for i, sozcuk in enumerate(sorted(sozcukler)):
        sonuclar[sozcuk] = analizci.parcala(sozcuk)
        
        # İlerleme göster
        if (i+1) % 100 == 0 or i+1 == islenecek_toplam:
            gecen_sure = time.time() - baslangic
            hiz = (i+1) / gecen_sure if gecen_sure > 0 else 0
            kalan_sure = (islenecek_toplam - (i+1)) / hiz if hiz > 0 else 0
            print(f"\rİlerleme: {i+1}/{islenecek_toplam} sözcük ({(i+1)/islenecek_toplam*100:.1f}%) | "
                  f"Hız: {hiz:.1f} sözcük/sn | Kalan: {kalan_sure:.1f} sn", end="")
    
    print()  # Yeni satır
    
    analizci.kapat()
    
    bitis = time.time()
    toplam_sure = bitis - baslangic
    print(f"\nAnaliz tamamlandı. {len(sonuclar)} sözcük {toplam_sure:.2f} saniyede işlendi.")
    print(f"Ortalama hız: {len(sonuclar) / toplam_sure:.2f} sözcük/saniye")
    
    return sonuclar

def klasordeki_dosyalari_bul(klasor_yolu: str, uzanti: str = ".txt") -> List[str]:
    """Belirtilen klasördeki tüm dosyaları bulur"""
    if not os.path.exists(klasor_yolu):
        print(f"HATA: Klasör bulunamadı: {klasor_yolu}")
        return []
    
    dosya_yollari = []
    
    # Klasördeki tüm dosyaları ve alt klasörleri dolaş
    for root, dirs, files in os.walk(klasor_yolu):
        for file in files:
            if file.endswith(uzanti):
                dosya_yolu = os.path.join(root, file)
                dosya_yollari.append(dosya_yolu)
    
    print(f"{len(dosya_yollari)} adet {uzanti} dosyası bulundu.")
    return dosya_yollari

def dosyalari_analiz_et(dosya_yollari: List[str], veritabani_yolu: str, 
                       cikti_klasoru: str, ozet_dosyasi: str,
                       zemberek_aktif: bool = False, sayilari_atla: bool = True) -> Dict:
    """Birden fazla dosyayı analiz eder ve sonuçları dosya başına kaydeder"""
    if not dosya_yollari:
        print("İşlenecek dosya bulunamadı.")
        return {}
    
    # Çıktı klasörünü oluştur
    if not os.path.exists(cikti_klasoru):
        os.makedirs(cikti_klasoru)
        print(f"Çıktı klasörü oluşturuldu: {cikti_klasoru}")
    
    tum_sozcukler = set()
    dosya_analiz_sonuclari = {}
    
    # Tüm dosyaları oku ve sözcükleri topla
    for i, dosya_yolu in enumerate(dosya_yollari):
        print(f"\n[{i+1}/{len(dosya_yollari)}] Dosya okunuyor: {dosya_yolu}")
        metin = dosya_oku(dosya_yolu)
        sozcukler = temizle_ve_parcala(metin, sayilari_atla)
        
        # Sözcükleri genel havuza ekle
        tum_sozcukler.update(sozcukler)
        
        # Dosya bazında sözcük listesini kaydet
        dosya_analiz_sonuclari[dosya_yolu] = sozcukler
        
        print(f"  Dosyadan {len(sozcukler)} benzersiz sözcük çıkarıldı.")
    
    print(f"\nToplam {len(tum_sozcukler)} benzersiz sözcük bulundu.")
    
    # Tüm sözcükleri analiz et
    sonuclar = analiz_et(tum_sozcukler, veritabani_yolu, zemberek_aktif)
    
    # Her dosya için ayrı analiz sonucu dosyası oluştur
    for dosya_yolu, sozcukler in dosya_analiz_sonuclari.items():
        dosya_adi = os.path.basename(dosya_yolu)
        cikti_dosyasi = os.path.join(cikti_klasoru, f"{os.path.splitext(dosya_adi)[0]}_analiz.txt")
        
        with open(cikti_dosyasi, 'w', encoding='utf-8') as f:
            f.write(f"# Dosya: {dosya_yolu}\n")
            f.write(f"# Toplam sözcük sayısı: {len(sozcukler)}\n\n")
            
            for sozcuk in sorted(sozcukler):
                sonuc = sonuclar.get(sozcuk, {'kok': sozcuk, 'ekler': [], 'source': 'bilinmiyor'})
                ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in sonuc.get('ekler', [])])
                f.write(f"{sozcuk} -> Kök: {sonuc.get('kok', sozcuk)}, " 
                       f"Ekler: {ekler_str if ekler_str else 'Yok'}, "
                       f"Kaynak: {sonuc.get('source', 'belirsiz')}\n")
        
        print(f"Dosya analizi kaydedildi: {cikti_dosyasi}")
    
    # Tüm sonuçları özet dosyasına yaz
    if ozet_dosyasi:
        with open(ozet_dosyasi, 'w', encoding='utf-8') as f:
            f.write(f"# Toplam {len(dosya_yollari)} dosya analiz edildi\n")
            f.write(f"# Toplam {len(tum_sozcukler)} benzersiz sözcük bulundu\n\n")
            
            for sozcuk, sonuc in sorted(sonuclar.items()):
                ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in sonuc.get('ekler', [])])
                f.write(f"{sozcuk} -> Kök: {sonuc.get('kok', sozcuk)}, " 
                       f"Ekler: {ekler_str if ekler_str else 'Yok'}, "
                       f"Kaynak: {sonuc.get('source', 'belirsiz')}\n")
        
        print(f"Özet sonuçlar kaydedildi: {ozet_dosyasi}")
    
    return sonuclar

def main():
    """Ana program fonksiyonu"""
    parser = argparse.ArgumentParser(description='Türkçe Morfolojik Analiz - Toplu Dosya İşleme Aracı')
    parser.add_argument('--dosya', '-f', help='İşlenecek tek metin dosyası')
    parser.add_argument('--klasor', '-k', help='İşlenecek metin dosyalarının bulunduğu klasör')
    parser.add_argument('--uzanti', '-u', default='.txt', help='İşlenecek dosya uzantısı (varsayılan: .txt)')
    parser.add_argument('--veritabani', '-db', default='turkce_morfoloji.db', help='Veritabanı dosya yolu')
    parser.add_argument('--cikti-klasoru', '-c', default='analiz_sonuclari', help='Çıktı dosyalarının kaydedileceği klasör')
    parser.add_argument('--ozet', '-o', default='tum_sonuclar.txt', help='Tüm sonuçların özet dosyası')
    parser.add_argument('--zemberek', '-z', action='store_true', help='Zemberek kullan')
    parser.add_argument('--sayilari-dahil-et', '-s', action='store_true', help='Sayıları analize dahil et')
    
    args = parser.parse_args()
    
    # Dosya veya klasör kontrolü
    if not args.dosya and not args.klasor:
        print("Hata: Dosya veya klasör belirtilmelidir.")
        parser.print_help()
        return
    
    # Tek dosya analizi
    if args.dosya:
        if not os.path.exists(args.dosya):
            print(f"Hata: Dosya bulunamadı: {args.dosya}")
            return
            
        dosya_yollari = [args.dosya]
    
    # Klasör analizi
    else:
        dosya_yollari = klasordeki_dosyalari_bul(args.klasor, args.uzanti)
    
    # Analiz başlat
    dosyalari_analiz_et(
        dosya_yollari=dosya_yollari,
        veritabani_yolu=args.veritabani,
        cikti_klasoru=args.cikti_klasoru,
        ozet_dosyasi=args.ozet,
        zemberek_aktif=args.zemberek,
        sayilari_atla=not args.sayilari_dahil_et
    )

if __name__ == "__main__":
    main()

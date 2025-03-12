#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Morfolojik Analiz - Basitleştirilmiş Analiz Aracı
Sayıları Filtreleyen Versiyon
"""

import os
import re
import argparse
import time
from typing import Dict, Set

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

def analiz_et(sozcukler, veritabani_yolu, zemberek_aktif=False):
    """Sözcükleri analiz et"""
    from turkce_morfologik_analiz import TurkceMorfologikAnaliz
    
    print(f"Toplam {len(sozcukler)} sözcük analiz edilecek.")
    
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

def dosyadan_analiz_et(dosya_yolu, veritabani_yolu, zemberek_aktif=False, cikti_dosyasi=None, sayilari_atla=True):
    """Dosyadan okuyarak analiz yapar"""
    start_time = time.time()
    try:
        with open(dosya_yolu, 'r', encoding='utf-8') as f:
            metin = f.read()
    except UnicodeDecodeError:
        # UTF-8 ile açılmazsa Latin-1 dene
        with open(dosya_yolu, 'r', encoding='latin-1') as f:
            metin = f.read()
    
    print(f"Dosya okuma: {time.time() - start_time:.2f} saniye")
    
    # Metni temizle ve sözcüklere ayır
    start_time = time.time()
    sozcukler = temizle_ve_parcala(metin, sayilari_atla)
    print(f"Metin temizleme: {time.time() - start_time:.2f} saniye")
    
    # Analiz et
    sonuclar = analiz_et(sozcukler, veritabani_yolu, zemberek_aktif)
    
    # Çıktı dosyasına yaz
    if cikti_dosyasi:
        with open(cikti_dosyasi, 'w', encoding='utf-8') as f:
            for sozcuk, sonuc in sorted(sonuclar.items()):
                ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in sonuc.get('ekler', [])])
                f.write(f"{sozcuk} -> Kök: {sonuc.get('kok', sozcuk)}, " 
                        f"Ekler: {ekler_str if ekler_str else 'Yok'}, "
                        f"Kaynak: {sonuc.get('source', 'belirsiz')}\n")
        print(f"Sonuçlar {cikti_dosyasi} dosyasına yazıldı.")
    
    return sonuclar

def main():
    """Ana program fonksiyonu"""
    parser = argparse.ArgumentParser(description='Türkçe Morfolojik Analiz Aracı (Basit)')
    parser.add_argument('--dosya', '-f', required=True, help='İşlenecek metin dosyası')
    parser.add_argument('--veritabani', '-db', default='turkce_morfoloji.db', help='Veritabanı dosya yolu')
    parser.add_argument('--cikti', '-o', default='analiz_sonuclari.txt', help='Çıktı dosyası')
    parser.add_argument('--zemberek', '-z', action='store_true', help='Zemberek kullan')
    parser.add_argument('--sayilari-dahil-et', '-s', action='store_true', help='Sayıları analize dahil et')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dosya):
        print(f"Hata: Dosya bulunamadı: {args.dosya}")
        return
    
    # Analiz başlat
    dosyadan_analiz_et(
        dosya_yolu=args.dosya,
        veritabani_yolu=args.veritabani,
        zemberek_aktif=args.zemberek,
        cikti_dosyasi=args.cikti,
        sayilari_atla=not args.sayilari_dahil_et
    )

if __name__ == "__main__":
    main()

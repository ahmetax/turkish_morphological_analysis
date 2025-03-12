#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Morfolojik Analiz - Toplu Dosya İşleme ve Frekans Analizi Aracı
Klasör veya tek dosya analizi yapabilir ve sözcük frekanslarını hesaplar
"""

import os
import re
import argparse
import time
import glob
import csv
from collections import Counter, defaultdict
from typing import Dict, Set, List, Tuple, Counter as CounterType

class FrekansBilgisi:
    """Sözcük frekans bilgisi sınıfı"""
    def __init__(self, sozcuk: str):
        self.sozcuk = sozcuk
        self.toplam_frekans = 0  # Tüm metinlerdeki toplam görülme sayısı
        self.belge_frekansi = 0  # Sözcüğün göründüğü belge sayısı
        self.belgeler = {}  # Belge başına frekans: {dosya_yolu: sayı}
        self.morfolojik_analiz = None  # Morfolojik analiz sonucu
        
    def belgeye_ekle(self, dosya_yolu: str, sayi: int = 1):
        """Sözcüğün belgedeki frekansını günceller"""
        self.toplam_frekans += sayi
        
        if dosya_yolu not in self.belgeler:
            self.belge_frekansi += 1
            self.belgeler[dosya_yolu] = sayi
        else:
            self.belgeler[dosya_yolu] += sayi
    
    def analiz_ekle(self, analiz_sonucu: dict):
        """Morfolojik analiz sonucunu ekler"""
        self.morfolojik_analiz = analiz_sonucu
        
    def get_kok(self) -> str:
        """Sözcüğün kökünü döndürür"""
        if self.morfolojik_analiz and 'kok' in self.morfolojik_analiz:
            return self.morfolojik_analiz['kok']
        return self.sozcuk
    
    def get_ekler(self) -> List[Tuple[str, str]]:
        """Sözcüğün eklerini döndürür"""
        if self.morfolojik_analiz and 'ekler' in self.morfolojik_analiz:
            return self.morfolojik_analiz['ekler']
        return []
    
    def get_kaynak(self) -> str:
        """Analiz kaynağını döndürür"""
        if self.morfolojik_analiz and 'source' in self.morfolojik_analiz:
            return self.morfolojik_analiz['source']
        return 'bilinmiyor'

def temizle_ve_parcala(metin: str, sayilari_atla: bool = True) -> Dict[str, int]:
    """Metni temizler ve sözcük frekanslarını döndürür"""
    # Noktalama işaretlerini temizle
    temiz_metin = re.sub(r'[^\w\s]', ' ', metin)
    
    # Sözcükleri ayır ve küçük harfe çevir
    sozcukler = temiz_metin.lower().split()
    
    # Sözcük frekanslarını sayar
    frekanslar = Counter()
    
    for sozcuk in sozcukler:
        if len(sozcuk) <= 1:  # Çok kısa sözcükleri atla
            continue
            
        if sayilari_atla and (sozcuk.isdigit() or re.match(r'^\d+[a-zA-Z]*$', sozcuk)):
            continue  # Sayıları atla
            
        frekanslar[sozcuk] += 1
        
    return frekanslar

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

def analiz_et(frekans_verileri: Dict[str, FrekansBilgisi], veritabani_yolu: str, zemberek_aktif: bool = False) -> None:
    """Sözcükleri analiz et ve frekans verilerine ekle"""
    from turkce_morfologik_analiz import TurkceMorfologikAnaliz
    
    sozcukler = list(frekans_verileri.keys())
    print(f"Toplam {len(sozcukler)} benzersiz sözcük analiz edilecek.")
    
    # Analizci oluştur
    analizci = TurkceMorfologikAnaliz(
        veritabani_path=veritabani_yolu,
        zemberek_jar_path="zemberek-full.jar" if zemberek_aktif else "non-existent.jar",
        interaktif=False,
        zemberek_oncelikli=zemberek_aktif
    )
    
    islenecek_toplam = len(sozcukler)
    
    baslangic = time.time()
    for i, sozcuk in enumerate(sorted(sozcukler)):
        analiz_sonuc = analizci.parcala(sozcuk)
        frekans_verileri[sozcuk].analiz_ekle(analiz_sonuc)
        
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
    print(f"\nAnaliz tamamlandı. {len(sozcukler)} sözcük {toplam_sure:.2f} saniyede işlendi.")
    print(f"Ortalama hız: {len(sozcukler) / toplam_sure:.2f} sözcük/saniye")

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
                       cikti_klasoru: str, ozet_dosyasi: str, csv_dosyasi: str,
                       zemberek_aktif: bool = False, sayilari_atla: bool = True) -> Dict[str, FrekansBilgisi]:
    """Birden fazla dosyayı analiz eder, frekans bilgilerini toplar"""
    if not dosya_yollari:
        print("İşlenecek dosya bulunamadı.")
        return {}
    
    # Çıktı klasörünü oluştur
    if not os.path.exists(cikti_klasoru):
        os.makedirs(cikti_klasoru)
        print(f"Çıktı klasörü oluşturuldu: {cikti_klasoru}")
    
    # Frekans verilerini topla
    frekans_verileri = {}  # {sozcuk: FrekansBilgisi}
    dosya_analiz_sonuclari = {}  # {dosya_yolu: {sozcuk: frekans}}
    
    # Tüm dosyaları oku ve frekans bilgilerini topla
    for i, dosya_yolu in enumerate(dosya_yollari):
        print(f"\n[{i+1}/{len(dosya_yollari)}] Dosya okunuyor: {dosya_yolu}")
        metin = dosya_oku(dosya_yolu)
        frekanslar = temizle_ve_parcala(metin, sayilari_atla)
        
        # Frekans verilerini güncelle
        for sozcuk, frekans in frekanslar.items():
            if sozcuk not in frekans_verileri:
                frekans_verileri[sozcuk] = FrekansBilgisi(sozcuk)
            
            frekans_verileri[sozcuk].belgeye_ekle(dosya_yolu, frekans)
        
        # Dosya bazında frekansları kaydet
        dosya_analiz_sonuclari[dosya_yolu] = frekanslar
        
        print(f"  Dosyadan {len(frekanslar)} benzersiz sözcük çıkarıldı (toplam kullanım: {sum(frekanslar.values())})")
    
    print(f"\nToplam {len(frekans_verileri)} benzersiz sözcük bulundu.")
    
    # Tüm sözcükleri analiz et
    analiz_et(frekans_verileri, veritabani_yolu, zemberek_aktif)
    
    # Her dosya için ayrı analiz sonucu dosyası oluştur
    for dosya_yolu, frekanslar in dosya_analiz_sonuclari.items():
        dosya_adi = os.path.basename(dosya_yolu)
        cikti_dosyasi = os.path.join(cikti_klasoru, f"{os.path.splitext(dosya_adi)[0]}_analiz.txt")
        
        with open(cikti_dosyasi, 'w', encoding='utf-8') as f:
            f.write(f"# Dosya: {dosya_yolu}\n")
            f.write(f"# Toplam sözcük sayısı: {sum(frekanslar.values())}\n")
            f.write(f"# Benzersiz sözcük sayısı: {len(frekanslar)}\n\n")
            f.write("# Sözcük\tFrekans\tKök\tEkler\tKaynak\n")
            
            # Frekansa göre sırala (en yüksekten en düşüğe)
            for sozcuk, frekans in sorted(frekanslar.items(), key=lambda x: x[1], reverse=True):
                veri = frekans_verileri[sozcuk]
                ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in veri.get_ekler()])
                
                f.write(f"{sozcuk}\t{frekans}\t{veri.get_kok()}\t{ekler_str if ekler_str else 'Yok'}\t{veri.get_kaynak()}\n")
        
        print(f"Dosya analizi kaydedildi: {cikti_dosyasi}")
    
    # Tüm sonuçları özet dosyasına yaz
    if ozet_dosyasi:
        with open(ozet_dosyasi, 'w', encoding='utf-8') as f:
            f.write(f"# Toplam {len(dosya_yollari)} dosya analiz edildi\n")
            f.write(f"# Toplam {len(frekans_verileri)} benzersiz sözcük bulundu\n\n")
            f.write("# Sözcük\tToplam_Frekans\tBelge_Frekansı\tKök\tEkler\tKaynak\n")
            
            # Frekansa göre sırala (en yüksekten en düşüğe)
            for sozcuk, veri in sorted(frekans_verileri.items(), key=lambda x: x[1].toplam_frekans, reverse=True):
                ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in veri.get_ekler()])
                
                f.write(f"{sozcuk}\t{veri.toplam_frekans}\t{veri.belge_frekansi}\t{veri.get_kok()}\t"
                       f"{ekler_str if ekler_str else 'Yok'}\t{veri.get_kaynak()}\n")
        
        print(f"Özet sonuçlar kaydedildi: {ozet_dosyasi}")
    
    # CSV formatında kaydet
    if csv_dosyasi:
        with open(csv_dosyasi, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Sözcük", "Toplam_Frekans", "Belge_Frekansı", "Kök", "Ekler", "Kaynak"])
            
            # Frekansa göre sırala (en yüksekten en düşüğe)
            for sozcuk, veri in sorted(frekans_verileri.items(), key=lambda x: x[1].toplam_frekans, reverse=True):
                ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in veri.get_ekler()])
                
                writer.writerow([
                    sozcuk, 
                    veri.toplam_frekans, 
                    veri.belge_frekansi, 
                    veri.get_kok(),
                    ekler_str if ekler_str else 'Yok',
                    veri.get_kaynak()
                ])
        
        print(f"CSV sonuçlar kaydedildi: {csv_dosyasi}")
    
    return frekans_verileri

def main():
    """Ana program fonksiyonu"""
    parser = argparse.ArgumentParser(description='Türkçe Morfolojik Analiz - Toplu Dosya ve Frekans Analizi Aracı')
    parser.add_argument('--dosya', '-f', help='İşlenecek tek metin dosyası')
    parser.add_argument('--klasor', '-k', help='İşlenecek metin dosyalarının bulunduğu klasör')
    parser.add_argument('--uzanti', '-u', default='.txt', help='İşlenecek dosya uzantısı (varsayılan: .txt)')
    parser.add_argument('--veritabani', '-db', default='turkce_morfoloji.db', help='Veritabanı dosya yolu')
    parser.add_argument('--cikti-klasoru', '-c', default='analiz_sonuclari', help='Çıktı dosyalarının kaydedileceği klasör')
    parser.add_argument('--ozet', '-o', default='tum_sonuclar.txt', help='Tüm sonuçların özet dosyası')
    parser.add_argument('--csv', '-csv', default='frekans_analizi.csv', help='CSV format özet dosyası')
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
        csv_dosyasi=args.csv,
        zemberek_aktif=args.zemberek,
        sayilari_atla=not args.sayilari_dahil_et
    )

if __name__ == "__main__":
    main()

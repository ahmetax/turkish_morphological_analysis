#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Morfolojik Analiz - Raporlama Aracı
"""

import sqlite3
import argparse
import os
import json
import csv
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
from collections import Counter

class MorfolojiRaporAracı:
    """Morfolojik analiz için raporlama ve istatistik aracı"""
    
    def __init__(self, veritabani_path: str = "turkce_morfoloji.db"):
        self.db_path = veritabani_path
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Veritabanı bulunamadı: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def kapat(self):
        """Veritabanı bağlantısını kapatır"""
        if self.conn:
            self.conn.close()
    
    def get_istatistikler(self) -> Dict:
        """Veritabanından genel istatistikleri çeker"""
        cursor = self.conn.cursor()
        
        istatistikler = {}
        
        # Kök istatistikleri
        cursor.execute("SELECT COUNT(*) as sayi FROM kokler")
        istatistikler['kok_sayisi'] = cursor.fetchone()['sayi']
        
        cursor.execute("SELECT tur, COUNT(*) as sayi FROM kokler GROUP BY tur")
        istatistikler['kok_turleri'] = {row['tur']: row['sayi'] for row in cursor.fetchall()}
        
        # Ek istatistikleri
        cursor.execute("SELECT COUNT(*) as sayi FROM ekler")
        istatistikler['ek_sayisi'] = cursor.fetchone()['sayi']
        
        cursor.execute("SELECT kategori, COUNT(*) as sayi FROM ekler GROUP BY kategori")
        istatistikler['ek_kategorileri'] = {row['kategori']: row['sayi'] for row in cursor.fetchall()}
        
        # Analiz istatistikleri
        cursor.execute("SELECT COUNT(*) as sayi FROM sozcuk_analizleri")
        istatistikler['analiz_sayisi'] = cursor.fetchone()['sayi']
        
        cursor.execute("SELECT COUNT(*) as sayi FROM sorunlu_sozcukler")
        istatistikler['sorunlu_sayi'] = cursor.fetchone()['sayi']
        
        cursor.execute("SELECT SUM(frekans) as toplam FROM sozcuk_analizleri")
        istatistikler['toplam_islem'] = cursor.fetchone()['toplam']
        
        # Kaynak istatistikleri
        cursor.execute(
            "SELECT json_extract(analiz_json, '$.source') as kaynak, COUNT(*) as sayi "
            "FROM sozcuk_analizleri GROUP BY kaynak"
        )
        istatistikler['analiz_kaynaklari'] = {row['kaynak']: row['sayi'] for row in cursor.fetchall()}
        
        return istatistikler
    
    def get_en_cok_kullanilan_kokler(self, limit: int = 20) -> List[Tuple[str, int]]:
        """En çok kullanılan kökleri listeler"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT k.kok, SUM(sa.frekans) as kullanim "
            "FROM kokler k "
            "JOIN sozcuk_analizleri sa ON k.id = sa.kok_id "
            "GROUP BY k.kok "
            "ORDER BY kullanim DESC "
            "LIMIT ?",
            (limit,)
        )
        return [(row['kok'], row['kullanim']) for row in cursor.fetchall()]
    
    def get_en_cok_kullanilan_ekler(self, limit: int = 20) -> List[Tuple[str, str, int]]:
        """En çok kullanılan ekleri listeler"""
        # Bu daha karmaşık, JSON'dan ekler dizisini çıkarıp saymalıyız
        cursor = self.conn.cursor()
        cursor.execute("SELECT analiz_json FROM sozcuk_analizleri")
        
        # Her bir analizdeki ekleri say
        ek_sayaci = Counter()
        for row in cursor.fetchall():
            analiz = json.loads(row['analiz_json'])
            for ek, kategori in analiz.get('ekler', []):
                ek_sayaci[(ek, kategori)] += 1
        
        # En çok kullanılan ekleri döndür
        en_cok_ekler = ek_sayaci.most_common(limit)
        return [(ek, kategori, sayi) for (ek, kategori), sayi in en_cok_ekler]
    
    def get_sorunlu_sozcukler(self) -> List[Dict]:
        """Çözülemeyen sorunlu sözcükleri listeler"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT sozcuk, durum, not, deneme_sayisi "
            "FROM sorunlu_sozcukler "
            "ORDER BY deneme_sayisi DESC"
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def csv_rapor_olustur(self, cikti_dosyasi: str = "rapor.csv"):
        """Analiz sonuçlarını CSV dosyasına kaydeder"""
        istatistikler = self.get_istatistikler()
        en_cok_kokler = self.get_en_cok_kullanilan_kokler()
        en_cok_ekler = self.get_en_cok_kullanilan_ekler()
        sorunlu_sozcukler = self.get_sorunlu_sozcukler()
        
        with open(cikti_dosyasi, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Genel istatistikler
            writer.writerow(["Genel İstatistikler", ""])
            writer.writerow(["Toplam Kök Sayısı", istatistikler['kok_sayisi']])
            writer.writerow(["Toplam Ek Sayısı", istatistikler['ek_sayisi']])
            writer.writerow(["Toplam Analiz Sayısı", istatistikler['analiz_sayisi']])
            writer.writerow(["Toplam İşlem Sayısı", istatistikler['toplam_islem']])
            writer.writerow(["Sorunlu Sözcük Sayısı", istatistikler['sorunlu_sayi']])
            writer.writerow([])
            
            # Kök türleri
            writer.writerow(["Kök Türleri", "Sayı"])
            for tur, sayi in istatistikler['kok_turleri'].items():
                writer.writerow([tur, sayi])
            writer.writerow([])
            
            # En çok kullanılan kökler
            writer.writerow(["En Çok Kullanılan Kökler", "Kullanım Sayısı"])
            for kok, sayi in en_cok_kokler:
                writer.writerow([kok, sayi])
            writer.writerow([])
            
            # En çok kullanılan ekler
            writer.writerow(["En Çok Kullanılan Ekler", "Kategori", "Kullanım Sayısı"])
            for ek, kategori, sayi in en_cok_ekler:
                writer.writerow([ek, kategori, sayi])
            writer.writerow([])
            
            # Sorunlu sözcükler
            writer.writerow(["Sorunlu Sözcükler", "Durum", "Not", "Deneme Sayısı"])
            for sozcuk in sorunlu_sozcukler:
                writer.writerow([
                    sozcuk['sozcuk'], 
                    sozcuk['durum'], 
                    sozcuk['not'], 
                    sozcuk['deneme_sayisi']
                ])
        
        print(f"Rapor oluşturuldu: {cikti_dosyasi}")
    
    def grafik_rapor_olustur(self, cikti_klasoru: str = "grafikler"):
        """Analiz sonuçlarından grafikler oluşturur"""
        istatistikler = self.get_istatistikler()
        en_cok_kokler = self.get_en_cok_kullanilan_kokler(10)
        en_cok_ekler = self.get_en_cok_kullanilan_ekler(10)
        
        # Çıktı klasörünü oluştur
        if not os.path.exists(cikti_klasoru):
            os.makedirs(cikti_klasoru)
        
        # 1. Kök türleri pasta grafiği
        plt.figure(figsize=(10, 6))
        labels = list(istatistikler['kok_turleri'].keys())
        sizes = list(istatistikler['kok_turleri'].values())
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title('Kök Türlerinin Dağılımı')
        plt.axis('equal')
        plt.savefig(os.path.join(cikti_klasoru, 'kok_turleri.png'))
        plt.close()
        
        # 2. En çok kullanılan kökler çubuk grafiği
        plt.figure(figsize=(12, 6))
        kokler, sayilar = zip(*en_cok_kokler)
        plt.bar(kokler, sayilar)
        plt.title('En Çok Kullanılan 10 Kök')
        plt.xlabel('Kökler')
        plt.ylabel('Kullanım Sayısı')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(cikti_klasoru, 'en_cok_kokler.png'))
        plt.close()
        
        # 3. En çok kullanılan ekler çubuk grafiği
        plt.figure(figsize=(12, 6))
        ekler = [f"{ek} ({kategori})" for ek, kategori, _ in en_cok_ekler]
        sayilar = [sayi for _, _, sayi in en_cok_ekler]
        plt.bar(ekler, sayilar)
        plt.title('En Çok Kullanılan 10 Ek')
        plt.xlabel('Ekler')
        plt.ylabel('Kullanım Sayısı')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(os.path.join(cikti_klasoru, 'en_cok_ekler.png'))
        plt.close()
        
        # 4. Analiz kaynakları pasta grafiği
        plt.figure(figsize=(10, 6))
        labels = list(istatistikler['analiz_kaynaklari'].keys())
        sizes = list(istatistikler['analiz_kaynaklari'].values())
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title('Analiz Kaynaklarının Dağılımı')
        plt.axis('equal')
        plt.savefig(os.path.join(cikti_klasoru, 'analiz_kaynaklari.png'))
        plt.close()
        
        print(f"Grafikler oluşturuldu: {cikti_klasoru}")

def main():
    """Ana program fonksiyonu"""
    parser = argparse.ArgumentParser(description='Türkçe Morfolojik Analiz Rapor Aracı')
    parser.add_argument('--veritabani', '-db', default='turkce_morfoloji.db', help='Veritabanı dosya yolu')
    parser.add_argument('--csv', '-c', default='rapor.csv', help='CSV rapor dosyası çıktısı')
    parser.add_argument('--grafik', '-g', action='store_true', help='Grafikler oluştur')
    parser.add_argument('--grafik-klasoru', '-gk', default='grafikler', help='Grafik çıktılarının kaydedileceği klasör')
    parser.add_argument('--istatistik', '-i', action='store_true', help='İstatistikleri ekrana yazdır')
    
    args = parser.parse_args()
    
    try:
        rapor_araci = MorfolojiRaporAracı(args.veritabani)
        
        if args.istatistik:
            istatistikler = rapor_araci.get_istatistikler()
            print("\n=== Genel İstatistikler ===")
            print(f"Toplam Kök Sayısı: {istatistikler['kok_sayisi']}")
            print(f"Toplam Ek Sayısı: {istatistikler['ek_sayisi']}")
            print(f"Toplam Analiz Sayısı: {istatistikler['analiz_sayisi']}")
            print(f"Toplam İşlem Sayısı: {istatistikler['toplam_islem']}")
            print(f"Sorunlu Sözcük Sayısı: {istatistikler['sorunlu_sayi']}")
            
            print("\n=== Kök Türleri ===")
            for tur, sayi in istatistikler['kok_turleri'].items():
                print(f"{tur}: {sayi}")
            
            print("\n=== Analiz Kaynakları ===")
            for kaynak, sayi in istatistikler['analiz_kaynaklari'].items():
                print(f"{kaynak}: {sayi}")
            
            print("\n=== En Çok Kullanılan 10 Kök ===")
            for kok, sayi in rapor_araci.get_en_cok_kullanilan_kokler(10):
                print(f"{kok}: {sayi}")
            
            print("\n=== En Çok Kullanılan 10 Ek ===")
            for ek, kategori, sayi in rapor_araci.get_en_cok_kullanilan_ekler(10):
                print(f"{ek} ({kategori}): {sayi}")
        
        if args.csv:
            rapor_araci.csv_rapor_olustur(args.csv)
        
        if args.grafik:
            rapor_araci.grafik_rapor_olustur(args.grafik_klasoru)
    
    finally:
        rapor_araci.kapat()

if __name__ == "__main__":
    main()

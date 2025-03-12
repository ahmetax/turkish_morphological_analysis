#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Morfolojik Analiz - Test Modülü
"""

import unittest
import os
import tempfile
import time
from turkce_morfologik_analiz import TurkceMorfologikAnaliz

class TestMorfolojikAnaliz(unittest.TestCase):
    """TurkceMorfologikAnaliz sınıfı için test"""
    
    @classmethod
    def setUpClass(cls):
        """Test sınıfı başlangıcında çalışır"""
        # Geçici veritabanı oluştur
        cls.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.temp_db.close()
        
        # Zemberek olmadan, non-interaktif modda test analizcisi
        cls.analizci = TurkceMorfologikAnaliz(
            veritabani_path=cls.temp_db.name,
            zemberek_jar_path="non-existent.jar",
            interaktif=False
        )
        
        # Test sözcük listesi
        cls.test_kokler = {
            "kitap": "isim",
            "ev": "isim",
            "gel": "fiil",
            "yap": "fiil",
            "güzel": "sıfat"
        }
        
        # Kökleri ekle
        for kok, tur in cls.test_kokler.items():
            cls.analizci.sozluk_ekle(kok, tur)
    
    @classmethod
    def tearDownClass(cls):
        """Test sınıfı bitiminde çalışır"""
        cls.analizci.kapat()
        os.unlink(cls.temp_db.name)
    
    def test_basit_kok_tespiti(self):
        """Basit kök tespiti testi"""
        for kok in self.test_kokler:
            sonuc = self.analizci.parcala(kok)
            self.assertEqual(sonuc['kok'], kok)
            self.assertEqual(len(sonuc['ekler']), 0)
    
    def test_basit_ek_tespiti(self):
        """Basit ek tespiti testi"""
        test_cases = [
            {"sozcuk": "evde", "kok": "ev", "ek": "de"},
            {"sozcuk": "kitaplar", "kok": "kitap", "ek": "lar"},
            {"sozcuk": "geldi", "kok": "gel", "ek": "di"},
            {"sozcuk": "yapıyor", "kok": "yap", "ek": "ıyor"}
        ]
        
        for test_case in test_cases:
            sonuc = self.analizci.parcala(test_case["sozcuk"])
            self.assertEqual(sonuc['kok'], test_case["kok"])
            self.assertEqual(len(sonuc['ekler']), 1)
            self.assertEqual(sonuc['ekler'][0][0], test_case["ek"])
    
    def test_unsuz_yumusama(self):
        """Ünsüz yumuşaması testi"""
        # Kitap -> Kitabı
        sonuc = self.analizci.parcala("kitabı")
        self.assertEqual(sonuc['kok'], "kitap")
        self.assertEqual(len(sonuc['ekler']), 1)
        self.assertEqual(sonuc['ekler'][0][0], "ı")
    
    def test_coklu_ek(self):
        """Çoklu ek tespiti testi"""
        # Evlerimizde
        self.analizci.sozluk_ekle("ev", "isim")
        sonuc = self.analizci.parcala("evlerimizde")
        self.assertEqual(sonuc['kok'], "ev")
        self.assertGreaterEqual(len(sonuc['ekler']), 2)
        
        # Kitaplarımızdan
        sonuc = self.analizci.parcala("kitaplarımızdan")
        self.assertEqual(sonuc['kok'], "kitap")
        self.assertGreaterEqual(len(sonuc['ekler']), 2)
    
    def test_metin_analizi(self):
        """Metin analizi testi"""
        test_metin = "evde kitap okuyorum ve güzel bir gün geçiriyorum"
        sonuclar = self.analizci.metinden_sozcukleri_coz(test_metin)
        
        self.assertIn("evde", sonuclar)
        self.assertIn("kitap", sonuclar)
        self.assertIn("güzel", sonuclar)
        
        self.assertEqual(sonuclar["evde"]["kok"], "ev")
        self.assertEqual(sonuclar["kitap"]["kok"], "kitap")
        self.assertEqual(sonuclar["güzel"]["kok"], "güzel")
    
    def test_performans(self):
        """Performans testi"""
        # Rastgele tekrarlı metin oluştur
        test_sozcukler = list(self.test_kokler.keys()) * 20  # 100 sözcük
        test_metin = " ".join(test_sozcukler)
        
        # Zamanla
        baslangic = time.time()
        self.analizci.metinden_sozcukleri_coz(test_metin)
        bitis = time.time()
        
        # İlk çalışmada veritabanı yazma yapacağı için ikinci kez dene
        baslangic = time.time()
        sonuclar = self.analizci.metinden_sozcukleri_coz(test_metin)
        bitis = time.time()
        
        # Sonuçları kontrol et
        self.assertEqual(len(sonuclar), len(self.test_kokler))
        
        # Saniyede işlenen sözcük sayısını hesapla (minimum 100)
        sozcuk_sayisi = len(test_sozcukler)
        sure = bitis - baslangic
        sozcuk_saniye = sozcuk_sayisi / sure if sure > 0 else float('inf')
        
        print(f"\nPerformans: {sozcuk_saniye:.2f} sözcük/saniye")
        self.assertGreaterEqual(sozcuk_saniye, 100, "Performans çok düşük")

if __name__ == "__main__":
    unittest.main()

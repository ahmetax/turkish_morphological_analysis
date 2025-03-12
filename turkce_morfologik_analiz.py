#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Türkçe Morfolojik Analiz - Ana Program
"""

import re
import os
import sys
import logging
import argparse
import json
from typing import List, Dict, Tuple, Set, Optional, Union

# Proje modülleri
from config_utils import config_yukle, config_kaydet, ornek_config_olustur
from veritabani import MorfolojikVeritabani
from zemberek_wrapper import ZemberekWrapper

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("morfoloji_analiz.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TurkceMorfAnaliz")

class TurkceMorfologikAnaliz:
    """Türkçe morfolojik analiz sınıfı"""
    
    def __init__(self, 
                 veritabani_path: str = "turkce_morfoloji.db", 
                 zemberek_jar_path: str = "zemberek-full.jar",
                 interaktif: bool = True,
                 max_derinlik: int = 5,
                 unlu_uyumu_kontrol: bool = True,
                 unsuz_yumusama_kontrol: bool = True,
                 zemberek_oncelikli: bool = True):
        self.veritabani = MorfolojikVeritabani(veritabani_path)
        self.zemberek = ZemberekWrapper(zemberek_jar_path)
        self.interaktif = interaktif
        self.max_derinlik = max_derinlik
        self.unlu_uyumu_kontrol = unlu_uyumu_kontrol
        self.unsuz_yumusama_kontrol = unsuz_yumusama_kontrol
        self.zemberek_oncelikli = zemberek_oncelikli
        
        # Veritabanından bilinen kökler ve ekleri yükle
        self.bilinen_kokler = self.veritabani.get_bilinen_kokler()
        self.ekler = self.veritabani.get_bilinen_ekler()
        
        # Bazı temel düzenli ifadeler
        self.unlu_harfler = set('aeıioöuü')
        self.unsuz_harfler = set('bcçdfgğhjklmnprsştvyz')
        
        logger.info(f"Morfolojik analiz başlatıldı - Veritabanı: {veritabani_path}")
        logger.info(f"Zemberek: {'Aktif' if self.zemberek.available else 'Devre dışı'}")
        logger.info(f"İnteraktif mod: {'Açık' if interaktif else 'Kapalı'}")
        logger.info(f"Gelişmiş ayarlar: max_derinlik={max_derinlik}, ünlü_uyumu={unlu_uyumu_kontrol}, ünsüz_yumuşama={unsuz_yumusama_kontrol}")
    
    def _bul_olasi_ekler(self, sozcuk: str) -> List[Tuple[str, str]]:
        """Sözcükteki olası ekleri bulur"""
        bulunan_ekler = []
        
        # Tüm ek kategorilerini kontrol et
        for kategori, ek_listesi in self.ekler.items():
            for ek in ek_listesi:
                if sozcuk.endswith(ek) and len(sozcuk) > len(ek):
                    bulunan_ekler.append((ek, kategori))
        
        # Uzunluğa göre sırala (daha uzun ekler önce gelsin)
        bulunan_ekler.sort(key=lambda x: len(x[0]), reverse=True)
        return bulunan_ekler
    
    def _kontrol_unlu_uyumu(self, kelime: str) -> bool:
        """Büyük ünlü uyumunu kontrol eder"""
        if not self.unlu_uyumu_kontrol:
            return True
            
        unluler = [harf for harf in kelime if harf in self.unlu_harfler]
        if not unluler:
            return True  # Ünlü yoksa sorun yok
            
        kalin_unluler = set('aıou')
        ince_unluler = set('eiöü')
        
        kalin_mi = unluler[0] in kalin_unluler
        if kalin_mi:
            return all(unlu in kalin_unluler for unlu in unluler)
        else:
            return all(unlu in ince_unluler for unlu in unluler)
    
    def _kontrol_yumusama(self, kok: str, ek: str) -> Optional[str]:
        """Ünsüz yumuşaması olup olmadığını kontrol eder"""
        if not self.unsuz_yumusama_kontrol:
            return None
            
        yumusama_harfleri = {
            'p': 'b',  # kitap -> kitabı
            't': 'd',  # ağaç -> ağacı
            'ç': 'c',  # taç -> tacı
            'k': 'ğ'   # çocuk -> çocuğu
        }
        
        if not kok or not ek:
            return None
            
        if kok[-1] in yumusama_harfleri and ek[0] in self.unlu_harfler:
            yumusak_hali = kok[:-1] + yumusama_harfleri[kok[-1]]
            return yumusak_hali
            
        return None
    
    def _kontrol_kucuk_unlu_uyumu(self, kok: str, ek: str) -> bool:
        """Küçük ünlü uyumunu kontrol eder"""
        if not self.unlu_uyumu_kontrol:
            return True
            
        if not kok or not ek:
            return True
            
        # Ekin içinde ünlü yoksa sorun yok
        ekteki_unluler = [harf for harf in ek if harf in self.unlu_harfler]
        if not ekteki_unluler:
            return True
            
        # Kökteki son ünlüyü bul
        kokteki_unluler = [harf for harf in kok if harf in self.unlu_harfler]
        if not kokteki_unluler:
            return True
            
        son_unlu = kokteki_unluler[-1]
        ilk_ek_unlu = ekteki_unluler[0]
        
        # Düzlük-yuvarlaklık uyumu
        duz_unluler = set('aeiı')
        duz_yuvarlak = set('öü')
        yuvarlak_duz = set('ou')
        
        if son_unlu in duz_unluler:
            return ilk_ek_unlu in duz_unluler
        elif son_unlu in duz_yuvarlak:
            return ilk_ek_unlu in duz_yuvarlak
        elif son_unlu in yuvarlak_duz:
            return ilk_ek_unlu in yuvarlak_duz
            
        return True
    
    def _kontrol_kok_gecerli(self, kok: str) -> bool:
        """Kökün geçerli olup olmadığını kontrol eder"""
        # 1. Bilinen kökler listesinde var mı?
        if kok in self.bilinen_kokler:
            return True
        
        # 2. En az bir sesli harf içeriyor mu?
        if not any(harf in self.unlu_harfler for harf in kok.lower()):
            return False
        
        # 3. Minimum uzunluk kontrolü
        if len(kok) < 2:
            return False
            
        # 4. Büyük ünlü uyumu kontrolü
        if self.unlu_uyumu_kontrol and not self._kontrol_unlu_uyumu(kok):
            return False
            
        return True
    
    def parcala(self, sozcuk: str, derinlik: int = 0) -> Dict:
        """Sözcüğü kök ve eklerine ayırır"""
        sozcuk = sozcuk.lower()
        
        # Maksimum derinlik kontrolü
        if derinlik >= self.max_derinlik:
            logger.debug(f"Maksimum derinliğe ulaşıldı ({self.max_derinlik}): {sozcuk}")
            return {
                'kok': sozcuk,
                'ekler': [],
                'source': 'max_derinlik_asildi'
            }
        
        # 1. Veritabanında bu sözcük için önceden yapılmış bir analiz var mı?
        onceki_analiz = self.veritabani.sozcuk_analizi_getir(sozcuk)
        if onceki_analiz:
            logger.debug(f"Veritabanından analiz bulundu: {sozcuk}")
            return onceki_analiz
        
        # 2. Zemberek'i dene
        if self.zemberek_oncelikli and self.zemberek.available:
            zemberek_analiz = self.zemberek.analyze(sozcuk)
            if zemberek_analiz:
                logger.debug(f"Zemberek analizi başarılı: {sozcuk}")
                
                # Analizi veritabanına kaydet
                kok_id = self.veritabani.kok_ekle(
                    zemberek_analiz['kok'], 
                    'isim',  # Zemberek'ten tur bilgisini almak daha karmaşık
                    'zemberek'
                )
                self.veritabani.sozcuk_analizi_kaydet(
                    sozcuk, 
                    kok_id, 
                    json.dumps(zemberek_analiz)
                )
                
                # Bilinen kökleri güncelle
                self.bilinen_kokler[zemberek_analiz['kok']] = 'isim'
                
                return zemberek_analiz
        
        # 3. Eğer sözcük zaten bilinen listede varsa, doğrudan köktür
        if sozcuk in self.bilinen_kokler:
            sonuc = {
                'kok': sozcuk,
                'ekler': [],
                'source': 'kokler_db'
            }
            
            # Veritabanına kaydet
            kok_id = self.veritabani.kok_ekle(sozcuk, self.bilinen_kokler[sozcuk], 'kokler_db')
            self.veritabani.sozcuk_analizi_kaydet(sozcuk, kok_id, json.dumps(sonuc))
            
            return sonuc
        
        # 4. Olası ekleri bul
        olasi_ekler = self._bul_olasi_ekler(sozcuk)
        
        # 5. Ekleri tek tek deneyerek geçerli kök bulmaya çalış
        for ek, kategori in olasi_ekler:
            olasi_kok = sozcuk[:-len(ek)]
            
            # a. Normal kök kontrolü
            if self._kontrol_kok_gecerli(olasi_kok):
                sonuc = {
                    'kok': olasi_kok,
                    'ekler': [(ek, kategori)],
                    'source': 'kendi_analiz'
                }
                
                # Veritabanına kaydet
                kok_id = self.veritabani.kok_ekle(olasi_kok, 'isim', 'kendi_analiz')
                self.veritabani.sozcuk_analizi_kaydet(sozcuk, kok_id, json.dumps(sonuc))
                
                # Bilinen kökleri güncelle
                self.bilinen_kokler[olasi_kok] = 'isim'
                
                return sonuc
                
            # b. Ünsüz yumuşaması kontrolü
            yumusak_kok = self._kontrol_yumusama(olasi_kok, ek)
            if yumusak_kok and yumusak_kok in self.bilinen_kokler:
                sonuc = {
                    'kok': yumusak_kok,
                    'ekler': [(ek, kategori)],
                    'source': 'kendi_analiz_yumusama'
                }
                
                # Veritabanına kaydet
                kok_id = self.veritabani.kok_ekle(yumusak_kok, self.bilinen_kokler.get(yumusak_kok, 'isim'), 'kendi_analiz_yumusama')
                self.veritabani.sozcuk_analizi_kaydet(sozcuk, kok_id, json.dumps(sonuc))
                
                return sonuc
        
        # 6. Birden fazla ek olabilir, recursive olarak dene
        for ek, kategori in olasi_ekler:
            if len(sozcuk) > len(ek):
                olasi_kok = sozcuk[:-len(ek)]
                alt_parcalama = self.parcala(olasi_kok, derinlik + 1)
                
                if alt_parcalama['kok'] != olasi_kok:  # Alt parçalama başarılı olduysa
                    ekler = alt_parcalama['ekler'] + [(ek, kategori)]
                    sonuc = {
                        'kok': alt_parcalama['kok'],
                        'ekler': ekler,
                        'source': 'kendi_analiz_recursif'
                    }
                    
                    # Veritabanına kaydet
                    kok_id = self.veritabani.kok_ekle(
                        alt_parcalama['kok'], 
                        self.bilinen_kokler.get(alt_parcalama['kok'], 'isim'), 
                        'kendi_analiz_recursif'
                    )
                    self.veritabani.sozcuk_analizi_kaydet(sozcuk, kok_id, json.dumps(sonuc))
                    
                    return sonuc
        
        # 7. Hiçbir kurala uymadıysa, sorunlu sözcük olarak işaretle
        self.veritabani.sorunlu_sozcuk_ekle(sozcuk, 'çözülemedi')
        
        if self.interaktif:
            try:
                print(f"\nSözcük çözümlenemedi: {sozcuk}")
                yanit = input("Bu sözcüğün kökü nedir? (Boş bırakırsanız sözcüğün kendisi kök kabul edilecek): ")
                
                if not yanit.strip():
                    yanit = sozcuk
                    
                tur = input("Kökün türü nedir? (isim/fiil/sıfat/default:isim): ") or "isim"
                
                # Kullanıcının verdiği kökü ekle
                self.veritabani.kok_ekle(yanit, tur, 'kullanici_giris')
                self.bilinen_kokler[yanit] = tur
                
                # Ekler kısmını hesapla
                ekler = []
                if yanit != sozcuk:
                    ek_kismi = sozcuk[len(yanit):]
                    if ek_kismi:
                        ekler = [(ek_kismi, 'kullanici_belirledi')]
                
                sonuc = {
                    'kok': yanit,
                    'ekler': ekler,
                    'source': 'kullanici_giris'
                }
                
                # Veritabanına kaydet
                kok_id = self.veritabani.kok_ekle(yanit, tur, 'kullanici_giris')
                self.veritabani.sozcuk_analizi_kaydet(sozcuk, kok_id, json.dumps(sonuc))
                
                # Sorunlu sözcük durumunu güncelle
                self.veritabani.sorunlu_sozcuk_ekle(sozcuk, 'çözüldü', f'Kök: {yanit}, Tür: {tur}')
                
                return sonuc
                
            except Exception as e:
                logger.error(f"Kullanıcı girişi sırasında hata: {e}")
        
        # İnteraktif mod değilse veya kullanıcı girişinde hata olduysa, sözcüğün kendisini kök olarak kabul et
        sonuc = {
            'kok': sozcuk,
            'ekler': [],
            'source': 'varsayilan'
        }
        
        return sonuc
    
    def metinden_sozcukleri_coz(self, metin: str) -> Dict[str, Dict]:
        """Bir metindeki tüm sözcükleri çözümler"""
        # Metni temizle ve sözcüklere ayır
        temiz_metin = re.sub(r'[^\w\s]', ' ', metin)
        sozcukler = [s for s in temiz_metin.lower().split() if s]
        
        # Benzersiz sözcükleri bul
        benzersiz_sozcukler = set(sozcukler)
        
        # Her bir sözcüğü çözümle
        sonuclar = {}
        for sozcuk in benzersiz_sozcukler:
            sonuclar[sozcuk] = self.parcala(sozcuk)
            
        return sonuclar
    
    def dosyadan_cozumle(self, dosya_yolu: str) -> Dict[str, Dict]:
        """Bir metin dosyasındaki tüm sözcükleri çözümler"""
        try:
            with open(dosya_yolu, 'r', encoding='utf-8') as f:
                metin = f.read()
            return self.metinden_sozcukleri_coz(metin)
        except Exception as e:
            logger.error(f"Dosya okuma hatası: {e}")
            return {}
    
    def sozluk_ekle(self, sozcuk: str, tur: str = 'isim'):
        """Bilinen sözcükler sözlüğüne yeni bir sözcük ekler"""
        self.veritabani.kok_ekle(sozcuk, tur, 'manuel_ekleme')
        self.bilinen_kokler[sozcuk] = tur
    
    def sozluk_yukle(self, dosya_yolu: str) -> int:
        """Harici bir sözcük listesi dosyasından sözlük yükler"""
        try:
            eklenen = 0
            with open(dosya_yolu, 'r', encoding='utf-8') as dosya:
                for satir in dosya:
                    bolumler = satir.strip().split('\t')
                    if len(bolumler) >= 2:
                        sozcuk = bolumler[0]
                        tur = bolumler[1]
                        self.sozluk_ekle(sozcuk, tur)
                        eklenen += 1
                    elif len(bolumler) == 1 and bolumler[0]:
                        sozcuk = bolumler[0]
                        self.sozluk_ekle(sozcuk, 'isim')
                        eklenen += 1
            
            logger.info(f"{eklenen} sözcük yüklendi: {dosya_yolu}")
            return eklenen
        except Exception as e:
            logger.error(f"Sözcük listesi yükleme hatası: {e}")
            return 0
    
    def kapat(self):
        """Kaynakları serbest bırakır"""
        self.veritabani.kapat()
        logger.info("Veritabanı bağlantısı kapatıldı")


def main():
    """Ana program fonksiyonu"""
    parser = argparse.ArgumentParser(description='Türkçe Morfolojik Analiz Aracı')
    parser.add_argument('--config', '-c', default='config.ini', help='Yapılandırma dosyası yolu')
    parser.add_argument('--dosya', '-f', help='İşlenecek metin dosyası (config dosyasını geçersiz kılar)')
    parser.add_argument('--metin', '-t', help='İşlenecek metin')
    parser.add_argument('--sozcuk', '-w', help='İşlenecek tek sözcük')
    parser.add_argument('--veritabani', '-db', help='Veritabanı dosya yolu (config dosyasını geçersiz kılar)')
    parser.add_argument('--zemberek', '-z', help='Zemberek JAR dosya yolu (config dosyasını geçersiz kılar)')
    parser.add_argument('--sozluk_yukle', '-sl', help='Yüklenecek sözcük listesi dosyası')
    parser.add_argument('--non-interaktif', '-ni', action='store_true', help='İnteraktif modu devre dışı bırak')
    parser.add_argument('--detayli', '-v', action='store_true', help='Detaylı log çıktısı')
    parser.add_argument('--ornek-config', action='store_true', help='Örnek yapılandırma dosyası oluştur')
    
    args = parser.parse_args()
    
    # Örnek config dosyası oluşturma
    if args.ornek_config:
        ornek_config_olustur()
        return
    
    # Yapılandırma dosyasını yükle
    config = config_yukle(args.config)
    
    # Log seviyesini ayarla
    log_seviyesi = config['Genel']['log_seviyesi']
    
    if args.detayli:
        log_seviyesi = 'DEBUG'
    
    numeric_level = getattr(logging, log_seviyesi.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Geçersiz log seviyesi: {log_seviyesi}')
    
    logging.getLogger("TurkceMorfAnaliz").setLevel(numeric_level)
    
    # Parametreleri belirle (öncelik sırası: komut satırı > config dosyası > varsayılan)
    veritabani_path = args.veritabani or config['Genel']['veritabani']
    zemberek_jar_path = args.zemberek or config['Genel']['zemberek_jar']
    interaktif = not args.non_interaktif and config['Genel'].getboolean('interaktif')
    
    # Gelişmiş ayarlar
    max_derinlik = config['Gelismis'].getint('max_derinlik', 5)
    unlu_uyumu_kontrol = config['Gelismis'].getboolean('unlu_uyumu_kontrol', True)
    unsuz_yumusama_kontrol = config['Gelismis'].getboolean('unsuz_yumusama_kontrol', True)
    zemberek_oncelikli = config['Gelismis'].getboolean('zemberek_oncelikli', True)
    
    # Analizci nesnesi oluştur
    analizci = TurkceMorfologikAnaliz(
        veritabani_path=veritabani_path,
        zemberek_jar_path=zemberek_jar_path,
        interaktif=interaktif,
        max_derinlik=max_derinlik,
        unlu_uyumu_kontrol=unlu_uyumu_kontrol,
        unsuz_yumusama_kontrol=unsuz_yumusama_kontrol,
        zemberek_oncelikli=zemberek_oncelikli
    )
    
    try:
        # Sözcük listesi yükleme
        sozluk_dosyasi = args.sozluk_yukle or config['Dosyalar']['sozluk_dosyasi']
        if sozluk_dosyasi:
            eklenen = analizci.sozluk_yukle(sozluk_dosyasi)
            print(f"{eklenen} sözcük sözlüğe eklendi.")
        
        # Çıktı dosyası
        cikti_dosyasi = config['Dosyalar']['cikti_dosyasi']
        cikti_dosyasi_acik = False
        f_cikti = None
        
        if cikti_dosyasi:
            try:
                f_cikti = open(cikti_dosyasi, 'w', encoding='utf-8')
                cikti_dosyasi_acik = True
                print(f"Sonuçlar '{cikti_dosyasi}' dosyasına yazılacak.")
            except Exception as e:
                print(f"Çıktı dosyası açılamadı: {e}")
        
        def sonuc_yazdir(mesaj):
            print(mesaj)
            if cikti_dosyasi_acik:
                f_cikti.write(mesaj + "\n")
        
        # Tek sözcük analizi
        if args.sozcuk:
            sonuc = analizci.parcala(args.sozcuk)
            ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in sonuc['ekler']])
            sonuc_yazdir(f"{args.sozcuk} -> Kök: {sonuc['kok']}, Ekler: {ekler_str if ekler_str else 'Yok'}")
            sonuc_yazdir(f"Kaynak: {sonuc.get('source', 'bilinmiyor')}")
        
        # Metin analizi
        elif args.metin:
            sonuclar = analizci.metinden_sozcukleri_coz(args.metin)
            for sozcuk, sonuc in sonuclar.items():
                ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in sonuc['ekler']])
                sonuc_yazdir(f"{sozcuk} -> Kök: {sonuc['kok']}, Ekler: {ekler_str if ekler_str else 'Yok'}")
        
        # Dosya analizi
        else:
            metin_dosyasi = args.dosya or config['Dosyalar']['metin_dosyasi']
            if metin_dosyasi:
                sonuclar = analizci.dosyadan_cozumle(metin_dosyasi)
                for sozcuk, sonuc in sorted(sonuclar.items()):
                    ekler_str = ", ".join([f"{ek} ({kategori})" for ek, kategori in sonuc['ekler']])
                    sonuc_yazdir(f"{sozcuk} -> Kök: {sonuc['kok']}, Ekler: {ekler_str if ekler_str else 'Yok'}")
            else:
                parser.print_help()
    
    finally:
        analizci.kapat()
        if cikti_dosyasi_acik:
            f_cikti.close()


if __name__ == "__main__":
    main()

"""
Türkçe Morfolojik Analiz - Veritabanı İşlemleri
"""

import sqlite3
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger("TurkceMorfAnaliz")

class MorfolojikVeritabani:
    """SQLite veritabanı yönetim sınıfı - Çoklu İşlem İçin Düzeltilmiş"""
    
    def __init__(self, db_path: str = "turkce_morfoloji.db", readonly: bool = False):
        self.db_path = db_path
        self.conn = None
        self.readonly = readonly
        self.initialize_db()
    
    def initialize_db(self):
        """Veritabanı bağlantısını başlatır ve gerekli tabloları oluşturur"""
        try:
            # Salt okunur mod için kontrol
            if self.readonly:
                if os.path.exists(self.db_path):
                    # URI modunda salt okunur bağlantı
                    self.conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
                    logger.info(f"Veritabanı salt okunur modda açıldı: {self.db_path}")
                    return
                else:
                    # Salt okunur modda veritabanı yoksa boş bir bağlantı oluştur
                    self.conn = sqlite3.connect(":memory:")
                    logger.warning(f"Salt okunur modda veritabanı bulunamadı. Hafıza içi DB oluşturuldu.")
                    return
            
            # İmmediate modunda bağlantı (SQLite kilitleme sorununu azaltır)
            self.conn = sqlite3.connect(self.db_path, isolation_level="IMMEDIATE", timeout=60.0)
            cursor = self.conn.cursor()
            
            # PRAGMA ayarları
            cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging modu
            cursor.execute("PRAGMA synchronous=NORMAL")  # Senkronizasyon seviyesini düşür
            cursor.execute("PRAGMA cache_size=10000")  # Önbellek boyutunu artır
            cursor.execute("PRAGMA temp_store=MEMORY")  # Geçici tabloları bellekte tut
            
            # Kökler tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS kokler (
                id INTEGER PRIMARY KEY,
                kok TEXT UNIQUE,
                tur TEXT,
                frekans INTEGER DEFAULT 1,
                guven_puani INTEGER DEFAULT 50,
                kaynak TEXT
            )
            ''')
            
            # Ekler tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ekler (
                id INTEGER PRIMARY KEY,
                ek TEXT,
                kategori TEXT,
                frekans INTEGER DEFAULT 1,
                UNIQUE(ek, kategori)
            )
            ''')
            
            # Sözcük analizleri tablosu
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sozcuk_analizleri (
                id INTEGER PRIMARY KEY,
                sozcuk TEXT UNIQUE,
                kok_id INTEGER,
                analiz_json TEXT,
                frekans INTEGER DEFAULT 1,
                son_guncelleme TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (kok_id) REFERENCES kokler (id)
            )
            ''')
            
            # Sorunlu sözcükler tablosu - 'not' yerine 'not_metni' kullan (SQLite reserved keyword sorunu)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sorunlu_sozcukler (
                id INTEGER PRIMARY KEY,
                sozcuk TEXT UNIQUE,
                durum TEXT,
                not_metni TEXT,
                deneme_sayisi INTEGER DEFAULT 1
            )
            ''')
            
            self.conn.commit()
            logger.info("Veritabanı başarıyla oluşturuldu/bağlandı.")
            
            # Varsayılan ekler sözlüğünü ekle
            self._add_default_ekler()
            
        except sqlite3.Error as e:
            logger.error(f"Veritabanı başlatma hatası: {e}")
            if self.conn:
                self.conn.close()
                self.conn = None
            raise
    
    def _add_default_ekler(self):
        """Varsayılan Türkçe ekleri veritabanına ekler"""
        if self.readonly:
            return  # Salt okunur modda ekleme yapmayız
        
        default_ekler = {
            'isim_cekimleri': ['ler', 'lar', 'in', 'ın', 'un', 'ün', 'a', 'e', 'i', 'ı', 'u', 'ü', 'da', 'de', 'ta', 'te', 'dan', 'den', 'tan', 'ten'],
            'fiil_cekimleri': ['di', 'dı', 'du', 'dü', 'ti', 'tı', 'tu', 'tü', 'miş', 'mış', 'muş', 'müş', 'yor', 'ecek', 'acak', 'ir', 'ır', 'ur', 'ür'],
            'sahiplik_ekleri': ['im', 'ım', 'um', 'üm', 'in', 'ın', 'un', 'ün', 'si', 'sı', 'su', 'sü', 'imiz', 'ımız', 'umuz', 'ümüz'],
            'yapim_ekleri': ['ci', 'cı', 'cu', 'cü', 'li', 'lı', 'lu', 'lü', 'lik', 'lık', 'luk', 'lük', 'siz', 'sız', 'suz', 'süz']
        }
        
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        for kategori, ek_listesi in default_ekler.items():
            for ek in ek_listesi:
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO ekler (ek, kategori) VALUES (?, ?)", 
                        (ek, kategori)
                    )
                except sqlite3.Error as e:
                    logger.warning(f"Ek ekleme hatası: {ek} - {e}")
        
        self.conn.commit()
    
    def kapat(self):
        """Veritabanı bağlantısını kapatır"""
        if self.conn:
            try:
                self.conn.close()
                self.conn = None
            except sqlite3.Error as e:
                logger.error(f"Veritabanı kapatma hatası: {e}")
    
    def _check_connection(self):
        """Veritabanı bağlantısının durumunu kontrol eder ve gerekirse yeniler"""
        if not self.conn:
            self.initialize_db()
            if not self.conn:
                raise sqlite3.Error("Veritabanı bağlantısı kurulamadı")
    
    def get_bilinen_kokler(self) -> Dict[str, str]:
        """Veritabanındaki bilinen kökleri çeker"""
        bilinen_kokler = {}
        try:
            self._check_connection()
            cursor = self.conn.cursor()
            cursor.execute("SELECT kok, tur FROM kokler")
            for row in cursor.fetchall():
                bilinen_kokler[row[0]] = row[1]
            return bilinen_kokler
        except sqlite3.Error as e:
            logger.error(f"Bilinen kökleri çekme hatası: {e}")
            return {}
    
    def get_bilinen_ekler(self) -> Dict[str, List[str]]:
        """Veritabanındaki bilinen ekleri kategorilerine göre çeker"""
        bilinen_ekler = {}
        try:
            self._check_connection()
            cursor = self.conn.cursor()
            cursor.execute("SELECT ek, kategori FROM ekler")
            for row in cursor.fetchall():
                ek, kategori = row
                if kategori not in bilinen_ekler:
                    bilinen_ekler[kategori] = []
                bilinen_ekler[kategori].append(ek)
            return bilinen_ekler
        except sqlite3.Error as e:
            logger.error(f"Bilinen ekleri çekme hatası: {e}")
            return {}
    
    def kok_ekle(self, kok: str, tur: str = 'isim', kaynak: str = 'kullanici') -> int:
        """Yeni bir kök ekler veya varsa frekansını artırır"""
        if self.readonly:
            return -1  # Salt okunur modda ekleme yapmayız
            
        try:
            self._check_connection()
            cursor = self.conn.cursor()
            
            # Retry mekanizması ekle
            max_retry = 3
            retry_count = 0
            
            while retry_count < max_retry:
                try:
                    cursor.execute(
                        "INSERT INTO kokler (kok, tur, kaynak) VALUES (?, ?, ?) "
                        "ON CONFLICT(kok) DO UPDATE SET frekans = frekans + 1",
                        (kok, tur, kaynak)
                    )
                    self.conn.commit()
                    
                    # Eklenen veya güncellenen kökün ID'sini getir
                    cursor.execute("SELECT id FROM kokler WHERE kok = ?", (kok,))
                    result = cursor.fetchone()
                    if result:
                        return result[0]
                    return -1
                    
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and retry_count < max_retry - 1:
                        retry_count += 1
                        import time
                        time.sleep(0.2 * (2 ** retry_count))  # Exponential backoff
                        continue
                    raise
                    
                except Exception:
                    raise
                    
        except sqlite3.Error as e:
            logger.error(f"Kök ekleme hatası: {kok} - {e}")
            return -1
    
    def ek_ekle(self, ek: str, kategori: str) -> bool:
        """Yeni bir ek ekler veya varsa frekansını artırır"""
        if self.readonly:
            return False  # Salt okunur modda ekleme yapmayız
            
        try:
            self._check_connection()
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO ekler (ek, kategori) VALUES (?, ?) "
                "ON CONFLICT(ek, kategori) DO UPDATE SET frekans = frekans + 1",
                (ek, kategori)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Ek ekleme hatası: {ek} - {e}")
            return False
    
    def sozcuk_analizi_kaydet(self, sozcuk: str, kok_id: int, analiz_json: str) -> bool:
        """Bir sözcüğün analiz sonucunu kaydeder"""
        if self.readonly:
            return False  # Salt okunur modda ekleme yapmayız
            
        try:
            self._check_connection()
            cursor = self.conn.cursor()
            
            # Retry mekanizması ekle
            max_retry = 3
            retry_count = 0
            
            while retry_count < max_retry:
                try:
                    cursor.execute(
                        "INSERT INTO sozcuk_analizleri (sozcuk, kok_id, analiz_json) VALUES (?, ?, ?) "
                        "ON CONFLICT(sozcuk) DO UPDATE SET "
                        "kok_id = ?, analiz_json = ?, frekans = frekans + 1, son_guncelleme = CURRENT_TIMESTAMP",
                        (sozcuk, kok_id, analiz_json, kok_id, analiz_json)
                    )
                    self.conn.commit()
                    return True
                    
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and retry_count < max_retry - 1:
                        retry_count += 1
                        import time
                        time.sleep(0.2 * (2 ** retry_count))  # Exponential backoff
                        continue
                    raise
                    
                except Exception:
                    raise
                    
        except sqlite3.Error as e:
            logger.error(f"Sözcük analizi kaydetme hatası: {sozcuk} - {e}")
            return False
    
    def sorunlu_sozcuk_ekle(self, sozcuk: str, durum: str = 'beklemede', not_metni: str = '') -> bool:
        """Sorunlu bir sözcüğü veritabanına ekler"""
        if self.readonly:
            return False  # Salt okunur modda ekleme yapmayız
            
        try:
            self._check_connection()
            cursor = self.conn.cursor()
            
            # Retry mekanizması ekle
            max_retry = 3
            retry_count = 0
            
            while retry_count < max_retry:
                try:
                    cursor.execute(
                        "INSERT INTO sorunlu_sozcukler (sozcuk, durum, not_metni) VALUES (?, ?, ?) "
                        "ON CONFLICT(sozcuk) DO UPDATE SET "
                        "deneme_sayisi = deneme_sayisi + 1, durum = ?, not_metni = ?",
                        (sozcuk, durum, not_metni, durum, not_metni)
                    )
                    self.conn.commit()
                    return True
                    
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and retry_count < max_retry - 1:
                        retry_count += 1
                        import time
                        time.sleep(0.2 * (2 ** retry_count))  # Exponential backoff
                        continue
                    raise
                    
                except Exception:
                    raise
        
        except sqlite3.Error as e:
            logger.error(f"Sorunlu sözcük ekleme hatası: {sozcuk} - {e}")
            return False
    
    def sozcuk_analizi_getir(self, sozcuk: str) -> Optional[Dict]:
        """Veritabanında kayıtlı bir sözcüğün analizini getirir"""
        try:
            self._check_connection()
            cursor = self.conn.cursor()
            
            # Retry mekanizması ekle
            max_retry = 3
            retry_count = 0
            
            while retry_count < max_retry:
                try:
                    cursor.execute(
                        "SELECT analiz_json FROM sozcuk_analizleri WHERE sozcuk = ?",
                        (sozcuk,)
                    )
                    result = cursor.fetchone()
                    if result:
                        import json
                        return json.loads(result[0])
                    return None
                    
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and retry_count < max_retry - 1:
                        retry_count += 1
                        import time
                        time.sleep(0.2 * (2 ** retry_count))  # Exponential backoff
                        continue
                    raise
                    
                except Exception:
                    raise
                    
        except sqlite3.Error as e:
            logger.error(f"Sözcük analizi getirme hatası: {sozcuk} - {e}")
            return None
"""
Türkçe Morfolojik Analiz - Yapılandırma Dosyası Yardımcıları
"""

import configparser
import os

def config_yukle(config_dosya_yolu='config.ini'):
    """Yapılandırma dosyasını yükler"""
    # Varsayılan config değerleri
    varsayilan_config = {
        'Genel': {
            'veritabani': 'turkce_morfoloji.db',
            'zemberek_jar': 'zemberek-full.jar',
            'log_seviyesi': 'INFO',
            'interaktif': 'True'
        },
        'Dosyalar': {
            'sozluk_dosyasi': '',
            'metin_dosyasi': '',
            'cikti_dosyasi': ''
        },
        'Gelismis': {
            'max_derinlik': '5',
            'unlu_uyumu_kontrol': 'True',
            'unsuz_yumusama_kontrol': 'True',
            'zemberek_oncelikli': 'True'
        }
    }
    
    config = configparser.ConfigParser()
    
    # Varsayılan değerleri ayarla
    for bolum, ayarlar in varsayilan_config.items():
        if not config.has_section(bolum):
            config.add_section(bolum)
        for anahtar, deger in ayarlar.items():
            config[bolum][anahtar] = deger
    
    # Eğer config dosyası varsa, oku ve değerleri güncelle
    if os.path.exists(config_dosya_yolu):
        config.read(config_dosya_yolu, encoding='utf-8')
    else:
        # Dosya yoksa, varsayılan config dosyasını oluştur
        with open(config_dosya_yolu, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        print(f"Varsayılan yapılandırma dosyası oluşturuldu: {config_dosya_yolu}")
    
    return config

def config_kaydet(config, config_dosya_yolu='config.ini'):
    """Yapılandırma dosyasını kaydeder"""
    with open(config_dosya_yolu, 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    print(f"Yapılandırma dosyası güncellendi: {config_dosya_yolu}")

def ornek_config_olustur():
    """Örnek config dosyası oluşturur"""
    config = configparser.ConfigParser()
    
    config['Genel'] = {
        'veritabani': 'turkce_morfoloji.db',
        'zemberek_jar': 'zemberek-full.jar',
        'log_seviyesi': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        'interaktif': 'True'
    }
    
    config['Dosyalar'] = {
        'sozluk_dosyasi': 'kokler.txt',
        'metin_dosyasi': 'ornek_metin.txt',
        'cikti_dosyasi': 'sonuclar.txt'
    }
    
    config['Gelismis'] = {
        'max_derinlik': '5',  # Özyinelemeli analiz maksimum derinliği
        'unlu_uyumu_kontrol': 'True',
        'unsuz_yumusama_kontrol': 'True',
        'zemberek_oncelikli': 'True'
    }
    
    with open('ornek_config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)
    
    print("Örnek yapılandırma dosyası oluşturuldu: ornek_config.ini")
    
    # Açıklamalı örnek config oluştur (yorumlu versiyon)
    with open('ornek_config_aciklamali.ini', 'w', encoding='utf-8') as f:
        f.write("""[Genel]
# Veritabanı dosya yolu
veritabani = turkce_morfoloji.db
# Zemberek JAR dosya yolu
zemberek_jar = zemberek-full.jar
# Log seviyesi: DEBUG, INFO, WARNING, ERROR, CRITICAL
log_seviyesi = INFO
# İnteraktif mod (True/False)
interaktif = True

[Dosyalar]
# Kök sözcük listesi dosyası (opsiyonel)
sozluk_dosyasi = kokler.txt
# İşlenecek metin dosyası (opsiyonel)
metin_dosyasi = ornek_metin.txt
# Çıktı dosyası (opsiyonel, belirtilmezse sadece konsola yazdırılır)
cikti_dosyasi = sonuclar.txt

[Gelismis]
# Özyinelemeli analiz maksimum derinliği
max_derinlik = 5
# Ünlü uyumu kontrolü
unlu_uyumu_kontrol = True
# Ünsüz yumuşaması kontrolü
unsuz_yumusama_kontrol = True
# Zemberek öncelikli çalışma modu
zemberek_oncelikli = True
""")
    print("Açıklamalı örnek yapılandırma dosyası oluşturuldu: ornek_config_aciklamali.ini")

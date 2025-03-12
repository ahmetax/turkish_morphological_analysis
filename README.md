# Türkçe Morfolojik Analiz

Öğrenebilen, yapılandırılabilir ve genişletilebilir Türkçe morfolojik analiz aracı. SQLite veritabanı entegrasyonu ve Zemberek desteği ile Türkçe sözcükleri kök ve eklerine ayıran, zamanla öğrenen bir sistem.

## Özellikler

- **Öğrenebilen Analiz**: Sistem analiz ettiği sözcükleri veritabanına kaydederek zaman içinde daha akıllı hale gelir
- **Zemberek Entegrasyonu**: Zemberek NLP kütüphanesi desteği
- **Kapsamlı Türkçe Dil Kuralları**: Büyük-küçük ünlü uyumu, ünsüz yumuşaması gibi kuralları uygular
- **Yapılandırılabilir**: Detaylı konfigürasyon dosyası desteği
- **Çoklu İşlem**: Büyük metinleri paralel işleme
- **Raporlama**: Analiz sonuçlarını grafik ve tablolarla raporlama

## Kurulum

### Gereksinimler

- Python 3.6+
- JPype1 (Zemberek entegrasyonu için)
- Matplotlib (Grafik raporlar için)

```bash
pip install -r requirements.txt
```

### Zemberek 

Zemberek desteği için, [zemberek-nlp](https://github.com/ahmetaa/zemberek-nlp) projesinden son sürüm JAR dosyasını indirin ve proje klasörüne kopyalayın.

## Kullanım

### Komut Satırı Arayüzü

```bash
# Tek bir sözcüğü analiz et
python turkce_morfologik_analiz.py --sozcuk "kitaplarımızdan"

# Bir metni analiz et
python turkce_morfologik_analiz.py --metin "Türkçe dilbilgisi çalışmalarına katkıda bulunmak istiyorum"

# Dosyadan okuyarak analiz et
python turkce_morfologik_analiz.py --dosya metin.txt

# Sözcük listesi yükle
python turkce_morfologik_analiz.py --sozluk_yukle kokler.txt
```

### Çoklu İşlem İle Büyük Dosya Analizi

```bash
python coklu_islem.py --dosya buyuk_metin.txt --cikti analiz_sonuclari.txt
```

### Raporlama

```bash
python rapor_araci.py --istatistik --csv rapor.csv --grafik
```

## Yapılandırma

Yapılandırma dosyası ile aracın davranışını değiştirebilirsiniz:

```bash
# Örnek yapılandırma dosyası oluştur
python turkce_morfologik_analiz.py --ornek-config

# Belirli bir yapılandırma dosyası kullan
python turkce_morfologik_analiz.py --config ozel_ayarlar.ini
```

## Geliştirme

### Test

```bash
# Testleri çalıştır
python -m pytest test_morfoloji.py

# Kod kapsama raporu ile
coverage run -m pytest test_morfoloji.py
coverage report -m
```

### Paketleme

```bash
# Pip paketi oluştur
python setup.py sdist bdist_wheel
```

## Lisans

MIT Lisansı altında dağıtılmaktadır.

## Katkıda Bulunanlar

Bu proje açık kaynaklıdır ve katkılarınızı bekliyoruz!

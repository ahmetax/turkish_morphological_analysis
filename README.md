# Türkçe Morfolojik Analiz

Öğrenebilen, yapılandırılabilir ve genişletilebilir Türkçe morfolojik analiz sistemi. SQLite veritabanı entegrasyonu ve opsiyonel Zemberek desteği ile Türkçe sözcükleri kök ve eklerine ayıran, zamanla öğrenen bir çözüm.

## Özellikler

- **Öğrenebilen Analiz**: Sistem analiz ettiği sözcükleri veritabanına kaydederek zaman içinde daha akıllı hale gelir
- **Kapsamlı Türkçe Dil Kuralları**: Büyük-küçük ünlü uyumu, ünsüz yumuşaması gibi kuralları uygular
- **Çoklu Dosya İşleme**: Toplu metin dosyası analizi yapabilme
- **Frekans Analizi**: Metinlerdeki sözcüklerin kullanım sıklığını tespit eder
- **Sorunlu Sözcük Takibi**: Çözümlenemeyen sözcüklerin hangi dosyalarda geçtiğini izler
- **İnteraktif Düzeltme Aracı**: Sorunlu sözcükleri kolayca düzeltmeyi sağlar
- **Yapılandırılabilir**: Detaylı konfigürasyon dosyası desteği
- **Zemberek Entegrasyonu** (opsiyonel): Zemberek NLP kütüphanesi desteği

## Modüller

Proje aşağıdaki temel modüllerden oluşur:

1. **turkce_morfologik_analiz.py**: Ana analiz motoru ve algoritması
2. **veritabani.py**: SQLite veritabanı işlemleri
3. **config_utils.py**: Yapılandırma dosyası işlemleri
4. **zemberek_wrapper.py**: Zemberek kütüphanesi entegrasyonu
5. **toplu_analiz_frekans.py**: Çoklu dosya ve frekans analizi
6. **toplu_analiz_sorunlu_takip.py**: Sorunlu sözcük takip sistemi
7. **sorunlu_duzeltme.py**: İnteraktif sözcük düzeltme aracı

## Kurulum

### Gereksinimler

- Python 3.6 veya üzeri
- Gerekli Python kütüphaneleri:

```bash
pip install -r requirements.txt
```

### Zemberek Kurulumu (Opsiyonel)

Zemberek desteğini kullanmak isterseniz:

1. [Zemberek NLP](https://github.com/ahmetaa/zemberek-nlp) projesinden JAR dosyasını indirin
2. JAR dosyasını proje klasörüne `zemberek-full.jar` adıyla kaydedin
3. JPype1 kütüphanesini yükleyin: `pip install JPype1`

## Kullanım

### Temel Analiz

Tek bir sözcüğü analiz etmek için:

```bash
python turkce_morfologik_analiz.py --sozcuk "kitaplarımızdan"
```

Bir metin dosyasını analiz etmek için:

```bash
python turkce_morfologik_analiz.py --dosya metin.txt
```

### Toplu Dosya ve Frekans Analizi

Bir klasördeki tüm metin dosyalarını analiz etmek ve frekans bilgisi çıkarmak için:

```bash
python toplu_analiz_frekans.py --klasor metinler_klasoru --cikti-klasoru sonuclar --csv frekanslar.csv
```

### Sorunlu Sözcük Takibi

Sorunlu sözcüklerin hangi dosyalarda geçtiğini izleyen gelişmiş analiz:

```bash
python toplu_analiz_sorunlu_takip.py --klasor metinler_klasoru --sorunlu sorunlu_kelimeler.txt
```

### Sorunlu Sözcük Düzeltme Aracı

İnteraktif düzeltme aracını başlatmak için:

```bash
python sorunlu_duzeltme.py
```

Bu araç ile:
- En sık kullanılan sorunlu sözcükleri görebilir
- Sözcüğün hangi dosyalarda, hangi bağlamlarda geçtiğini inceleyebilir
- Akıllı tahminler yardımıyla sözcükleri hızlıca düzeltebilir
- Toplu düzeltmeler yapabilirsiniz

## Yapılandırma

Varsayılan yapılandırma dosyası oluşturmak için:

```bash
python turkce_morfologik_analiz.py --ornek-config
```

## Nasıl Çalışır?

1. **Morfolojik Analiz**: 
   - Sözcükleri olası kök ve eklerine ayırır
   - Türkçe dil kurallarını uygular (ünlü uyumu, ünsüz yumuşaması)
   - Veritabanında kayıtlı kökleri kontrol eder

2. **Öğrenme Mekanizması**:
   - Başarılı analizleri veritabanına kaydeder
   - Sorunlu sözcükleri işaretler
   - Kullanıcı düzeltmelerini öğrenir

3. **Frekans Analizi**:
   - Sözcüklerin metin içindeki kullanım sıklığını hesaplar
   - Belge bazında ve toplam kullanım istatistikleri çıkarır

4. **Sorunlu Sözcük Yönetimi**:
   - Çözümlenemeyen sözcükleri tespit eder
   - Bu sözcüklerin geçtiği dosya ve bağlamları kaydeder
   - İnteraktif düzeltme imkanı sunar

## Katkıda Bulunma

Projeye katkıda bulunmak için:

1. Bu repoyu fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inize push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## Yapılacaklar

- [ ] Özel isim tanıma sistemi
- [ ] Yabancı kelime desteği
- [ ] Makine öğrenmesi entegrasyonu
- [ ] Web arayüzü
- [ ] GPU hızlandırmalı toplu işleme

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## İletişim

Ahmet Aksoy - [@ahmetax](https://github.com/ahmetax)

Proje Linki: [https://github.com/ahmetax/turkish_morphological_analysis](https://github.com/ahmetax/turkish_morphological_analysis)

Bu proje Claude 3.7 Sonnet - (https://claude.ai) katkısıyla geliştirilmiştir.


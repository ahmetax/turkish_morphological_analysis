#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zemberek JAR testi - Sürüm ve API uyumluluğunu test et
"""

import os
import sys
import argparse
import jpype
import jpype.imports

def test_zemberek(jar_path):
    """Zemberek JAR dosyasını test et"""
    print(f"JPype sürümü: {jpype.__version__}")
    print(f"Python sürümü: {sys.version}")
    print(f"Test edilecek JAR: {jar_path}")
    
    if not os.path.exists(jar_path):
        print(f"HATA: JAR dosyası bulunamadı: {jar_path}")
        return False
    
    # JVM başlat
    if not jpype.isJVMStarted():
        jpype.startJVM(classpath=[jar_path])
        print("JVM başlatıldı.")
    
    # Zemberek sürümünü tespit etmeye çalış
    try:
        version = jpype.java.lang.System.getProperty("zemberek.version", "Sürüm bilgisi bulunamadı")
        print(f"Zemberek sürümü: {version}")
    except:
        print("Zemberek sürüm bilgisi alınamadı.")
    
    # TurkishMorphology sınıfını bulmaya çalış
    try:
        TurkishMorphology = jpype.JClass("zemberek.morphology.TurkishMorphology")
        print("TurkishMorphology sınıfı bulundu.")
        
        # TurkishMorphology örneği oluştur
        morphology = TurkishMorphology.createWithDefaults()
        print("TurkishMorphology örneği oluşturuldu.")
        
        # API metodlarını keşfet
        print("\nAPI metodları:")
        methods = [method for method in dir(morphology.__class__) 
                  if not method.startswith("_") and callable(getattr(morphology.__class__, method))]
        for method in sorted(methods):
            print(f"- {method}")
        
        # Örnek bir analiz yap
        test_words = ["kitap", "kitaba", "kitaplarımızdan", "geliyorum", "anlaşılmayabiliyordu"]
        
        print("\nÖrnek analizler:")
        for word in test_words:
            analyze_word(morphology, word)
            
        return True
        
    except Exception as e:
        print(f"TurkishMorphology sınıfı yüklenemedi: {e}")
        return False

def analyze_word(morphology, word):
    """Bir kelimeyi analiz et ve sonuçları yazdır"""
    print(f"\nSözcük: {word}")
    
    try:
        results = morphology.analyze(word)
        
        # Sonuç türünü görüntüle
        result_type = type(results).__name__
        print(f"Sonuç türü: {result_type}")
        
        # Sonuç yapısını keşfet
        print(f"Java sınıfı: {results.getClass().getName()}")
        
        # API metodlarını keşfet
        result_methods = [method for method in dir(results.__class__) 
                         if not method.startswith("_") and callable(getattr(results.__class__, method))]
        print(f"Mevcut metodlar: {', '.join(sorted(result_methods[:5]))}...")
        
        # Listeye çevir
        analysis_results = list(results)
        print(f"Analiz sonuçları sayısı: {len(analysis_results)}")
        
        if analysis_results:
            first_result = analysis_results[0]
            print(f"İlk sonuç türü: {type(first_result).__name__}")
            print(f"Java sınıfı: {first_result.getClass().getName()}")
            
            # İlk sonucun metodlarını keşfet
            first_result_methods = [method for method in dir(first_result.__class__) 
                                  if not method.startswith("_") and callable(getattr(first_result.__class__, method))]
            print(f"Mevcut metodlar: {', '.join(sorted(first_result_methods[:5]))}...")
            
            # Lemmaları almaya çalış
            try:
                if hasattr(first_result, 'getLemmas') and callable(getattr(first_result, 'getLemmas')):
                    lemmas = first_result.getLemmas()
                    if lemmas:
                        print(f"Lemmalar: {list(lemmas)}")
                elif hasattr(first_result, 'getLemma') and callable(getattr(first_result, 'getLemma')):
                    lemma = first_result.getLemma()
                    print(f"Lemma: {lemma}")
            except Exception as e:
                print(f"Lemma hatası: {e}")
            
            # Morfemleri almaya çalış
            try:
                if hasattr(first_result, 'getMorphemes') and callable(getattr(first_result, 'getMorphemes')):
                    morphemes = first_result.getMorphemes()
                    if morphemes:
                        print(f"Morfemler: {list(morphemes)}")
            except Exception as e:
                print(f"Morfem hatası: {e}")
        
    except Exception as e:
        print(f"Analiz hatası: {e}")

def main():
    """Ana program fonksiyonu"""
    parser = argparse.ArgumentParser(description='Zemberek JAR test aracı')
    parser.add_argument('--jar', '-j', default='zemberek-full.jar', help='Zemberek JAR dosya yolu')
    
    args = parser.parse_args()
    test_zemberek(args.jar)

if __name__ == "__main__":
    main()

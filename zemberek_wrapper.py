"""
Türkçe Morfolojik Analiz - Zemberek Kütüphanesi Wrapper Sınıfı
"""

import os
import logging
from typing import Optional, Dict

# Zemberek entegrasyonu için JPype gerekecek (pip install JPype1)
try:
    import jpype
    import jpype.imports
    ZEMBEREK_MEVCUT = True
except ImportError:
    ZEMBEREK_MEVCUT = False

logger = logging.getLogger("TurkceMorfAnaliz")

class ZemberekWrapper:
    """Zemberek kütüphanesi için wrapper sınıf"""
    
    def __init__(self, zemberek_jar_path: str = "zemberek-full.jar"):
        self.available = False
        self.morphology = None
        
        if not ZEMBEREK_MEVCUT:
            logger.warning("JPype kurulu değil. Zemberek kullanılamayacak.")
            return
            
        if not os.path.exists(zemberek_jar_path):
            logger.warning(f"Zemberek JAR dosyası bulunamadı: {zemberek_jar_path}")
            return
            
        try:
            # JVM başlat
            if not jpype.isJVMStarted():
                jpype.startJVM(classpath=[jar_path for jar_path in [zemberek_jar_path] if os.path.exists(jar_path)])
                logger.info("JVM başlatıldı.")
            
            # TurkishMorphology sınıfını yükle
            try:
                TurkishMorphology = jpype.JClass("zemberek.morphology.TurkishMorphology")
                self.morphology = TurkishMorphology.createWithDefaults()
                self.available = True
                logger.info("TurkishMorphology başarıyla yüklendi.")
            except Exception as e:
                logger.error(f"TurkishMorphology yükleme hatası: {e}")
                
        except Exception as e:
            logger.error(f"Zemberek başlatma hatası: {e}")
    
    def analyze(self, word: str) -> Optional[Dict]:
        """Kelimeyi zemberek ile analiz eder"""
        if not self.available or self.morphology is None:
            return None
            
        try:
            # Test çıktısından: TurkishMorphology.analyze metodu mevcut
            results = self.morphology.analyze(word)
            
            # Sonuçları kontrol et
            if results is None:
                return None
            
            # Test çıktısından: analysisCount metodu kullanılabilir
            if hasattr(results, 'analysisCount') and callable(getattr(results, 'analysisCount')):
                if results.analysisCount() == 0:
                    return None
            
            # Test çıktısından: getAnalysisResults metodu mevcut
            analysis_results = None
            if hasattr(results, 'getAnalysisResults') and callable(getattr(results, 'getAnalysisResults')):
                analysis_results = results.getAnalysisResults()
                if analysis_results and len(analysis_results) > 0:
                    best_analysis = analysis_results[0]
                else:
                    return None
            else:
                # Alternatif olarak liste gibi davranabilir
                analysis_results = list(results)
                if analysis_results:
                    best_analysis = analysis_results[0]
                else:
                    return None
            
            # Kök bilgisini al
            root = word  # Varsayılan olarak kelimeyi döndür
            
            # Test çıktısından: getLemmas mevcut ve liste döndürüyor
            if hasattr(best_analysis, 'getLemmas') and callable(getattr(best_analysis, 'getLemmas')):
                lemmas = best_analysis.getLemmas()
                if lemmas and len(lemmas) > 0:
                    root = str(lemmas[0])  # İlk lemmayı al
            
            # Ekleri al
            morphemes = []
            
            # Test çıktısından: getMorphemes mevcut
            if hasattr(best_analysis, 'getMorphemes') and callable(getattr(best_analysis, 'getMorphemes')):
                java_morphemes = best_analysis.getMorphemes()
                if java_morphemes:
                    # İlk morfem genellikle kök olduğu için atlıyoruz
                    for i, morpheme in enumerate(java_morphemes):
                        if i > 0:  # İlk öğeyi atla (kök)
                            morphemes.append((str(morpheme), "zemberek"))
            
            # Sonuç olarak döndür
            return {
                'kok': root,
                'ekler': morphemes,
                'source': 'zemberek'
            }
            
        except Exception as e:
            logger.error(f"Zemberek analiz hatası: {e}")
            return None
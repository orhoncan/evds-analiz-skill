#!/usr/bin/env python3
"""
EVDS Gelişmiş Analiz Modülü
- Çoklu değişken analizi
- Mevsimsellik temizleme
- Anomali/Outlier tespiti
- Dashboard modu
- Veri kalitesi kontrolü
"""

import os
import pandas as pd
import numpy as np
import html
from typing import Dict, List
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Renk paleti
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#34495E',
    'accent1': '#E74C3C',
    'accent2': '#3498DB',
    'accent3': '#F39C12',
    'accent4': '#16A085',
    'accent5': '#9B59B6',
    'accent6': '#27AE60',
    'background': '#FFFFFF',
    'grid': '#ECF0F1',
    'text': '#2C3E50',
    'text_secondary': '#95A5A6',
    'warning': '#F39C12',
    'danger': '#E74C3C',
    'success': '#27AE60'
}

PALETTE = ['#2C3E50', '#E74C3C', '#3498DB', '#F39C12', '#16A085', '#9B59B6', '#27AE60']


# ============================================================================
# 1. VERİ KALİTESİ KONTROLÜ
# ============================================================================

def veri_kalitesi_kontrolu(df: pd.DataFrame) -> Dict:
    """
    Kapsamlı veri kalitesi analizi yapar.
    
    Kontroller:
    - Eksik veri analizi
    - Duplicate kayıtlar
    - Outlier tespiti (IQR + Z-score)
    - Veri tipi tutarlılığı
    - Zaman serisi sürekliliği
    - İstatistiksel özellikler
    
    Returns:
    --------
    dict
        Veri kalitesi raporu
    """
    rapor = {
        'genel': {},
        'sutunlar': {},
        'zaman_serisi': {},
        'uyarilar': [],
        'puan': 100  # Kalite puanı (100 üzerinden)
    }
    
    # Sütun bazlı analiz verilerini önceden hesapla
    isna_sums = df.isna().sum()
    n_unique = df.nunique()
    eksik_toplam = int(isna_sums.sum())
    toplam_hucre = df.size

    satir_sayisi = len(df)

    # Oranları vektörel hesapla
    if satir_sayisi > 0:
        eksik_orans = (isna_sums / satir_sayisi * 100).round(2)
        benzersiz_orans = (n_unique / satir_sayisi * 100).round(2)
    else:
        eksik_orans = pd.Series(0.0, index=df.columns)
        benzersiz_orans = pd.Series(0.0, index=df.columns)

    dtypes = df.dtypes.astype(str)

    # Genel bilgiler
    rapor['genel'] = {
        'satir_sayisi': satir_sayisi,
        'sutun_sayisi': len(df.columns),
        'toplam_hucre': toplam_hucre,
        'eksik_toplam': eksik_toplam,
        'eksik_oran': round(eksik_toplam / toplam_hucre * 100, 2) if toplam_hucre > 0 else 0.0,
        'duplicate_satir': df.duplicated().sum(),
        'bellek_kullanimi': f"{df.memory_usage(deep=True).sum() / 1024:.2f} KB"
    }
    
    # Eksik veri için puan düşür
    if rapor['genel']['eksik_oran'] > 10:
        rapor['puan'] -= 20
        rapor['uyarilar'].append(f"⚠️ Yüksek eksik veri oranı: %{rapor['genel']['eksik_oran']}")
    elif rapor['genel']['eksik_oran'] > 5:
        rapor['puan'] -= 10
        rapor['uyarilar'].append(f"⚠️ Orta düzeyde eksik veri: %{rapor['genel']['eksik_oran']}")
    
    # Duplicate için puan düşür
    if rapor['genel']['duplicate_satir'] > 0:
        rapor['puan'] -= 5
        rapor['uyarilar'].append(f"⚠️ {rapor['genel']['duplicate_satir']} duplicate satır bulundu")
    
    # Sütun bazlı analiz
    for col in df.columns:
        seri = df[col]

        col_info = {
            'tip': dtypes[col],
            'eksik': int(isna_sums[col]),
            'eksik_oran': float(eksik_orans[col]),
            'benzersiz': int(n_unique[col]),
            'benzersiz_oran': float(benzersiz_orans[col])
        }
        
        # Sayısal sütunlar için ek analiz
        if pd.api.types.is_numeric_dtype(seri):
            seri_temiz = seri.dropna()
            if len(seri_temiz) > 0:
                # IQR outlier tespiti
                Q1 = seri_temiz.quantile(0.25)
                Q3 = seri_temiz.quantile(0.75)
                IQR = Q3 - Q1
                alt_sinir = Q1 - 1.5 * IQR
                ust_sinir = Q3 + 1.5 * IQR
                outlier_iqr = ((seri_temiz < alt_sinir) | (seri_temiz > ust_sinir)).sum()
                
                # Z-score outlier tespiti
                z_scores = np.abs((seri_temiz - seri_temiz.mean()) / seri_temiz.std())
                outlier_zscore = (z_scores > 3).sum()
                
                col_info.update({
                    'min': round(seri_temiz.min(), 4),
                    'max': round(seri_temiz.max(), 4),
                    'ortalama': round(seri_temiz.mean(), 4),
                    'medyan': round(seri_temiz.median(), 4),
                    'std': round(seri_temiz.std(), 4),
                    'carpiklik': round(seri_temiz.skew(), 4),
                    'basiklik': round(seri_temiz.kurtosis(), 4),
                    'outlier_iqr': int(outlier_iqr),
                    'outlier_zscore': int(outlier_zscore),
                    'iqr_sinirlar': (round(alt_sinir, 4), round(ust_sinir, 4))
                })
                
                # Çarpıklık kontrolü
                if abs(col_info['carpiklik']) > 2:
                    rapor['uyarilar'].append(f"⚠️ {col}: Yüksek çarpıklık ({col_info['carpiklik']}) - Log dönüşümü düşünün")
                
                # Outlier kontrolü
                if outlier_iqr > len(seri_temiz) * 0.05:
                    rapor['puan'] -= 5
                    rapor['uyarilar'].append(f"⚠️ {col}: %{outlier_iqr/len(seri_temiz)*100:.1f} outlier (IQR)")
        
        rapor['sutunlar'][col] = col_info
    
    # Zaman serisi sürekliliği kontrolü
    if isinstance(df.index, pd.DatetimeIndex):
        rapor['zaman_serisi']['baslangic'] = df.index.min().strftime('%Y-%m-%d')
        rapor['zaman_serisi']['bitis'] = df.index.max().strftime('%Y-%m-%d')
        
        # Frekans tespiti
        freq = pd.infer_freq(df.index)
        rapor['zaman_serisi']['tespit_edilen_frekans'] = freq or 'Düzensiz'
        
        # Boşluk kontrolü
        if freq:
            beklenen_tarihler = pd.date_range(df.index.min(), df.index.max(), freq=freq)
            eksik_tarihler = beklenen_tarihler.difference(df.index)
            rapor['zaman_serisi']['eksik_tarih_sayisi'] = len(eksik_tarihler)
            
            if len(eksik_tarihler) > 0:
                rapor['puan'] -= min(10, len(eksik_tarihler))
                rapor['uyarilar'].append(f"⚠️ Zaman serisinde {len(eksik_tarihler)} eksik tarih var")
                rapor['zaman_serisi']['eksik_tarihler_ornek'] = eksik_tarihler[:5].strftime('%Y-%m-%d').tolist()
    
    # Final puan
    rapor['puan'] = max(0, rapor['puan'])
    
    # Kalite değerlendirmesi
    if rapor['puan'] >= 90:
        rapor['degerlendirme'] = "✅ Mükemmel veri kalitesi"
    elif rapor['puan'] >= 75:
        rapor['degerlendirme'] = "✓ İyi veri kalitesi"
    elif rapor['puan'] >= 60:
        rapor['degerlendirme'] = "⚠️ Orta düzeyde veri kalitesi - İyileştirme önerilir"
    else:
        rapor['degerlendirme'] = "❌ Düşük veri kalitesi - Dikkatli kullanın"
    
    return rapor


def format_veri_kalitesi(rapor: Dict) -> str:
    """Veri kalitesi raporunu formatlar."""
    metin = f"""
📊 VERİ KALİTESİ RAPORU
{'═' * 50}

{rapor['degerlendirme']}
Kalite Puanı: {rapor['puan']}/100

📋 GENEL BİLGİLER
{'─' * 40}
• Satır sayısı: {rapor['genel']['satir_sayisi']:,}
• Sütun sayısı: {rapor['genel']['sutun_sayisi']}
• Toplam eksik: {rapor['genel']['eksik_toplam']:,} (%{rapor['genel']['eksik_oran']})
• Duplicate satır: {rapor['genel']['duplicate_satir']}
• Bellek: {rapor['genel']['bellek_kullanimi']}
"""
    
    if rapor['zaman_serisi']:
        metin += f"""
📅 ZAMAN SERİSİ
{'─' * 40}
• Dönem: {rapor['zaman_serisi'].get('baslangic', '-')} → {rapor['zaman_serisi'].get('bitis', '-')}
• Frekans: {rapor['zaman_serisi'].get('tespit_edilen_frekans', '-')}
• Eksik tarih: {rapor['zaman_serisi'].get('eksik_tarih_sayisi', 0)}
"""
    
    if rapor['uyarilar']:
        metin += f"""
⚠️ UYARILAR
{'─' * 40}
"""
        for uyari in rapor['uyarilar']:
            metin += f"{uyari}\n"
    
    return metin


# ============================================================================
# 2. ANOMALİ / OUTLIER TESPİTİ
# ============================================================================

def anomali_tespiti(
    df: pd.DataFrame,
    metot: str = 'iqr',
    esik: float = 1.5,
    pencere: int = None
) -> Dict:
    """
    Çoklu yöntemle anomali/outlier tespiti yapar.
    
    Yöntemler:
    - 'iqr': Interquartile Range (varsayılan)
    - 'zscore': Z-score (3 sigma)
    - 'mad': Median Absolute Deviation
    - 'isolation': Isolation Forest (sklearn gerekli)
    - 'rolling': Rolling window (trend-aware)
    
    Parameters:
    -----------
    df : pd.DataFrame
        Analiz edilecek veri
    metot : str
        Anomali tespit yöntemi
    esik : float
        IQR için çarpan (varsayılan 1.5), zscore için sigma (varsayılan 3)
    pencere : int
        Rolling metodu için pencere boyutu
    
    Returns:
    --------
    dict
        Her sütun için anomali indeksleri ve değerleri
    """
    sonuclar = {}
    
    for col in df.select_dtypes(include=[np.number]).columns:
        seri = df[col].dropna()
        
        if len(seri) < 10:
            sonuclar[col] = {'anomali_yok': True, 'mesaj': 'Yetersiz veri'}
            continue
        
        if metot == 'iqr':
            Q1 = seri.quantile(0.25)
            Q3 = seri.quantile(0.75)
            IQR = Q3 - Q1
            alt = Q1 - esik * IQR
            ust = Q3 + esik * IQR
            anomaliler = seri[(seri < alt) | (seri > ust)]
            
        elif metot == 'zscore':
            z = np.abs((seri - seri.mean()) / seri.std())
            anomaliler = seri[z > esik]
            alt = seri.mean() - esik * seri.std()
            ust = seri.mean() + esik * seri.std()
            
        elif metot == 'mad':
            medyan = seri.median()
            mad = np.median(np.abs(seri - medyan))
            modified_z = 0.6745 * (seri - medyan) / mad
            anomaliler = seri[np.abs(modified_z) > esik]
            alt = medyan - esik * mad / 0.6745
            ust = medyan + esik * mad / 0.6745
            
        elif metot == 'rolling':
            pencere = pencere or min(12, len(seri) // 4)
            rolling_mean = seri.rolling(window=pencere, center=True).mean()
            rolling_std = seri.rolling(window=pencere, center=True).std()
            alt = rolling_mean - esik * rolling_std
            ust = rolling_mean + esik * rolling_std
            anomaliler = seri[(seri < alt) | (seri > ust)]
            
        elif metot == 'isolation':
            try:
                from sklearn.ensemble import IsolationForest
                model = IsolationForest(contamination=0.05, random_state=42)
                yhat = model.fit_predict(seri.values.reshape(-1, 1))
                anomaliler = seri[yhat == -1]
                alt, ust = None, None
            except ImportError:
                return {'hata': 'sklearn paketi yüklü değil. pip install scikit-learn'}
        else:
            return {'hata': f'Bilinmeyen metot: {metot}'}
        
        sonuclar[col] = {
            'metot': metot,
            'anomali_sayisi': len(anomaliler),
            'anomali_oran': round(len(anomaliler) / len(seri) * 100, 2),
            'anomali_indeksler': anomaliler.index.tolist(),
            'anomali_degerler': anomaliler.values.tolist(),
            'sinirlar': (round(alt, 4) if alt else None, round(ust, 4) if ust else None),
            'istatistik': {
                'ortalama': round(seri.mean(), 4),
                'std': round(seri.std(), 4),
                'min': round(seri.min(), 4),
                'max': round(seri.max(), 4)
            }
        }
        
        # Anomali detayları
        if len(anomaliler) > 0:
            detaylar = []
            for idx, val in anomaliler.items():
                tarih_str = idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx)
                sapma = (val - seri.mean()) / seri.std() if seri.std() != 0 else 0
                detaylar.append({
                    'tarih': tarih_str,
                    'deger': round(val, 4),
                    'z_score': round(sapma, 2),
                    'tip': 'yüksek' if val > seri.mean() else 'düşük'
                })
            sonuclar[col]['detaylar'] = sorted(detaylar, key=lambda x: abs(x['z_score']), reverse=True)[:10]
    
    return sonuclar


def format_anomali(sonuclar: Dict) -> str:
    """Anomali tespit sonuçlarını formatlar."""
    metin = f"""
🔍 ANOMALİ TESPİT RAPORU
{'═' * 50}
"""
    
    for col, data in sonuclar.items():
        if 'hata' in data:
            metin += f"\n❌ {col}: {data['hata']}"
            continue
        
        if data.get('anomali_yok'):
            metin += f"\n✓ {col}: {data['mesaj']}"
            continue
        
        metin += f"""
📊 {col}
{'─' * 40}
• Yöntem: {data['metot'].upper()}
• Anomali sayısı: {data['anomali_sayisi']} (%{data['anomali_oran']})
• Sınırlar: [{data['sinirlar'][0]} - {data['sinirlar'][1]}]
"""
        
        if data.get('detaylar'):
            metin += "• En belirgin anomaliler:\n"
            for d in data['detaylar'][:5]:
                emoji = "📈" if d['tip'] == 'yüksek' else "📉"
                metin += f"  {emoji} {d['tarih']}: {d['deger']} (z={d['z_score']})\n"
    
    return metin


# ============================================================================
# 3. MEVSİMSELLİK TEMİZLEME
# ============================================================================

def mevsimsellik_temizle(
    seri: pd.Series,
    periyot: int = 12,
    metot: str = 'stl',
    robust: bool = True
) -> Dict:
    """
    Mevsimselliği temizleyerek düzeltilmiş seri üretir.
    
    Yöntemler:
    - 'stl': STL decomposition (varsayılan)
    - 'x11': X-11 tarzı (basitleştirilmiş)
    - 'ma': Moving average (klasik)
    
    Parameters:
    -----------
    seri : pd.Series
        Mevsimselliği temizlenecek seri
    periyot : int
        Mevsimsel periyot (aylık için 12)
    metot : str
        Temizleme yöntemi
    robust : bool
        Outlier'lara karşı dayanıklı tahmin
    
    Returns:
    --------
    dict
        Orijinal, trend, mevsimsel, artık ve düzeltilmiş seriler
    """
    seri = seri.dropna()
    
    if len(seri) < 2 * periyot:
        return {'hata': f'Yetersiz veri. En az {2*periyot} gözlem gerekli.'}
    
    if metot == 'stl':
        try:
            from statsmodels.tsa.seasonal import STL
            stl = STL(seri, period=periyot, robust=robust)
            sonuc = stl.fit()
            
            trend = sonuc.trend
            mevsimsel = sonuc.seasonal
            artik = sonuc.resid
            duzeltilmis = seri - mevsimsel  # Seasonally adjusted
            
        except ImportError:
            return {'hata': 'statsmodels paketi yüklü değil'}
    
    elif metot == 'ma':
        # Klasik hareketli ortalama ayrıştırma
        trend = seri.rolling(window=periyot, center=True).mean()
        trend_temiz = trend.bfill().ffill()
        
        # Mevsimsel bileşen
        detrended = seri / trend_temiz
        mevsimsel = detrended.groupby(detrended.index.month).transform('mean')
        mevsimsel = mevsimsel / mevsimsel.mean()  # Normalize
        
        artik = seri / (trend_temiz * mevsimsel)
        duzeltilmis = seri / mevsimsel
        
    elif metot == 'x11':
        # Basitleştirilmiş X-11 benzeri
        # İlk trend tahmini
        trend1 = seri.rolling(window=periyot, center=True).mean()
        
        # İlk mevsimsel tahmin
        si = seri - trend1
        mevsimsel1 = si.groupby(si.index.month).transform('mean')
        
        # Düzeltilmiş seri
        duzeltilmis1 = seri - mevsimsel1
        
        # İkinci trend tahmini (Henderson filtresi yerine ağırlıklı MA)
        weights = np.array([1, 2, 3, 3, 3, 2, 1])
        weights = weights / weights.sum()
        trend = duzeltilmis1.rolling(window=7, center=True).apply(
            lambda x: np.dot(x, weights) if len(x) == 7 else np.nan
        )
        trend = trend.bfill().ffill()
        
        # Final mevsimsel
        si2 = seri - trend
        mevsimsel = si2.groupby(si2.index.month).transform('mean')
        
        artik = seri - trend - mevsimsel
        duzeltilmis = seri - mevsimsel
        
    else:
        return {'hata': f'Bilinmeyen metot: {metot}'}
    
    # Mevsimsellik gücü hesapla
    var_artik = artik.var()
    var_mevsimsel = mevsimsel.var()
    mevsimsel_guc = 1 - (var_artik / (var_artik + var_mevsimsel)) if (var_artik + var_mevsimsel) > 0 else 0
    
    # Aylık mevsimsel faktörler
    mevsimsel_faktorler = {}
    for ay in range(1, 13):
        mask = mevsimsel.index.month == ay
        if mask.any():
            mevsimsel_faktorler[ay] = round(mevsimsel[mask].mean(), 4)
    
    return {
        'orijinal': seri,
        'trend': trend,
        'mevsimsel': mevsimsel,
        'artik': artik,
        'duzeltilmis': duzeltilmis,  # Seasonally adjusted series
        'metot': metot,
        'periyot': periyot,
        'mevsimsel_guc': round(mevsimsel_guc, 4),
        'mevsimsel_faktorler': mevsimsel_faktorler,
        'istatistik': {
            'orijinal_std': round(seri.std(), 4),
            'duzeltilmis_std': round(duzeltilmis.std(), 4),
            'trend_std': round(trend.std(), 4),
            'artik_std': round(artik.std(), 4)
        }
    }


def format_mevsimsellik(sonuc: Dict) -> str:
    """Mevsimsellik temizleme sonuçlarını formatlar."""
    if 'hata' in sonuc:
        return f"❌ Hata: {sonuc['hata']}"
    
    metin = f"""
📅 MEVSİMSELLİK TEMİZLEME RAPORU
{'═' * 50}
• Yöntem: {sonuc['metot'].upper()}
• Periyot: {sonuc['periyot']}
• Mevsimsellik gücü: {sonuc['mevsimsel_guc']:.1%}

📊 İSTATİSTİKLER
{'─' * 40}
• Orijinal std: {sonuc['istatistik']['orijinal_std']}
• Düzeltilmiş std: {sonuc['istatistik']['duzeltilmis_std']}
• Volatilite azalması: {(1 - sonuc['istatistik']['duzeltilmis_std']/sonuc['istatistik']['orijinal_std'])*100:.1f}%

📆 AYLIK MEVSİMSEL FAKTÖRLER
{'─' * 40}
"""
    
    ay_isimleri = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 
                   'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
    
    for ay, faktor in sonuc['mevsimsel_faktorler'].items():
        bar = "█" * int(abs(faktor) * 10 / max(abs(f) for f in sonuc['mevsimsel_faktorler'].values()) * 10)
        yön = "+" if faktor > 0 else ""
        metin += f"  {ay_isimleri[ay-1]}: {yön}{faktor:>8.4f} {bar}\n"
    
    return metin


# ============================================================================
# 4. ÇOKLU DEĞİŞKEN ANALİZİ
# ============================================================================

def coklu_degisken_analizi(
    df: pd.DataFrame,
    bagimli: str = None,
    bagimsizlar: List[str] = None,
    analizler: List[str] = None
) -> Dict:
    """
    Kapsamlı çoklu değişken analizi yapar.
    
    Analizler:
    - korelasyon: Pearson, Spearman, Kendall korelasyonları
    - pca: Principal Component Analysis
    - granger: Granger nedensellik testleri
    - var: Vector Autoregression
    - vecm: Vector Error Correction Model (kointegrasyon varsa)
    - regresyon: Çoklu regresyon
    
    Parameters:
    -----------
    df : pd.DataFrame
        Analiz edilecek veri
    bagimli : str, optional
        Bağımlı değişken (regresyon için)
    bagimsizlar : list, optional
        Bağımsız değişkenler
    analizler : list, optional
        Yapılacak analizler listesi (varsayılan: hepsi)
    
    Returns:
    --------
    dict
        Tüm analiz sonuçları
    """
    if analizler is None:
        analizler = ['korelasyon', 'pca', 'granger']
    
    sonuclar = {}
    df_temiz = df.select_dtypes(include=[np.number]).dropna()
    
    if len(df_temiz.columns) < 2:
        return {'hata': 'En az 2 sayısal sütun gerekli'}
    
    # 1. Korelasyon Analizi
    if 'korelasyon' in analizler:
        sonuclar['korelasyon'] = {
            'pearson': df_temiz.corr(method='pearson').round(4).to_dict(),
            'spearman': df_temiz.corr(method='spearman').round(4).to_dict(),
            'kendall': df_temiz.corr(method='kendall').round(4).to_dict()
        }
        
        # En güçlü ilişkiler
        pearson = df_temiz.corr(method='pearson')
        iliskiler = []
        for i in range(len(pearson.columns)):
            for j in range(i + 1, len(pearson.columns)):
                r = pearson.iloc[i, j]
                iliskiler.append({
                    'seri1': pearson.columns[i],
                    'seri2': pearson.columns[j],
                    'r': round(r, 4),
                    'r2': round(r**2, 4),
                    'guc': 'çok güçlü' if abs(r) >= 0.8 else 'güçlü' if abs(r) >= 0.6 else 'orta' if abs(r) >= 0.4 else 'zayıf'
                })
        sonuclar['korelasyon']['en_guclu'] = sorted(iliskiler, key=lambda x: abs(x['r']), reverse=True)[:10]
    
    # 2. PCA Analizi
    if 'pca' in analizler:
        try:
            from sklearn.preprocessing import StandardScaler
            from sklearn.decomposition import PCA
            
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(df_temiz)
            
            n_components = min(len(df_temiz.columns), 5)
            pca = PCA(n_components=n_components)
            pca.fit(X_scaled)
            
            sonuclar['pca'] = {
                'aciklanan_varyans': pca.explained_variance_ratio_.round(4).tolist(),
                'kumulatif_varyans': np.cumsum(pca.explained_variance_ratio_).round(4).tolist(),
                'bilesenlerin_yuklemeleri': {
                    f'PC{i+1}': dict(zip(df_temiz.columns, pca.components_[i].round(4)))
                    for i in range(n_components)
                }
            }
            
            # Kaç bileşen %95 açıklıyor?
            kumulatif = np.cumsum(pca.explained_variance_ratio_)
            sonuclar['pca']['%95_icin_bilesen'] = int(np.argmax(kumulatif >= 0.95) + 1) if any(kumulatif >= 0.95) else n_components
            
        except ImportError:
            sonuclar['pca'] = {'hata': 'sklearn paketi yüklü değil'}
    
    # 3. Granger Nedensellik
    if 'granger' in analizler:
        try:
            from statsmodels.tsa.stattools import grangercausalitytests
            
            granger_sonuc = {}
            max_lag = min(12, len(df_temiz) // 5)
            
            for col1 in df_temiz.columns:
                for col2 in df_temiz.columns:
                    if col1 != col2:
                        try:
                            test = grangercausalitytests(
                                df_temiz[[col1, col2]], 
                                maxlag=max_lag, 
                                verbose=False
                            )
                            
                            # En düşük p-değerli lag
                            min_p = min(test[lag][0]['ssr_ftest'][1] for lag in range(1, max_lag + 1))
                            best_lag = min(range(1, max_lag + 1), key=lambda x: test[x][0]['ssr_ftest'][1])
                            
                            granger_sonuc[f"{col2} → {col1}"] = {
                                'p_value': round(min_p, 4),
                                'best_lag': best_lag,
                                'nedensellik': 'VAR' if min_p < 0.05 else 'YOK',
                                'guven': '%99' if min_p < 0.01 else '%95' if min_p < 0.05 else '%90' if min_p < 0.10 else '-'
                            }
                        except Exception:
                            pass
            
            sonuclar['granger'] = granger_sonuc
            
        except ImportError:
            sonuclar['granger'] = {'hata': 'statsmodels paketi yüklü değil'}
    
    # 4. Çoklu Regresyon
    if 'regresyon' in analizler and bagimli and bagimsizlar:
        try:
            import statsmodels.api as sm
            
            y = df_temiz[bagimli]
            X = df_temiz[bagimsizlar]
            X = sm.add_constant(X)
            
            model = sm.OLS(y, X).fit()
            
            sonuclar['regresyon'] = {
                'r2': round(model.rsquared, 4),
                'r2_adj': round(model.rsquared_adj, 4),
                'f_stat': round(model.fvalue, 2),
                'f_pvalue': round(model.f_pvalue, 4),
                'durbin_watson': round(sm.stats.stattools.durbin_watson(model.resid), 2),
                'katsayilar': {k: round(v, 4) for k, v in model.params.items()},
                'p_values': {k: round(v, 4) for k, v in model.pvalues.items()},
                'std_errors': {k: round(v, 4) for k, v in model.bse.items()},
                'guven_araliklari': {
                    k: (round(model.conf_int().loc[k, 0], 4), round(model.conf_int().loc[k, 1], 4))
                    for k in model.params.index
                }
            }
            
        except ImportError:
            sonuclar['regresyon'] = {'hata': 'statsmodels paketi yüklü değil'}
        except Exception as e:
            sonuclar['regresyon'] = {'hata': str(e)}
    
    return sonuclar


def format_coklu_analiz(sonuclar: Dict) -> str:
    """Çoklu değişken analizi sonuçlarını formatlar."""
    metin = f"""
📊 ÇOKLU DEĞİŞKEN ANALİZİ
{'═' * 50}
"""
    
    if 'korelasyon' in sonuclar:
        metin += f"""
📈 KORELASYON ANALİZİ
{'─' * 40}
En güçlü ilişkiler (Pearson):
"""
        for iliski in sonuclar['korelasyon'].get('en_guclu', [])[:5]:
            yön = "+" if iliski['r'] > 0 else ""
            metin += f"  • {iliski['seri1']} ↔ {iliski['seri2']}: r={yön}{iliski['r']} ({iliski['guc']})\n"
    
    if 'pca' in sonuclar and 'hata' not in sonuclar['pca']:
        metin += f"""
🔬 PCA (Temel Bileşenler)
{'─' * 40}
• %95 varyans için gereken bileşen: {sonuclar['pca']['%95_icin_bilesen']}
• Açıklanan varyans oranları:
"""
        for i, var in enumerate(sonuclar['pca']['aciklanan_varyans']):
            bar = "█" * int(var * 30)
            metin += f"  PC{i+1}: {var:.1%} {bar}\n"
    
    if 'granger' in sonuclar and 'hata' not in sonuclar['granger']:
        nedensellik_var = [k for k, v in sonuclar['granger'].items() if v.get('nedensellik') == 'VAR']
        metin += f"""
🔄 GRANGER NEDENSELLİK
{'─' * 40}
• Tespit edilen nedensellik sayısı: {len(nedensellik_var)}
"""
        for iliski in nedensellik_var[:10]:
            data = sonuclar['granger'][iliski]
            metin += f"  ✓ {iliski} (p={data['p_value']}, lag={data['best_lag']}, {data['guven']})\n"
    
    if 'regresyon' in sonuclar and 'hata' not in sonuclar['regresyon']:
        reg = sonuclar['regresyon']
        metin += f"""
📉 ÇOKLU REGRESYON
{'─' * 40}
• R²: {reg['r2']} (Düzeltilmiş: {reg['r2_adj']})
• F-istatistiği: {reg['f_stat']} (p={reg['f_pvalue']})
• Durbin-Watson: {reg['durbin_watson']}

Katsayılar:
"""
        for var, coef in reg['katsayilar'].items():
            p = reg['p_values'][var]
            sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
            metin += f"  • {var}: {coef}{sig} (p={p})\n"
    
    return metin


# ============================================================================
# 5. DASHBOARD MODU
# ============================================================================

def dashboard_olustur(
    df: pd.DataFrame,
    baslik: str = "EVDS Dashboard",
    dosya_adi: str = "dashboard.html",
    analizler: List[str] = None
) -> str:
    """
    Kapsamlı interaktif HTML dashboard oluşturur.
    
    İçerik:
    - Veri kalitesi özeti
    - Tanımlayıcı istatistikler
    - Trend grafikleri
    - Korelasyon matrisi
    - Anomali tespiti
    - Mevsimsellik analizi
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dashboard verileri
    baslik : str
        Dashboard başlığı
    dosya_adi : str
        Çıktı dosya adı
    analizler : list, optional
        Dahil edilecek analizler
    
    Returns:
    --------
    str
        HTML dosya yolu
    """
    import json
    
    if analizler is None:
        analizler = ['ozet', 'trend', 'korelasyon', 'anomali', 'kalite']
    
    # Veri hazırlığı
    df_numeric = df.select_dtypes(include=[np.number])
    
    # Tanımlayıcı istatistikler
    stats_data = []
    for col in df_numeric.columns:
        seri = df_numeric[col].dropna()
        if len(seri) > 0:
            stats_data.append({
                'Seri': col,
                'Gözlem': len(seri),
                'Ortalama': round(seri.mean(), 2),
                'Std': round(seri.std(), 2),
                'Min': round(seri.min(), 2),
                'Max': round(seri.max(), 2),
                'Son': round(seri.iloc[-1], 2)
            })
    
    # Zaman serisi verileri
    if isinstance(df.index, pd.DatetimeIndex):
        tarihler = df.index.strftime('%Y-%m-%d').tolist()
    else:
        tarihler = list(range(len(df)))
    
    series_data = []
    for i, col in enumerate(df_numeric.columns):
        series_data.append({
            'name': col,
            'data': df_numeric[col].fillna(0).round(4).tolist(),
            'color': PALETTE[i % len(PALETTE)]
        })
    
    # Korelasyon matrisi
    corr = df_numeric.corr().round(3)
    corr_data = {
        'labels': corr.columns.tolist(),
        'values': corr.values.tolist()
    }
    
    # Anomali özeti
    anomali_sonuc = anomali_tespiti(df_numeric, metot='iqr')
    anomali_ozet = []
    for col, data in anomali_sonuc.items():
        if not data.get('anomali_yok') and 'hata' not in data:
            anomali_ozet.append({
                'seri': col,
                'sayi': data['anomali_sayisi'],
                'oran': data['anomali_oran']
            })
    
    # Kalite puanı
    kalite = veri_kalitesi_kontrolu(df)
    
    # Güvenlik: Kullanıcı verilerini escape et
    baslik_esc = html.escape(baslik)

    html_content = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{baslik_esc}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f6fa;
            color: {COLORS['text']};
            padding: 20px;
        }}
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, {COLORS['primary']}, {COLORS['secondary']});
            color: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
        }}
        .header h1 {{ font-size: 28px; margin-bottom: 5px; }}
        .header p {{ opacity: 0.9; font-size: 14px; }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .card-title {{
            font-size: 14px;
            color: {COLORS['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 15px;
        }}
        .metric {{
            font-size: 36px;
            font-weight: 700;
            color: {COLORS['primary']};
        }}
        .metric-sub {{ font-size: 14px; color: {COLORS['text_secondary']}; }}
        
        .chart-card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            margin-bottom: 20px;
        }}
        .chart {{ height: 400px; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid {COLORS['grid']};
        }}
        th {{
            background: {COLORS['grid']};
            color: {COLORS['secondary']};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 11px;
        }}
        th:first-child, td:first-child {{ text-align: left; }}
        tr:hover {{ background: #fafbfc; }}
        
        .quality-bar {{
            height: 8px;
            background: {COLORS['grid']};
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .quality-fill {{
            height: 100%;
            border-radius: 4px;
            transition: width 0.5s ease;
        }}
        .quality-good {{ background: {COLORS['success']}; }}
        .quality-medium {{ background: {COLORS['warning']}; }}
        .quality-bad {{ background: {COLORS['danger']}; }}
        
        .anomaly-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }}
        .anomaly-high {{ background: #ffeaea; color: {COLORS['danger']}; }}
        .anomaly-low {{ background: #fff8e6; color: {COLORS['warning']}; }}
        
        .footer {{
            text-align: center;
            color: {COLORS['text_secondary']};
            font-size: 12px;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>{baslik_esc}</h1>
            <p>Oluşturulma: {datetime.now().strftime('%d.%m.%Y %H:%M')} | Kaynak: TCMB EVDS</p>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="card-title">Veri Kalitesi</div>
                <div class="metric">{kalite['puan']}/100</div>
                <div class="metric-sub">{kalite['degerlendirme']}</div>
                <div class="quality-bar">
                    <div class="quality-fill {'quality-good' if kalite['puan'] >= 75 else 'quality-medium' if kalite['puan'] >= 50 else 'quality-bad'}" 
                         style="width: {kalite['puan']}%"></div>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Toplam Gözlem</div>
                <div class="metric">{kalite['genel']['satir_sayisi']:,}</div>
                <div class="metric-sub">{kalite['genel']['sutun_sayisi']} seri</div>
            </div>
            <div class="card">
                <div class="card-title">Eksik Veri</div>
                <div class="metric">{kalite['genel']['eksik_oran']}%</div>
                <div class="metric-sub">{kalite['genel']['eksik_toplam']:,} hücre</div>
            </div>
            <div class="card">
                <div class="card-title">Anomali Sayısı</div>
                <div class="metric">{sum(a['sayi'] for a in anomali_ozet)}</div>
                <div class="metric-sub">{len(anomali_ozet)} seride tespit</div>
            </div>
        </div>
        
        <div class="chart-card">
            <div class="card-title">Zaman Serisi Trendi</div>
            <div id="trendChart" class="chart"></div>
        </div>
        
        <div class="grid" style="grid-template-columns: 1fr 1fr;">
            <div class="chart-card">
                <div class="card-title">Korelasyon Matrisi</div>
                <div id="corrChart" class="chart"></div>
            </div>
            <div class="card">
                <div class="card-title">Özet İstatistikler</div>
                <table>
                    <thead>
                        <tr>
                            <th>Seri</th>
                            <th>N</th>
                            <th>Ort.</th>
                            <th>Std</th>
                            <th>Min</th>
                            <th>Max</th>
                            <th>Son</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(f"<tr><td>{html.escape(str(s['Seri']))}</td><td>{s['Gözlem']}</td><td>{s['Ortalama']}</td><td>{s['Std']}</td><td>{s['Min']}</td><td>{s['Max']}</td><td>{s['Son']}</td></tr>" for s in stats_data)}
                    </tbody>
                </table>
            </div>
        </div>
        
        {'<div class="card"><div class="card-title">Tespit Edilen Anomaliler</div><table><thead><tr><th>Seri</th><th>Anomali Sayısı</th><th>Oran</th></tr></thead><tbody>' + ''.join(f"<tr><td>{html.escape(str(a['seri']))}</td><td>{a['sayi']}</td><td><span class=\\'anomaly-badge {'anomaly-high' if a['oran'] > 5 else 'anomaly-low'}\\'>{a['oran']}%</span></td></tr>" for a in anomali_ozet) + '</tbody></table></div>' if anomali_ozet else ''}
        
        <div class="footer">
            Dashboard by EVDS Analiz Skill | Veri: TCMB EVDS
        </div>
    </div>
    
    <script>
        // Trend Chart
        var trendData = {json.dumps(series_data).replace('<', '\\u003c')};
        var tarihler = {json.dumps(tarihler).replace('<', '\\u003c')};
        
        var trendTraces = trendData.map(function(s) {{
            return {{
                x: tarihler,
                y: s.data,
                name: s.name,
                type: 'scatter',
                mode: 'lines',
                line: {{ color: s.color, width: 2 }}
            }};
        }});
        
        Plotly.newPlot('trendChart', trendTraces, {{
            margin: {{ l: 50, r: 30, t: 20, b: 40 }},
            xaxis: {{ gridcolor: '{COLORS['grid']}' }},
            yaxis: {{ gridcolor: '{COLORS['grid']}' }},
            hovermode: 'x unified',
            legend: {{ orientation: 'h', y: 1.1 }}
        }}, {{ responsive: true, displayModeBar: false }});
        
        // Correlation Chart
        var corrData = {json.dumps(corr_data).replace('<', '\\u003c')};
        
        Plotly.newPlot('corrChart', [{{
            z: corrData.values,
            x: corrData.labels,
            y: corrData.labels,
            type: 'heatmap',
            colorscale: [
                [0, '#E74C3C'],
                [0.5, '#ECF0F1'],
                [1, '#3498DB']
            ],
            zmin: -1,
            zmax: 1,
            showscale: true,
            colorbar: {{ title: 'r' }}
        }}], {{
            margin: {{ l: 100, r: 50, t: 20, b: 100 }},
            xaxis: {{ tickangle: -45 }}
        }}, {{ responsive: true, displayModeBar: false }});
    </script>
</body>
</html>"""
    
    dosya_adi = os.path.basename(dosya_adi)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return dosya_adi


# ============================================================================
# YARDIMCI FONKSİYONLAR
# ============================================================================

def durgunluk_testi(seri: pd.Series, test: str = 'adf') -> Dict:
    """
    Durağanlık testi yapar (ADF, KPSS, PP).
    
    Parameters:
    -----------
    seri : pd.Series
        Test edilecek seri
    test : str
        'adf', 'kpss', veya 'pp'
    
    Returns:
    --------
    dict
        Test sonuçları
    """
    seri = seri.dropna()
    
    try:
        if test == 'adf':
            from statsmodels.tsa.stattools import adfuller
            sonuc = adfuller(seri, autolag='AIC')
            return {
                'test': 'ADF',
                'istatistik': round(sonuc[0], 4),
                'p_value': round(sonuc[1], 4),
                'lag': sonuc[2],
                'gozlem': sonuc[3],
                'kritik_degerler': {k: round(v, 4) for k, v in sonuc[4].items()},
                'duragan': sonuc[1] < 0.05,
                'yorum': "Durağan (H0 reddedildi)" if sonuc[1] < 0.05 else "Durağan DEĞİL (H0 reddedilemedi)"
            }
        
        elif test == 'kpss':
            from statsmodels.tsa.stattools import kpss
            sonuc = kpss(seri, regression='c', nlags='auto')
            return {
                'test': 'KPSS',
                'istatistik': round(sonuc[0], 4),
                'p_value': round(sonuc[1], 4),
                'lag': sonuc[2],
                'kritik_degerler': {k: round(v, 4) for k, v in sonuc[3].items()},
                'duragan': sonuc[1] > 0.05,
                'yorum': "Durağan (H0 reddedilemedi)" if sonuc[1] > 0.05 else "Durağan DEĞİL (H0 reddedildi)"
            }
        
        elif test == 'pp':
            from statsmodels.tsa.stattools import adfuller
            # PP test için Phillips-Perron, statsmodels'de direkt yok, ADF approx kullanılabilir
            sonuc = adfuller(seri, autolag='AIC', regression='c')
            return {
                'test': 'PP (ADF approx)',
                'istatistik': round(sonuc[0], 4),
                'p_value': round(sonuc[1], 4),
                'duragan': sonuc[1] < 0.05
            }
        
    except ImportError:
        return {'hata': 'statsmodels paketi yüklü değil'}
    except Exception as e:
        return {'hata': str(e)}


def frekans_donusumu(
    df: pd.DataFrame,
    hedef_frekans: str,
    metot: str = 'mean'
) -> pd.DataFrame:
    """
    Frekans dönüşümü yapar (örn: günlük → aylık).
    
    Parameters:
    -----------
    df : pd.DataFrame
        Tarih indexli DataFrame
    hedef_frekans : str
        Pandas frekans kodu ('MS': ay başı, 'W': hafta, 'Q': çeyrek, 'Y': yıl)
    metot : str
        'mean', 'sum', 'last', 'first', 'min', 'max'
    
    Returns:
    --------
    pd.DataFrame
        Dönüştürülmüş DataFrame
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("DataFrame'in tarih indexi olmalı")
    
    if metot == 'mean':
        return df.resample(hedef_frekans).mean()
    elif metot == 'sum':
        return df.resample(hedef_frekans).sum()
    elif metot == 'last':
        return df.resample(hedef_frekans).last()
    elif metot == 'first':
        return df.resample(hedef_frekans).first()
    elif metot == 'min':
        return df.resample(hedef_frekans).min()
    elif metot == 'max':
        return df.resample(hedef_frekans).max()
    else:
        raise ValueError(f"Bilinmeyen metot: {metot}")


if __name__ == "__main__":
    print("EVDS Gelişmiş Analiz Modülü yüklendi.")
    print("\nKullanılabilir fonksiyonlar:")
    print("  - veri_kalitesi_kontrolu(df)")
    print("  - anomali_tespiti(df, metot='iqr')")
    print("  - mevsimsellik_temizle(seri, periyot=12)")
    print("  - coklu_degisken_analizi(df)")
    print("  - dashboard_olustur(df, baslik='...')")
    print("  - durgunluk_testi(seri, test='adf')")
    print("  - frekans_donusumu(df, hedef_frekans='MS')")

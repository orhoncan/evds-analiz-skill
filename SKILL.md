---
name: evds-analiz
description: TCMB EVDS (Elektronik Veri Dağıtım Sistemi) API'si ile Türkiye ekonomik verilerine erişim, analiz ve görselleştirme. Kullanıcı API anahtarı girerek TCMB verilerini çeker. Akıllı seri keşfi, hazır analiz şablonları (enflasyon, döviz, faiz, cari denge, GSYH, işsizlik, para arzı), tanımlayıcı istatistikler, regresyon (OLS, ARIMA, VAR), korelasyon analizi ve interaktif Plotly grafikleri sunar. Türkçe arayüz. Kullanıcı "EVDS", "TCMB verisi", "Merkez Bankası verisi", "enflasyon verisi", "döviz kuru verisi", "ekonomik veri analizi" dediğinde tetiklenir.
---

# EVDS Analiz Skill

## GENEL BAKIŞ

Bu skill, TCMB EVDS API'si üzerinden Türkiye ekonomik verilerine erişim sağlar. Kullanıcı seri kodlarını bilmese bile akıllı keşif ile ihtiyacı olan verilere ulaşır.

## TEMEL İLKELER

1. **API Key her seferinde kullanıcıdan alınır** - Güvenlik için saklanmaz
2. **Türkçe arayüz** - Tüm çıktılar Türkçe
3. **Kullanıcı yönlendirmeli** - Analiz derinliği kullanıcı tercihine göre
4. **Tarih aralığı kullanıcıdan alınır** - Varsayılan yok, her zaman sor

## API ERİŞİM FORMATI (KRİTİK - 5 Nisan 2024 Güncellemesi)

**ÖNEMLİ:** EVDS API'si 5 Nisan 2024'ten itibaren yeni format kullanıyor.

### Doğru Format (URL Path + Header Key)
```python
import requests

API_KEY = "kullanici_api_key"
headers = {'key': API_KEY}

# URL formatı: parametreler & ile ayrılmış, URL path içinde
url = "https://evds3.tcmb.gov.tr/igmevdsms-dis/series=TP.DK.USD.A&startDate=01-01-2024&endDate=31-12-2024&type=json"

response = requests.get(url, headers=headers, timeout=60)
data = response.json()
```

### Yanlış Format (Artık Çalışmıyor)
```python
# ❌ Query string ile parametre geçme ÇALIŞMAZ
url = "https://evds3.tcmb.gov.tr/igmevdsms-dis"
params = {'series': 'TP.DK.USD.A', 'startDate': '01-01-2024', ...}
requests.get(url, params=params)  # 404 verir!

# ❌ URL'de key parametre olarak ÇALIŞMAZ
url = "...&key=API_KEY"  # 403/404 verir!
```

### Çoklu Seri Çekme
```python
# Seriler tire (-) ile ayrılır
url = "https://evds3.tcmb.gov.tr/igmevdsms-dis/series=TP.DK.USD.A-TP.DK.EUR.A&startDate=01-01-2024&endDate=31-12-2024&type=json"
```

### Metadata Endpoint'leri (Seri Keşfi İçin)
```python
# Kategorileri listele
url = "https://evds3.tcmb.gov.tr/igmevdsms-dis/categories/type=json"

# Veri gruplarını listele
url = "https://evds3.tcmb.gov.tr/igmevdsms-dis/datagroups/mode=0&type=json"

# Bir gruptaki serileri listele
url = "https://evds3.tcmb.gov.tr/igmevdsms-dis/serieList/type=json&code=bie_tukfiy4"
```

## RENK PALETI (orhon-viz uyumlu)

```python
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
    'text_secondary': '#95A5A6'
}

PALETTE = ['#2C3E50', '#E74C3C', '#3498DB', '#F39C12', '#16A085', '#9B59B6', '#27AE60']
```

## SIK KULLANILAN SERİLER VE TARİH FORMATLARI

### TÜFE (Enflasyon) - Aylık
| Seri Kodu | Açıklama | Tarih Formatı | Birim |
|-----------|----------|---------------|-------|
| `TP.FG.J0` | TÜFE Genel Endeks (2003=100) | `2024-1` (yıl-ay) | Endeks |
| `TP.FG.J01` | Gıda ve Alkolsüz İçecekler | `2024-1` | Endeks |

**Not:** TÜFE verisinden yıllık değişim hesaplamak için 12 ay önceki değerle karşılaştır:
```python
df['yillik_degisim'] = df['endeks'].pct_change(12) * 100
```

### Döviz Kurları - Günlük
| Seri Kodu | Açıklama | Tarih Formatı | Birim |
|-----------|----------|---------------|-------|
| `TP.DK.USD.A` | USD Döviz Alış | `01-01-2024` (gg-aa-yyyy) | TL |
| `TP.DK.EUR.A` | EUR Döviz Alış | `01-01-2024` | TL |
| `TP.DK.GBP.A` | GBP Döviz Alış | `01-01-2024` | TL |

### YP Mevduat - Haftalık
| Seri Kodu | Açıklama | Tarih Formatı | Birim |
|-----------|----------|---------------|-------|
| `TP.YPMEVD.M01` | Toplam YP Mevduatlar | `07-01-2024` (gg-aa-yyyy) | Bin TL |
| `TP.YPMEVD.M03` | Bankalardaki Toplam YP Mevduat | `07-01-2024` | Bin TL |
| `TP.YPMEVD.M05` | Yurtiçi Yerleşikler YP Mevduat | `07-01-2024` | Bin TL |
| `TP.HPBITABLO4.1` | Toplam YP Mevduat (Milyon USD) | `07-01-2024` | Milyon USD |

### DTH (Döviz Tevdiat Hesapları) - Haftalık
| Seri Kodu | Açıklama | Tarih Formatı | Birim |
|-----------|----------|---------------|-------|
| `TP.TLDTHVADE.KB6` | TL Mevduat Toplam | `07-01-2024` | Bin TL |
| `TP.TLDTHVADE.KB12` | DTH Toplam | `07-01-2024` | Bin TL |
| `TP.TLDTHVADE.KB18` | Toplam Mevduat | `07-01-2024` | Bin TL |

### KKM (Kur Korumalı Mevduat) - Aylık
| Seri Kodu | Açıklama | Birim |
|-----------|----------|-------|
| `TP.KKM.K1` | DDKKM Toplam | Milyar USD Karşılığı |
| `TP.KKM.K4` | TL KKM Toplam | Milyar TL |

## TARİH FORMATI PARSE ETMENİN DOĞRU YOLU

```python
import pandas as pd
import re

def parse_evds_tarih(df):
    """EVDS tarih formatını otomatik algıla ve parse et."""
    tarih_serisi = df['Tarih'].astype(str).str.strip()
    ornek = tarih_serisi.iloc[0]

    if re.match(r'^\d{4}-\d{1,2}$', ornek):
        # Aylık: 2024-1 / 2024-12
        parsed = pd.to_datetime(tarih_serisi, format='%Y-%m')
    elif re.match(r'^\d{2}-\d{2}-\d{4}$', ornek):
        # Günlük/Haftalık: 07-01-2024
        parsed = pd.to_datetime(tarih_serisi, format='%d-%m-%Y')
    elif re.match(r'^\d{4}-Q[1-4]$', ornek):
        # Çeyreklik: 2024-Q1 -> 2024-01-01
        ceyrek_map = {'Q1': '01', 'Q2': '04', 'Q3': '07', 'Q4': '10'}
        aylik = tarih_serisi.str.replace(
            r'^(\d{4})-(Q[1-4])$',
            lambda m: f"{m.group(1)}-{ceyrek_map[m.group(2)]}",
            regex=True
        )
        parsed = pd.to_datetime(aylik, format='%Y-%m')
    elif re.match(r'^\d{4}$', ornek):
        # Yıllık: 2024
        parsed = pd.to_datetime(tarih_serisi, format='%Y')
    else:
        parsed = pd.to_datetime(tarih_serisi, errors='coerce', dayfirst=True)
        if parsed.isna().all():
            parsed = pd.to_datetime(tarih_serisi, errors='coerce', format='mixed')

    df['Tarih'] = parsed
    
    return df.set_index('Tarih').sort_index()
```

## FREKANS DÖNÜŞÜMÜ

Farklı frekanstaki verileri karşılaştırmak için aynı frekansa dönüştür:

```python
# Haftalık → Aylık (ortalama)
aylik = haftalik_df.resample('MS').mean()  # MS = Month Start

# Günlük → Aylık (ortalama)
aylik = gunluk_df.resample('MS').mean()

# Aylık veride ay başı indeksi için
aylik_df.index = aylik_df.index.to_period('M').to_timestamp()
```

## VERİ GRUPLARI (Seri Keşfi İçin)

| Grup Kodu | Açıklama | Frekans |
|-----------|----------|---------|
| `bie_tukfiy4` | TÜFE (2003=100) | Aylık |
| `bie_dkdovytl` | Döviz Kurları | Günlük |
| `bie_ypmevd` | YP Mevduatlar (Arşiv) | Haftalık |
| `bie_hpbitablo4` | YP Mevduat (Milyon USD) | Haftalık |
| `bie_TLDTHVADE` | TL ve DTH Vadelerine Göre | Haftalık |
| `bie_kkm` | Kur Korumalı Mevduat | Aylık |
| `bie_polfaiz` | TCMB Politika Faizi | Günlük |
| `bie_mevfaiz` | Mevduat Faiz Oranları | Haftalık |

## İŞ AKIŞI

### Adım 1: API Anahtarı Al
```
"EVDS API anahtarınızı girin. 
(Anahtarınız yoksa: evds3.tcmb.gov.tr → Üye Ol → Profil → API Anahtarı)"
```

### Adım 2: Kullanıcı İhtiyacını Anla
- Kullanıcı seri kodu biliyorsa → Doğrudan çek
- Bilmiyorsa → Akıllı keşif başlat (yukarıdaki tablolara bak)

### Adım 3: Tarih Aralığı Al
```
"Hangi tarih aralığını çekelim? (Örn: 01-01-2020 ile 31-12-2024 arası)"
```

### Adım 4: Veri Çek ve Otomatik Analiz
```python
def evds_cek(seri, baslangic, bitis, api_key):
    headers = {'key': api_key}
    url = f"https://evds3.tcmb.gov.tr/igmevdsms-dis/series={seri}&startDate={baslangic}&endDate={bitis}&type=json"
    r = requests.get(url, headers=headers, timeout=60)
    
    if r.status_code != 200:
        raise Exception(f"API Hatası: {r.status_code}")
    
    return r.json()
```

### Adım 5: Görselleştir
- Plotly ile interaktif HTML oluştur
- Çoklu seri varsa otomatik korelasyon matrisi sun

### Adım 6: İleri Analiz Öner
```
"Başka analiz ister misiniz?
• Regresyon analizi (OLS)
• Zaman serisi modeli (ARIMA)
• VAR modeli (çoklu seri için)
• Mevsimsellik analizi
• Granger nedensellik testi"
```

### Adım 7: CSV İndir Seçeneği Sun
Her analizden sonra ham veriyi CSV olarak sunma seçeneği ver.

## HAZIR ANALİZ ŞABLONLARI

| Şablon | Seriler | Varsayılan Analiz |
|--------|---------|-------------------|
| Enflasyon | `TP.FG.J0` | Yıllık değişim hesapla, trend |
| Döviz Kuru | `TP.DK.USD.A`, `TP.DK.EUR.A` | Günlük/aylık trend, volatilite |
| Faiz-Enflasyon | Politika faizi, TÜFE | Korelasyon, reel faiz hesabı |
| Dolarizasyon | `TP.FG.J0`, `TP.YPMEVD.M01` | Korelasyon, yıllık karşılaştırma |
| KKM Analizi | `TP.KKM.K1`, `TP.KKM.K4` | Trend, toplam hacim |

## ÇIKTI FORMATLARI

### 1. Tanımlayıcı İstatistikler (Her zaman)
```
📊 TÜFE (Yıllık % Değişim) - Özet
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dönem: Ocak 2022 - Aralık 2024
Gözlem: 36
Ortalama: 61.8%
Std. Sapma: 13.2%
Min: 38.2% (Haziran 2023)
Max: 85.5% (Ekim 2022)
Son Değer: 44.4%
Trend: ↘ Düşüş eğiliminde
```

### 2. İnteraktif HTML Grafik
- Plotly ile oluştur
- Hover ile değer göster
- Zoom/pan destekle
- orhon-viz renk paleti

### 3. CSV Dosyası (İsteğe bağlı)
Ham veri + hesaplanan değişkenler

## HATA YÖNETİMİ

| Hata | Sebep | Çözüm |
|------|-------|-------|
| 403 Forbidden | API key header'da değil | `headers = {'key': API_KEY}` kullan |
| 404 Not Found | URL formatı yanlış | URL path formatı kullan, query string değil |
| Boş veri | Tarih aralığı uygun değil | Seri aktif mi, tarih formatı doğru mu kontrol et |
| Tarih parse hatası | Farklı frekans formatları | `parse_evds_tarih()` fonksiyonunu kullan |

## SCRIPTS KULLANIMI

`scripts/` klasörü altındaki modülleri kullanarak analiz yapabilirsiniz:

### 1. EVDS Client (`scripts/evds_client.py`)
```python
from scripts.evds_client import EVDSClient

client = EVDSClient(api_key="YOUR_KEY")

# Veri çek
df = client.veri_cek('TP.DK.USD.A', '01-01-2024', '31-12-2024')

# Kategori listesi
kategoriler = client.kategorileri_getir()

# Veri grubu serileri
seriler = client.grup_serileri('bie_tukfiy4')

# Tanımlayıcı istatistikler
from scripts.evds_client import tanimlayici_istatistikler, istatistik_ozeti_formatla
ist = tanimlayici_istatistikler(df)
print(istatistik_ozeti_formatla(ist))
```

### 2. Analiz (`scripts/analiz.py`)
```python
from scripts.analiz import (
    korelasyon_analizi,
    ols_regresyon,
    arima_analizi,
    var_analizi,
    mevsimsellik_analizi,
    format_ols,
    format_arima,
    format_korelasyon
)

# Korelasyon
corr = korelasyon_analizi(df)
print(format_korelasyon(corr))

# OLS Regresyon
ols = ols_regresyon(y=df['USD'], X=df[['EUR', 'GBP']])
print(format_ols(ols, 'USD'))

# ARIMA
arima = arima_analizi(df['USD'], tahmin_donemi=12)
print(format_arima(arima, 'USD'))

# VAR (çoklu seri)
var = var_analizi(df, degiskenler=['USD', 'EUR', 'GBP'])

# Mevsimsellik
mevsim = mevsimsellik_analizi(df['TÜFE'], periyot=12)
```

### 3. Grafik (`scripts/grafik.py`)
```python
from scripts.grafik import (
    cizgi_grafik,
    coklu_eksen_grafik,
    korelasyon_matrisi_grafik,
    bar_grafik,
    mevsimsellik_grafik,
    tahmin_grafik
)

# Çizgi grafik
cizgi_grafik(df, 'USD/TL Kur', 'TL', 'usd_grafik.html')

# Çoklu eksen (farklı birimler)
coklu_eksen_grafik(df, ['USD', 'EUR'], 'Döviz Kurları', 'doviz.html')

# Korelasyon matrisi
korelasyon_matrisi_grafik(df, 'Korelasyon Matrisi', 'korelasyon.html')

# Bar grafik
bar_grafik(df, 'Aylık Ortalamalar', 'TL', 'bar.html')

# Mevsimsellik grafik
mevsimsellik_grafik(df['TÜFE'], 'TÜFE Mevsimsellik', 'mevsim.html')

# Tahmin grafik (ARIMA sonrası)
tahmin_grafik(df['USD'], tahminler, 'Tahmin', 'tahmin.html')
```

### 4. Gelişmiş Analiz (`scripts/gelismis_analiz.py`)
```python
from scripts.gelismis_analiz import (
    veri_kalitesi_kontrolu,
    anomali_tespiti,
    mevsimsellik_temizle,
    coklu_degisken_analizi,
    dashboard_olustur,
    durgunluk_testi,
    frekans_donusumu,
    format_veri_kalitesi,
    format_anomali,
    format_mevsimsellik,
    format_coklu_analiz
)

# Veri kalitesi kontrolü (100 üzerinden puan)
kalite = veri_kalitesi_kontrolu(df)
print(format_veri_kalitesi(kalite))

# Outlier tespiti (IQR, Z-score, MAD, Isolation Forest)
outliers = anomali_tespiti(df['USD'])
print(format_anomali(outliers))

# Mevsimsellik temizleme (STL, MA, X11)
adjusted = mevsimsellik_temizle(df, 'STL')
print(format_mevsimsellik(adjusted))

# Çoklu değişken analizi (PCA, Granger, tüm korelasyonlar)
coklu = coklu_degisken_analizi(df)
print(format_coklu_analiz(coklu))

# Durağanlık testleri (ADF, KPSS)
adf = durgunluk_testi(df['USD'], test='adf')
kpss = durgunluk_testi(df['USD'], test='kpss')

# Frekans dönüşümü
aylik = frekans_donusumu(haftalik_df, 'aylik')
ceyreklik = frekans_donusumu(aylik_df, 'ceyreklik')

# Dashboard (tek komutla kapsamlı rapor)
dashboard_olustur(
    seriler=[df1, df2, df3],
    baslik='Ekonomik Analiz Dashboard',
    dosya_adi='dashboard.html'
)
```

## KRİTİK NOKTALAR

1. **API key MUTLAKA header'da gönderilmeli** - `headers = {'key': API_KEY}`
2. **URL formatı**: `series=X&startDate=gg-aa-yyyy&endDate=gg-aa-yyyy&type=json`
3. **Tarih formatı girdide**: `gg-aa-yyyy` (örn: 01-01-2024)
4. **Tarih formatı çıktıda**: Seriye göre değişir (aylık: `2024-1`, günlük: `01-01-2024`)
5. **Çoklu seri**: Tire (-) ile ayır (örn: `TP.DK.USD.A-TP.DK.EUR.A`)
6. **Birim dönüşümü**: YP Mevduat Bin TL cinsinden gelir, Milyar TL için `/1e9` yap
7. **Frekans eşleştirme**: Farklı frekanstaki verileri `.resample('MS').mean()` ile aylığa çevir

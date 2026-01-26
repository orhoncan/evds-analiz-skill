# EVDS Analiz

TCMB Elektronik Veri Dağıtım Sistemi (EVDS) API entegrasyonu ile Türkiye ekonomik verilerine erişim, analiz ve görselleştirme aracı.

## Özellikler

### Veri Erişimi
- TCMB EVDS API üzerinden doğrudan veri çekme
- Enflasyon (TÜFE), döviz kurları, faiz oranları, cari denge, GSYH, işsizlik ve para arzı verileri
- Çoklu seri desteği ile karşılaştırmalı analiz
- Otomatik tarih formatı algılama ve dönüştürme

### Akıllı Seri Keşfi
- Kullanıcı seri kodlarını bilmese bile anahtar kelime ile arama
- Hazır veri grubu katalogları
- Frekans bilgisi ve birim açıklamaları

### İstatistiksel Analiz
- **Tanımlayıcı istatistikler**: Ortalama, standart sapma, min/max, trend
- **Korelasyon analizi**: Çoklu seri ilişki matrisi
- **Regresyon modelleri**: OLS (En Küçük Kareler)
- **Zaman serisi modelleri**: ARIMA, VAR
- **Ek analizler**: Mevsimsellik, Granger nedensellik testi

### 🆕 Gelişmiş Analiz Özellikleri (v2.0)

| Özellik | Açıklama |
|---------|----------|
| 🔍 **Veri Kalitesi Kontrolü** | Eksik veri, outlier, süreklilik analizi + kalite puanı (100 üzerinden) |
| 🎯 **Anomali/Outlier Tespiti** | IQR, Z-score, MAD, Rolling, Isolation Forest yöntemleri |
| 📅 **Mevsimsellik Temizleme** | STL, MA, X11 ile seasonally adjusted seri üretimi |
| 📊 **Çoklu Değişken Analizi** | Korelasyon (Pearson/Spearman/Kendall), PCA, Granger nedensellik |
| 📋 **Dashboard Modu** | Tek komutla kapsamlı interaktif HTML dashboard |
| 📈 **Durağanlık Testleri** | ADF, KPSS testleri |
| 🔄 **Frekans Dönüşümü** | Günlük→Aylık, Haftalık→Çeyreklik vb. dönüşümler |

**Yeni modül:** `scripts/gelismis_analiz.py`

### Görselleştirme
- Plotly tabanlı interaktif HTML grafikler
- Hover ile değer gösterimi, zoom/pan desteği
- Çoklu seri karşılaştırma grafikleri

## Kullanım

### 1. API Anahtarı Edinme
EVDS API anahtarı almak için:
1. [evds2.tcmb.gov.tr](https://evds2.tcmb.gov.tr) adresine gidin
2. Üye olun veya giriş yapın
3. Profil sayfasından API anahtarınızı kopyalayın

### 2. Temel İş Akışı
```
Kullanıcı: "Enflasyon verisi çekmek istiyorum"
Claude: API anahtarı ister → Tarih aralığı sorar → Veri çeker → Analiz sunar
```

### 3. Hazır Analiz Şablonları

| Şablon | İçerik |
|--------|--------|
| **Enflasyon** | TÜFE endeksi, yıllık değişim hesaplama, trend analizi |
| **Döviz Kuru** | USD/EUR paritesi, günlük/aylık trend, volatilite |
| **Faiz-Enflasyon** | Politika faizi ile TÜFE korelasyonu, reel faiz |
| **Dolarizasyon** | YP mevduat oranı, enflasyon ilişkisi |
| **KKM Analizi** | Kur Korumalı Mevduat hacim ve trend |


### Sık Kullanılan Seri Kodları

| Kategori | Seri Kodu | Açıklama | Frekans |
|----------|-----------|----------|---------|
| Enflasyon | `TP.FG.J0` | TÜFE Genel Endeks | Aylık |
| Döviz | `TP.DK.USD.A` | USD Alış Kuru | Günlük |
| Döviz | `TP.DK.EUR.A` | EUR Alış Kuru | Günlük |
| Mevduat | `TP.YPMEVD.M01` | Toplam YP Mevduat | Haftalık |
| KKM | `TP.KKM.K1` | KKM Toplam (USD karşılığı) | Aylık |

### Tarih Formatları
- **API girdi**: `gg-aa-yyyy` (örn: `01-01-2024`)
- **Aylık veri çıktı**: `yyyy-a` (örn: `2024-1`)
- **Günlük/haftalık çıktı**: `gg-aa-yyyy` (örn: `07-01-2024`)

### Frekans Dönüşümü
Farklı frekanstaki verileri karşılaştırmak için:
```python
# Günlük/Haftalık → Aylık
aylik = df.resample('MS').mean()
```

## Çıktı Formatları

1. **Tanımlayıcı İstatistikler**: Her analiz için otomatik özet tablo
2. **İnteraktif HTML Grafik**: Plotly ile oluşturulmuş, indirilebilir
3. **CSV Dosyası**: Ham veri ve hesaplanan değişkenler (isteğe bağlı)


## Gereksinimler

- Python 3.8+
- requests
- pandas
- plotly
- statsmodels (istatistiksel analizler için)

## Lisans

MIT

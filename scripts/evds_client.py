#!/usr/bin/env python3
"""
EVDS API Client
TCMB Elektronik Veri Dağıtım Sistemi için Python wrapper.

ÖNEMLİ: 5 Nisan 2024 güncellemesi ile API formatı değişti.
- URL path formatı kullanılmalı (query string değil)
- API key header'da gönderilmeli
- EVDS3 base URL kullanılmalı: https://evds3.tcmb.gov.tr/igmevdsms-dis
"""

import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Union
import re

class EVDSClient:
    """TCMB EVDS API istemcisi."""
    
    BASE_URL = "https://evds3.tcmb.gov.tr/igmevdsms-dis"
    
    # Frekans kodları
    FREKANS = {
        'gunluk': 1, 'isgunu': 2, 'haftalik': 3, 'ayda2': 4,
        'aylik': 5, 'ceyreklik': 6, '6aylik': 7, 'yillik': 8
    }
    
    # Formül kodları
    FORMUL = {
        'duzey': 0, 'yuzde_degisim': 1, 'fark': 2,
        'yillik_yuzde': 3, 'yillik_fark': 4,
        'yilsonu_yuzde': 5, 'yilsonu_fark': 6,
        'hareketli_ort': 7, 'hareketli_toplam': 8
    }
    
    # Aggregation kodları
    AGGREGATION = {
        'ortalama': 'avg', 'min': 'min', 'max': 'max',
        'ilk': 'first', 'son': 'last', 'toplam': 'sum'
    }
    
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        """
        Parameters:
        -----------
        api_key : str
            EVDS API anahtarı
        base_url : str, optional
            EVDS servis URL'i. Varsayılan: EVDS3
        """
        self.api_key = api_key
        self.headers = {'key': api_key}
        self.base_url = (base_url or self.BASE_URL).rstrip('/')
        self._kategoriler = None
    
    def _extract_records(self, data: Union[dict, list], endpoint: str) -> List[dict]:
        """EVDS yanıtından kayıt listesini çıkarır (dict/list uyumluluğu)."""
        if isinstance(data, list):
            return data
        
        if isinstance(data, dict):
            if 'items' in data and isinstance(data['items'], list):
                return data['items']
            for key in ('data', 'results', 'result', 'value'):
                if key in data and isinstance(data[key], list):
                    return data[key]
        
        raise ValueError(f"{endpoint} endpoint'i beklenen veri formatını döndürmedi.")
    
    def _request_metadata(self, endpoint: str) -> Union[dict, list]:
        """Metadata endpoint'leri için istek gönderir (kategoriler, seri listesi vb.)."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                raise ValueError("API anahtarı geçersiz veya eksik. Lütfen kontrol edin.")
            raise e
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Bağlantı hatası: {e}")
    
    def kategorileri_getir(self) -> pd.DataFrame:
        """Tüm ana kategorileri listeler."""
        if self._kategoriler is None:
            data = self._request_metadata("categories/type=json")
            self._kategoriler = pd.DataFrame(self._extract_records(data, "categories"))
        return self._kategoriler
    
    def veri_gruplarini_getir(self, kategori_id: int = None) -> pd.DataFrame:
        """
        Veri gruplarını listeler.
        
        Parameters:
        -----------
        kategori_id : int, optional
            Kategori ID'si. None ise tüm grupları getirir.
        """
        if kategori_id:
            endpoint = f"datagroups/mode=2&code={kategori_id}&type=json"
        else:
            endpoint = "datagroups/mode=0&type=json"
        
        data = self._request_metadata(endpoint)
        return pd.DataFrame(self._extract_records(data, "datagroups"))
    
    def serileri_getir(self, veri_grubu_kodu: str) -> pd.DataFrame:
        """
        Bir veri grubundaki serileri listeler.
        
        Parameters:
        -----------
        veri_grubu_kodu : str
            Veri grubu kodu (örn: 'bie_dkdovytl')
        """
        endpoint = f"serieList/type=json&code={veri_grubu_kodu}"
        data = self._request_metadata(endpoint)
        return pd.DataFrame(self._extract_records(data, "serieList"))
    
    def veri_cek(
        self,
        seriler: Union[str, List[str]],
        baslangic: str,
        bitis: str,
        frekans: Optional[Union[int, str]] = None,
        formul: Optional[Union[int, str, List]] = None,
        aggregation: Optional[Union[str, List[str]]] = None
    ) -> pd.DataFrame:
        """
        EVDS'den veri çeker.
        
        ÖNEMLİ: 5 Nisan 2024'ten itibaren URL path formatı kullanılmalı!
        
        Parameters:
        -----------
        seriler : str or list
            Seri kodu veya kodları listesi
        baslangic : str
            Başlangıç tarihi (gg-aa-yyyy)
        bitis : str
            Bitiş tarihi (gg-aa-yyyy)
        frekans : int or str, optional
            Frekans kodu veya adı
        formul : int or str or list, optional
            Formül kodu/adı veya listesi
        aggregation : str or list, optional
            Aggregation yöntemi
        
        Returns:
        --------
        pd.DataFrame
            Tarih indexli veri
        """
        # Serileri hazırla
        if isinstance(seriler, str):
            seriler = [seriler]
        seri_str = "-".join(seriler)
        
        # URL path formatında parametreleri oluştur (5 Nisan 2024 güncellemesi)
        url = f"{self.base_url}/series={seri_str}&startDate={baslangic}&endDate={bitis}&type=json"
        
        # Opsiyonel parametreler
        if frekans:
            if isinstance(frekans, str):
                frekans = self.FREKANS.get(frekans.lower(), frekans)
            url += f"&frequency={frekans}"
        
        if formul:
            if isinstance(formul, list):
                formul_str = "-".join(str(self.FORMUL.get(f, f) if isinstance(f, str) else f) for f in formul)
            else:
                formul_str = str(self.FORMUL.get(formul, formul) if isinstance(formul, str) else formul)
            url += f"&formulas={formul_str}"
        
        if aggregation:
            if isinstance(aggregation, list):
                agg_str = "-".join(self.AGGREGATION.get(a.lower(), a) for a in aggregation)
            else:
                agg_str = self.AGGREGATION.get(aggregation.lower(), aggregation)
            url += f"&aggregationTypes={agg_str}"
        
        # İstek gönder (key header'da)
        try:
            response = requests.get(url, headers=self.headers, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                raise ValueError("API anahtarı geçersiz veya eksik. Lütfen kontrol edin.")
            elif response.status_code == 404:
                raise ValueError("Veri bulunamadı. URL formatını veya seri kodlarını kontrol edin.")
            raise e
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Bağlantı hatası: {e}")
        
        if not data:
            raise ValueError("Veri bulunamadı. Tarih aralığını ve seri kodlarını kontrol edin.")
        
        kayitlar = self._extract_records(data, "series")
        if not kayitlar:
            raise ValueError("Veri bulunamadı. Tarih aralığını ve seri kodlarını kontrol edin.")
        
        # DataFrame oluştur
        df = pd.DataFrame(kayitlar)
        
        # Tarih sütununu bul ve parse et
        tarih_sutunu = next(
            (
                col for col in df.columns
                if str(col).strip().lower() in {'tarih', 'date', 'tarih_str'}
            ),
            df.columns[0]
        )
        df = self._parse_tarih(df, tarih_sutunu)
        
        # Sayısal sütunları dönüştür
        cols_to_convert = [col for col in df.columns if col not in ['UNIXTIME', 'YEARWEEK']]
        if cols_to_convert:
            # Sadece object (string) sütunlarda temizlik yap
            obj_cols = df[cols_to_convert].select_dtypes(include=['object']).columns
            if not obj_cols.empty:
                # Virgülleri noktaya çevir ve boşlukları NA yap (vectorized)
                df[obj_cols] = df[obj_cols].astype(str).replace(',', '.', regex=True).replace(r'^\s*$', pd.NA, regex=True)

            # Sayısal dönüşümü toplu yap
            df[cols_to_convert] = df[cols_to_convert].apply(pd.to_numeric, errors='coerce')
        
        # Gereksiz sütunları kaldır
        for col in ['UNIXTIME', 'YEARWEEK']:
            if col in df.columns:
                df = df.drop(col, axis=1)
        
        return df.sort_index()
    
    def _parse_tarih(self, df: pd.DataFrame, tarih_sutunu: str) -> pd.DataFrame:
        """
        EVDS tarih formatını otomatik algıla ve parse et.
        
        Formatlar:
        - Aylık: 2024-1, 2024-12
        - Günlük/Haftalık: 01-01-2024, 07-01-2024
        - Çeyreklik: 2024-Q1
        - Yıllık: 2024
        """
        tarih_serisi = df[tarih_sutunu].astype(str).str.strip()
        if tarih_serisi.empty:
            raise ValueError("Tarih sütunu boş.")
        
        ornek = str(tarih_serisi.iloc[0])
        
        if re.match(r'^\d{4}-\d{1,2}$', ornek):
            # Aylık: 2024-1, 2024-12
            parsed = pd.to_datetime(tarih_serisi, format='%Y-%m')
        elif re.match(r'^\d{2}-\d{2}-\d{4}$', ornek):
            # Günlük: 01-01-2024
            parsed = pd.to_datetime(tarih_serisi, format='%d-%m-%Y')
        elif re.match(r'^\d{4}-Q[1-4]$', ornek):
            # Çeyreklik: 2024-Q1 -> 2024-01-01
            quarter_map = {'Q1': '01', 'Q2': '04', 'Q3': '07', 'Q4': '10'}
            aylik = tarih_serisi.str.replace(
                r'^(\d{4})-(Q[1-4])$',
                lambda m: f"{m.group(1)}-{quarter_map[m.group(2)]}",
                regex=True
            )
            parsed = pd.to_datetime(aylik, format='%Y-%m')
        elif re.match(r'^\d{4}$', ornek):
            # Yıllık: 2024
            parsed = pd.to_datetime(tarih_serisi, format='%Y')
        else:
            # Fallback: önce gün-öncelikli, gerekirse mixed
            parsed = pd.to_datetime(tarih_serisi, errors='coerce', dayfirst=True)
            if parsed.isna().all():
                parsed = pd.to_datetime(tarih_serisi, errors='coerce', format='mixed')
            if parsed.isna().all():
                raise ValueError(f"Tarih formatı çözümlenemedi: {ornek}")
        
        df[tarih_sutunu] = parsed
        
        df = df.set_index(tarih_sutunu)
        df.index.name = 'Tarih'
        return df.sort_index()
    
    def seri_ara(self, anahtar_kelime: str) -> Dict[str, str]:
        """
        Anahtar kelimeye göre seri arar.
        
        Parameters:
        -----------
        anahtar_kelime : str
            Aranacak kelime (Türkçe)
        
        Returns:
        --------
        dict
            Seri kodu → Seri adı eşleştirmesi
        """
        SERILER = {
            'enflasyon': {
                'TP.FG.J0': 'TÜFE - Genel Endeks (2003=100)',
            },
            'tüfe': {
                'TP.FG.J0': 'TÜFE - Genel Endeks (2003=100)',
            },
            'döviz': {
                'TP.DK.USD.A': 'USD/TRY Alış',
                'TP.DK.EUR.A': 'EUR/TRY Alış',
            },
            'dolar': {'TP.DK.USD.A': 'USD/TRY'},
            'euro': {'TP.DK.EUR.A': 'EUR/TRY'},
            'faiz': {'TP.PF.FF.GUN': 'TCMB Politika Faizi'},
            'işsizlik': {'TP.UR.U01': 'İşsizlik Oranı (%)'},
            'yp mevduat': {
                'TP.YPMEVD.M01': 'Toplam YP Mevduatlar (Bin TL)',
                'TP.HPBITABLO4.1': 'Toplam YP Mevduat (Milyon USD)',
            },
            'dolarizasyon': {
                'TP.YPMEVD.M01': 'Toplam YP Mevduatlar (Bin TL)',
            },
            'kkm': {
                'TP.KKM.K1': 'DDKKM Toplam (Milyar USD)',
                'TP.KKM.K4': 'TL KKM Toplam (Milyar TL)',
            },
            'dth': {
                'TP.TLDTHVADE.KB12': 'DTH Toplam (Bin TL)',
                'TP.TLDTHVADE.KB6': 'TL Mevduat Toplam (Bin TL)',
            },
        }
        
        kelime = anahtar_kelime.lower()
        for k, v in SERILER.items():
            if k in kelime:
                return v
        return {}


def tanimlayici_istatistikler(df: pd.DataFrame) -> Dict:
    """
    DataFrame için tanımlayıcı istatistikler hesaplar.
    
    Returns:
    --------
    dict
        Her sütun için istatistikler
    """
    sonuclar = {}
    
    for col in df.columns:
        seri = df[col].dropna()
        
        if len(seri) == 0:
            continue
        
        # Trend belirleme
        if len(seri) >= 12:
            son_12 = seri.tail(12)
            ilk_6 = son_12.head(6).mean()
            son_6 = son_12.tail(6).mean()
            if ilk_6 != 0:
                degisim = (son_6 - ilk_6) / abs(ilk_6) * 100
                if degisim > 5:
                    trend = "↗ Yükseliş"
                elif degisim < -5:
                    trend = "↘ Düşüş"
                else:
                    trend = "→ Yatay"
            else:
                trend = "→ Yatay"
        else:
            trend = "Yetersiz veri"
        
        sonuclar[col] = {
            'baslangic': seri.index.min().strftime('%d.%m.%Y'),
            'bitis': seri.index.max().strftime('%d.%m.%Y'),
            'gozlem': len(seri),
            'ortalama': round(seri.mean(), 2),
            'std': round(seri.std(), 2),
            'min': round(seri.min(), 2),
            'min_tarih': seri.idxmin().strftime('%d.%m.%Y'),
            'max': round(seri.max(), 2),
            'max_tarih': seri.idxmax().strftime('%d.%m.%Y'),
            'son_deger': round(seri.iloc[-1], 2),
            'trend': trend,
            'eksik': df[col].isna().sum()
        }
    
    return sonuclar


def istatistik_ozeti_formatla(istatistikler: Dict) -> str:
    """İstatistikleri okunabilir formata çevirir."""
    cikti = []
    
    for seri, stats in istatistikler.items():
        metin = f"""
📊 {seri} - Özet
{'━' * 40}
Dönem: {stats['baslangic']} - {stats['bitis']}
Gözlem: {stats['gozlem']}
Ortalama: {stats['ortalama']}
Std. Sapma: {stats['std']}
Min: {stats['min']} ({stats['min_tarih']})
Max: {stats['max']} ({stats['max_tarih']})
Son Değer: {stats['son_deger']}
Trend: {stats['trend']}
"""
        if stats['eksik'] > 0:
            metin += f"⚠️ Eksik Veri: {stats['eksik']} gözlem\n"
        
        cikti.append(metin)
    
    return "\n".join(cikti)


if __name__ == "__main__":
    print("EVDS Client modülü yüklendi.")
    print("Kullanım: client = EVDSClient('API_KEY')")
    print("\nÖRNEK:")
    print("  client = EVDSClient('your_api_key')")
    print("  df = client.veri_cek('TP.DK.USD.A', '01-01-2024', '31-12-2024')")

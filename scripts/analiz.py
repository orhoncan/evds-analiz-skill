#!/usr/bin/env python3
"""
EVDS Analiz Modulu
Istatistiksel analizler: OLS, ARIMA, VAR, mevsimsellik, korelasyon.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


def korelasyon_analizi(df: pd.DataFrame, metot: str = 'pearson') -> Dict:
    """Korelasyon analizi yapar."""
    corr = df.corr(method=metot)
    
    mask = np.triu(np.ones(corr.shape), k=1).astype(bool)
    rows, cols = np.where(mask)
    col_names = corr.columns
    r_values = corr.values[rows, cols]

    stacked = pd.DataFrame({
        'seri1': col_names[rows],
        'seri2': col_names[cols],
        'r': r_values
    })

    abs_r = stacked['r'].abs()
    stacked['guc'] = np.select(
        [
            abs_r >= 0.8,
            abs_r >= 0.6,
            abs_r >= 0.4,
            abs_r >= 0.2
        ],
        [
            "cok guclu",
            "guclu",
            "orta",
            "zayif"
        ],
        default="ihmal edilebilir"
    )

    stacked['yon'] = np.where(stacked['r'] > 0, "pozitif", "negatif")
    stacked['r'] = stacked['r'].round(3)

    yorumlar = stacked.to_dict('records')
    
    return {'matris': corr, 'yorumlar': yorumlar}


def ols_regresyon(y: pd.Series, X: pd.DataFrame, sabit_ekle: bool = True) -> Dict:
    """OLS regresyon analizi yapar."""
    try:
        import statsmodels.api as sm
    except ImportError:
        return {'hata': 'statsmodels paketi yuklu degil. pip install statsmodels'}
    
    data = pd.concat([y, X], axis=1).dropna()
    y_clean = data.iloc[:, 0]
    X_clean = data.iloc[:, 1:]
    
    if sabit_ekle:
        X_clean = sm.add_constant(X_clean)
    
    model = sm.OLS(y_clean, X_clean).fit()
    dw = sm.stats.stattools.durbin_watson(model.resid)
    
    return {
        'r_kare': round(model.rsquared, 4),
        'duzeltilmis_r_kare': round(model.rsquared_adj, 4),
        'f_istatistigi': round(model.fvalue, 2),
        'f_p_degeri': model.f_pvalue,
        'katsayilar': {k: round(v, 4) for k, v in model.params.items()},
        'p_degerleri': {k: round(v, 4) for k, v in model.pvalues.items()},
        'standart_hatalar': {k: round(v, 4) for k, v in model.bse.items()},
        'durbin_watson': round(dw, 2),
        'gozlem': int(model.nobs),
        'model': model
    }


def arima_analizi(y: pd.Series, tahmin_donemi: int = 12, mevsimsel: bool = True, m: int = 12) -> Dict:
    """ARIMA/SARIMA analizi yapar."""
    try:
        from pmdarima import auto_arima
    except ImportError:
        return {'hata': 'pmdarima paketi yuklu degil. pip install pmdarima'}
    
    y_clean = y.dropna()
    
    model = auto_arima(
        y_clean, start_p=0, start_q=0, max_p=5, max_q=5,
        seasonal=mevsimsel, m=m if mevsimsel else 1,
        start_P=0, start_Q=0, max_P=2, max_Q=2,
        d=None, D=None, trace=False, error_action='ignore',
        suppress_warnings=True, stepwise=True, information_criterion='aic'
    )
    
    tahmin, guven_araligi = model.predict(n_periods=tahmin_donemi, return_conf_int=True, alpha=0.05)
    
    son_tarih = y_clean.index[-1]
    if isinstance(son_tarih, pd.Timestamp):
        freq = pd.infer_freq(y_clean.index) or 'MS'
        tahmin_tarihleri = pd.date_range(start=son_tarih, periods=tahmin_donemi + 1, freq=freq)[1:]
    else:
        tahmin_tarihleri = list(range(len(y_clean), len(y_clean) + tahmin_donemi))
    
    return {
        'order': model.order,
        'seasonal_order': model.seasonal_order if mevsimsel else None,
        'aic': round(model.aic(), 2),
        'bic': round(model.bic(), 2),
        'tahmin': pd.Series(tahmin, index=tahmin_tarihleri),
        'guven_araligi_alt': pd.Series(guven_araligi[:, 0], index=tahmin_tarihleri),
        'guven_araligi_ust': pd.Series(guven_araligi[:, 1], index=tahmin_tarihleri),
        'model': model
    }


def var_analizi(df: pd.DataFrame, degiskenler: List[str], max_lag: int = 12) -> Dict:
    """VAR modeli tahmin eder."""
    try:
        from statsmodels.tsa.api import VAR
    except ImportError:
        return {'hata': 'statsmodels paketi yuklu degil'}
    
    data = df[degiskenler].dropna()
    model = VAR(data)
    
    lag_secimi = model.select_order(maxlags=max_lag)
    optimal_lag = lag_secimi.aic
    
    sonuclar = model.fit(optimal_lag)
    
    granger = {}
    for hedef in degiskenler:
        for kaynak in degiskenler:
            if hedef != kaynak:
                test = sonuclar.test_causality(hedef, [kaynak], kind='f')
                granger[f"{kaynak} -> {hedef}"] = {
                    'f_stat': round(test.test_statistic, 3),
                    'p_value': round(test.pvalue, 4),
                    'sonuc': "Nedensellik VAR" if test.pvalue < 0.05 else "Nedensellik YOK"
                }
    
    return {
        'optimal_lag': optimal_lag,
        'granger': granger,
        'model': sonuclar
    }


def mevsimsellik_analizi(y: pd.Series, periyot: int = 12) -> Dict:
    """STL decomposition ile mevsimsellik analizi."""
    try:
        from statsmodels.tsa.seasonal import STL
    except ImportError:
        return {'hata': 'statsmodels paketi yuklu degil'}
    
    y_clean = y.dropna()
    stl = STL(y_clean, period=periyot, robust=True)
    sonuc = stl.fit()
    
    return {
        'trend': sonuc.trend,
        'mevsimsel': sonuc.seasonal,
        'artik': sonuc.resid,
        'mevsimsel_guc': round(sonuc.seasonal.std() / y_clean.std(), 3),
        'trend_guc': round(sonuc.trend.std() / y_clean.std(), 3)
    }


def format_ols(sonuc: Dict, bagimli: str) -> str:
    """OLS sonuclarini formatlar."""
    if 'hata' in sonuc:
        return f"Hata: {sonuc['hata']}"
    
    metin = f"\nOLS Regresyon Sonuclari\n{'='*40}\nBagimli Degisken: {bagimli}\n\n"
    metin += f"R2: {sonuc['r_kare']}\nDuzeltilmis R2: {sonuc['duzeltilmis_r_kare']}\n"
    metin += f"F-istatistigi: {sonuc['f_istatistigi']} (p={sonuc['f_p_degeri']:.4f})\n\nKatsayilar:\n"
    
    for var, katsayi in sonuc['katsayilar'].items():
        p = sonuc['p_degerleri'][var]
        sig = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""
        metin += f"  {var}: {katsayi}{sig} (p={p:.4f})\n"
    
    metin += f"\nDurbin-Watson: {sonuc['durbin_watson']}\nGozlem: {sonuc['gozlem']}\n"
    return metin


def format_arima(sonuc: Dict, seri_adi: str) -> str:
    """ARIMA sonuclarini formatlar."""
    if 'hata' in sonuc:
        return f"Hata: {sonuc['hata']}"
    
    model_str = f"ARIMA{sonuc['order']}"
    if sonuc['seasonal_order']:
        model_str += f"x{sonuc['seasonal_order']}"
    
    metin = f"\nARIMA Model Sonuclari\n{'='*40}\nSeri: {seri_adi}\nModel: {model_str}\n"
    metin += f"AIC: {sonuc['aic']}\nBIC: {sonuc['bic']}\n\nTahminler:\n"
    
    for tarih, deger in sonuc['tahmin'].items():
        alt = sonuc['guven_araligi_alt'][tarih]
        ust = sonuc['guven_araligi_ust'][tarih]
        tarih_str = tarih.strftime('%Y-%m') if hasattr(tarih, 'strftime') else str(tarih)
        metin += f"  {tarih_str}: {deger:.2f} [{alt:.2f} - {ust:.2f}]\n"
    
    return metin


def format_var(sonuc: Dict) -> str:
    """VAR sonuclarini formatlar."""
    if 'hata' in sonuc:
        return f"Hata: {sonuc['hata']}"
    
    metin = f"\nVAR Model Sonuclari\n{'='*40}\nOptimal Gecikme: {sonuc['optimal_lag']}\n\n"
    metin += "Granger Nedensellik Testleri:\n"
    
    for ilski, test in sonuc['granger'].items():
        sembol = "+" if test['sonuc'] == "Nedensellik VAR" else "-"
        metin += f"  [{sembol}] {ilski}: F={test['f_stat']}, p={test['p_value']}\n"
    
    return metin


def format_korelasyon(sonuc: Dict) -> str:
    """Korelasyon sonuclarini formatlar."""
    metin = "\nKorelasyon Analizi\n" + "="*40 + "\n"
    
    for y in sonuc['yorumlar']:
        if y['guc'] != 'ihmal edilebilir':
            metin += f"  {y['seri1']} <-> {y['seri2']}: r={y['r']:.3f} ({y['guc']} {y['yon']})\n"
    
    return metin


if __name__ == "__main__":
    print("Analiz modulu yuklendi.")

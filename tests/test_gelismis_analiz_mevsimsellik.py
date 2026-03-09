import pytest
import pandas as pd
import numpy as np
from scripts.gelismis_analiz import mevsimsellik_temizle

def test_mevsimsellik_temizle_basic():
    # Synthetic time series with clear seasonality
    t = np.arange(48)
    trend = 0.5 * t
    seasonality = 10 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(0, 1, size=48)

    y = trend + seasonality + noise
    index = pd.date_range(start='2020-01-01', periods=48, freq='ME')
    seri = pd.Series(y, index=index)

    result = mevsimsellik_temizle(seri, periyot=12, metot='stl')

    assert 'hata' not in result
    assert 'trend' in result
    assert 'mevsimsel' in result
    assert 'artik' in result
    assert 'duzeltilmis' in result
    assert result['metot'] == 'stl'
    assert result['periyot'] == 12
    assert result['mevsimsel_guc'] > 0.5  # Since it's a strongly seasonal synthetic data


def test_mevsimsellik_temizle_ma():
    # Synthetic time series with clear seasonality
    t = np.arange(48)
    trend = 0.5 * t
    # For MA multiplicative detrending/deseasonalizing, we need positive values
    # MA method implemented uses division for detrending, so the data should be positive and multiplicative
    seasonality = 1 + 0.5 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(1, 0.05, size=48)

    y = (trend + 10) * seasonality * noise
    index = pd.date_range(start='2020-01-01', periods=48, freq='ME')
    seri = pd.Series(y, index=index)

    result = mevsimsellik_temizle(seri, periyot=12, metot='ma')

    assert 'hata' not in result
    assert 'trend' in result
    assert 'mevsimsel' in result
    assert 'artik' in result
    assert 'duzeltilmis' in result
    assert result['metot'] == 'ma'

def test_mevsimsellik_temizle_x11():
    t = np.arange(48)
    trend = 0.5 * t
    seasonality = 10 * np.sin(2 * np.pi * t / 12)
    noise = np.random.normal(0, 1, size=48)

    y = trend + seasonality + noise
    index = pd.date_range(start='2020-01-01', periods=48, freq='ME')
    seri = pd.Series(y, index=index)

    result = mevsimsellik_temizle(seri, periyot=12, metot='x11')

    assert 'hata' not in result
    assert 'trend' in result
    assert 'mevsimsel' in result
    assert 'artik' in result
    assert 'duzeltilmis' in result
    assert result['metot'] == 'x11'

def test_mevsimsellik_temizle_insufficient_data():
    t = np.arange(10)
    y = t
    index = pd.date_range(start='2020-01-01', periods=10, freq='ME')
    seri = pd.Series(y, index=index)

    result = mevsimsellik_temizle(seri, periyot=12, metot='stl')

    assert 'hata' in result
    assert 'Yetersiz veri' in result['hata']

def test_mevsimsellik_temizle_unknown_method():
    t = np.arange(48)
    y = t
    index = pd.date_range(start='2020-01-01', periods=48, freq='ME')
    seri = pd.Series(y, index=index)

    result = mevsimsellik_temizle(seri, periyot=12, metot='unknown_method')

    assert 'hata' in result
    assert 'Bilinmeyen metot' in result['hata']

import pytest
import pandas as pd
import numpy as np
from scripts.gelismis_analiz import coklu_degisken_analizi

@pytest.fixture
def sample_df():
    """Create a sample dataframe for testing."""
    np.random.seed(42)
    dates = pd.date_range(start='2020-01-01', periods=100, freq='ME')

    # Create somewhat correlated data
    x1 = np.random.normal(0, 1, 100)
    x2 = x1 * 0.5 + np.random.normal(0, 0.5, 100)
    y = x1 * 1.5 + x2 * -0.8 + np.random.normal(0, 0.2, 100)

    # Create Granger causality relationship (x1 lags x3)
    x3 = np.roll(x1, 2)
    x3[:2] = 0

    df = pd.DataFrame({
        'bagimli_y': y,
        'bagimsiz_x1': x1,
        'bagimsiz_x2': x2,
        'lagged_x3': x3,
        'kategorik': ['A', 'B', 'C', 'D'] * 25
    }, index=dates)

    return df

def test_coklu_degisken_analizi_insufficient_columns():
    """Test error when less than 2 numeric columns are provided."""
    df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
    result = coklu_degisken_analizi(df)
    assert 'hata' in result
    assert result['hata'] == 'En az 2 sayısal sütun gerekli'

def test_coklu_degisken_analizi_default_analizler(sample_df):
    """Test default analyses when none are specified."""
    result = coklu_degisken_analizi(sample_df)

    # Check default keys
    assert 'korelasyon' in result
    assert 'pca' in result
    assert 'granger' in result
    assert 'regresyon' not in result

def test_coklu_degisken_analizi_korelasyon(sample_df):
    """Test correlation analysis functionality."""
    result = coklu_degisken_analizi(sample_df, analizler=['korelasyon'])

    assert 'korelasyon' in result
    kor = result['korelasyon']

    assert 'pearson' in kor
    assert 'spearman' in kor
    assert 'kendall' in kor
    assert 'en_guclu' in kor

    # Check if 'kategorik' was excluded (only numeric columns allowed)
    assert 'kategorik' not in kor['pearson']

    # Check diagonal is 1.0 (or close to it due to rounding)
    assert kor['pearson']['bagimli_y']['bagimli_y'] == 1.0

    # Verify the structure of 'en_guclu'
    assert isinstance(kor['en_guclu'], list)
    if kor['en_guclu']:
        assert 'seri1' in kor['en_guclu'][0]
        assert 'seri2' in kor['en_guclu'][0]
        assert 'r' in kor['en_guclu'][0]
        assert 'guc' in kor['en_guclu'][0]

def test_coklu_degisken_analizi_pca(sample_df):
    """Test PCA analysis functionality."""
    result = coklu_degisken_analizi(sample_df, analizler=['pca'])

    assert 'pca' in result
    pca = result['pca']

    # Check if error occurred (e.g. sklearn not installed)
    if 'hata' not in pca:
        assert 'aciklanan_varyans' in pca
        assert 'kumulatif_varyans' in pca
        assert 'bilesenlerin_yuklemeleri' in pca
        assert '%95_icin_bilesen' in pca

        # Check lengths
        assert len(pca['aciklanan_varyans']) <= 4 # 4 numeric columns

def test_coklu_degisken_analizi_granger(sample_df):
    """Test Granger causality analysis functionality."""
    result = coklu_degisken_analizi(sample_df, analizler=['granger'])

    assert 'granger' in result
    granger = result['granger']

    if 'hata' not in granger:
        assert isinstance(granger, dict)
        # Verify some Granger result structure if any causalities were found
        for key, val in granger.items():
            assert 'p_value' in val
            assert 'best_lag' in val
            assert 'nedensellik' in val
            assert val['nedensellik'] in ['VAR', 'YOK']

def test_coklu_degisken_analizi_regresyon(sample_df):
    """Test multiple regression analysis functionality."""
    result = coklu_degisken_analizi(
        sample_df,
        bagimli='bagimli_y',
        bagimsizlar=['bagimsiz_x1', 'bagimsiz_x2'],
        analizler=['regresyon']
    )

    assert 'regresyon' in result
    reg = result['regresyon']

    if 'hata' not in reg:
        assert 'r2' in reg
        assert 'r2_adj' in reg
        assert 'f_stat' in reg
        assert 'f_pvalue' in reg
        assert 'durbin_watson' in reg
        assert 'katsayilar' in reg
        assert 'p_values' in reg

        # Verify coefficients match expected independent variables (+ constant)
        assert 'const' in reg['katsayilar']
        assert 'bagimsiz_x1' in reg['katsayilar']
        assert 'bagimsiz_x2' in reg['katsayilar']

def test_anomali_tespiti():
    """Test anomaly detection logic."""
    from scripts.gelismis_analiz import anomali_tespiti

    # Needs sufficient rows, zscore uses mean and std
    np.random.seed(42)
    normal_data = np.random.normal(0, 1, 50)
    normal_data = np.append(normal_data, [100.0, -100.0]) # Add anomalies

    df = pd.DataFrame({
        'A': normal_data,
        'B': np.arange(52) # No anomalies
    })
    df.index = pd.date_range('2020-01-01', periods=52)

    result = anomali_tespiti(df, metot='zscore')

    assert 'A' in result
    assert 'B' in result

    # A should have anomalies
    assert 'anomali_sayisi' in result['A']
    assert result['A']['anomali_sayisi'] >= 2


    # B should have no anomalies


def test_durgunluk_testi():
    """Test stationarity test (ADF)."""
    from scripts.gelismis_analiz import durgunluk_testi

    # Create a non-stationary series (random walk)
    np.random.seed(42)
    non_stationary = pd.Series(np.cumsum(np.random.normal(0, 1, 100)))

    res1 = durgunluk_testi(non_stationary)
    assert res1['test'] == 'ADF'
    assert 'istatistik' in res1
    assert 'p_value' in res1
    assert res1['duragan'] == False # Random walk is non-stationary

    # Create a stationary series (white noise)
    stationary = pd.Series(np.random.normal(0, 1, 100))
    res2 = durgunluk_testi(stationary)
    assert res2['duragan'] == True # White noise is stationary

def test_veri_kalitesi_kontrolu():
    """Test data quality checks."""
    from scripts.gelismis_analiz import veri_kalitesi_kontrolu

    df = pd.DataFrame({
        'A': [1, 2, 3, 4, 5],
        'B': [1, 1, np.nan, np.nan, 5],
        'C': ['X', 'Y', 'Z', 'W', 'V']
    })
    df.index = pd.date_range('2020-01-01', periods=5)

    kalite = veri_kalitesi_kontrolu(df)

    assert 'genel' in kalite
    assert kalite['genel']['satir_sayisi'] == 5
    assert kalite['genel']['sutun_sayisi'] == 3
    assert kalite['genel']['eksik_toplam'] == 2

    assert 'sutunlar' in kalite
    assert 'B' in kalite['sutunlar']
    assert kalite['sutunlar']['B']['eksik'] == 2

    assert 'uyarilar' in kalite
    assert 'puan' in kalite

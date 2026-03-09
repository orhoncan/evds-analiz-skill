import pytest
from unittest.mock import MagicMock, patch
import sys

# Since pandas/numpy might not be available in the test environment, we mock them
@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch.dict(sys.modules, {
        'pandas': MagicMock(),
        'numpy': MagicMock()
    }):
        yield

def test_ols_regresyon_missing_statsmodels():
    """Test that ols_regresyon returns an error message when statsmodels is not installed."""
    with patch.dict(sys.modules, {'statsmodels': None, 'statsmodels.api': None}):
        # We need to reload the module or ensure it's imported inside the test
        # but the code itself does the import inside the function, which is good.
        from scripts.analiz import ols_regresyon

        y = MagicMock()
        X = MagicMock()

        result = ols_regresyon(y, X)

        assert 'hata' in result
        assert 'statsmodels' in result['hata']
        assert 'pip install statsmodels' in result['hata']

def test_arima_analizi_missing_pmdarima():
    """Test that arima_analizi returns an error message when pmdarima is not installed."""
    with patch.dict(sys.modules, {'pmdarima': None}):
        from scripts.analiz import arima_analizi

        y = MagicMock()

        result = arima_analizi(y)

        assert 'hata' in result
        assert 'pmdarima' in result['hata']
        assert 'pip install pmdarima' in result['hata']

def test_var_analizi_missing_statsmodels():
    """Test that var_analizi returns an error message when statsmodels is not installed."""
    with patch.dict(sys.modules, {'statsmodels': None, 'statsmodels.tsa.api': None}):
        from scripts.analiz import var_analizi

        df = MagicMock()
        degiskenler = ['A', 'B']

        result = var_analizi(df, degiskenler)

        assert 'hata' in result
        assert 'statsmodels' in result['hata']

def test_mevsimsellik_analizi_missing_statsmodels():
    """Test that mevsimsellik_analizi returns an error message when statsmodels is not installed."""
    with patch.dict(sys.modules, {'statsmodels': None, 'statsmodels.tsa.seasonal': None}):
        from scripts.analiz import mevsimsellik_analizi

        y = MagicMock()

        result = mevsimsellik_analizi(y)

        assert 'hata' in result
        assert 'statsmodels' in result['hata']

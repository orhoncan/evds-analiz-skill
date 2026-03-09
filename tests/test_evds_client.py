import pytest
import pandas as pd
import requests
from unittest.mock import patch, MagicMock
from scripts.evds_client import EVDSClient

@pytest.fixture
def client():
    # Instantiate client with dummy API key
    return EVDSClient(api_key="dummy_key")

def test_parse_tarih_aylik(client):
    # Test format: 2024-1, 2024-12
    df = pd.DataFrame({"Tarih": ["2024-1", "2024-12", "2023-05"]})
    result = client._parse_tarih(df, "Tarih")

    assert result.index.name == "Tarih"
    assert len(result) == 3
    assert result.index[0] == pd.Timestamp("2023-05-01")
    assert result.index[1] == pd.Timestamp("2024-01-01")
    assert result.index[2] == pd.Timestamp("2024-12-01")

def test_parse_tarih_gunluk(client):
    # Test format: 01-01-2024, 07-01-2024
    df = pd.DataFrame({"Tarih": ["01-01-2024", "07-01-2024"]})
    result = client._parse_tarih(df, "Tarih")

    assert result.index.name == "Tarih"
    assert len(result) == 2
    assert result.index[0] == pd.Timestamp("2024-01-01")
    assert result.index[1] == pd.Timestamp("2024-01-07")

def test_parse_tarih_ceyreklik(client):
    # Test format: 2024-Q1, 2024-Q4
    df = pd.DataFrame({"Tarih": ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]})
    result = client._parse_tarih(df, "Tarih")

    assert result.index.name == "Tarih"
    assert len(result) == 4
    assert result.index[0] == pd.Timestamp("2024-01-01")
    assert result.index[1] == pd.Timestamp("2024-04-01")
    assert result.index[2] == pd.Timestamp("2024-07-01")
    assert result.index[3] == pd.Timestamp("2024-10-01")

def test_parse_tarih_yillik(client):
    # Test format: 2023, 2024
    df = pd.DataFrame({"Tarih": ["2023", "2024"]})
    result = client._parse_tarih(df, "Tarih")

    assert result.index.name == "Tarih"
    assert len(result) == 2
    assert result.index[0] == pd.Timestamp("2023-01-01")
    assert result.index[1] == pd.Timestamp("2024-01-01")

def test_parse_tarih_fallback(client):
    # Test fallback format e.g. 2024/01/01
    df = pd.DataFrame({"Tarih": ["01/05/2024", "15/05/2024"]})
    result = client._parse_tarih(df, "Tarih")

    assert result.index.name == "Tarih"
    assert len(result) == 2
    assert result.index[0] == pd.Timestamp("2024-05-01")
    assert result.index[1] == pd.Timestamp("2024-05-15")

def test_parse_tarih_mixed_fallback(client):
    # Test format='mixed' fallback
    # The first fallback tries dayfirst=True, which will fail if day > 12 when parsing in monthfirst style.
    # To force the mixed fallback, we can provide ambiguous dates that require format='mixed'.
    # Actually, pd.to_datetime with dayfirst=True can fail if the string is clearly MM/DD/YYYY with DD > 12 and month > 12.
    # Example: '13/13/2024' is invalid. But wait, if we pass '01/13/2024', dayfirst=True treats '01' as day, '13' as month, which fails since month > 12.
    # So '01/13/2024' forces it to fail the first parse, then it uses format='mixed' which parses it as Jan 13.
    df = pd.DataFrame({"Tarih": ["01/13/2024", "02/15/2024"]})
    result = client._parse_tarih(df, "Tarih")

    assert result.index.name == "Tarih"
    assert len(result) == 2
    assert result.index[0] == pd.Timestamp("2024-01-13")
    assert result.index[1] == pd.Timestamp("2024-02-15")

def test_parse_tarih_empty_df(client):
    # Test empty dataframe
    df = pd.DataFrame({"Tarih": []})
    with pytest.raises(ValueError, match="Tarih sütunu boş."):
        client._parse_tarih(df, "Tarih")

def test_parse_tarih_invalid_format(client):
    # Test unresolvable format
    df = pd.DataFrame({"Tarih": ["invalid_date_1", "invalid_date_2"]})
    with pytest.raises(ValueError, match="Tarih formatı çözümlenemedi"):
        client._parse_tarih(df, "Tarih")

def test_parse_tarih_preserves_other_columns(client):
    # Ensure other columns are kept intact
    df = pd.DataFrame({
        "Tarih": ["2024-1", "2024-2"],
        "Değer": [10.5, 20.0]
    })
    result = client._parse_tarih(df, "Tarih")

    assert "Değer" in result.columns
    assert list(result["Değer"]) == [10.5, 20.0]
    assert result.index[0] == pd.Timestamp("2024-01-01")
    assert result.index[1] == pd.Timestamp("2024-02-01")

@patch("requests_cache.CachedSession.get")
def test_veri_cek_happy_path(mock_get, client):
    # Prepare a dummy response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "totalCount": 2,
        "items": [
            {
                "Tarih": "01-01-2024",
                "TP_DK_USD_A": "29.50",
                "UNIXTIME": {"$numberLong": "1704067200"}
            },
            {
                "Tarih": "02-01-2024",
                "TP_DK_USD_A": "29.60",
                "UNIXTIME": {"$numberLong": "1704153600"}
            }
        ]
    }
    mock_get.return_value = mock_response

    # Test the function
    df = client.veri_cek(seriler="TP.DK.USD.A", baslangic="01-01-2024", bitis="02-01-2024", frekans=1)

    # Verify that get was called with the correct URL
    mock_get.assert_called_once()
    called_url = mock_get.call_args[0][0]
    assert "series=TP.DK.USD.A" in called_url
    assert "startDate=01-01-2024" in called_url
    assert "endDate=02-01-2024" in called_url
    assert "frequency=1" in called_url

    # Verify output dataframe
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "TP_DK_USD_A" in df.columns
    assert "UNIXTIME" not in df.columns

    # Assert dates and values
    assert df.index.name == "Tarih"
    assert df.index[0] == pd.Timestamp("2024-01-01")
    assert df.index[1] == pd.Timestamp("2024-01-02")
    assert df["TP_DK_USD_A"].iloc[0] == 29.50
    assert df["TP_DK_USD_A"].iloc[1] == 29.60

@patch("requests_cache.CachedSession.get")
def test_veri_cek_http_error_403(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="API anahtarı geçersiz veya eksik"):
        client.veri_cek(seriler="TP.DK.USD.A", baslangic="01-01-2024", bitis="02-01-2024")

@patch("requests_cache.CachedSession.get")
def test_veri_cek_http_error_404(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Veri bulunamadı. URL formatını veya seri kodlarını kontrol edin."):
        client.veri_cek(seriler="INVALID_SERIES", baslangic="01-01-2024", bitis="02-01-2024")

@patch("requests_cache.CachedSession.get")
def test_veri_cek_connection_error(mock_get, client):
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection timeout")

    with pytest.raises(ConnectionError, match="Bağlantı hatası: Connection timeout"):
        client.veri_cek(seriler="TP.DK.USD.A", baslangic="01-01-2024", bitis="02-01-2024")

@patch("requests_cache.CachedSession.get")
def test_veri_cek_missing_data(mock_get, client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    # "items" present but empty
    mock_response.json.return_value = {"totalCount": 0, "items": []}
    mock_get.return_value = mock_response

    with pytest.raises(ValueError, match="Veri bulunamadı. Tarih aralığını ve seri kodlarını kontrol edin."):
        client.veri_cek(seriler="TP.DK.USD.A", baslangic="01-01-2024", bitis="02-01-2024")

def test_seri_ara(client):
    """Test searching for a series."""
    # seri_ara is an offline hardcoded lookup function
    result = client.seri_ara("enflasyon")
    assert isinstance(result, dict)
    assert 'TP.FG.J0' in result
    assert 'TÜFE' in result['TP.FG.J0']

def test_tanimlayici_istatistikler():
    """Test basic descriptive statistics generation."""
    from scripts.evds_client import tanimlayici_istatistikler
    import pandas as pd
    import numpy as np
    df = pd.DataFrame({
        'A': [1.0, 2.0, 3.0, 4.0, 5.0],
        'B': [10, 20, 30, 40, np.nan]
    })
    df.index = pd.date_range('2020-01-01', periods=5)

    stats = tanimlayici_istatistikler(df)

    assert 'A' in stats
    assert 'B' in stats
    assert stats['A']['gozlem'] == 5
    assert stats['A']['ortalama'] == 3.0
    assert stats['B']['gozlem'] == 4
    assert stats['B']['min'] == 10.0

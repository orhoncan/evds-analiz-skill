import pytest
import pandas as pd
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

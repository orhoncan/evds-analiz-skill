import os
import pytest
from unittest.mock import MagicMock, patch
import sys


# Helper to provide dummy data for plotting functions
def get_dummy_data():
    import pandas as pd
    import numpy as np

    # We will create actual pandas DataFrame because mocking it deeply is difficult
    df = pd.DataFrame({'col1': [1, 2, 3]})
    df.index = pd.date_range('2023-01-01', periods=3)
    return df

@patch('builtins.open')
def test_dashboard_olustur_path_traversal(mock_open):
    from scripts.gelismis_analiz import dashboard_olustur
    import pandas as pd
    import numpy as np

    # We will mock internally within the function rather than at the decorator level
    # due to how pytest imports modules during collection vs execution
    with patch('scripts.gelismis_analiz.veri_kalitesi_kontrolu') as mock_kalite, \
         patch('scripts.gelismis_analiz.anomali_tespiti') as mock_anomali:

        # Mock return values for dependent functions
        mock_anomali.return_value = {}
        mock_kalite.return_value = {
            'puan': 100,
            'degerlendirme': 'Test',
            'genel': {'satir_sayisi': 3, 'sutun_sayisi': 1, 'eksik_oran': 0, 'eksik_toplam': 0}
        }

        # Create actual pandas DataFrame to avoid isinstance and other mocking issues
        df = pd.DataFrame({'col1': [1, 2, 3]})
        df.index = pd.date_range('2023-01-01', periods=3)

        # Payload with path traversal
        payload_dosya_adi = "../../../tmp/malicious_dashboard.html"

        returned_dosya_adi = dashboard_olustur(df, dosya_adi=payload_dosya_adi)

        # Assert return value is correctly sanitized
        assert returned_dosya_adi == "malicious_dashboard.html"
        # Assert file was opened with the sanitized name
        mock_open.assert_called_with("malicious_dashboard.html", 'w', encoding='utf-8')

@patch('builtins.open')
def test_cizgi_grafik_path_traversal(mock_open):
    from scripts.grafik import cizgi_grafik
    import pandas as pd

    df = pd.DataFrame({'col1': [1, 2, 3]})
    df.index = pd.date_range('2023-01-01', periods=3)

    # Payload with path traversal
    payload_dosya_adi = "/etc/passwd_grafik.html"

    returned_dosya_adi = cizgi_grafik(df, baslik="Test", dosya_adi=payload_dosya_adi)

    # Assert return value is correctly sanitized
    assert returned_dosya_adi == "passwd_grafik.html"
    # Assert file was opened with the sanitized name
    mock_open.assert_called_with("passwd_grafik.html", 'w', encoding='utf-8')

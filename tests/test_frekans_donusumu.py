import pytest
import pandas as pd
from scripts.gelismis_analiz import frekans_donusumu

@pytest.fixture
def daily_df_two_months():
    # Create a daily DatetimeIndex spanning two months: Jan 1 to Feb 10
    dates = pd.date_range(start="2024-01-01", end="2024-02-10", freq="D")
    df = pd.DataFrame({
        "A": range(1, len(dates) + 1), # values from 1 to 41
    }, index=dates)
    return df

def test_frekans_donusumu_mean(daily_df_two_months):
    # Jan 1 to Jan 31 -> 31 days. A values: 1 to 31. Mean: 16.0
    # Feb 1 to Feb 10 -> 10 days. A values: 32 to 41. Mean: 36.5
    result = frekans_donusumu(daily_df_two_months, 'MS', metot='mean')

    assert len(result) == 2
    assert result.index[0] == pd.Timestamp("2024-01-01")
    assert result.index[1] == pd.Timestamp("2024-02-01")
    assert result.iloc[0]["A"] == 16.0
    assert result.iloc[1]["A"] == 36.5

def test_frekans_donusumu_sum(daily_df_two_months):
    result = frekans_donusumu(daily_df_two_months, 'MS', metot='sum')
    assert result.iloc[0]["A"] == sum(range(1, 32))  # 496
    assert result.iloc[1]["A"] == sum(range(32, 42))  # 365

def test_frekans_donusumu_last(daily_df_two_months):
    result = frekans_donusumu(daily_df_two_months, 'MS', metot='last')
    assert result.iloc[0]["A"] == 31
    assert result.iloc[1]["A"] == 41

def test_frekans_donusumu_first(daily_df_two_months):
    result = frekans_donusumu(daily_df_two_months, 'MS', metot='first')
    assert result.iloc[0]["A"] == 1
    assert result.iloc[1]["A"] == 32

def test_frekans_donusumu_min(daily_df_two_months):
    result = frekans_donusumu(daily_df_two_months, 'MS', metot='min')
    assert result.iloc[0]["A"] == 1
    assert result.iloc[1]["A"] == 32

def test_frekans_donusumu_max(daily_df_two_months):
    result = frekans_donusumu(daily_df_two_months, 'MS', metot='max')
    assert result.iloc[0]["A"] == 31
    assert result.iloc[1]["A"] == 41

def test_frekans_donusumu_non_datetime_index():
    df = pd.DataFrame({"A": [1, 2, 3]})
    with pytest.raises(ValueError, match="DataFrame'in tarih indexi olmalı"):
        frekans_donusumu(df, 'MS')

def test_frekans_donusumu_unknown_method(daily_df_two_months):
    with pytest.raises(ValueError, match="Bilinmeyen metot: unknown"):
        frekans_donusumu(daily_df_two_months, 'MS', metot='unknown')

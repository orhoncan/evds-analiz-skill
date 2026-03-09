#!/usr/bin/env python3
"""
EVDS Grafik Modülü
orhon-viz tasarım ilkelerine uygun interaktif Plotly grafikleri.
"""

import os
import pandas as pd
import numpy as np
from typing import List, Dict, Union
import json
import html

# orhon-viz Renk Paleti
COLORS = {
    'primary': '#2C3E50',
    'secondary': '#34495E',
    'accent1': '#E74C3C',
    'accent2': '#3498DB',
    'accent3': '#F39C12',
    'accent4': '#16A085',
    'accent5': '#9B59B6',
    'accent6': '#27AE60',
    'background': '#FFFFFF',
    'grid': '#ECF0F1',
    'text': '#2C3E50',
    'text_secondary': '#95A5A6'
}

PALETTE = ['#2C3E50', '#E74C3C', '#3498DB', '#F39C12', '#16A085', '#9B59B6', '#27AE60']


def cizgi_grafik(
    df: pd.DataFrame,
    baslik: str,
    y_ekseni: str = "",
    dosya_adi: str = "grafik.html"
) -> str:
    """
    İnteraktif çizgi grafik oluşturur.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Tarih indexli veri
    baslik : str
        Grafik başlığı
    y_ekseni : str
        Y ekseni etiketi
    dosya_adi : str
        Çıktı dosya adı
    
    Returns:
    --------
    str
        HTML dosya yolu
    """
    # Veri hazırlığı
    traces = []
    for i, col in enumerate(df.columns):
        renk = PALETTE[i % len(PALETTE)]
        seri = df[col].dropna()
        
        trace = {
            'x': seri.index.strftime('%Y-%m-%d').tolist(),
            'y': seri.values.tolist(),
            'name': col,
            'type': 'scatter',
            'mode': 'lines',
            'line': {'color': renk, 'width': 2.5},
            'hovertemplate': f'<b>{col}</b><br>Tarih: %{{x}}<br>Değer: %{{y:.2f}}<extra></extra>'
        }
        traces.append(trace)
    
    layout = {
        'title': {
            'text': baslik,
            'font': {'size': 18, 'color': COLORS['primary'], 'family': 'Arial, sans-serif'},
            'x': 0,
            'xanchor': 'left'
        },
        'xaxis': {
            'title': {'text': 'Tarih', 'font': {'size': 12, 'color': COLORS['secondary']}},
            'gridcolor': COLORS['grid'],
            'linecolor': COLORS['text_secondary'],
            'tickfont': {'size': 10, 'color': COLORS['text_secondary']}
        },
        'yaxis': {
            'title': {'text': y_ekseni, 'font': {'size': 12, 'color': COLORS['secondary']}},
            'gridcolor': COLORS['grid'],
            'linecolor': COLORS['text_secondary'],
            'tickfont': {'size': 10, 'color': COLORS['text_secondary']}
        },
        'plot_bgcolor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'hovermode': 'x unified',
        'legend': {
            'orientation': 'h',
            'yanchor': 'bottom',
            'y': 1.02,
            'xanchor': 'left',
            'x': 0,
            'font': {'size': 11, 'color': COLORS['secondary']}
        },
        'margin': {'l': 60, 'r': 30, 't': 80, 'b': 60}
    }
    
    html_content = _html_sablonu(traces, layout, baslik)
    
    dosya_adi = os.path.basename(dosya_adi)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return dosya_adi


def coklu_eksen_grafik(
    df: pd.DataFrame,
    sol_seriler: List[str],
    sag_seriler: List[str],
    baslik: str,
    sol_etiket: str = "",
    sag_etiket: str = "",
    dosya_adi: str = "grafik_coklu.html"
) -> str:
    """
    İki Y eksenli grafik oluşturur.
    """
    traces = []
    
    # Sol eksen serileri
    for i, col in enumerate(sol_seriler):
        if col not in df.columns:
            continue
        seri = df[col].dropna()
        trace = {
            'x': seri.index.strftime('%Y-%m-%d').tolist(),
            'y': seri.values.tolist(),
            'name': col,
            'type': 'scatter',
            'mode': 'lines',
            'line': {'color': PALETTE[i], 'width': 2.5},
            'yaxis': 'y',
            'hovertemplate': f'<b>{col}</b><br>%{{y:.2f}}<extra></extra>'
        }
        traces.append(trace)
    
    # Sağ eksen serileri
    for i, col in enumerate(sag_seriler):
        if col not in df.columns:
            continue
        seri = df[col].dropna()
        trace = {
            'x': seri.index.strftime('%Y-%m-%d').tolist(),
            'y': seri.values.tolist(),
            'name': col,
            'type': 'scatter',
            'mode': 'lines',
            'line': {'color': PALETTE[len(sol_seriler) + i], 'width': 2.5, 'dash': 'dash'},
            'yaxis': 'y2',
            'hovertemplate': f'<b>{col}</b><br>%{{y:.2f}}<extra></extra>'
        }
        traces.append(trace)
    
    layout = {
        'title': {'text': baslik, 'font': {'size': 18, 'color': COLORS['primary']}, 'x': 0},
        'xaxis': {'gridcolor': COLORS['grid']},
        'yaxis': {
            'title': {'text': sol_etiket, 'font': {'color': PALETTE[0]}},
            'gridcolor': COLORS['grid'],
            'tickfont': {'color': PALETTE[0]}
        },
        'yaxis2': {
            'title': {'text': sag_etiket, 'font': {'color': PALETTE[len(sol_seriler)]}},
            'overlaying': 'y',
            'side': 'right',
            'tickfont': {'color': PALETTE[len(sol_seriler)]}
        },
        'plot_bgcolor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'legend': {'orientation': 'h', 'y': 1.1},
        'hovermode': 'x unified'
    }
    
    html_content = _html_sablonu(traces, layout, baslik)
    
    dosya_adi = os.path.basename(dosya_adi)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return dosya_adi


def korelasyon_matrisi_grafik(
    df: pd.DataFrame,
    baslik: str = "Korelasyon Matrisi",
    dosya_adi: str = "korelasyon.html"
) -> str:
    """
    Korelasyon matrisi ısı haritası oluşturur.
    """
    corr = df.corr()
    
    # Diverging renk skalası
    colorscale = [
        [0.0, '#E74C3C'],
        [0.25, '#F5B7B1'],
        [0.5, '#ECF0F1'],
        [0.75, '#AED6F1'],
        [1.0, '#3498DB']
    ]
    
    # Hover için metin
    hover_text = []
    for i, row in enumerate(corr.index):
        hover_row = []
        for j, col in enumerate(corr.columns):
            hover_row.append(f'{row} - {col}<br>r = {corr.iloc[i, j]:.3f}')
        hover_text.append(hover_row)
    
    trace = {
        'z': corr.values.tolist(),
        'x': corr.columns.tolist(),
        'y': corr.index.tolist(),
        'type': 'heatmap',
        'colorscale': colorscale,
        'zmin': -1,
        'zmax': 1,
        'text': hover_text,
        'hovertemplate': '%{text}<extra></extra>',
        'showscale': True,
        'colorbar': {'title': 'Korelasyon'}
    }
    
    # Değerleri hücrelere yaz
    annotations = []
    for i, row in enumerate(corr.index):
        for j, col in enumerate(corr.columns):
            val = corr.iloc[i, j]
            annotations.append({
                'x': col, 'y': row,
                'text': f'{val:.2f}',
                'font': {'color': 'white' if abs(val) > 0.5 else COLORS['text'], 'size': 12},
                'showarrow': False
            })
    
    layout = {
        'title': {'text': baslik, 'font': {'size': 18, 'color': COLORS['primary']}, 'x': 0},
        'annotations': annotations,
        'plot_bgcolor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'xaxis': {'tickangle': -45},
        'margin': {'l': 100, 'r': 50, 't': 80, 'b': 100}
    }
    
    html_content = _html_sablonu([trace], layout, baslik)
    
    dosya_adi = os.path.basename(dosya_adi)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return dosya_adi


def bar_grafik(
    kategoriler: List[str],
    degerler: List[float],
    baslik: str,
    y_ekseni: str = "",
    dosya_adi: str = "bar_grafik.html"
) -> str:
    """
    Bar grafik oluşturur.
    """
    # Renkleri değere göre ayarla (pozitif/negatif)
    renkler = [COLORS['accent4'] if v >= 0 else COLORS['accent1'] for v in degerler]
    
    trace = {
        'x': kategoriler,
        'y': degerler,
        'type': 'bar',
        'marker': {'color': renkler},
        'hovertemplate': '<b>%{x}</b><br>Değer: %{y:.2f}<extra></extra>'
    }
    
    layout = {
        'title': {'text': baslik, 'font': {'size': 18, 'color': COLORS['primary']}, 'x': 0},
        'xaxis': {'tickangle': -45, 'gridcolor': COLORS['grid']},
        'yaxis': {'title': {'text': y_ekseni}, 'gridcolor': COLORS['grid']},
        'plot_bgcolor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'margin': {'b': 100}
    }
    
    html_content = _html_sablonu([trace], layout, baslik)
    
    dosya_adi = os.path.basename(dosya_adi)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return dosya_adi


def mevsimsellik_grafik(
    tarihler: pd.DatetimeIndex,
    orijinal: pd.Series,
    trend: pd.Series,
    mevsimsel: pd.Series,
    artik: pd.Series,
    baslik: str = "Mevsimsellik Ayrıştırması",
    dosya_adi: str = "mevsimsellik.html"
) -> str:
    """
    STL decomposition sonuçlarını görselleştirir.
    """
    tarih_str = tarihler.strftime('%Y-%m-%d').tolist()
    
    traces = [
        {'x': tarih_str, 'y': orijinal.tolist(), 'name': 'Orijinal', 
         'type': 'scatter', 'mode': 'lines', 'line': {'color': COLORS['primary']}},
        {'x': tarih_str, 'y': trend.tolist(), 'name': 'Trend',
         'type': 'scatter', 'mode': 'lines', 'line': {'color': COLORS['accent2']}},
        {'x': tarih_str, 'y': mevsimsel.tolist(), 'name': 'Mevsimsel',
         'type': 'scatter', 'mode': 'lines', 'line': {'color': COLORS['accent3']}},
        {'x': tarih_str, 'y': artik.tolist(), 'name': 'Artık',
         'type': 'scatter', 'mode': 'lines', 'line': {'color': COLORS['text_secondary']}}
    ]
    
    layout = {
        'title': {'text': baslik, 'font': {'size': 18, 'color': COLORS['primary']}, 'x': 0},
        'grid': {'rows': 4, 'columns': 1, 'pattern': 'independent'},
        'plot_bgcolor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'showlegend': True,
        'legend': {'orientation': 'h', 'y': 1.05}
    }
    
    html_content = _html_sablonu(traces, layout, baslik)
    
    dosya_adi = os.path.basename(dosya_adi)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return dosya_adi


def tahmin_grafik(
    tarihler: pd.DatetimeIndex,
    gercek: pd.Series,
    tahmin: pd.Series,
    tahmin_tarihleri: pd.DatetimeIndex,
    alt_sinir: pd.Series = None,
    ust_sinir: pd.Series = None,
    baslik: str = "Tahmin",
    dosya_adi: str = "tahmin.html"
) -> str:
    """
    Gerçek değerler ve tahminleri görselleştirir.
    """
    tarih_str = tarihler.strftime('%Y-%m-%d').tolist()
    tahmin_tarih_str = tahmin_tarihleri.strftime('%Y-%m-%d').tolist()
    
    traces = [
        {'x': tarih_str, 'y': gercek.tolist(), 'name': 'Gerçek',
         'type': 'scatter', 'mode': 'lines', 'line': {'color': COLORS['primary'], 'width': 2.5}},
        {'x': tahmin_tarih_str, 'y': tahmin.tolist(), 'name': 'Tahmin',
         'type': 'scatter', 'mode': 'lines', 'line': {'color': COLORS['accent1'], 'width': 2, 'dash': 'dash'}}
    ]
    
    # Güven aralığı
    if alt_sinir is not None and ust_sinir is not None:
        traces.append({
            'x': tahmin_tarih_str + tahmin_tarih_str[::-1],
            'y': ust_sinir.tolist() + alt_sinir.tolist()[::-1],
            'fill': 'toself',
            'fillcolor': 'rgba(231, 76, 60, 0.2)',
            'line': {'color': 'rgba(255,255,255,0)'},
            'name': '95% Güven Aralığı',
            'showlegend': True
        })
    
    layout = {
        'title': {'text': baslik, 'font': {'size': 18, 'color': COLORS['primary']}, 'x': 0},
        'xaxis': {'gridcolor': COLORS['grid']},
        'yaxis': {'gridcolor': COLORS['grid']},
        'plot_bgcolor': COLORS['background'],
        'paper_bgcolor': COLORS['background'],
        'legend': {'orientation': 'h', 'y': 1.05},
        'hovermode': 'x unified'
    }
    
    html_content = _html_sablonu(traces, layout, baslik)
    
    dosya_adi = os.path.basename(dosya_adi)
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return dosya_adi


def _html_sablonu(traces: List[dict], layout: dict, baslik: str) -> str:
    """Plotly HTML şablonu oluşturur."""
    baslik_esc = html.escape(baslik)
    traces_json = json.dumps(traces).replace("<", r"\u003c")
    layout_json = json.dumps(layout).replace("<", r"\u003c")
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{baslik_esc}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: {COLORS['background']};
            color: {COLORS['text']};
        }}
        #grafik {{
            width: 100%;
            height: 600px;
        }}
        .baslik {{
            font-size: 14px;
            color: {COLORS['text_secondary']};
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="baslik">Kaynak: TCMB EVDS</div>
    <div id="grafik"></div>
    <script>
        var traces = {traces_json};
        var layout = {layout_json};
        var config = {{
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToRemove: ['lasso2d', 'select2d'],
            displaylogo: false,
            locale: 'tr'
        }};
        Plotly.newPlot('grafik', traces, layout, config);
    </script>
</body>
</html>"""


if __name__ == "__main__":
    print("Grafik modülü yüklendi.")
    print(f"Renk paleti: {PALETTE}")

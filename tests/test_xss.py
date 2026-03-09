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

def test_html_sablonu_xss_baslik():
    from scripts.grafik import _html_sablonu
    traces = [{'x': [1, 2], 'y': [3, 4]}]
    layout = {'title': 'Test'}
    baslik = "<script>alert('xss')</script>"

    html_content = _html_sablonu(traces, layout, baslik)

    assert "<script>alert('xss')</script>" not in html_content
    assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" in html_content

def test_html_sablonu_xss_traces_layout():
    from scripts.grafik import _html_sablonu
    traces = [{'name': "<script>alert('xss-trace')</script>"}]
    layout = {'title': "<script>alert('xss-layout')</script>"}
    baslik = "Normal Başlık"

    html_content = _html_sablonu(traces, layout, baslik)

    # In JS context, <script> should be replaced with \u003cscript>
    # So we don't expect the raw <script> tags to exist inside traces/layout JSON payload.
    assert "<script>alert('xss-trace')</script>" not in html_content
    assert "\\u003cscript>alert('xss-trace')\\u003c/script>" in html_content

    assert "<script>alert('xss-layout')</script>" not in html_content
    assert "\\u003cscript>alert('xss-layout')\\u003c/script>" in html_content

"""Unit tests for UI components and visualizations to ensure zero HTML escaping/leakage and valid choropleth output."""
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from src.components import empty_state, insight_line, kpi_card, page_header
from src.visualizations import choropleth_map


def test_kpi_card_renders_clean_html():
    """Verify that kpi_card produces clean HTML without markdown-breaking leading spaces."""
    with patch("streamlit.markdown") as mock_markdown:
        kpi_card("Total Movies", "45,083", subtitle="Full catalog", icon="🎬")
        assert mock_markdown.called
        call_args = mock_markdown.call_args
        html_content = call_args[0][0]
        kwargs = call_args[1]
        
        # Must enable unsafe_allow_html
        assert kwargs.get("unsafe_allow_html") is True
        # Must contain classes and values
        assert "Total Movies" in html_content
        assert "45,083" in html_content
        assert "Full catalog" in html_content
        assert "🎬" in html_content
        # Must not contain raw indented lines starting with 4+ spaces that break markdown
        for line in html_content.splitlines():
            assert not line.startswith("    <div")


def test_empty_state_and_insight_line_rendering():
    """Verify empty_state and insight_line render clean HTML with unsafe_allow_html=True."""
    with patch("streamlit.markdown") as mock_markdown:
        empty_state("No data", "Adjust filters")
        assert mock_markdown.call_args[1].get("unsafe_allow_html") is True
        
        insight_line("Revenue was $100M")
        assert mock_markdown.call_args[1].get("unsafe_allow_html") is True


def test_choropleth_map_iso3_conversion():
    """Verify that choropleth_map correctly converts ISO-2 to ISO-3 and assigns data."""
    test_df = pd.DataFrame({
        "country_name": ["United States", "India", "United Kingdom"],
        "iso_3166_1": ["US", "IN", "GB"],
        "movie_count": [100, 80, 60]
    })
    fig = choropleth_map(test_df, locations="iso_3166_1", z="movie_count", hover_name="country_name")
    assert len(fig.data) == 1
    trace = fig.data[0]
    assert list(trace.locations) == ["USA", "IND", "GBR"]
    assert list(trace.z) == [100, 80, 60]
    assert trace.locationmode == "ISO-3"

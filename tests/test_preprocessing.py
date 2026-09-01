"""Unit tests for data preprocessing and transformations."""
import numpy as np
import pandas as pd
import pytest

from src.preprocessing import clean_credits, clean_keywords, clean_movies_metadata, safe_parse_json
from src.transformations import add_financial_metrics, build_display_strings


def test_safe_parse_json():
    """Verify safe JSON parsing under valid, malformed, and empty inputs."""
    assert safe_parse_json("[{'id': 1, 'name': 'Action'}]") == [{'id': 1, 'name': 'Action'}]
    assert safe_parse_json("{'id': 1, 'name': 'Action'}") == [{'id': 1, 'name': 'Action'}]
    assert safe_parse_json("[]") == []
    assert safe_parse_json("") == []
    assert safe_parse_json(None) == []
    assert safe_parse_json("corrupted python syntax { [") == []


def test_clean_movies_metadata_malformed_and_zeros():
    """Verify malformed row removal, zero-to-NaN conversion, and status filtering."""
    raw_data = {
        "id": ["100", "1997-08-20", "200", "200", "300"],  # one malformed date, one duplicate '200'
        "title": ["Movie 1", "Corrupt Movie", "Movie 2 Duplicate A", "Movie 2 Duplicate B", "Movie 3 Planned"],
        "budget": ["0", "5000000", "10000000", "10000000", "2000000"],
        "revenue": ["0", "15000000", "25000000", "25000000", "0"],
        "runtime": ["0", "120", "95", "95", "110"],
        "vote_average": ["7.5", "6.0", "8.0", "8.0", "5.0"],
        "vote_count": ["100", "50", "250", "250", "10"],
        "popularity": ["15.5", "10.0", "25.0", "25.0", "5.0"],
        "release_date": ["2010-05-15", "1997-08-20", "2015-11-20", "2015-11-20", "2020-01-01"],
        "status": ["Released", "Released", "Released", "Released", "Planned"],
        "overview": ["Test 1", "Test corrupt", "Test 2", "Test 2", "Test 3"],
        "tagline": ["Tag 1", "Tag corrupt", "Tag 2", None, "Tag 3"]
    }
    raw_df = pd.DataFrame(raw_data)
    
    cleaned = clean_movies_metadata(raw_df)
    
    # 1. Malformed row (date string in id) must be dropped
    assert 1997 not in cleaned["movie_id"].values
    
    # 2. Planned status must be excluded
    assert 300 not in cleaned["movie_id"].values
    
    # 3. Duplicate '200' must be deduplicated to 1 row
    assert (cleaned["movie_id"] == 200).sum() == 1
    
    # 4. Budget == 0 and Revenue == 0 must be converted to NaN
    m1 = cleaned[cleaned["movie_id"] == 100].iloc[0]
    assert np.isnan(m1["budget"])
    assert np.isnan(m1["revenue"])
    assert np.isnan(m1["runtime"])
    
    # 5. Derived release_year must match
    assert m1["release_year"] == 2010
    assert m1["release_decade"] == 2010


def test_add_financial_metrics():
    """Verify profit and ROI calculations strictly operate on valid positive numbers."""
    df = pd.DataFrame({
        "budget": [100.0, np.nan, 50.0, 0.0],
        "revenue": [250.0, 100.0, np.nan, 0.0]
    })
    
    res = add_financial_metrics(df)
    
    # Row 0: valid both -> profit = 150, roi = 1.5
    assert res.loc[0, "profit"] == 150.0
    assert res.loc[0, "roi"] == 1.5
    
    # Row 1, 2, 3: missing one or both -> NaN
    assert np.isnan(res.loc[1, "profit"])
    assert np.isnan(res.loc[1, "roi"])
    assert np.isnan(res.loc[2, "profit"])
    assert np.isnan(res.loc[2, "roi"])
    assert np.isnan(res.loc[3, "profit"])
    assert np.isnan(res.loc[3, "roi"])

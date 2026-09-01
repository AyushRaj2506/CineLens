"""Unit tests for the rule-based insight engine."""
import pandas as pd
import pytest

from src.insights import generate_insights, rule_most_common_genre


def test_insight_engine_empty_input():
    """Verify that insight engine returns an empty list on empty dataframe."""
    empty_df = pd.DataFrame()
    insights = generate_insights("overview", empty_df, empty_df, empty_df, empty_df)
    assert insights == []


def test_rule_most_common_genre():
    """Verify most common genre rule calculates correctly."""
    movies_df = pd.DataFrame([
        {"movie_id": 1},
        {"movie_id": 2},
        {"movie_id": 3}
    ])
    genre_bridge = pd.DataFrame([
        {"movie_id": 1, "genre_name": "Drama"},
        {"movie_id": 2, "genre_name": "Drama"},
        {"movie_id": 3, "genre_name": "Action"}
    ])
    
    sentence = rule_most_common_genre(movies_df, genre_bridge)
    assert sentence is not None
    assert "Drama" in sentence
    assert "66.7%" in sentence

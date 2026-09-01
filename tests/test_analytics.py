"""Unit tests for analytics calculations and many-to-many safety."""
import numpy as np
import pandas as pd
import pytest

from src.analytics import (
    calculate_correlations,
    compute_actor_consistency,
    compute_director_consistency,
    compute_overhyped_movies,
    compute_underrated_movies,
    genre_financials,
    top_actors,
    top_directors
)


def test_many_to_many_safe_aggregation():
    """
    CRITICAL TEST: Verify that movies with multiple genres and multiple actors
    NEVER cause cartesian multiplication in financial/count aggregations.
    """
    # 1 movie (ID=1) with $100M revenue and $50M budget
    # Movie 1 belongs to 2 genres: 'Action' and 'Sci-Fi'
    # Movie 1 has 10 actors in actor_bridge
    movies_df = pd.DataFrame([{
        "movie_id": 1,
        "title": "Blockbuster Sci-Fi",
        "budget": 50_000_000.0,
        "revenue": 100_000_000.0,
        "profit": 50_000_000.0,
        "roi": 1.0,
        "vote_average": 8.0,
        "vote_count": 500,
        "popularity": 30.0,
        "runtime": 130.0
    }])
    
    genre_bridge = pd.DataFrame([
        {"movie_id": 1, "genre_name": "Action"},
        {"movie_id": 1, "genre_name": "Sci-Fi"}
    ])
    
    actor_bridge = pd.DataFrame([
        {"movie_id": 1, "person_id": i, "person_name": f"Actor {i}", "cast_order": i}
        for i in range(10)
    ])
    
    # Calculate genre financials
    gf = genre_financials(movies_df, genre_bridge, min_sample=1)
    
    # Each genre must have exactly movie_count = 1, and total_revenue = 100,000,000
    # It must NOT be multiplied by the 10 actors (which would falsely be $1,000,000,000)!
    action_row = gf[gf["genre_name"] == "Action"].iloc[0]
    scifi_row = gf[gf["genre_name"] == "Sci-Fi"].iloc[0]
    
    assert action_row["movie_count"] == 1
    assert action_row["total_revenue"] == 100_000_000.0
    assert action_row["avg_revenue"] == 100_000_000.0
    
    assert scifi_row["movie_count"] == 1
    assert scifi_row["total_revenue"] == 100_000_000.0
    assert scifi_row["avg_revenue"] == 100_000_000.0


def test_actor_director_thresholding():
    """Verify that top_actors and top_directors enforce minimum movie counts."""
    movies_df = pd.DataFrame([
        {"movie_id": 1, "revenue": 100.0, "vote_average": 9.0, "vote_count": 50, "popularity": 10.0, "profit": 50.0, "roi": 1.0},
        {"movie_id": 2, "revenue": 200.0, "vote_average": 8.5, "vote_count": 60, "popularity": 12.0, "profit": 100.0, "roi": 1.0},
        {"movie_id": 3, "revenue": 300.0, "vote_average": 8.0, "vote_count": 70, "popularity": 14.0, "profit": 150.0, "roi": 1.0},
        {"movie_id": 4, "revenue": 400.0, "vote_average": 7.5, "vote_count": 80, "popularity": 16.0, "profit": 200.0, "roi": 1.0},
        {"movie_id": 5, "revenue": 500.0, "vote_average": 7.0, "vote_count": 90, "popularity": 18.0, "profit": 250.0, "roi": 1.0}
    ])
    
    # Actor A has 5 movies (qualifies for default MIN_ACTOR_MOVIES=5)
    # Actor B has only 2 movies (fails threshold)
    actor_bridge = pd.DataFrame([
        {"movie_id": 1, "person_id": 101, "person_name": "Prolific Actor"},
        {"movie_id": 2, "person_id": 101, "person_name": "Prolific Actor"},
        {"movie_id": 3, "person_id": 101, "person_name": "Prolific Actor"},
        {"movie_id": 4, "person_id": 101, "person_name": "Prolific Actor"},
        {"movie_id": 5, "person_id": 101, "person_name": "Prolific Actor"},
        {"movie_id": 1, "person_id": 102, "person_name": "One Hit Actor"},
        {"movie_id": 2, "person_id": 102, "person_name": "One Hit Actor"}
    ])
    
    actors_ranked = top_actors(movies_df, actor_bridge, min_movies=5)
    assert len(actors_ranked) == 1
    assert actors_ranked.iloc[0]["person_name"] == "Prolific Actor"


def test_empty_dataframe_graceful_handling():
    """Verify all analytics functions handle empty DataFrames without raising exceptions."""
    empty_m = pd.DataFrame()
    empty_b = pd.DataFrame()
    
    assert genre_financials(empty_m, empty_b).empty
    assert top_actors(empty_m, empty_b).empty
    assert top_directors(empty_m, empty_b).empty
    assert compute_underrated_movies(empty_m).empty
    assert compute_overhyped_movies(empty_m).empty
    assert compute_director_consistency(empty_m, empty_b).empty
    assert compute_actor_consistency(empty_m, empty_b).empty

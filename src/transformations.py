"""Data transformation functions for feature engineering and metrics calculation."""
import numpy as np
import pandas as pd

def add_financial_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute profit and ROI strictly where both budget and revenue are valid (>0 and non-null).
    Otherwise profit and roi are set to NaN.
    """
    df = df.copy()
    valid_financials = (df["budget"].notna()) & (df["budget"] > 0) & (df["revenue"].notna()) & (df["revenue"] > 0)
    
    df["profit"] = np.nan
    df.loc[valid_financials, "profit"] = df.loc[valid_financials, "revenue"] - df.loc[valid_financials, "budget"]
    
    df["roi"] = np.nan
    df.loc[valid_financials, "roi"] = (
        (df.loc[valid_financials, "revenue"] - df.loc[valid_financials, "budget"]) / df.loc[valid_financials, "budget"]
    )
    
    return df

def build_display_strings(
    movies_df: pd.DataFrame,
    genre_bridge: pd.DataFrame,
    keyword_bridge: pd.DataFrame,
    director_bridge: pd.DataFrame,
    actor_bridge: pd.DataFrame
) -> pd.DataFrame:
    """
    Precompute denormalized display strings for the movie explorer & detail views.
    Ensures zero string operations or JSON parsing at Streamlit runtime.
    """
    df = movies_df.copy()
    
    # Genres display: comma-separated list of genre names
    if not genre_bridge.empty:
        genres_grp = genre_bridge.groupby("movie_id")["genre_name"].apply(lambda s: ", ".join(s.dropna().astype(str)))
        df["genres_display"] = df["movie_id"].map(genres_grp).fillna("Not specified")
    else:
        df["genres_display"] = "Not specified"
        
    # Keywords display: comma-separated list of top keywords (up to 10 for display)
    if not keyword_bridge.empty:
        keywords_grp = keyword_bridge.groupby("movie_id")["keyword_name"].apply(lambda s: ", ".join(s.dropna().astype(str).iloc[:10]))
        df["keywords_display"] = df["movie_id"].map(keywords_grp).fillna("No keywords recorded")
    else:
        df["keywords_display"] = "No keywords recorded"
        
    # Directors display: comma-separated list of directors
    if not director_bridge.empty:
        director_grp = director_bridge.groupby("movie_id")["person_name"].apply(lambda s: ", ".join(s.dropna().astype(str)))
        df["director_display"] = df["movie_id"].map(director_grp).fillna("Not credited")
    else:
        df["director_display"] = "Not credited"
        
    # Top cast display: top 5 billed cast members
    if not actor_bridge.empty:
        # actor_bridge is already cast_order < 10, pick top 5
        top_actors = actor_bridge[actor_bridge["cast_order"] < 5].sort_values("cast_order")
        actor_grp = top_actors.groupby("movie_id")["person_name"].apply(lambda s: ", ".join(s.dropna().astype(str)))
        df["top_cast_display"] = df["movie_id"].map(actor_grp).fillna("Not credited")
    else:
        df["top_cast_display"] = "Not credited"
        
    return df

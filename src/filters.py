"""Global filter system for CineLens Analytics with lazy-loading support."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import pandas as pd
import streamlit as st

from src.utils import VALID_GENRES, VOTE_COUNT_MIN

# Precomputed top production countries for instant filter population without scanning bridge tables
TOP_PRECOMPUTED_COUNTRIES = [
    "United States of America", "United Kingdom", "France", "Germany", "Italy",
    "Canada", "Japan", "Spain", "India", "Hong Kong",
    "Australia", "South Korea", "Russia", "China", "Mexico",
    "Sweden", "Netherlands", "Belgium", "Denmark", "Brazil"
]


@dataclass
class FilterState:
    year_range: Tuple[int, int] = (1900, 2025)
    genres: List[str] = field(default_factory=list)
    countries: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    min_rating: float = 0.0
    min_popularity: float = 0.0


def rated_movies(df: pd.DataFrame, min_votes: int = VOTE_COUNT_MIN) -> pd.DataFrame:
    """Helper to filter movies with statistically reliable vote counts."""
    if df.empty or "vote_count" not in df.columns:
        return df
    return df[df["vote_count"].fillna(0) >= min_votes]


def render_global_filters(
    movies_df: pd.DataFrame,
    genre_bridge: Optional[pd.DataFrame] = None,
    country_bridge: Optional[pd.DataFrame] = None
) -> FilterState:
    """
    Render global filter controls in the Streamlit sidebar.
    Optimized to require ONLY the fact table (movies_df), avoiding heavy bridge table scans.
    Optional bridge parameters are accepted for backward compatibility.
    """
    st.sidebar.markdown("### 🔍 Global Catalog Filters")
    
    # Calculate dataset boundaries dynamically from fact table
    min_year_data = int(movies_df["release_year"].dropna().min()) if not movies_df["release_year"].dropna().empty else 1900
    max_year_data = int(movies_df["release_year"].dropna().max()) if not movies_df["release_year"].dropna().empty else 2025
    
    # Year Range Slider
    year_range = st.sidebar.slider(
        "Release Year Range",
        min_value=min_year_data,
        max_value=max_year_data,
        value=(max(1970, min_year_data), max_year_data),
        step=1,
        help="Filters catalog by release year."
    )
    
    # Genre Multiselect from closed taxonomy (no bridge table scan needed!)
    selected_genres = st.sidebar.multiselect(
        "Genres",
        options=VALID_GENRES,
        default=[],
        help="Select one or more genres to include."
    )
    
    # Language Multiselect (top 15 from fact table)
    top_langs = (
        movies_df["original_language"].value_counts().head(15).index.tolist()
        if "original_language" in movies_df.columns else []
    )
    selected_langs = st.sidebar.multiselect(
        "Original Language",
        options=top_langs,
        default=[],
        help="Filter by movie original language code (e.g. 'en', 'fr', 'ja')."
    )
    
    # Country Multiselect
    selected_countries = st.sidebar.multiselect(
        "Production Country",
        options=TOP_PRECOMPUTED_COUNTRIES,
        default=[],
        help="Filter by primary production country."
    )
    
    # Rating & Popularity threshold sliders
    col1, col2 = st.sidebar.columns(2)
    with col1:
        min_rating = st.slider("Min Rating ★", 0.0, 10.0, 0.0, 0.5)
    with col2:
        min_pop = st.slider("Min Popularity", 0.0, 50.0, 0.0, 2.0)
        
    state = FilterState(
        year_range=year_range,
        genres=selected_genres,
        countries=selected_countries,
        languages=selected_langs,
        min_rating=min_rating,
        min_popularity=min_pop
    )
    st.session_state["global_filters"] = state
    return state


def apply_global_filters(
    movies_df: pd.DataFrame,
    filter_state: FilterState,
    genre_bridge: Optional[pd.DataFrame] = None,
    country_bridge: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Apply global filter conditions vectorized across the movies fact table.
    Ensures zero duplicate rows and sub-second response times.
    """
    if movies_df.empty:
        return movies_df
        
    mask = pd.Series(True, index=movies_df.index)
    
    # 1. Year filter
    if "release_year" in movies_df.columns and filter_state.year_range:
        y_min, y_max = filter_state.year_range
        year_valid = movies_df["release_year"].notna()
        mask &= year_valid & (movies_df["release_year"] >= y_min) & (movies_df["release_year"] <= y_max)
        
    # 2. Rating filter
    if filter_state.min_rating > 0 and "vote_average" in movies_df.columns:
        mask &= movies_df["vote_average"].fillna(0) >= filter_state.min_rating
        
    # 3. Popularity filter
    if filter_state.min_popularity > 0 and "popularity" in movies_df.columns:
        mask &= movies_df["popularity"].fillna(0) >= filter_state.min_popularity
        
    # 4. Language filter
    if filter_state.languages and "original_language" in movies_df.columns:
        mask &= movies_df["original_language"].isin(filter_state.languages)
        
    # 5. Fast genre check on precomputed genres_display string (fallback if bridge not passed)
    if filter_state.genres:
        if genre_bridge is not None and not genre_bridge.empty:
            matching_movie_ids = genre_bridge[genre_bridge["genre_name"].isin(filter_state.genres)]["movie_id"].unique()
            mask &= movies_df["movie_id"].isin(matching_movie_ids)
        elif "genres_display" in movies_df.columns:
            genre_pattern = "|".join(filter_state.genres)
            mask &= movies_df["genres_display"].fillna("").str.contains(genre_pattern, case=False, regex=True)
            
    # 6. Country bridge filter (optional lazy)
    if filter_state.countries and country_bridge is not None and not country_bridge.empty:
        matching_movie_ids = country_bridge[country_bridge["country_name"].isin(filter_state.countries)]["movie_id"].unique()
        mask &= movies_df["movie_id"].isin(matching_movie_ids)
        
    return movies_df[mask].copy()

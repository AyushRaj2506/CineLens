"""Global filter system for CineLens Analytics (Compact & Performance Optimized)."""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
import pandas as pd
import streamlit as st

from src.components import render_sidebar_brand
from src.utils import VALID_GENRES, VOTE_COUNT_MIN

# Precomputed top production countries to avoid runtime bridge scans
TOP_PRECOMPUTED_COUNTRIES = [
    "United States of America", "United Kingdom", "France", "Germany",
    "Italy", "Canada", "Japan", "Spain", "Russia", "India",
    "Hong Kong", "Australia", "China", "South Korea", "Sweden"
]


@dataclass
class FilterState:
    """Represents the global filter criteria active across the dashboard."""
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
    render_sidebar_brand()
    
    st.sidebar.markdown(
        '<div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.08em; margin: 0.75rem 0 0.5rem 0;">Catalog Filters</div>',
        unsafe_allow_html=True
    )
    
    # Calculate dataset boundaries dynamically from fact table
    min_year_data = int(movies_df["release_year"].dropna().min()) if not movies_df["release_year"].dropna().empty else 1900
    max_year_data = int(movies_df["release_year"].dropna().max()) if not movies_df["release_year"].dropna().empty else 2025
    
    # Year Range Slider
    year_range = st.sidebar.slider(
        "Release Year",
        min_value=min_year_data,
        max_value=max_year_data,
        value=(max(1970, min_year_data), max_year_data),
        step=1
    )
    
    # Genre Multiselect from closed taxonomy
    selected_genres = st.sidebar.multiselect(
        "Genres",
        options=VALID_GENRES,
        default=[]
    )
    
    # Country Multiselect
    selected_countries = st.sidebar.multiselect(
        "Production Country",
        options=TOP_PRECOMPUTED_COUNTRIES,
        default=[]
    )
    
    # Language Multiselect (top 15)
    top_langs = (
        movies_df["original_language"].value_counts().head(15).index.tolist()
        if "original_language" in movies_df.columns else []
    )
    selected_langs = st.sidebar.multiselect(
        "Language Code",
        options=top_langs,
        default=[]
    )
    
    # Advanced Filters in compact expander to prevent scroll overload
    with st.sidebar.expander("⚙️ Advanced Thresholds", expanded=False):
        min_rating = st.slider("Min Rating (★)", 0.0, 10.0, 0.0, 0.5)
        min_pop = st.slider("Min Popularity", 0.0, 50.0, 0.0, 2.0)
        
    state = FilterState(
        year_range=year_range,
        genres=selected_genres,
        countries=selected_countries,
        languages=selected_langs,
        min_rating=min_rating,
        min_popularity=min_pop
    )
    return state


def apply_global_filters(
    movies_df: pd.DataFrame,
    filters: FilterState,
    genre_bridge: Optional[pd.DataFrame] = None,
    country_bridge: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Apply filter state to the movies fact table in a vectorized, zero-copy fashion.
    """
    if movies_df.empty:
        return movies_df
        
    df = movies_df
    
    # 1. Year range
    if "release_year" in df.columns and filters.year_range:
        mask = (df["release_year"] >= filters.year_range[0]) & (df["release_year"] <= filters.year_range[1])
        # Preserve NaNs in release_year only if year_range covers the min dataset boundary
        min_dataset_year = int(df["release_year"].dropna().min()) if not df["release_year"].dropna().empty else 1900
        if filters.year_range[0] <= min_dataset_year:
            mask = mask | df["release_year"].isna()
        df = df[mask]

    # 2. Genres
    if filters.genres:
        if genre_bridge is not None and not genre_bridge.empty:
            matching_ids = genre_bridge[genre_bridge["genre_name"].isin(filters.genres)]["movie_id"].unique()
            df = df[df["movie_id"].isin(matching_ids)]
        elif "genres_display" in df.columns:
            genre_pattern = "|".join([g.replace(" ", r"\s") for g in filters.genres])
            df = df[df["genres_display"].str.contains(genre_pattern, case=False, na=False, regex=True)]

    # 3. Production Countries
    if filters.countries:
        if country_bridge is not None and not country_bridge.empty:
            matching_ids = country_bridge[country_bridge["country_name"].isin(filters.countries)]["movie_id"].unique()
            df = df[df["movie_id"].isin(matching_ids)]
        elif "countries_display" in df.columns:
            country_pattern = "|".join([c.replace(" ", r"\s") for c in filters.countries])
            df = df[df["countries_display"].str.contains(country_pattern, case=False, na=False, regex=True)]

    # 4. Languages
    if filters.languages and "original_language" in df.columns:
        df = df[df["original_language"].isin(filters.languages)]

    # 5. Rating threshold
    if filters.min_rating > 0.0 and "vote_average" in df.columns:
        df = df[df["vote_average"].fillna(0) >= filters.min_rating]

    # 6. Popularity threshold
    if filters.min_popularity > 0.0 and "popularity" in df.columns:
        df = df[df["popularity"].fillna(0) >= filters.min_popularity]

    return df

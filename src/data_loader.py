"""Data loader module with Streamlit caching and lazy-loading for Parquet files."""
from pathlib import Path
import pandas as pd
import streamlit as st

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"


@st.cache_data(ttl=None, show_spinner=False)
def load_movies() -> pd.DataFrame:
    """Load the main movie fact table."""
    file_path = PROCESSED_DIR / "movies.parquet"
    if not file_path.exists():
        raise FileNotFoundError(f"Missing processed data file: {file_path}. Run scripts/preprocess.py first.")
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_overview_kpis() -> pd.DataFrame:
    """Load precomputed single-row overview KPIs table."""
    file_path = PROCESSED_DIR / "overview_kpis.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_genre_summary() -> pd.DataFrame:
    """Load precomputed genre analytical summary."""
    file_path = PROCESSED_DIR / "genre_summary.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_yearly_summary() -> pd.DataFrame:
    """Load precomputed yearly volume and financial summary."""
    file_path = PROCESSED_DIR / "yearly_summary.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_country_summary() -> pd.DataFrame:
    """Load precomputed country production summary."""
    file_path = PROCESSED_DIR / "country_summary.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_keyword_summary() -> pd.DataFrame:
    """Load precomputed keyword thematic summary."""
    file_path = PROCESSED_DIR / "keyword_summary.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_actor_summary() -> pd.DataFrame:
    """Load precomputed top actor rankings."""
    file_path = PROCESSED_DIR / "actor_summary.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_director_summary() -> pd.DataFrame:
    """Load precomputed top director rankings."""
    file_path = PROCESSED_DIR / "director_summary.parquet"
    if not file_path.exists():
        return pd.DataFrame()
    return pd.read_parquet(file_path)


# Lazy Bridge Table Loaders (Loaded strictly on-demand)
@st.cache_data(ttl=None, show_spinner=False)
def load_genre_bridge() -> pd.DataFrame:
    file_path = PROCESSED_DIR / "genre_bridge.parquet"
    if not file_path.exists():
        return pd.DataFrame(columns=["movie_id", "genre_id", "genre_name"])
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_country_bridge() -> pd.DataFrame:
    file_path = PROCESSED_DIR / "country_bridge.parquet"
    if not file_path.exists():
        return pd.DataFrame(columns=["movie_id", "iso_3166_1", "country_name"])
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_keyword_bridge() -> pd.DataFrame:
    file_path = PROCESSED_DIR / "keyword_bridge.parquet"
    if not file_path.exists():
        return pd.DataFrame(columns=["movie_id", "keyword_id", "keyword_name"])
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_actor_bridge() -> pd.DataFrame:
    file_path = PROCESSED_DIR / "actor_bridge.parquet"
    if not file_path.exists():
        return pd.DataFrame(columns=["movie_id", "person_id", "person_name", "character", "cast_order"])
    return pd.read_parquet(file_path)


@st.cache_data(ttl=None, show_spinner=False)
def load_director_bridge() -> pd.DataFrame:
    file_path = PROCESSED_DIR / "director_bridge.parquet"
    if not file_path.exists():
        return pd.DataFrame(columns=["movie_id", "person_id", "person_name"])
    return pd.read_parquet(file_path)

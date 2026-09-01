"""CineLens Analytics — Main Application Portal & Shell."""
from pathlib import Path
import streamlit as st

from src.components import filter_status_bar, inject_custom_css, kpi_card, page_header
from src.data_loader import load_movies, load_overview_kpis
from src.filters import apply_global_filters, render_global_filters
from src.utils import format_currency, format_number

# 1. Page Configuration
st.set_page_config(
    page_title="CineLens Analytics — Movie Intelligence Platform",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Central Design System
inject_custom_css()

# 3. Check for preprocessed data
processed_movies_file = Path("data/processed/movies.parquet")
if not processed_movies_file.exists():
    st.error("⚠️ Processed dataset not found! Please run `python scripts/preprocess.py` to generate optimized Parquet files.")
    st.stop()

# 4. Lazy Load Fact Table
movies_df = load_movies()

# 5. Render Global Sidebar Filters
filters = render_global_filters(movies_df)
filtered_movies = apply_global_filters(movies_df, filters)

# 6. Hero Page Header
page_header(
    title="Executive Movie Intelligence",
    subtitle="Interactive analytical dashboard exploring box office outcomes, creative talent, genre dynamics, and global production trends across 45,000+ films.",
    eyebrow="PLATFORM PORTAL"
)

# 7. Active Filter Status Strip
filter_status_bar(filters, len(movies_df), len(filtered_movies))

# 8. Core KPI Summary Row
col1, col2, col3, col4, col5 = st.columns(5)
is_default = (len(filtered_movies) == len(movies_df))

if is_default:
    kpi_df = load_overview_kpis()
    if not kpi_df.empty:
        k_row = kpi_df.iloc[0]
        with col1: kpi_card("Catalog Titles", format_number(k_row["total_movies"]), subtitle="Full archive", icon="🎞️")
        with col2: kpi_card("Total Box Office", format_currency(k_row["total_revenue"]), subtitle="7,014 reporting", icon="💰")
        with col3: kpi_card("Avg Revenue / Film", format_currency(k_row["avg_revenue"]), subtitle="Non-zero revenue", icon="💵")
        with col4: kpi_card("Avg Rating", f"{k_row['avg_rating']:.2f} ★", subtitle="Votes ≥ 20", icon="⭐")
        with col5: kpi_card("Avg Popularity", f"{k_row['avg_popularity']:.1f}", subtitle="TMDB score", icon="🔥")
    else:
        with col1: kpi_card("Catalog Titles", format_number(len(filtered_movies)), subtitle="Full archive", icon="🎞️")
        with col2: kpi_card("Total Box Office", format_currency(filtered_movies.loc[filtered_movies["revenue"] > 0, "revenue"].sum()), icon="💰")
        with col3: kpi_card("Avg Revenue", format_currency(filtered_movies.loc[filtered_movies["revenue"] > 0, "revenue"].mean()), icon="💵")
        with col4: kpi_card("Avg Rating", f"{filtered_movies.loc[filtered_movies['vote_count'] >= 20, 'vote_average'].mean():.2f} ★", icon="⭐")
        with col5: kpi_card("Avg Popularity", f"{filtered_movies['popularity'].mean():.1f}", icon="🔥")
else:
    rev_sub = filtered_movies[filtered_movies["revenue"] > 0]
    rate_sub = filtered_movies[filtered_movies["vote_count"] >= 20]
    with col1: kpi_card("Filtered Titles", format_number(len(filtered_movies)), subtitle=f"of {len(movies_df):,} total", icon="🎞️")
    with col2: kpi_card("Total Box Office", format_currency(rev_sub["revenue"].sum() if not rev_sub.empty else 0), subtitle=f"{len(rev_sub):,} reporting", icon="💰")
    with col3: kpi_card("Avg Revenue", format_currency(rev_sub["revenue"].mean() if not rev_sub.empty else None), subtitle="In filtered scope", icon="💵")
    with col4: kpi_card("Avg Rating", f"{rate_sub['vote_average'].mean():.2f} ★" if not rate_sub.empty else "N/A", subtitle="Votes ≥ 20", icon="⭐")
    with col5: kpi_card("Avg Popularity", f"{filtered_movies['popularity'].mean():.1f}" if "popularity" in filtered_movies.columns else "N/A", subtitle="TMDB score", icon="🔥")

st.markdown("<br>", unsafe_allow_html=True)

# 9. Quick Launch Navigation Cards
st.markdown('<div style="font-size: 1.15rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.85rem;">Analytical Suites</div>', unsafe_allow_html=True)

nc1, nc2, nc3 = st.columns(3)
with nc1:
    st.markdown("""
    <div class="kpi-card" style="min-height: 140px;">
        <div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.35rem;">1. Executive Overview</div>
        <div style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.4;">Macro release trends, box office trajectory, rating distributions, and automated insights.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="kpi-card" style="min-height: 140px; margin-top: 0.75rem;">
        <div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.35rem;">4. Talent Intelligence</div>
        <div style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.4;">Director & Actor career track records, leaderboards, and interactive filmography timelines.</div>
    </div>
    """, unsafe_allow_html=True)

with nc2:
    st.markdown("""
    <div class="kpi-card" style="min-height: 140px;">
        <div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.35rem;">2. Movie Explorer</div>
        <div style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.4;">Instant vectorized title search, pagination, and comprehensive individual film intelligence profiles.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="kpi-card" style="min-height: 140px; margin-top: 0.75rem;">
        <div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.35rem;">5. Genres & Themes</div>
        <div style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.4;">Relational-safe cross-genre box office benchmarks and narrative plot keyword clustering.</div>
    </div>
    """, unsafe_allow_html=True)

with nc3:
    st.markdown("""
    <div class="kpi-card" style="min-height: 140px;">
        <div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.35rem;">3. Performance & Economics</div>
        <div style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.4;">Gross revenues, net profits, high-ROI multipliers, and WebGL Budget-Revenue regressions.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="kpi-card" style="min-height: 140px; margin-top: 0.75rem;">
        <div style="font-size: 1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.35rem;">6. Trends & Geography</div>
        <div style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.4;">Decadal genre evolutions and international ISO-3166-1 choropleth production footprint.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
with st.expander("ℹ️ Data Architecture & Pipeline Audit"):
    st.markdown("""
    - **Source Catalog**: 45,083 unique feature films deduplicated from TMDB.
    - **Zero Runtime JSON**: All JSON structures pre-exploded into relational Parquet bridge tables.
    - **Safe Financials**: Converted unverified 0 values to `NaN` to prevent metric distortion.
    - **Thresholding**: Minimum 20 votes required for statistical rating metrics.
    """)

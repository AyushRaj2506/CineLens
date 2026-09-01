"""CineLens Analytics — Main Application Shell & Entry Point (7-Section Architecture)."""
from pathlib import Path
import streamlit as st

from src.components import inject_custom_css, kpi_card, page_header
from src.data_loader import load_movies
from src.filters import apply_global_filters, render_global_filters
from src.utils import format_currency, format_number

# 1. Page Configuration
st.set_page_config(
    page_title="CineLens Analytics — Movie Intelligence Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Design Tokens & Typography
inject_custom_css()

# 3. Check for preprocessed data
processed_movies_file = Path("data/processed/movies.parquet")
if not processed_movies_file.exists():
    st.error("⚠️ Processed dataset not found! Please run `python scripts/preprocess.py` to generate optimized Parquet files.")
    st.stop()

# 4. Lazy Load ONLY Fact Table for Instant Startup
with st.spinner("Loading CineLens database..."):
    movies_df = load_movies()

# 5. Render Global Sidebar Filters
filters = render_global_filters(movies_df)
filtered_movies = apply_global_filters(movies_df, filters)

# 6. Welcome Header & Portal Overview
page_header(
    title="🎬 CineLens Analytics",
    subtitle="Enterprise movie intelligence, catalog analytics, and box office insights powered by normalized relational data."
)

st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ About Dataset & Cleaning Audit"):
    st.markdown("""
    **Dataset Scope:** 45,000+ catalog titles from TMDB metadata, credits, and keywords.
    - **Dropped Corruptions:** 3 malformed rows with date strings in `id`.
    - **Deduplication:** Fact table deduplicated via completeness heuristics.
    - **Status Filter:** Excluded 351 unreleased titles (Rumored, Planned, In Production, Canceled).
    - **Zero-to-NaN:** 0 budget, revenue, and runtime converted to `NaN` to prevent severe distortion.
    - **Relational Integrity:** Zero orphan IDs; independent bridge tables prevent double-counting.
    """)

# Quick KPI Summary Banner
col1, col2, col3, col4 = st.columns(4)
is_default = (len(filtered_movies) == len(movies_df))

if is_default:
    from src.data_loader import load_overview_kpis
    kpi_df = load_overview_kpis()
    if not kpi_df.empty:
        k_row = kpi_df.iloc[0]
        with col1:
            kpi_card("Catalog Titles", format_number(k_row["total_movies"]), subtitle="Full catalog", icon="🎥")
        with col2:
            kpi_card("Total Box Office", format_currency(k_row["total_revenue"]), subtitle="Reported gross revenue", icon="💰")
        with col3:
            kpi_card("Avg Catalog Rating", f"{k_row['avg_rating']:.2f} ★", subtitle="Min 20 votes", icon="⭐")
        with col4:
            kpi_card("Avg Popularity", f"{k_row['avg_popularity']:.1f}", subtitle="TMDB score", icon="🔥")
    else:
        with col1: kpi_card("Catalog Titles", format_number(len(filtered_movies)), icon="🎥")
        with col2: kpi_card("Total Box Office", format_currency(filtered_movies.loc[filtered_movies["revenue"] > 0, "revenue"].sum()), icon="💰")
        with col3: kpi_card("Avg Catalog Rating", f"{filtered_movies.loc[filtered_movies['vote_count'] >= 20, 'vote_average'].mean():.2f} ★", icon="⭐")
        with col4: kpi_card("Avg Popularity", f"{filtered_movies['popularity'].mean():.1f}", icon="🔥")
else:
    with col1:
        kpi_card("Filtered Titles", format_number(len(filtered_movies)), subtitle=f"of {len(movies_df):,} total catalog", icon="🎥")
    with col2:
        rev_sum = filtered_movies.loc[filtered_movies["revenue"] > 0, "revenue"].sum()
        kpi_card("Total Box Office", format_currency(rev_sum), subtitle="Reported gross revenue", icon="💰")
    with col3:
        rate_avg = filtered_movies.loc[filtered_movies["vote_count"] >= 20, "vote_average"].mean()
        kpi_card("Avg Catalog Rating", f"{rate_avg:.2f} ★" if rate_avg == rate_avg else "N/A", subtitle="Min 20 votes", icon="⭐")
    with col4:
        kpi_card("Active Year Span", f"{filters.year_range[0]} – {filters.year_range[1]}", subtitle="Global slider selection", icon="📅")

st.markdown("""
### 🧭 Navigation & Analytical Sections
Select any of the **7 focused analytical sections** from the sidebar:

| Section | Focus Area | Key Capabilities |
|---|---|---|
| **1. Overview** | Executive Summary | Macro catalog KPIs, release volume, box office trajectory, and automated insights. |
| **2. Movie Explorer** | Catalog Search | Vectorized substring title search, multi-metric filtering, pagination (25/page), detail inspector. |
| **3. Performance** | Financials & Ratings | High-grossing leaderboards, net profits, high-ROI rankings ($1M guard), WebGL regressions, rating dynamics. |
| **4. People** | Talent Intelligence | Director & Actor leaderboards, career filmography timelines, career averages, genre specialization. |
| **5. Genres & Themes** | Categories & Plot Tags | Relational-safe cross-genre box office benchmarks, single-genre deep-dives, thematic keyword clustering. |
| **6. Trends** | Time Series & Geography | Decadal stacked genre evolution, annual volume growth, worldwide ISO-3166-1 production choropleth map. |
| **7. Insights** | Statistical Modeling & Tools | Dynamic plain-language rule engine, z-score underrated/overhyped anomalies, side-by-side title comparison. |
""")

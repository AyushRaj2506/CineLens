"""Page 5: Genre Intelligence & Thematic Tag Analytics (Redesigned SaaS Layout)."""
import streamlit as st
import pandas as pd

from src.analytics import genre_financials, keyword_stats, keywords_by_genre
from src.components import (
    empty_state,
    filter_status_bar,
    inject_custom_css,
    page_header
)
from src.data_loader import (
    load_genre_bridge,
    load_genre_summary,
    load_keyword_bridge,
    load_keyword_summary,
    load_movies
)
from src.filters import apply_global_filters, render_global_filters
from src.utils import MIN_GENRE_SAMPLE, MIN_KEYWORD_SUPPORT, ROI_MIN_BUDGET, VOTE_COUNT_MIN, format_currency
from src.visualizations import (
    ACCENT_FINANCE,
    PRIMARY_COLOR,
    RATING_COLOR,
    SECONDARY_COLOR,
    bar_chart
)

inject_custom_css()

# 1. Lazy load fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

# 3. Page Header & Filter Status
page_header(
    title="Genres & Thematic Keywords",
    subtitle="Relational-integrity-safe cross-genre box office benchmarks and narrative plot keyword clustering.",
    eyebrow="GENRE INTELLIGENCE"
)
filter_status_bar(filters, len(movies_df), len(filtered_df))

if filtered_df.empty:
    empty_state("No movie records found matching active filter criteria.")
    st.stop()

is_default = (len(filtered_df) == len(movies_df))

tab_genres, tab_keywords = st.tabs(["🏷️ Genre Intelligence", "🔑 Thematic Plot Keywords"])

# ==================== TAB 1: GENRES ====================
with tab_genres:
    st.markdown("### Cross-Genre Performance (Zero Double-Counting)")
    st.caption("🛡️ **Relational Integrity Safe**: Bridge tables are merged independently against the unique fact table, guaranteeing no cartesian revenue inflation.")
    
    if is_default:
        genre_stats = load_genre_summary()
    else:
        genre_bridge = load_genre_bridge()
        genre_stats = genre_financials(filtered_df, genre_bridge, min_sample=MIN_GENRE_SAMPLE)
        
    if not genre_stats.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_gc = bar_chart(
                genre_stats,
                x="movie_count",
                y="genre_name",
                orientation="h",
                bar_color=PRIMARY_COLOR,
                title="Production Volume by Genre (Total Films)"
            )
            st.plotly_chart(fig_gc, use_container_width=True)
        with col_g2:
            fig_gr = bar_chart(
                genre_stats.sort_values("total_revenue", ascending=False),
                x="total_revenue",
                y="genre_name",
                orientation="h",
                bar_color=ACCENT_FINANCE,
                title="Total Box Office Gross by Genre ($ USD)"
            )
            st.plotly_chart(fig_gr, use_container_width=True)
            
        col_g3, col_g4 = st.columns(2)
        with col_g3:
            fig_rate = bar_chart(
                genre_stats.sort_values("avg_rating", ascending=False),
                x="avg_rating",
                y="genre_name",
                orientation="h",
                bar_color=RATING_COLOR,
                title=f"Average Critical Rating (Votes ≥ {VOTE_COUNT_MIN})"
            )
            st.plotly_chart(fig_rate, use_container_width=True)
        with col_g4:
            fig_roi = bar_chart(
                genre_stats.sort_values("avg_roi", ascending=False),
                x="avg_roi",
                y="genre_name",
                orientation="h",
                bar_color=SECONDARY_COLOR,
                title=f"Average ROI Multiplier (Budget ≥ {format_currency(ROI_MIN_BUDGET)})"
            )
            st.plotly_chart(fig_roi, use_container_width=True)
            
        # Single Genre Deep-Dive
        with st.expander("🎯 Single Genre Deep-Dive & Top Titles", expanded=False):
            selected_genre = st.selectbox("Select Genre to Inspect Top Titles:", genre_stats["genre_name"].tolist(), index=0)
            genre_bridge = load_genre_bridge()
            g_m_ids = genre_bridge[genre_bridge["genre_name"] == selected_genre]["movie_id"].unique()
            g_movies = filtered_df[filtered_df["movie_id"].isin(g_m_ids)]
            
            top_g_rev = g_movies[g_movies["revenue"] > 0].sort_values("revenue", ascending=False).head(10)
            if not top_g_rev.empty:
                st.dataframe(
                    top_g_rev[["title", "release_year", "revenue", "budget", "vote_average", "director_display"]].rename(columns={
                        "title": "Title", "release_year": "Year", "revenue": "Gross ($)", "budget": "Budget ($)", "vote_average": "Rating ★", "director_display": "Director"
                    }),
                    hide_index=True,
                    use_container_width=True
                )
    else:
        st.info("Insufficient genre data in selection.")

# ==================== TAB 2: KEYWORDS ====================
with tab_keywords:
    st.markdown("### Thematic Plot Keywords & Box Office Associations")
    st.caption(f"ℹ️ Filtered to keywords with at least {MIN_KEYWORD_SUPPORT} titles in the catalog archive.")
    
    if is_default:
        kw_data = load_keyword_summary()
    else:
        keyword_bridge = load_keyword_bridge()
        kw_data = keyword_stats(filtered_df, keyword_bridge, min_support=MIN_KEYWORD_SUPPORT, top_n=20)
        
    if not kw_data.empty:
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            fig_kw_cnt = bar_chart(
                kw_data.head(10),
                x="movie_count",
                y="keyword_name",
                orientation="h",
                bar_color=PRIMARY_COLOR,
                title="Top 10 Narrative Themes by Frequency"
            )
            st.plotly_chart(fig_kw_cnt, use_container_width=True)
        with col_k2:
            fig_kw_rev = bar_chart(
                kw_data.sort_values("avg_revenue", ascending=False).head(10),
                x="avg_revenue",
                y="keyword_name",
                orientation="h",
                bar_color=ACCENT_FINANCE,
                title="Top 10 Grossing Narrative Themes (Avg Revenue / Film)"
            )
            st.plotly_chart(fig_kw_rev, use_container_width=True)
            
        with st.expander("🎭 Keyword Themes Clustered by Genre", expanded=False):
            genre_bridge = load_genre_bridge()
            keyword_bridge = load_keyword_bridge()
            g_for_kw = st.selectbox("Choose Genre:", sorted(genre_bridge["genre_name"].dropna().unique().tolist()), key="kw_genre_select")
            genre_kw = keywords_by_genre(g_for_kw, filtered_df, keyword_bridge, genre_bridge, top_n=10)
            if not genre_kw.empty:
                fig_gkw = bar_chart(
                    genre_kw,
                    x="movie_count",
                    y="keyword_name",
                    orientation="h",
                    bar_color=SECONDARY_COLOR,
                    title=f"Top 10 Thematic Tags in {g_for_kw} Films"
                )
                st.plotly_chart(fig_gkw, use_container_width=True)
            else:
                st.write("No keywords recorded for this genre in selection.")
    else:
        st.info("No keywords meet the support threshold in the active selection.")

"""Page 6: Historical & Geographic Trends (Optimized Performance)."""
import streamlit as st
import pandas as pd

from src.analytics import country_financials, decade_genre_heatmap, yearly_financials
from src.components import empty_state, inject_custom_css, page_header
from src.data_loader import (
    load_country_bridge,
    load_country_summary,
    load_genre_bridge,
    load_movies,
    load_yearly_summary
)
from src.filters import apply_global_filters, render_global_filters
from src.utils import VOTE_COUNT_MIN
from src.visualizations import bar_chart, choropleth_map, line_chart, stacked_area_chart

inject_custom_css()
page_header("📈 Historical & Geographic Trends", "Longitudinal release evolutions, decadal genre shares, and international film production footprint.")

# 1. Lazy load fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

if filtered_df.empty:
    empty_state("No movie records found for active filters.")
    st.stop()

is_default = (len(filtered_df) == len(movies_df))

tab_historical, tab_geo = st.tabs(["📅 Historical & Decadal Trends", "🌍 Global Production Footprint"])

# ==================== TAB 1: HISTORICAL ====================
with tab_historical:
    st.markdown("### 📅 Longitudinal Catalog & Box Office Growth")
    yearly_data = load_yearly_summary() if is_default else yearly_financials(filtered_df)
    
    if not yearly_data.empty:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_vol = line_chart(yearly_data, x="release_year", y="movie_count", title="Annual Movie Release Count")
            st.plotly_chart(fig_vol, use_container_width=True)
        with col_t2:
            fig_rev = line_chart(yearly_data, x="release_year", y=["total_revenue", "total_budget"], title="Total Box Office & Budget Trajectory ($ USD)")
            st.plotly_chart(fig_rev, use_container_width=True)
            
        # Decadal Stacked Area
        st.markdown("#### 🏷️ Decadal Shift in Genre Production Volume")
        genre_bridge = load_genre_bridge()
        decade_data = decade_genre_heatmap(filtered_df, genre_bridge, metric="movie_count")
        if not decade_data.empty:
            fig_area = stacked_area_chart(
                decade_data.sort_values("release_decade"),
                x="release_decade",
                y="value",
                color="genre_name",
                title="Proportion of Genre Production Across Decades"
            )
            st.plotly_chart(fig_area, use_container_width=True)
    else:
        st.info("Insufficient dated records in active selection.")

# ==================== TAB 2: GEOGRAPHIC ====================
with tab_geo:
    st.markdown("### 🌍 Worldwide Film Production Footprint")
    st.caption("ℹ️ **~13.8%** of catalog titles have no recorded production country; these are excluded from regional breakdowns to avoid an uninformative 'Unknown' country bucket.")
    
    if is_default:
        country_stats = load_country_summary()
    else:
        country_bridge = load_country_bridge()
        country_stats = country_financials(filtered_df, country_bridge, min_sample=5)
        
    if not country_stats.empty:
        map_metric = st.selectbox(
            "Choropleth Metric",
            options=["movie_count", "total_revenue", "avg_rating", "avg_popularity"],
            format_func=lambda x: {
                "movie_count": "Total Movie Production Count",
                "total_revenue": "Total Box Office Revenue ($)",
                "avg_rating": f"Average Rating (Min {VOTE_COUNT_MIN} Votes)",
                "avg_popularity": "Average TMDB Popularity Score"
            }.get(x, x)
        )
        
        metric_title = {
            "movie_count": "Production Volume (Titles)",
            "total_revenue": "Total Box Office ($ USD)",
            "avg_rating": "Average Rating (★)",
            "avg_popularity": "Average Popularity Score"
        }.get(map_metric, map_metric)
        
        fig_map = choropleth_map(
            country_stats,
            locations="iso_3166_1",
            z=map_metric,
            hover_name="country_name",
            title=f"Global Film Production Footprint — {metric_title}"
        )
        st.plotly_chart(fig_map, use_container_width=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_top_cnt = bar_chart(country_stats.head(10), x="movie_count", y="country_name", orientation="h", title="Top 10 Countries by Production Volume")
            st.plotly_chart(fig_top_cnt, use_container_width=True)
        with col_c2:
            fig_top_rev = bar_chart(country_stats.sort_values("total_revenue", ascending=False).head(10), x="total_revenue", y="country_name", orientation="h", title="Top 10 Countries by Box Office ($ USD)")
            st.plotly_chart(fig_top_rev, use_container_width=True)
    else:
        st.info("Insufficient country data in selection.")

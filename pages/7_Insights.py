"""Page 7: Automated Insights & Movie Comparison (Optimized Performance)."""
import streamlit as st
import pandas as pd

from src.analytics import compute_overhyped_movies, compute_underrated_movies
from src.components import empty_state, inject_custom_css, insight_line, page_header
from src.data_loader import load_actor_bridge, load_director_bridge, load_genre_bridge, load_movies
from src.filters import apply_global_filters, render_global_filters
from src.insights import generate_insights
from src.utils import VOTE_COUNT_MIN, format_currency, format_number, format_pct
from src.visualizations import grouped_bar_chart

inject_custom_css()
page_header("🧠 Automated Insights & Comparison", "Algorithmic anomaly detection, automated catalog synthesis, and side-by-side title benchmarking.")

# 1. Lazy load ONLY fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

if filtered_df.empty:
    empty_state("No movie records found for active filters.")
    st.stop()

tab_insights, tab_comparison = st.tabs(["💡 Automated Synthesis & Anomalies", "⚖️ Movie Comparison Tool"])

# ==================== TAB 1: INSIGHTS & ANOMALIES ====================
with tab_insights:
    st.markdown("### 💡 Dynamic Rule-Based Insight Engine")
    with st.spinner("Generating automated insights..."):
        genre_bridge = load_genre_bridge()
        actor_bridge = load_actor_bridge()
        director_bridge = load_director_bridge()
        insights = generate_insights("advanced", filtered_df, genre_bridge, actor_bridge, director_bridge)
        
    if insights:
        for item in insights:
            insight_line(item)
    else:
        st.info("Insufficient data in the active filter selection to generate automated insight rules.")
        
    st.markdown("---")
    st.markdown("### 💎 Statistical Cohort Outlier Detection")
    c_out1, c_out2 = st.columns(2)
    
    with c_out1:
        st.markdown("#### 💎 Underrated Gems")
        with st.expander("Methodology ($z_{\\text{rating}} \\ge 1.28$, $z_{\\text{pop}} \\le 0.0$)"):
            st.caption("Films in the top 10% rating z-score and bottom 50% popularity z-score relative to their release-year cohort (min 20 votes).")
        underrated = compute_underrated_movies(filtered_df, min_votes=VOTE_COUNT_MIN, top_n=10)
        if not underrated.empty:
            st.dataframe(
                underrated[["title", "release_year", "vote_average", "vote_count", "popularity", "director_display"]].rename(columns={
                    "title": "Title", "release_year": "Year", "vote_average": "Rating ★", "vote_count": "Votes", "popularity": "Popularity", "director_display": "Director"
                }),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.write("No underrated outliers in selection.")
            
    with c_out2:
        st.markdown("#### 📢 Overhyped Titles")
        with st.expander("Methodology ($z_{\\text{pop}} \\ge 1.28$, $z_{\\text{rating}} \\le 0.0$)"):
            st.caption("Films in the top 10% popularity z-score and bottom 50% rating z-score relative to their release-year cohort.")
        overhyped = compute_overhyped_movies(filtered_df, min_votes=VOTE_COUNT_MIN, top_n=10)
        if not overhyped.empty:
            st.dataframe(
                overhyped[["title", "release_year", "popularity", "vote_average", "vote_count", "director_display"]].rename(columns={
                    "title": "Title", "release_year": "Year", "popularity": "Popularity", "vote_average": "Rating ★", "vote_count": "Votes", "director_display": "Director"
                }),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.write("No overhyped outliers in selection.")

# ==================== TAB 2: COMPARISON ====================
with tab_comparison:
    st.markdown("### ⚖️ Side-by-Side Title Comparison")
    
    # Pre-format select options cheaply
    options_series = filtered_df["title"].fillna("Untitled") + " (" + filtered_df["release_year"].fillna(0).astype(str) + ")"
    available_labels = options_series.tolist()
    
    default_titles = ["Titanic (1997)", "Avatar (2009)", "The Dark Knight (2008)"]
    valid_defaults = [d for d in default_titles if d in available_labels]
    if len(valid_defaults) < 2 and len(available_labels) >= 2:
        valid_defaults = available_labels[:2]
        
    selected_labels = st.multiselect(
        "Search & select 2 to 3 movies to compare:",
        options=available_labels,
        default=valid_defaults,
        max_selections=3
    )
    
    if len(selected_labels) >= 2:
        selected_movies = filtered_df[options_series.isin(selected_labels)].copy()
        
        # Comparison Table
        metrics_data = []
        for _, row in selected_movies.iterrows():
            metrics_data.append({
                "Movie Title": str(row["title"]),
                "Release Year": str(int(row["release_year"])) if pd.notna(row["release_year"]) else "Not reported",
                "Genres": str(row.get("genres_display", "Not specified")),
                "Director": str(row.get("director_display", "Not credited")),
                "Rating": f"{row['vote_average']} ★" if pd.notna(row["vote_average"]) else "Not reported",
                "Votes": format_number(row["vote_count"]),
                "Popularity": f"{row['popularity']:.2f}" if pd.notna(row["popularity"]) else "Not reported",
                "Budget": format_currency(row["budget"]),
                "Revenue": format_currency(row["revenue"]),
                "Profit": format_currency(row["profit"]),
                "ROI": format_pct(row["roi"]) if pd.notna(row["roi"]) else "Not reported",
                "Runtime": f"{int(row['runtime'])} min" if pd.notna(row["runtime"]) and row["runtime"] > 0 else "Not reported"
            })
        st.dataframe(pd.DataFrame(metrics_data).set_index("Movie Title").T, use_container_width=True)
        
        # Dual-Axis Grouped Charts
        col_comp1, col_comp2 = st.columns(2)
        with col_comp1:
            chart_crit = pd.DataFrame({
                "Movie": selected_movies["title"],
                "Rating (★ x10)": selected_movies["vote_average"] * 10,
                "Popularity": selected_movies["popularity"],
                "Runtime (min)": selected_movies["runtime"].fillna(0)
            })
            fig_crit = grouped_bar_chart(chart_crit, x="Movie", y_cols=["Rating (★ x10)", "Popularity", "Runtime (min)"], title="Engagement & Runtime Comparison")
            st.plotly_chart(fig_crit, use_container_width=True)
            
        with col_comp2:
            chart_fin = pd.DataFrame({
                "Movie": selected_movies["title"],
                "Budget ($)": selected_movies["budget"].fillna(0),
                "Revenue ($)": selected_movies["revenue"].fillna(0),
                "Profit ($)": selected_movies["profit"].fillna(0)
            })
            fig_fin = grouped_bar_chart(chart_fin, x="Movie", y_cols=["Budget ($)", "Revenue ($)", "Profit ($)"], title="Box Office Financials Comparison")
            st.plotly_chart(fig_fin, use_container_width=True)
    else:
        st.info("👉 Select at least 2 titles above to render side-by-side comparison.")

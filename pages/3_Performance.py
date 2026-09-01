"""Page 3: Movie Performance, Financials & Ratings Dynamics."""
import streamlit as st
import pandas as pd

from src.analytics import calculate_correlations
from src.components import empty_state, inject_custom_css, kpi_card, page_header
from src.data_loader import load_movies
from src.filters import apply_global_filters, rated_movies, render_global_filters
from src.utils import ROI_MIN_BUDGET, VOTE_COUNT_MIN, format_currency, format_number, format_pct
from src.visualizations import bar_chart, histogram_chart, scatter_plot

inject_custom_css()
page_header("🏆 Performance, Financials & Ratings", "Box office leaderboards, production economics, critical ratings, and audience engagement.")

# 1. Lazy load ONLY fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

if filtered_df.empty:
    empty_state("No movie records found for active filters.")
    st.stop()

# 3. High-level KPI Bar
c1, c2, c3, c4 = st.columns(4)
rev_sub = filtered_df[filtered_df["revenue"] > 0]
prof_sub = filtered_df[filtered_df["profit"].notna()]
rated_sub = rated_movies(filtered_df, VOTE_COUNT_MIN)
roi_sub = filtered_df[filtered_df["roi"].notna() & (filtered_df["budget"] >= ROI_MIN_BUDGET)]

with c1:
    kpi_card("Total Box Office", format_currency(rev_sub["revenue"].sum() if not rev_sub.empty else 0), subtitle=f"{len(rev_sub):,} reporting", icon="💰")
with c2:
    kpi_card("Total Net Profit", format_currency(prof_sub["profit"].sum() if not prof_sub.empty else 0), subtitle=f"{len(prof_sub):,} with both", icon="📈")
with c3:
    avg_r = rated_sub["vote_average"].mean() if not rated_sub.empty else None
    kpi_card("Avg Rating", f"{avg_r:.2f} ★" if avg_r is not None else "N/A", subtitle=f"Min {VOTE_COUNT_MIN} votes", icon="⭐")
with c4:
    avg_roi = roi_sub["roi"].mean() if not roi_sub.empty else None
    kpi_card("Average ROI", format_pct(avg_roi) if avg_roi is not None else "N/A", subtitle="Budget ≥ $1M", icon="⚡")

st.markdown("<br>", unsafe_allow_html=True)

# 4. Three High-Impact Tabs
tab_leaderboards, tab_economics, tab_ratings = st.tabs([
    "🥇 Box Office & Profitability",
    "💵 Production Economics & Correlations",
    "⭐ Critical Ratings & Popularity"
])

# ----------------- TAB 1: LEADERBOARDS -----------------
with tab_leaderboards:
    st.markdown("### 🥇 Top Box Office & Return Rankings")
    rank_type = st.radio("Select Leaderboard", ["Highest Grossing", "Most Profitable", "Highest ROI (Budget ≥ $1M)"], horizontal=True)
    
    if rank_type == "Highest Grossing":
        top_gross = rev_sub.sort_values("revenue", ascending=False).head(15)
        if not top_gross.empty:
            fig_g = bar_chart(top_gross, x="revenue", y="title", orientation="h", title="Top 15 Highest Grossing Films (USD)")
            st.plotly_chart(fig_g, use_container_width=True)
            st.dataframe(
                top_gross[["title", "release_year", "revenue", "budget", "vote_average", "director_display"]].rename(columns={
                    "title": "Title", "release_year": "Year", "revenue": "Revenue ($)", "budget": "Budget ($)", "vote_average": "Rating ★", "director_display": "Director"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No box office records in selection.")
            
    elif rank_type == "Most Profitable":
        top_prof = prof_sub.sort_values("profit", ascending=False).head(15)
        if not top_prof.empty:
            fig_p = bar_chart(top_prof, x="profit", y="title", orientation="h", title="Top 15 Most Profitable Films (USD)")
            st.plotly_chart(fig_p, use_container_width=True)
            st.dataframe(
                top_prof[["title", "release_year", "profit", "revenue", "budget", "roi"]].rename(columns={
                    "title": "Title", "release_year": "Year", "profit": "Net Profit ($)", "revenue": "Revenue ($)", "budget": "Budget ($)", "roi": "ROI Multiplier"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No profitability records in selection.")
            
    else:
        top_roi = roi_sub.sort_values("roi", ascending=False).head(15)
        st.caption(f"ℹ️ Verified budget threshold ≥ {format_currency(ROI_MIN_BUDGET)} applied to filter out micro-budget reporting noise.")
        if not top_roi.empty:
            fig_roi = bar_chart(top_roi, x="roi", y="title", orientation="h", title="Top 15 Highest ROI Films (Budget ≥ $1M)")
            st.plotly_chart(fig_roi, use_container_width=True)
            st.dataframe(
                top_roi[["title", "release_year", "roi", "budget", "revenue", "profit"]].rename(columns={
                    "title": "Title", "release_year": "Year", "roi": "ROI Multiplier", "budget": "Budget ($)", "revenue": "Revenue ($)", "profit": "Net Profit ($)"
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No qualifying ROI films in selection.")

# ----------------- TAB 2: ECONOMICS -----------------
with tab_economics:
    st.markdown("### 🔬 Production Economics & Regressions")
    st.info("📌 **Methodology Note**: ~20% of movies report budget and ~16% report revenue. Figures are nominal USD (not inflation adjusted). All averages and regressions operate on verified non-zero data.")
    
    corrs = calculate_correlations(filtered_df)
    c_m1, c_m2, c_m3 = st.columns(3)
    with c_m1:
        st.metric("Budget vs. Revenue r", f"{corrs.get('budget_vs_revenue', 0.0):.3f}" if pd.notna(corrs.get('budget_vs_revenue')) else "N/A")
    with c_m2:
        st.metric("Budget vs. Rating r", f"{corrs.get('budget_vs_rating', 0.0):.3f}" if pd.notna(corrs.get('budget_vs_rating')) else "N/A")
    with c_m3:
        st.metric("Revenue vs. Popularity r", f"{corrs.get('revenue_vs_popularity', 0.0):.3f}" if pd.notna(corrs.get('revenue_vs_popularity')) else "N/A")
        
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        bud_rev_df = filtered_df[filtered_df["budget"].notna() & (filtered_df["budget"] > 0) & filtered_df["revenue"].notna() & (filtered_df["revenue"] > 0)]
        if not bud_rev_df.empty:
            fig_br = scatter_plot(
                bud_rev_df,
                x="budget",
                y="revenue",
                hover_name="title",
                title="Budget vs. Box Office Gross (WebGL + OLS)",
                trendline="ols",
                use_webgl=True
            )
            st.plotly_chart(fig_br, use_container_width=True)
            
    with col_e2:
        bud_rate_df = filtered_df[filtered_df["budget"].notna() & (filtered_df["budget"] > 0) & (filtered_df["vote_count"].fillna(0) >= VOTE_COUNT_MIN)]
        if not bud_rate_df.empty:
            fig_brt = scatter_plot(
                bud_rate_df,
                x="budget",
                y="vote_average",
                hover_name="title",
                title="Budget vs. Critical Rating (★)",
                trendline="ols",
                use_webgl=True
            )
            st.plotly_chart(fig_brt, use_container_width=True)

# ----------------- TAB 3: RATINGS & ENGAGEMENT -----------------
with tab_ratings:
    st.markdown("### ⭐ Critical Ratings & Popularity Dynamics")
    st.caption(f"ℹ️ Titles with under {VOTE_COUNT_MIN} votes are filtered from ranking averages to eliminate 1-vote anomalies.")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        # Funnel chart: Vote count vs rating
        vote_rate_df = filtered_df[(filtered_df["vote_count"].fillna(0) > 0) & filtered_df["vote_average"].notna()]
        if not vote_rate_df.empty:
            fig_vr = scatter_plot(
                vote_rate_df,
                x="vote_count",
                y="vote_average",
                hover_name="title",
                log_x=True,
                title="Vote Count vs. Rating (Funnel Convergence)",
                use_webgl=True
            )
            st.plotly_chart(fig_vr, use_container_width=True)
            
    with col_r2:
        rate_pop_df = rated_sub[rated_sub["popularity"].notna()]
        if not rate_pop_df.empty:
            fig_rp = scatter_plot(
                rate_pop_df,
                x="popularity",
                y="vote_average",
                hover_name="title",
                log_x=True,
                title="Popularity Score vs. Rating (★)",
                trendline="ols",
                use_webgl=True
            )
            st.plotly_chart(fig_rp, use_container_width=True)
            
    # Longest / Shortest runtime expander
    with st.expander("⏱️ View Runtime Extremes (Longest & Shortest Films)"):
        run_valid = filtered_df[filtered_df["runtime"] > 0]
        c_rt1, c_rt2 = st.columns(2)
        with c_rt1:
            p99 = run_valid["runtime"].quantile(0.99) if not run_valid.empty else 300
            longest = run_valid[run_valid["runtime"] <= p99].sort_values("runtime", ascending=False).head(10)
            st.markdown("#### Longest Films (≤ 99th Percentile)")
            st.dataframe(longest[["title", "release_year", "runtime", "genres_display"]], hide_index=True, use_container_width=True)
        with c_rt2:
            shortest = run_valid.sort_values("runtime", ascending=True).head(10)
            st.markdown("#### Shortest Films (Non-Zero)")
            st.dataframe(shortest[["title", "release_year", "runtime", "genres_display"]], hide_index=True, use_container_width=True)

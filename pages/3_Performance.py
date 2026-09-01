"""Page 3: Financial Performance & Audience Rating Dynamics (Redesigned SaaS Layout)."""
import streamlit as st
import pandas as pd

from src.analytics import calculate_correlations
from src.components import (
    empty_state,
    filter_status_bar,
    inject_custom_css,
    kpi_card,
    page_header
)
from src.data_loader import load_movies
from src.filters import apply_global_filters, rated_movies, render_global_filters
from src.utils import ROI_MIN_BUDGET, VOTE_COUNT_MIN, format_currency, format_number, format_pct
from src.visualizations import (
    ACCENT_FINANCE,
    POSITIVE_COLOR,
    PRIMARY_COLOR,
    RATING_COLOR,
    SECONDARY_COLOR,
    bar_chart,
    histogram_chart,
    scatter_plot
)

inject_custom_css()

# 1. Lazy load fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

# 3. Page Header & Filter Status Strip
page_header(
    title="Performance, Economics & Ratings",
    subtitle="Box office grosses, net margins, return on investment, production cost regressions, and audience reception dynamics.",
    eyebrow="FINANCIAL INTELLIGENCE"
)
filter_status_bar(filters, len(movies_df), len(filtered_df))

if filtered_df.empty:
    empty_state("No movie records found matching active filter criteria.")
    st.stop()

# 4. Top Financial KPIs
c_f1, c_f2, c_f3, c_f4 = st.columns(4)
rev_valid = filtered_df[filtered_df["revenue"].notna() & (filtered_df["revenue"] > 0)]
bud_valid = filtered_df[filtered_df["budget"].notna() & (filtered_df["budget"] > 0)]
prof_valid = filtered_df[filtered_df["profit"].notna()]
roi_valid = filtered_df[filtered_df["roi"].notna() & (filtered_df["budget"] >= ROI_MIN_BUDGET)]

with c_f1: kpi_card("Total Reported Gross", format_currency(rev_valid["revenue"].sum() if not rev_valid.empty else 0), subtitle=f"{len(rev_valid):,} reporting titles", icon="💰")
with c_f2: kpi_card("Average Budget", format_currency(bud_valid["budget"].mean() if not bud_valid.empty else None), subtitle=f"{len(bud_valid):,} reporting titles", icon="💵")
with c_f3: kpi_card("Total Net Profit", format_currency(prof_valid["profit"].sum() if not prof_valid.empty else None), subtitle=f"{len(prof_valid):,} with budget+rev", icon="📈")
with c_f4: kpi_card("Profitable Ratio", format_pct((prof_valid["profit"] > 0).mean() if not prof_valid.empty else None), subtitle="Of reporting films", icon="🎯")

st.markdown("<br>", unsafe_allow_html=True)

# 5. Segmented Tabs
tab_boxoffice, tab_econ, tab_ratings = st.tabs(["💰 Box Office & Margins", "📊 Production Economics", "⭐ Audience Dynamics"])

# ==================== TAB 1: BOX OFFICE & PROFITABILITY ====================
with tab_boxoffice:
    st.markdown("### Box Office & Profitability Leaderboards")
    c_m1, c_m2 = st.columns([1, 1])
    with c_m1:
        perf_metric = st.selectbox(
            "Ranking Dimension",
            options=["revenue", "profit", "roi"],
            format_func=lambda x: {
                "revenue": "Top Grossing Titles (Revenue)",
                "profit": "Top Net Profitable Titles (Revenue - Budget)",
                "roi": f"Highest Return on Investment (Budget ≥ {format_currency(ROI_MIN_BUDGET)})"
            }.get(x, x),
            key="perf_metric_select"
        )
    with c_m2:
        top_n_films = st.slider("Number of Titles to Display", 5, 25, 10, 5, key="perf_top_n")

    if perf_metric == "revenue":
        leaderboard = rev_valid.sort_values("revenue", ascending=False).head(top_n_films)
        if not leaderboard.empty:
            fig_bar = bar_chart(
                leaderboard,
                x="revenue",
                y="title",
                orientation="h",
                bar_color=ACCENT_FINANCE,
                title=f"Top {top_n_films} Films by Box Office Gross ($ USD)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
    elif perf_metric == "profit":
        leaderboard = prof_valid.sort_values("profit", ascending=False).head(top_n_films)
        if not leaderboard.empty:
            fig_bar = bar_chart(
                leaderboard,
                x="profit",
                y="title",
                orientation="h",
                bar_color=POSITIVE_COLOR,
                title=f"Top {top_n_films} Films by Net Box Office Profit ($ USD)"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
    elif perf_metric == "roi":
        leaderboard = roi_valid.sort_values("roi", ascending=False).head(top_n_films)
        if not leaderboard.empty:
            fig_bar = bar_chart(
                leaderboard,
                x="roi",
                y="title",
                orientation="h",
                bar_color=PRIMARY_COLOR,
                title=f"Top {top_n_films} Films by ROI Multiplier (Budget ≥ {format_currency(ROI_MIN_BUDGET)})"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

# ==================== TAB 2: PRODUCTION ECONOMICS ====================
with tab_econ:
    st.markdown("### Production Economics & Regression Analysis")
    st.caption("🔬 WebGL-accelerated scatter plots with Ordinary Least Squares (OLS) trendline regressions.")
    
    both_fin = filtered_df[filtered_df["budget"].notna() & (filtered_df["budget"] > 0) & filtered_df["revenue"].notna() & (filtered_df["revenue"] > 0)].copy()
    
    if not both_fin.empty:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            fig_scat1 = scatter_plot(
                both_fin,
                x="budget",
                y="revenue",
                hover_name="title",
                trendline="ols",
                log_x=True,
                log_y=True,
                use_webgl=True,
                title="Production Budget vs. Box Office Gross (Log Scale)"
            )
            st.plotly_chart(fig_scat1, use_container_width=True)
            
        with col_s2:
            fig_scat2 = scatter_plot(
                both_fin[both_fin["vote_count"] >= VOTE_COUNT_MIN],
                x="budget",
                y="vote_average",
                hover_name="title",
                trendline="ols",
                log_x=True,
                use_webgl=True,
                title=f"Budget vs. Audience Rating (Votes ≥ {VOTE_COUNT_MIN})"
            )
            st.plotly_chart(fig_scat2, use_container_width=True)
            
        # Pearson Correlation Matrix
        corr_data = calculate_correlations(both_fin)
        if not corr_data.empty:
            with st.expander("📊 View Statistical Pearson Correlation Coefficients"):
                st.dataframe(corr_data.style.format("{:.3f}"), use_container_width=True)
    else:
        st.info("Insufficient movies with both non-zero budget and revenue in the active filter selection.")

# ==================== TAB 3: AUDIENCE RATINGS ====================
with tab_ratings:
    st.markdown("### Audience Reception & Popularity Dynamics")
    rated_df = rated_movies(filtered_df, VOTE_COUNT_MIN)
    
    if not rated_df.empty:
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            fig_r_dist = histogram_chart(
                rated_df,
                x="vote_average",
                title=f"Rating Score Distribution (Votes ≥ {VOTE_COUNT_MIN})",
                nbins=25,
                bar_color=RATING_COLOR
            )
            st.plotly_chart(fig_r_dist, use_container_width=True)
            
        with col_r2:
            fig_r_funnel = scatter_plot(
                rated_df,
                x="vote_count",
                y="vote_average",
                hover_name="title",
                log_x=True,
                use_webgl=True,
                title="Sample Size Reliability Funnel (Rating vs. Vote Count)"
            )
            st.plotly_chart(fig_r_funnel, use_container_width=True)
    else:
        st.info(f"No titles have at least {VOTE_COUNT_MIN} audience votes in the active selection.")

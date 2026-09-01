"""Page 1: Executive Overview Dashboard (Optimized Sub-Second Performance)."""
import streamlit as st
import pandas as pd

from src.analytics import yearly_financials
from src.components import empty_state, inject_custom_css, insight_line, kpi_card, page_header
from src.data_loader import load_movies, load_overview_kpis, load_yearly_summary
from src.filters import apply_global_filters, rated_movies, render_global_filters
from src.utils import VOTE_COUNT_MIN, format_currency, format_number
from src.visualizations import histogram_chart, line_chart

inject_custom_css()
page_header("📊 Executive Catalog Overview", "High-level summary of catalog volume, global box office gross, and audience engagement.")

# 1. Lazy load ONLY fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_movies = apply_global_filters(movies_df, filters)

if filtered_movies.empty:
    empty_state("No movies match the current global filter criteria.")
    st.stop()

# Check if default unfiltered catalog
is_default = (len(filtered_movies) == len(movies_df))

# 3. Dynamic Key Insights (Lightweight, 2-3 bullets max)
st.markdown("### 💡 Key Catalog Takeaways")
rev_valid = filtered_movies[filtered_movies["revenue"] > 0]
rated_sub = rated_movies(filtered_movies, VOTE_COUNT_MIN)

if not rev_valid.empty:
    top_rev = rev_valid.sort_values("revenue", ascending=False).iloc[0]
    total_rev = rev_valid["revenue"].sum()
    insight_line(f"Total reported box office reaches **{format_currency(total_rev)}**, led by **{top_rev['title']}** ({format_currency(top_rev['revenue'])}).")

if not rated_sub.empty:
    top_rated = rated_sub.sort_values("vote_average", ascending=False).iloc[0]
    insight_line(f"Top critical rating belongs to **{top_rated['title']}** ({top_rated['vote_average']} ★ with {int(top_rated['vote_count']):,} votes).")

st.markdown("<br>", unsafe_allow_html=True)

# 4. Core Catalog KPIs (Instant precomputed read on default)
st.markdown("### 📈 Core Catalog KPIs")
c1, c2, c3, c4, c5 = st.columns(5)

if is_default:
    kpi_df = load_overview_kpis()
    if not kpi_df.empty:
        k_row = kpi_df.iloc[0]
        with c1: kpi_card("Total Movies", format_number(k_row["total_movies"]), subtitle="Full catalog", icon="🎬")
        with c2: kpi_card("Total Box Office", format_currency(k_row["total_revenue"]), subtitle="Reported revenue", icon="💰")
        with c3: kpi_card("Avg Revenue", format_currency(k_row["avg_revenue"]), subtitle="Non-zero revenue", icon="💵")
        with c4: kpi_card("Avg Rating", f"{k_row['avg_rating']:.2f} ★", subtitle=f"Min {VOTE_COUNT_MIN} votes", icon="⭐")
        with c5: kpi_card("Avg Popularity", f"{k_row['avg_popularity']:.1f}", subtitle="TMDB score", icon="🔥")
    else:
        with c1: kpi_card("Total Movies", format_number(len(filtered_movies)), icon="🎬")
        with c2: kpi_card("Total Box Office", format_currency(rev_valid["revenue"].sum() if not rev_valid.empty else 0), icon="💰")
        with c3: kpi_card("Avg Revenue", format_currency(rev_valid["revenue"].mean() if not rev_valid.empty else None), icon="💵")
        with c4: kpi_card("Avg Rating", f"{rated_sub['vote_average'].mean():.2f} ★" if not rated_sub.empty else "N/A", icon="⭐")
        with c5: kpi_card("Avg Popularity", f"{filtered_movies['popularity'].mean():.1f}", icon="🔥")
else:
    with c1: kpi_card("Total Movies", format_number(len(filtered_movies)), subtitle=f"of {len(movies_df):,} total", icon="🎬")
    with c2: kpi_card("Total Box Office", format_currency(rev_valid["revenue"].sum() if not rev_valid.empty else 0), subtitle=f"{len(rev_valid):,} reporting", icon="💰")
    with c3: kpi_card("Avg Revenue", format_currency(rev_valid["revenue"].mean() if not rev_valid.empty else None), subtitle="Non-zero revenue", icon="💵")
    with c4: kpi_card("Avg Rating", f"{rated_sub['vote_average'].mean():.2f} ★" if not rated_sub.empty else "N/A", subtitle=f"Min {VOTE_COUNT_MIN} votes", icon="⭐")
    with c5: kpi_card("Avg Popularity", f"{filtered_movies['popularity'].mean():.1f}" if "popularity" in filtered_movies.columns else "N/A", subtitle="TMDB score", icon="🔥")

st.markdown("<br>", unsafe_allow_html=True)

# 5. Core Macro Charts (Strictly 4 visible charts, uses precomputed table on default)
st.markdown("### 📉 Macro Volume & Rating Distributions")
row1_c1, row1_c2 = st.columns(2)

yearly_stats = load_yearly_summary() if is_default else yearly_financials(filtered_movies)

with row1_c1:
    if not yearly_stats.empty:
        fig_vol = line_chart(yearly_stats, x="release_year", y="movie_count", title="Movies Released by Year")
        st.plotly_chart(fig_vol, use_container_width=True)

with row1_c2:
    if not yearly_stats.empty:
        fig_rev = line_chart(yearly_stats, x="release_year", y="total_revenue", title="Total Box Office Revenue by Year (USD)")
        st.plotly_chart(fig_rev, use_container_width=True)

row2_c1, row2_c2 = st.columns(2)
with row2_c1:
    if not rated_sub.empty:
        fig_rate = histogram_chart(rated_sub, x="vote_average", title=f"Rating Distribution (Vote Count ≥ {VOTE_COUNT_MIN})", nbins=25)
        st.plotly_chart(fig_rate, use_container_width=True)

with row2_c2:
    fig_pop = histogram_chart(filtered_movies, x="popularity", title="Popularity Score Distribution", nbins=30, log_x=True)
    st.plotly_chart(fig_pop, use_container_width=True)

# 6. Top 10 Box Office Table
st.markdown("### 🏆 Top Box Office Grosses in Selection")
top_10 = rev_valid.sort_values("revenue", ascending=False).head(10)
if not top_10.empty:
    st.dataframe(
        top_10[["title", "release_year", "genres_display", "revenue", "budget", "vote_average", "director_display"]].rename(columns={
            "title": "Title", "release_year": "Year", "genres_display": "Genres", "revenue": "Revenue ($)", "budget": "Budget ($)", "vote_average": "Rating ★", "director_display": "Director"
        }),
        use_container_width=True,
        hide_index=True
    )

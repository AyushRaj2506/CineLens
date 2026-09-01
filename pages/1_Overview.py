"""Page 1: Executive Overview Dashboard (Redesigned Modern SaaS Layout)."""
import streamlit as st
import pandas as pd

from src.analytics import yearly_financials
from src.components import (
    empty_state,
    filter_status_bar,
    inject_custom_css,
    insight_card,
    kpi_card,
    page_header
)
from src.data_loader import load_movies, load_overview_kpis, load_yearly_summary
from src.filters import apply_global_filters, rated_movies, render_global_filters
from src.utils import VOTE_COUNT_MIN, format_currency, format_number
from src.visualizations import (
    ACCENT_FINANCE,
    PRIMARY_COLOR,
    RATING_COLOR,
    SECONDARY_COLOR,
    histogram_chart,
    line_chart
)

inject_custom_css()

# 1. Lazy load fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_movies = apply_global_filters(movies_df, filters)

if filtered_movies.empty:
    empty_state("No movies match the current global filter criteria.")
    st.stop()

# 3. Header & Filter Status Strip
page_header(
    title="Executive Catalog Overview",
    subtitle="Macro release trajectories, global box office gross, rating dynamics, and high-level catalog intelligence.",
    eyebrow="EXECUTIVE DASHBOARD"
)
filter_status_bar(filters, len(movies_df), len(filtered_movies))

is_default = (len(filtered_movies) == len(movies_df))
rev_valid = filtered_movies[filtered_movies["revenue"] > 0]
rated_sub = rated_movies(filtered_movies, VOTE_COUNT_MIN)

# 4. Core Catalog KPIs
c1, c2, c3, c4, c5 = st.columns(5)
if is_default:
    kpi_df = load_overview_kpis()
    if not kpi_df.empty:
        k_row = kpi_df.iloc[0]
        with c1: kpi_card("Total Movies", format_number(k_row["total_movies"]), subtitle="Full catalog archive", icon="🎞️")
        with c2: kpi_card("Total Box Office", format_currency(k_row["total_revenue"]), subtitle="7,014 reporting titles", icon="💰")
        with c3: kpi_card("Avg Revenue / Film", format_currency(k_row["avg_revenue"]), subtitle="Non-zero reported", icon="💵")
        with c4: kpi_card("Avg Rating", f"{k_row['avg_rating']:.2f} ★", subtitle=f"Votes ≥ {VOTE_COUNT_MIN}", icon="⭐")
        with c5: kpi_card("Avg Popularity", f"{k_row['avg_popularity']:.1f}", subtitle="TMDB score", icon="🔥")
    else:
        with c1: kpi_card("Total Movies", format_number(len(filtered_movies)), icon="🎞️")
        with c2: kpi_card("Total Box Office", format_currency(rev_valid["revenue"].sum() if not rev_valid.empty else 0), icon="💰")
        with c3: kpi_card("Avg Revenue", format_currency(rev_valid["revenue"].mean() if not rev_valid.empty else None), icon="💵")
        with c4: kpi_card("Avg Rating", f"{rated_sub['vote_average'].mean():.2f} ★" if not rated_sub.empty else "N/A", icon="⭐")
        with c5: kpi_card("Avg Popularity", f"{filtered_movies['popularity'].mean():.1f}", icon="🔥")
else:
    with c1: kpi_card("Filtered Titles", format_number(len(filtered_movies)), subtitle=f"of {len(movies_df):,} total", icon="🎞️")
    with c2: kpi_card("Total Box Office", format_currency(rev_valid["revenue"].sum() if not rev_valid.empty else 0), subtitle=f"{len(rev_valid):,} reporting", icon="💰")
    with c3: kpi_card("Avg Revenue", format_currency(rev_valid["revenue"].mean() if not rev_valid.empty else None), subtitle="In filtered scope", icon="💵")
    with c4: kpi_card("Avg Rating", f"{rated_sub['vote_average'].mean():.2f} ★" if not rated_sub.empty else "N/A", subtitle=f"Votes ≥ {VOTE_COUNT_MIN}", icon="⭐")
    with c5: kpi_card("Avg Popularity", f"{filtered_movies['popularity'].mean():.1f}" if "popularity" in filtered_movies.columns else "N/A", subtitle="TMDB score", icon="🔥")

st.markdown("<br>", unsafe_allow_html=True)

# 5. Strategic Intelligence Takeaways
st.markdown('<div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.65rem;">Key Intelligence Takeaways</div>', unsafe_allow_html=True)

if not rev_valid.empty:
    top_rev = rev_valid.sort_values("revenue", ascending=False).iloc[0]
    total_rev = rev_valid["revenue"].sum()
    insight_card(
        "01",
        f"Global box office gross reaches <strong>{format_currency(total_rev)}</strong> across {len(rev_valid):,} reporting titles, led by <strong>{top_rev['title']}</strong> at <strong>{format_currency(top_rev['revenue'])}</strong>."
    )

if not rated_sub.empty:
    top_rated = rated_sub.sort_values("vote_average", ascending=False).iloc[0]
    insight_card(
        "02",
        f"Critical rating benchmark is held by <strong>{top_rated['title']}</strong> (<strong>{top_rated['vote_average']} ★</strong> with {int(top_rated['vote_count']):,} verified audience votes)."
    )

runtime_valid = filtered_movies.loc[filtered_movies["runtime"] > 0, "runtime"]
if not runtime_valid.empty:
    avg_run = runtime_valid.mean()
    insight_card(
        "03",
        f"Average feature runtime across the active selection is <strong>{int(round(avg_run))} minutes</strong>, reflecting standard international theatrical formats."
    )

st.markdown("<br>", unsafe_allow_html=True)

# 6. Core Macro Charts (2x2 Grid)
st.markdown('<div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.65rem;">Longitudinal & Distribution Dynamics</div>', unsafe_allow_html=True)

yearly_stats = load_yearly_summary() if is_default else yearly_financials(filtered_movies)

row1_c1, row1_c2 = st.columns(2)
with row1_c1:
    if not yearly_stats.empty:
        fig_vol = line_chart(yearly_stats, x="release_year", y="movie_count", title="Annual Production Volume Trajectory")
        st.plotly_chart(fig_vol, use_container_width=True)

with row1_c2:
    if not yearly_stats.empty:
        fig_rev = line_chart(yearly_stats, x="release_year", y="total_revenue", title="Annual Box Office Gross Trajectory ($ USD)")
        st.plotly_chart(fig_rev, use_container_width=True)

row2_c1, row2_c2 = st.columns(2)
with row2_c1:
    if not rated_sub.empty:
        fig_rate = histogram_chart(
            rated_sub,
            x="vote_average",
            title=f"Audience Rating Distribution (Votes ≥ {VOTE_COUNT_MIN})",
            nbins=25,
            bar_color=RATING_COLOR
        )
        st.plotly_chart(fig_rate, use_container_width=True)

with row2_c2:
    fig_pop = histogram_chart(
        filtered_movies,
        x="popularity",
        title="Audience Engagement Score Distribution",
        nbins=30,
        log_x=True,
        bar_color=SECONDARY_COLOR
    )
    st.plotly_chart(fig_pop, use_container_width=True)

# 7. Top Box Office Grosses Table
st.markdown('<div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-top: 1rem; margin-bottom: 0.65rem;">Top Grossing Titles in Selection</div>', unsafe_allow_html=True)
top_10 = rev_valid.sort_values("revenue", ascending=False).head(10)
if not top_10.empty:
    st.dataframe(
        top_10[["title", "release_year", "genres_display", "revenue", "budget", "vote_average", "director_display"]].rename(columns={
            "title": "Title",
            "release_year": "Year",
            "genres_display": "Genres",
            "revenue": "Revenue ($)",
            "budget": "Budget ($)",
            "vote_average": "Rating ★",
            "director_display": "Director"
        }),
        use_container_width=True,
        hide_index=True
    )

"""Page 4: Creative Talent Intelligence — Directors & Actors (Redesigned SaaS Layout)."""
import streamlit as st
import pandas as pd

from src.analytics import actor_detail, director_detail, top_actors, top_directors
from src.components import (
    empty_state,
    filter_status_bar,
    inject_custom_css,
    kpi_card,
    page_header
)
from src.data_loader import (
    load_actor_bridge,
    load_actor_summary,
    load_director_bridge,
    load_director_summary,
    load_genre_bridge,
    load_movies
)
from src.filters import apply_global_filters, render_global_filters
from src.utils import MIN_ACTOR_MOVIES, MIN_DIRECTOR_MOVIES, VOTE_COUNT_MIN, format_currency, format_number
from src.visualizations import ACCENT_FINANCE, PRIMARY_COLOR, bar_chart, scatter_plot

inject_custom_css()

# 1. Lazy load fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

# 3. Page Header & Filter Status
page_header(
    title="Talent & Creative Intelligence",
    subtitle="Director and actor career track records, box office averages, critical reception, and filmography timelines.",
    eyebrow="CREATIVE TALENT"
)
filter_status_bar(filters, len(movies_df), len(filtered_df))

if filtered_df.empty:
    empty_state("No movie records found matching active filter criteria.")
    st.stop()

is_default = (len(filtered_df) == len(movies_df))

tab_directors, tab_actors = st.tabs(["🎥 Director Intelligence", "🎭 Main-Cast Actor Intelligence"])

# ==================== TAB 1: DIRECTORS ====================
with tab_directors:
    st.markdown("### Director Rankings & Track Records")
    c_d1, c_d2 = st.columns([1, 1])
    with c_d1:
        min_dir_films = st.slider("Minimum Directed Films Threshold", 1, 10, MIN_DIRECTOR_MOVIES, 1, key="dir_min_films")
    with c_d2:
        dir_sort = st.selectbox(
            "Rank Directors By",
            options=["total_revenue", "avg_revenue", "avg_rating", "avg_roi", "movie_count"],
            format_func=lambda x: {
                "total_revenue": "Total Associated Box Office Gross",
                "avg_revenue": "Average Box Office per Film",
                "avg_rating": f"Average Critical Rating (Votes ≥ {VOTE_COUNT_MIN})",
                "avg_roi": "Average ROI Multiplier",
                "movie_count": "Total Directed Feature Films"
            }.get(x, x),
            key="dir_sort_metric"
        )
        
    st.caption(f"ℹ️ Minimum threshold requires at least {min_dir_films} directed titles to guard against single-film outliers.")
    
    if is_default and min_dir_films == MIN_DIRECTOR_MOVIES:
        pre_dirs = load_director_summary()
        if not pre_dirs.empty and dir_sort in pre_dirs.columns:
            dir_rankings = pre_dirs.sort_values(dir_sort, ascending=False).head(15)
        else:
            director_bridge = load_director_bridge()
            dir_rankings = top_directors(filtered_df, director_bridge, min_movies=min_dir_films, sort_by=dir_sort, top_n=15)
    else:
        director_bridge = load_director_bridge()
        dir_rankings = top_directors(filtered_df, director_bridge, min_movies=min_dir_films, sort_by=dir_sort, top_n=15)
        
    if not dir_rankings.empty:
        fig_d = bar_chart(
            dir_rankings.head(10),
            x=dir_sort,
            y="person_name",
            orientation="h",
            bar_color=PRIMARY_COLOR,
            title=f"Top 10 Directors by {dir_sort.replace('_', ' ').title()}"
        )
        st.plotly_chart(fig_d, use_container_width=True)
    else:
        st.info("No directors meet the specified film count threshold.")
        
    # Director Explorer
    st.markdown("#### 🎬 Director Filmography Profile")
    director_bridge = load_director_bridge()
    active_dirs = director_bridge[director_bridge["movie_id"].isin(filtered_df["movie_id"])]["person_name"].value_counts()
    if not active_dirs.empty:
        selected_dir = st.selectbox("Select Director to Inspect:", options=active_dirs.index.tolist()[:100], index=0, key="dir_select_box")
        genre_bridge = load_genre_bridge()
        d_detail = director_detail(selected_dir, filtered_df, director_bridge, genre_bridge)
        if d_detail:
            c_k1, c_k2, c_k3, c_k4 = st.columns(4)
            with c_k1: kpi_card("Feature Films", format_number(d_detail["movie_count"]), subtitle="In active selection", icon="🎥")
            with c_k2: kpi_card("Total Gross", format_currency(d_detail["total_revenue"]), subtitle="Cumulative box office", icon="💰")
            with c_k3: kpi_card("Avg Rating", f"{d_detail['avg_rating']:.2f} ★" if pd.notna(d_detail['avg_rating']) else "N/A", subtitle=f"Votes ≥ {VOTE_COUNT_MIN}", icon="⭐")
            with c_k4: kpi_card("Core Genre Profile", ", ".join(d_detail["top_genres"]) if d_detail["top_genres"] else "Varied", subtitle="Top associated genres", icon="🏷️")
            
            with st.expander(f"📜 View {selected_dir}'s Complete Filmography Table & Timeline", expanded=True):
                filmography = d_detail["filmography"]
                if not filmography.empty and "release_year" in filmography.columns:
                    t_valid = filmography[filmography["release_year"].notna()].sort_values("release_year")
                    if not t_valid.empty:
                        fig_t = scatter_plot(t_valid, x="release_year", y="vote_average", hover_name="title", size="revenue", title="Release Year vs. Audience Rating (Bubble = Box Office Gross)")
                        st.plotly_chart(fig_t, use_container_width=True)
                st.dataframe(
                    filmography[["title", "release_year", "genres_display", "vote_average", "revenue", "budget"]].rename(columns={
                        "title": "Title", "release_year": "Year", "genres_display": "Genres", "vote_average": "Rating ★", "revenue": "Gross ($)", "budget": "Budget ($)"
                    }),
                    hide_index=True,
                    use_container_width=True
                )

# ==================== TAB 2: ACTORS ====================
with tab_actors:
    st.markdown("### Main-Cast Actor Rankings")
    c_a1, c_a2 = st.columns([1, 1])
    with c_a1:
        min_act_films = st.slider("Minimum Credited Roles Threshold", 1, 15, MIN_ACTOR_MOVIES, 1, key="act_min_films")
    with c_a2:
        act_sort = st.selectbox(
            "Rank Actors By",
            options=["total_revenue", "avg_revenue", "avg_rating", "avg_popularity", "movie_count"],
            format_func=lambda x: {
                "total_revenue": "Total Associated Box Office Gross",
                "avg_revenue": "Average Box Office per Film",
                "avg_rating": f"Average Critical Rating (Votes ≥ {VOTE_COUNT_MIN})",
                "avg_popularity": "Average TMDB Popularity",
                "movie_count": "Total Credited Main-Cast Roles"
            }.get(x, x),
            key="act_sort_metric"
        )
        
    st.caption(f"ℹ️ Main cast threshold requires at least {min_act_films} credited feature roles (billing order < 10).")
    
    if is_default and min_act_films == MIN_ACTOR_MOVIES:
        pre_acts = load_actor_summary()
        if not pre_acts.empty and act_sort in pre_acts.columns:
            act_rankings = pre_acts.sort_values(act_sort, ascending=False).head(15)
        else:
            actor_bridge = load_actor_bridge()
            act_rankings = top_actors(filtered_df, actor_bridge, min_movies=min_act_films, sort_by=act_sort, top_n=15)
    else:
        actor_bridge = load_actor_bridge()
        act_rankings = top_actors(filtered_df, actor_bridge, min_movies=min_act_films, sort_by=act_sort, top_n=15)
        
    if not act_rankings.empty:
        fig_a = bar_chart(
            act_rankings.head(10),
            x=act_sort,
            y="person_name",
            orientation="h",
            bar_color=ACCENT_FINANCE,
            title=f"Top 10 Actors by {act_sort.replace('_', ' ').title()}"
        )
        st.plotly_chart(fig_a, use_container_width=True)
    else:
        st.info("No actors meet the specified role count threshold.")
        
    # Actor Explorer
    st.markdown("#### 👤 Actor Career Profile")
    actor_bridge = load_actor_bridge()
    active_actors = actor_bridge[actor_bridge["movie_id"].isin(filtered_df["movie_id"])]["person_name"].value_counts()
    if not active_actors.empty:
        selected_actor = st.selectbox("Select Actor to Inspect:", options=active_actors.index.tolist()[:100], index=0, key="act_select_box")
        genre_bridge = load_genre_bridge()
        a_detail = actor_detail(selected_actor, filtered_df, actor_bridge, genre_bridge)
        if a_detail:
            c_ak1, c_ak2, c_ak3, c_ak4 = st.columns(4)
            with c_ak1: kpi_card("Feature Roles", format_number(a_detail["movie_count"]), subtitle="Main-cast billing", icon="🎭")
            with c_ak2: kpi_card("Total Gross", format_currency(a_detail["total_revenue"]), subtitle="Cumulative box office", icon="💰")
            with c_ak3: kpi_card("Avg Rating", f"{a_detail['avg_rating']:.2f} ★" if pd.notna(a_detail['avg_rating']) else "N/A", subtitle=f"Votes ≥ {VOTE_COUNT_MIN}", icon="⭐")
            with c_ak4: kpi_card("Core Genre Profile", ", ".join(a_detail["top_genres"]) if a_detail["top_genres"] else "Varied", subtitle="Top associated genres", icon="🏷️")
            
            with st.expander(f"📜 View {selected_actor}'s Complete Filmography Table & Timeline", expanded=True):
                filmography = a_detail["filmography"]
                if not filmography.empty and "release_year" in filmography.columns:
                    t_valid = filmography[filmography["release_year"].notna()].sort_values("release_year")
                    if not t_valid.empty:
                        fig_at = scatter_plot(t_valid, x="release_year", y="vote_average", hover_name="title", size="revenue", title="Release Year vs. Audience Rating (Bubble = Box Office Gross)")
                        st.plotly_chart(fig_at, use_container_width=True)
                st.dataframe(
                    filmography[["title", "release_year", "character", "vote_average", "revenue", "budget"]].rename(columns={
                        "title": "Title", "release_year": "Year", "character": "Character", "vote_average": "Rating ★", "revenue": "Gross ($)", "budget": "Budget ($)"
                    }),
                    hide_index=True,
                    use_container_width=True
                )

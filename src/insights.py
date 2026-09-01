"""Rule-based automated insight engine for CineLens Analytics."""
from typing import List, Optional
import numpy as np
import pandas as pd

from src.analytics import (
    compute_underrated_movies,
    genre_financials,
    genre_growth_trends,
    top_actors,
    top_directors
)
from src.utils import (
    MIN_ACTOR_MOVIES,
    MIN_DIRECTOR_MOVIES,
    MIN_GENRE_SAMPLE,
    ROI_MIN_BUDGET,
    VOTE_COUNT_MIN,
    format_currency,
    format_pct
)


def rule_most_common_genre(movies_df: pd.DataFrame, genre_bridge: pd.DataFrame) -> Optional[str]:
    """Rule 1: Identify most represented genre in current selection."""
    if movies_df.empty or genre_bridge.empty:
        return None
    merged = genre_bridge[genre_bridge["movie_id"].isin(movies_df["movie_id"])]
    if merged.empty:
        return None
    counts = merged["genre_name"].value_counts()
    if counts.empty:
        return None
    top_genre = str(counts.index[0])
    total_unique_movies = movies_df["movie_id"].nunique()
    pct = (counts.iloc[0] / total_unique_movies) * 100 if total_unique_movies > 0 else 0
    return f"**{top_genre}** is the most frequently represented genre, appearing in **{pct:.1f}%** of movies in the current selection."


def rule_highest_revenue_genre(movies_df: pd.DataFrame, genre_bridge: pd.DataFrame) -> Optional[str]:
    """Rule 2: Identify highest total grossing genre."""
    gf = genre_financials(movies_df, genre_bridge, min_sample=MIN_GENRE_SAMPLE)
    if gf.empty or gf["total_revenue"].max() <= 0:
        return None
    top_row = gf.sort_values(by="total_revenue", ascending=False).iloc[0]
    genre = top_row["genre_name"]
    total = top_row["total_revenue"]
    return f"**{genre}** generates the highest total box office revenue, totaling **{format_currency(total)}**."


def rule_best_roi_genre(movies_df: pd.DataFrame, genre_bridge: pd.DataFrame) -> Optional[str]:
    """Rule 3: Highest ROI genre among qualifying movies."""
    gf = genre_financials(movies_df, genre_bridge, min_sample=MIN_GENRE_SAMPLE)
    valid = gf[gf["avg_roi"].notna() & (gf["movie_count"] >= MIN_GENRE_SAMPLE)]
    if valid.empty:
        return None
    top_row = valid.sort_values(by="avg_roi", ascending=False).iloc[0]
    genre = top_row["genre_name"]
    roi = top_row["avg_roi"]
    return f"Among genres with at least {MIN_GENRE_SAMPLE} qualifying films (budget ≥ {format_currency(ROI_MIN_BUDGET)}), **{genre}** delivers the highest average ROI at **{format_pct(roi)}**."


def rule_fastest_growing_genre(movies_df: pd.DataFrame, genre_bridge: pd.DataFrame) -> Optional[str]:
    """Rule 4: Identify genre with strongest recent growth slope."""
    trends = genre_growth_trends(movies_df, genre_bridge, n_years=10)
    if trends.empty or trends["growth_slope"].max() <= 0:
        return None
    top_row = trends.iloc[0]
    genre = top_row["genre_name"]
    return f"**{genre}** shows the strongest upward trajectory in annual release volume over recent years."


def rule_top_director_revenue(movies_df: pd.DataFrame, director_bridge: pd.DataFrame) -> Optional[str]:
    """Rule 5: Director with highest average box office return."""
    dirs = top_directors(movies_df, director_bridge, min_movies=MIN_DIRECTOR_MOVIES, sort_by="avg_revenue", top_n=5)
    if dirs.empty or dirs["avg_revenue"].dropna().empty:
        return None
    top_row = dirs.iloc[0]
    d_name = top_row["person_name"]
    avg_rev = top_row["avg_revenue"]
    n = top_row["movie_count"]
    return f"**{d_name}** leads directors with at least {MIN_DIRECTOR_MOVIES} films, averaging **{format_currency(avg_rev)}** in revenue per film across {n} titles."


def rule_top_actor_rating(movies_df: pd.DataFrame, actor_bridge: pd.DataFrame) -> Optional[str]:
    """Rule 6: Actor with highest average rating."""
    actors = top_actors(movies_df, actor_bridge, min_movies=MIN_ACTOR_MOVIES, sort_by="avg_rating", top_n=5)
    if actors.empty or actors["avg_rating"].dropna().empty:
        return None
    top_row = actors.iloc[0]
    a_name = top_row["person_name"]
    rating = top_row["avg_rating"]
    n = top_row["movie_count"]
    return f"**{a_name}** maintains the highest average rating among actors with at least {MIN_ACTOR_MOVIES} movies, scoring **{rating:.2f}/10** across {n} films."


def rule_underrated_highlight(movies_df: pd.DataFrame) -> Optional[str]:
    """Rule 7: Highlight a standout underrated movie."""
    underrated = compute_underrated_movies(movies_df, min_votes=VOTE_COUNT_MIN, top_n=1)
    if underrated.empty:
        return None
    top_movie = underrated.iloc[0]
    title = top_movie["title"]
    yr = int(top_movie["release_year"]) if pd.notna(top_movie["release_year"]) else ""
    rate = top_movie["vote_average"]
    return f"**{title}** ({yr}) stands out as an underrated gem: scoring **{rate:.1f} ★** while maintaining modest popularity compared to its release cohort."


def rule_revenue_trend(movies_df: pd.DataFrame) -> Optional[str]:
    """Rule 8: Multi-year revenue trajectory."""
    if movies_df.empty or "release_year" not in movies_df.columns:
        return None
    rev_valid = movies_df[movies_df["revenue"].notna() & (movies_df["revenue"] > 0) & movies_df["release_year"].notna()]
    if rev_valid.empty:
        return None
    yearly = rev_valid.groupby("release_year")["revenue"].sum().sort_index()
    if len(yearly) < 5:
        return None
    start_yr, end_yr = int(yearly.index[0]), int(yearly.index[-1])
    rev_start, rev_end = yearly.iloc[0], yearly.iloc[-1]
    if rev_start > 0:
        pct_change = ((rev_end - rev_start) / rev_start) * 100
        direction = "increased" if pct_change >= 0 else "decreased"
        return f"Total reported box office revenue {direction} by **{abs(pct_change):.1f}%** between **{start_yr}** and **{end_yr}** in the current selection."
    return None


def rule_rating_trend(movies_df: pd.DataFrame) -> Optional[str]:
    """Rule 9: Multi-year average rating trajectory."""
    rated = movies_df[(movies_df["vote_count"].fillna(0) >= VOTE_COUNT_MIN) & movies_df["release_year"].notna() & movies_df["vote_average"].notna()]
    if rated.empty:
        return None
    yearly = rated.groupby("release_year")["vote_average"].mean().sort_index()
    if len(yearly) < 5:
        return None
    start_yr, end_yr = int(yearly.index[0]), int(yearly.index[-1])
    r_start, r_end = yearly.iloc[0], yearly.iloc[-1]
    diff = r_end - r_start
    dir_str = "rose" if diff >= 0 else "fell"
    return f"Average rating for qualifying movies {dir_str} from **{r_start:.2f}** to **{r_end:.2f}** between {start_yr} and {end_yr}."


def generate_insights(
    scope: str,
    movies_df: pd.DataFrame,
    genre_bridge: pd.DataFrame,
    actor_bridge: pd.DataFrame,
    director_bridge: pd.DataFrame
) -> List[str]:
    """
    Orchestrate insight rules based on scope ('overview' or 'advanced').
    Gracefully skips rules with insufficient data and returns a list of insight sentences.
    """
    if movies_df.empty:
        return []
        
    insights = []
    
    # Overview Scope Rules
    r_genre = rule_most_common_genre(movies_df, genre_bridge)
    if r_genre: insights.append(r_genre)
    
    r_rev_genre = rule_highest_revenue_genre(movies_df, genre_bridge)
    if r_rev_genre: insights.append(r_rev_genre)
    
    r_dir = rule_top_director_revenue(movies_df, director_bridge)
    if r_dir: insights.append(r_dir)
    
    r_act = rule_top_actor_rating(movies_df, actor_bridge)
    if r_act: insights.append(r_act)
    
    if scope == "advanced":
        r_roi = rule_best_roi_genre(movies_df, genre_bridge)
        if r_roi: insights.append(r_roi)
        
        r_grow = rule_fastest_growing_genre(movies_df, genre_bridge)
        if r_grow: insights.append(r_grow)
        
        r_under = rule_underrated_highlight(movies_df)
        if r_under: insights.append(r_under)
        
        r_rev_t = rule_revenue_trend(movies_df)
        if r_rev_t: insights.append(r_rev_t)
        
        r_rate_t = rule_rating_trend(movies_df)
        if r_rate_t: insights.append(r_rate_t)
        
    return insights

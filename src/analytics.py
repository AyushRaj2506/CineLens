"""Core analytical calculations, aggregations, and statistical models."""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.utils import (
    MIN_ACTOR_MOVIES,
    MIN_DIRECTOR_MOVIES,
    MIN_GENRE_SAMPLE,
    MIN_GENRE_YEAR_MOVIES,
    MIN_KEYWORD_SUPPORT,
    ROI_MIN_BUDGET,
    VOTE_COUNT_MIN
)


# ==========================================
# 1. GENRE ANALYTICS
# ==========================================

def genre_financials(
    movies_df: pd.DataFrame,
    genre_bridge: pd.DataFrame,
    min_sample: int = MIN_GENRE_SAMPLE
) -> pd.DataFrame:
    """
    Safely aggregate financials and ratings by genre with vectorized operations.
    Adheres strictly to the Many-to-Many rule by merging genre_bridge with movies fact table.
    """
    if movies_df.empty or genre_bridge.empty:
        return pd.DataFrame(columns=[
            "genre_name", "movie_count", "total_revenue", "avg_revenue",
            "avg_budget", "avg_profit", "avg_roi", "avg_rating", "avg_popularity", "avg_runtime"
        ])
        
    merged = genre_bridge.merge(
        movies_df[["movie_id", "budget", "revenue", "profit", "roi", "vote_average", "vote_count", "popularity", "runtime"]],
        on="movie_id",
        how="inner"
    )
    if merged.empty:
        return pd.DataFrame()

    # 1. Movie count
    counts = merged.groupby("genre_name", observed=True)["movie_id"].nunique().reset_index(name="movie_count")
    counts = counts[counts["movie_count"] >= min_sample]
    if counts.empty:
        return pd.DataFrame()
        
    qual = merged.merge(counts[["genre_name"]], on="genre_name", how="inner")
    
    # 2. Revenue aggregates (revenue > 0)
    rev_sub = qual[qual["revenue"].notna() & (qual["revenue"] > 0)]
    rev_agg = rev_sub.groupby("genre_name", observed=True)["revenue"].agg(
        total_revenue="sum", avg_revenue="mean"
    ).reset_index() if not rev_sub.empty else pd.DataFrame(columns=["genre_name", "total_revenue", "avg_revenue"])
    
    # 3. Budget aggregates (budget > 0)
    bud_sub = qual[qual["budget"].notna() & (qual["budget"] > 0)]
    bud_agg = bud_sub.groupby("genre_name", observed=True)["budget"].mean().reset_index(name="avg_budget") if not bud_sub.empty else pd.DataFrame(columns=["genre_name", "avg_budget"])
    
    # 4. Profit & ROI (budget >= ROI_MIN_BUDGET)
    prof_sub = qual[qual["profit"].notna()]
    prof_agg = prof_sub.groupby("genre_name", observed=True)["profit"].mean().reset_index(name="avg_profit") if not prof_sub.empty else pd.DataFrame(columns=["genre_name", "avg_profit"])
    
    roi_sub = qual[qual["roi"].notna() & (qual["budget"] >= ROI_MIN_BUDGET)]
    roi_agg = roi_sub.groupby("genre_name", observed=True)["roi"].mean().reset_index(name="avg_roi") if not roi_sub.empty else pd.DataFrame(columns=["genre_name", "avg_roi"])
    
    # 5. Rating (vote_count >= VOTE_COUNT_MIN)
    rate_sub = qual[qual["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
    rate_agg = rate_sub.groupby("genre_name", observed=True)["vote_average"].mean().reset_index(name="avg_rating") if not rate_sub.empty else pd.DataFrame(columns=["genre_name", "avg_rating"])
    
    # 6. Popularity & Runtime (runtime > 0)
    pop_agg = qual.groupby("genre_name", observed=True)["popularity"].mean().reset_index(name="avg_popularity")
    run_sub = qual[qual["runtime"].notna() & (qual["runtime"] > 0)]
    run_agg = run_sub.groupby("genre_name", observed=True)["runtime"].mean().reset_index(name="avg_runtime") if not run_sub.empty else pd.DataFrame(columns=["genre_name", "avg_runtime"])
    
    # 7. Merge all
    res = counts.merge(rev_agg, on="genre_name", how="left")
    res["total_revenue"] = res["total_revenue"].fillna(0.0)
    res = res.merge(bud_agg, on="genre_name", how="left")
    res = res.merge(prof_agg, on="genre_name", how="left")
    res = res.merge(roi_agg, on="genre_name", how="left")
    res = res.merge(rate_agg, on="genre_name", how="left")
    res = res.merge(pop_agg, on="genre_name", how="left")
    res = res.merge(run_agg, on="genre_name", how="left")
    
    res.sort_values(by="movie_count", ascending=False, inplace=True)
    return res


def genre_growth_trends(
    movies_df: pd.DataFrame,
    genre_bridge: pd.DataFrame,
    min_avg_movies: int = MIN_GENRE_YEAR_MOVIES,
    n_years: int = 10
) -> pd.DataFrame:
    """Compute year-over-year genre counts and linear growth slopes over recent years."""
    if movies_df.empty or genre_bridge.empty or "release_year" not in movies_df.columns:
        return pd.DataFrame(columns=["genre_name", "growth_slope", "recent_movie_count"])
        
    merged = genre_bridge.merge(movies_df[["movie_id", "release_year"]], on="movie_id", how="inner")
    valid = merged[merged["release_year"].notna()]
    if valid.empty:
        return pd.DataFrame()
        
    max_year = int(valid["release_year"].max())
    min_eval_year = max_year - n_years + 1
    
    yearly_counts = valid.groupby(["genre_name", "release_year"], observed=True).size().reset_index(name="count")
    
    slopes = []
    for genre, grp in yearly_counts.groupby("genre_name", observed=True):
        recent_grp = grp[grp["release_year"] >= min_eval_year].sort_values("release_year")
        if len(recent_grp) >= 2 and recent_grp["count"].mean() >= min_avg_movies:
            x = recent_grp["release_year"].values.astype(float)
            y = recent_grp["count"].values.astype(float)
            slope = np.polyfit(x, y, 1)[0]
            slopes.append({
                "genre_name": str(genre),
                "growth_slope": float(slope),
                "recent_movie_count": int(recent_grp["count"].sum())
            })
            
    res_df = pd.DataFrame(slopes)
    if not res_df.empty:
        res_df.sort_values(by="growth_slope", ascending=False, inplace=True)
    return res_df


def decade_genre_heatmap(
    movies_df: pd.DataFrame,
    genre_bridge: pd.DataFrame,
    metric: str = "movie_count"
) -> pd.DataFrame:
    """Compute decade x genre cross tabulation."""
    if movies_df.empty or genre_bridge.empty or "release_decade" not in movies_df.columns:
        return pd.DataFrame()
        
    merged = genre_bridge.merge(
        movies_df[["movie_id", "release_decade", "revenue", "vote_average", "vote_count"]],
        on="movie_id",
        how="inner"
    )
    merged = merged[merged["release_decade"].notna() & (merged["release_decade"] >= 1920)]
    if merged.empty:
        return pd.DataFrame()
        
    merged["release_decade"] = merged["release_decade"].astype(int)
    
    if metric == "movie_count":
        grouped = merged.groupby(["genre_name", "release_decade"], observed=True)["movie_id"].nunique().reset_index(name="value")
    elif metric == "avg_rating":
        rate_sub = merged[merged["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
        grouped = rate_sub.groupby(["genre_name", "release_decade"], observed=True)["vote_average"].mean().reset_index(name="value")
    elif metric == "total_revenue":
        rev_sub = merged[merged["revenue"].notna() & (merged["revenue"] > 0)]
        grouped = rev_sub.groupby(["genre_name", "release_decade"], observed=True)["revenue"].sum().reset_index(name="value")
    else:
        grouped = merged.groupby(["genre_name", "release_decade"], observed=True)["movie_id"].nunique().reset_index(name="value")
        
    return grouped


# ==========================================
# 2. ACTOR ANALYTICS
# ==========================================

def top_actors(
    movies_df: pd.DataFrame,
    actor_bridge: pd.DataFrame,
    min_movies: int = MIN_ACTOR_MOVIES,
    sort_by: str = "total_revenue",
    top_n: int = 15
) -> pd.DataFrame:
    """Compute actor leaderboards with vectorized aggregation and sample size thresholding."""
    if movies_df.empty or actor_bridge.empty:
        return pd.DataFrame(columns=["person_id", "person_name", "movie_count", "total_revenue", "avg_revenue", "avg_rating", "avg_popularity"])
        
    merged = actor_bridge.merge(
        movies_df[["movie_id", "revenue", "vote_average", "vote_count", "popularity"]],
        on="movie_id",
        how="inner"
    )
    if merged.empty:
        return pd.DataFrame()
        
    # 1. Movie count filter
    counts = merged.groupby(["person_id", "person_name"], observed=True)["movie_id"].nunique().reset_index(name="movie_count")
    counts = counts[counts["movie_count"] >= min_movies]
    if counts.empty:
        return pd.DataFrame()
        
    qual_merged = merged.merge(counts[["person_id", "person_name"]], on=["person_id", "person_name"], how="inner")
    
    # 2. Revenue aggregates (revenue > 0)
    rev_sub = qual_merged[qual_merged["revenue"].notna() & (qual_merged["revenue"] > 0)]
    rev_agg = rev_sub.groupby(["person_id", "person_name"], observed=True)["revenue"].agg(
        total_revenue="sum", avg_revenue="mean"
    ).reset_index()
    
    # 3. Rating aggregates (vote_count >= VOTE_COUNT_MIN)
    rate_sub = qual_merged[qual_merged["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
    rate_agg = rate_sub.groupby(["person_id", "person_name"], observed=True)["vote_average"].mean().reset_index(name="avg_rating")
    
    # 4. Popularity aggregates
    pop_agg = qual_merged.groupby(["person_id", "person_name"], observed=True)["popularity"].mean().reset_index(name="avg_popularity")
    
    # 5. Assemble result
    res_df = counts.merge(rev_agg, on=["person_id", "person_name"], how="left")
    res_df["total_revenue"] = res_df["total_revenue"].fillna(0.0)
    res_df = res_df.merge(rate_agg, on=["person_id", "person_name"], how="left")
    res_df = res_df.merge(pop_agg, on=["person_id", "person_name"], how="left")
    
    if sort_by in res_df.columns:
        res_df.sort_values(by=sort_by, ascending=False, inplace=True)
    return res_df.head(top_n)


def actor_detail(
    person_name: str,
    movies_df: pd.DataFrame,
    actor_bridge: pd.DataFrame,
    genre_bridge: pd.DataFrame
) -> Dict:
    """Retrieve complete filmography and metrics for an individual actor."""
    actor_rows = actor_bridge[actor_bridge["person_name"] == person_name]
    if actor_rows.empty:
        return {}
        
    actor_movie_ids = actor_rows["movie_id"].unique()
    filmography = movies_df[movies_df["movie_id"].isin(actor_movie_ids)].copy()
    filmography = filmography.merge(actor_rows[["movie_id", "character", "cast_order"]], on="movie_id", how="left")
    
    # Top genres for actor
    genres = genre_bridge[genre_bridge["movie_id"].isin(actor_movie_ids)]
    top_genres = genres["genre_name"].value_counts().head(3).index.tolist() if not genres.empty else []
    
    rev_sub = filmography[filmography["revenue"].notna() & (filmography["revenue"] > 0)]
    rate_sub = filmography[filmography["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
    
    best_rated = rate_sub.sort_values("vote_average", ascending=False).iloc[0] if not rate_sub.empty else None
    highest_grossing = rev_sub.sort_values("revenue", ascending=False).iloc[0] if not rev_sub.empty else None
    most_popular = filmography.sort_values("popularity", ascending=False).iloc[0] if not filmography.empty else None
    
    return {
        "person_name": person_name,
        "movie_count": len(filmography),
        "total_revenue": rev_sub["revenue"].sum() if not rev_sub.empty else 0.0,
        "avg_revenue": rev_sub["revenue"].mean() if not rev_sub.empty else np.nan,
        "avg_rating": rate_sub["vote_average"].mean() if not rate_sub.empty else np.nan,
        "avg_popularity": filmography["popularity"].mean() if not filmography.empty else np.nan,
        "top_genres": top_genres,
        "filmography": filmography.sort_values("release_year", ascending=False),
        "best_rated": best_rated,
        "highest_grossing": highest_grossing,
        "most_popular": most_popular
    }


def actor_collaborations(
    person_name: str,
    actor_bridge: pd.DataFrame,
    top_n: int = 10
) -> pd.DataFrame:
    """Compute frequent co-stars on-demand for a single actor."""
    actor_rows = actor_bridge[actor_bridge["person_name"] == person_name]
    if actor_rows.empty:
        return pd.DataFrame(columns=["co_star", "shared_movies"])
        
    m_ids = actor_rows["movie_id"].unique()
    co_actors = actor_bridge[actor_bridge["movie_id"].isin(m_ids) & (actor_bridge["person_name"] != person_name)]
    if co_actors.empty:
        return pd.DataFrame(columns=["co_star", "shared_movies"])
        
    counts = co_actors.groupby("person_name")["movie_id"].nunique().reset_index(name="shared_movies")
    counts.rename(columns={"person_name": "co_star"}, inplace=True)
    counts.sort_values("shared_movies", ascending=False, inplace=True)
    return counts.head(top_n)


# ==========================================
# 3. DIRECTOR ANALYTICS
# ==========================================

def top_directors(
    movies_df: pd.DataFrame,
    director_bridge: pd.DataFrame,
    min_movies: int = MIN_DIRECTOR_MOVIES,
    sort_by: str = "total_revenue",
    top_n: int = 15
) -> pd.DataFrame:
    """Compute director rankings with vectorized aggregation and sample size thresholding."""
    if movies_df.empty or director_bridge.empty:
        return pd.DataFrame(columns=["person_id", "person_name", "movie_count", "total_revenue", "avg_revenue", "avg_rating", "avg_popularity", "avg_roi"])
        
    merged = director_bridge.merge(
        movies_df[["movie_id", "revenue", "vote_average", "vote_count", "popularity", "profit", "roi"]],
        on="movie_id",
        how="inner"
    )
    if merged.empty:
        return pd.DataFrame()
        
    # 1. Movie count filter
    counts = merged.groupby(["person_id", "person_name"], observed=True)["movie_id"].nunique().reset_index(name="movie_count")
    counts = counts[counts["movie_count"] >= min_movies]
    if counts.empty:
        return pd.DataFrame()
        
    qual_merged = merged.merge(counts[["person_id", "person_name"]], on=["person_id", "person_name"], how="inner")
    
    # 2. Revenue aggregates (revenue > 0)
    rev_sub = qual_merged[qual_merged["revenue"].notna() & (qual_merged["revenue"] > 0)]
    rev_agg = rev_sub.groupby(["person_id", "person_name"], observed=True)["revenue"].agg(
        total_revenue="sum", avg_revenue="mean"
    ).reset_index()
    
    # 3. Rating aggregates (vote_count >= VOTE_COUNT_MIN)
    rate_sub = qual_merged[qual_merged["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
    rate_agg = rate_sub.groupby(["person_id", "person_name"], observed=True)["vote_average"].mean().reset_index(name="avg_rating")
    
    # 4. Popularity and ROI
    pop_agg = qual_merged.groupby(["person_id", "person_name"], observed=True)["popularity"].mean().reset_index(name="avg_popularity")
    roi_sub = qual_merged[qual_merged["roi"].notna()]
    roi_agg = roi_sub.groupby(["person_id", "person_name"], observed=True)["roi"].mean().reset_index(name="avg_roi")
    
    # 5. Assemble result
    res_df = counts.merge(rev_agg, on=["person_id", "person_name"], how="left")
    res_df["total_revenue"] = res_df["total_revenue"].fillna(0.0)
    res_df = res_df.merge(rate_agg, on=["person_id", "person_name"], how="left")
    res_df = res_df.merge(pop_agg, on=["person_id", "person_name"], how="left")
    res_df = res_df.merge(roi_agg, on=["person_id", "person_name"], how="left")
    
    if sort_by in res_df.columns:
        res_df.sort_values(by=sort_by, ascending=False, inplace=True)
    return res_df.head(top_n)


def director_detail(
    person_name: str,
    movies_df: pd.DataFrame,
    director_bridge: pd.DataFrame,
    genre_bridge: pd.DataFrame
) -> Dict:
    """Retrieve filmography and metrics for an individual director."""
    dir_rows = director_bridge[director_bridge["person_name"] == person_name]
    if dir_rows.empty:
        return {}
        
    dir_movie_ids = dir_rows["movie_id"].unique()
    filmography = movies_df[movies_df["movie_id"].isin(dir_movie_ids)].copy()
    
    genres = genre_bridge[genre_bridge["movie_id"].isin(dir_movie_ids)]
    top_genres = genres["genre_name"].value_counts().head(3).index.tolist() if not genres.empty else []
    
    rev_sub = filmography[filmography["revenue"].notna() & (filmography["revenue"] > 0)]
    rate_sub = filmography[filmography["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
    
    best_rated = rate_sub.sort_values("vote_average", ascending=False).iloc[0] if not rate_sub.empty else None
    highest_grossing = rev_sub.sort_values("revenue", ascending=False).iloc[0] if not rev_sub.empty else None
    most_popular = filmography.sort_values("popularity", ascending=False).iloc[0] if not filmography.empty else None
    
    return {
        "person_name": person_name,
        "movie_count": len(filmography),
        "total_revenue": rev_sub["revenue"].sum() if not rev_sub.empty else 0.0,
        "avg_revenue": rev_sub["revenue"].mean() if not rev_sub.empty else np.nan,
        "avg_rating": rate_sub["vote_average"].mean() if not rate_sub.empty else np.nan,
        "avg_popularity": filmography["popularity"].mean() if not filmography.empty else np.nan,
        "top_genres": top_genres,
        "filmography": filmography.sort_values("release_year", ascending=False),
        "best_rated": best_rated,
        "highest_grossing": highest_grossing,
        "most_popular": most_popular
    }


# ==========================================
# 4. FINANCIAL & YEARLY ANALYTICS
# ==========================================

def yearly_financials(movies_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate financial and rating trends by release year."""
    if movies_df.empty or "release_year" not in movies_df.columns:
        return pd.DataFrame(columns=[
            "release_year", "movie_count", "revenue_count", "total_revenue",
            "avg_revenue", "budget_count", "total_budget", "avg_budget", "avg_rating", "avg_popularity"
        ])
        
    valid = movies_df[movies_df["release_year"].notna()].copy()
    valid["release_year"] = valid["release_year"].astype(int)
    
    records = []
    for yr, grp in valid.groupby("release_year"):
        rev_sub = grp[grp["revenue"].notna() & (grp["revenue"] > 0)]
        bud_sub = grp[grp["budget"].notna() & (grp["budget"] > 0)]
        rate_sub = grp[grp["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
        
        records.append({
            "release_year": yr,
            "movie_count": len(grp),
            "revenue_count": len(rev_sub),
            "total_revenue": rev_sub["revenue"].sum() if not rev_sub.empty else 0.0,
            "avg_revenue": rev_sub["revenue"].mean() if not rev_sub.empty else np.nan,
            "budget_count": len(bud_sub),
            "total_budget": bud_sub["budget"].sum() if not bud_sub.empty else 0.0,
            "avg_budget": bud_sub["budget"].mean() if not bud_sub.empty else np.nan,
            "avg_rating": rate_sub["vote_average"].mean() if not rate_sub.empty else np.nan,
            "avg_popularity": grp["popularity"].mean() if grp["popularity"].notna().any() else np.nan
        })
        
    res_df = pd.DataFrame(records)
    if not res_df.empty:
        res_df.sort_values("release_year", inplace=True)
    return res_df


# ==========================================
# 5. COUNTRY & KEYWORD ANALYTICS
# ==========================================

def country_financials(
    movies_df: pd.DataFrame,
    country_bridge: pd.DataFrame,
    min_sample: int = 5
) -> pd.DataFrame:
    """Aggregate production statistics by country with vectorized operations and ISO-3 codes."""
    if movies_df.empty or country_bridge.empty:
        return pd.DataFrame(columns=["country_name", "iso_3166_1", "iso_3166_1_alpha3", "movie_count", "total_revenue", "avg_revenue", "avg_rating", "avg_popularity"])
        
    merged = country_bridge.merge(
        movies_df[["movie_id", "revenue", "vote_average", "vote_count", "popularity"]],
        on="movie_id",
        how="inner"
    )
    if merged.empty:
        return pd.DataFrame()
        
    # Group columns: include iso_3166_1_alpha3 if present
    group_cols = ["country_name", "iso_3166_1"]
    if "iso_3166_1_alpha3" in merged.columns:
        group_cols.append("iso_3166_1_alpha3")
        
    # 1. Movie count
    counts = merged.groupby(group_cols, observed=True)["movie_id"].nunique().reset_index(name="movie_count")
    counts = counts[counts["movie_count"] >= min_sample]
    if counts.empty:
        return pd.DataFrame()
        
    qual = merged.merge(counts[group_cols], on=group_cols, how="inner")
    
    # 2. Revenue (revenue > 0)
    rev_sub = qual[qual["revenue"].notna() & (qual["revenue"] > 0)]
    rev_agg = rev_sub.groupby(group_cols, observed=True)["revenue"].agg(
        total_revenue="sum", avg_revenue="mean"
    ).reset_index() if not rev_sub.empty else pd.DataFrame(columns=group_cols + ["total_revenue", "avg_revenue"])
    
    # 3. Rating (vote_count >= VOTE_COUNT_MIN)
    rate_sub = qual[qual["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
    rate_agg = rate_sub.groupby(group_cols, observed=True)["vote_average"].mean().reset_index(name="avg_rating") if not rate_sub.empty else pd.DataFrame(columns=group_cols + ["avg_rating"])
    
    # 4. Popularity
    pop_agg = qual.groupby(group_cols, observed=True)["popularity"].mean().reset_index(name="avg_popularity")
    
    # 5. Assemble
    res_df = counts.merge(rev_agg, on=group_cols, how="left")
    res_df["total_revenue"] = res_df["total_revenue"].fillna(0.0)
    res_df = res_df.merge(rate_agg, on=group_cols, how="left")
    res_df = res_df.merge(pop_agg, on=group_cols, how="left")
    
    # Ensure iso_3166_1_alpha3 exists
    if "iso_3166_1_alpha3" not in res_df.columns:
        from src.utils import ISO2_TO_ISO3
        res_df["iso_3166_1_alpha3"] = res_df["iso_3166_1"].map(ISO2_TO_ISO3)
        
    res_df.sort_values(by="movie_count", ascending=False, inplace=True)
    return res_df


def keyword_stats(
    movies_df: pd.DataFrame,
    keyword_bridge: pd.DataFrame,
    min_support: int = MIN_KEYWORD_SUPPORT,
    top_n: int = 20
) -> pd.DataFrame:
    """Compute keyword frequency and revenue associations with support thresholding."""
    if movies_df.empty or keyword_bridge.empty:
        return pd.DataFrame(columns=["keyword_name", "movie_count", "avg_revenue", "avg_rating"])
        
    merged = keyword_bridge.merge(
        movies_df[["movie_id", "revenue", "vote_average", "vote_count"]],
        on="movie_id",
        how="inner"
    )
    if merged.empty:
        return pd.DataFrame()
        
    kw_counts = merged.groupby("keyword_name")["movie_id"].nunique()
    qualifying = kw_counts[kw_counts >= min_support].index
    
    filtered = merged[merged["keyword_name"].isin(qualifying)]
    records = []
    for kw, grp in filtered.groupby("keyword_name"):
        rev_sub = grp[grp["revenue"].notna() & (grp["revenue"] > 0)]
        rate_sub = grp[grp["vote_count"].fillna(0) >= VOTE_COUNT_MIN]
        
        records.append({
            "keyword_name": kw,
            "movie_count": grp["movie_id"].nunique(),
            "avg_revenue": rev_sub["revenue"].mean() if not rev_sub.empty else np.nan,
            "avg_rating": rate_sub["vote_average"].mean() if not rate_sub.empty else np.nan
        })
        
    res_df = pd.DataFrame(records)
    if not res_df.empty:
        res_df.sort_values("movie_count", ascending=False, inplace=True)
        return res_df.head(top_n)
    return res_df


def keywords_by_genre(
    genre_name: str,
    movies_df: pd.DataFrame,
    keyword_bridge: pd.DataFrame,
    genre_bridge: pd.DataFrame,
    top_n: int = 15
) -> pd.DataFrame:
    """Top keywords for a specific genre."""
    genre_m_ids = genre_bridge[genre_bridge["genre_name"] == genre_name]["movie_id"].unique()
    if len(genre_m_ids) == 0 or keyword_bridge.empty:
        return pd.DataFrame(columns=["keyword_name", "movie_count"])
        
    kw_subset = keyword_bridge[keyword_bridge["movie_id"].isin(genre_m_ids)]
    top_kw = kw_subset["keyword_name"].value_counts().head(top_n).reset_index()
    top_kw.columns = ["keyword_name", "movie_count"]
    return top_kw


# ==========================================
# 6. ADVANCED STATISTICAL METRICS
# ==========================================

def compute_underrated_movies(
    movies_df: pd.DataFrame,
    min_votes: int = VOTE_COUNT_MIN,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Flag underrated movies using release-year cohort z-scores.
    Condition: vote_average z-score >= 1.28 (top 10%) & popularity z-score <= 0.0 (bottom 50%).
    """
    if movies_df.empty or "vote_count" not in movies_df.columns:
        return pd.DataFrame()

    valid = movies_df[
        (movies_df["vote_count"].fillna(0) >= min_votes) &
        movies_df["release_year"].notna() &
        movies_df["vote_average"].notna() &
        movies_df["popularity"].notna()
    ].copy()
    
    if len(valid) < 20:
        return pd.DataFrame()
        
    r_mean = valid.groupby("release_year")["vote_average"].transform("mean")
    r_std = valid.groupby("release_year")["vote_average"].transform("std").fillna(0)
    p_mean = valid.groupby("release_year")["popularity"].transform("mean")
    p_std = valid.groupby("release_year")["popularity"].transform("std").fillna(0)
    cohort_count = valid.groupby("release_year")["vote_average"].transform("count")

    valid["rating_z"] = np.where((cohort_count >= 5) & (r_std > 0), (valid["vote_average"] - r_mean) / r_std, np.nan)
    valid["pop_z"] = np.where((cohort_count >= 5) & (p_std > 0), (valid["popularity"] - p_mean) / p_std, np.nan)

    underrated = valid[(valid["rating_z"] >= 1.28) & (valid["pop_z"] <= 0.0)].copy()
    if not underrated.empty:
        underrated.sort_values(by="rating_z", ascending=False, inplace=True)
        return underrated.head(top_n)
    return pd.DataFrame()


def compute_overhyped_movies(
    movies_df: pd.DataFrame,
    min_votes: int = VOTE_COUNT_MIN,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Flag overhyped movies using release-year cohort z-scores.
    Condition: popularity z-score >= 1.28 (top 10%) & vote_average z-score <= 0.0 (bottom 50%).
    """
    if movies_df.empty or "vote_count" not in movies_df.columns:
        return pd.DataFrame()

    valid = movies_df[
        (movies_df["vote_count"].fillna(0) >= min_votes) &
        movies_df["release_year"].notna() &
        movies_df["vote_average"].notna() &
        movies_df["popularity"].notna()
    ].copy()
    
    if len(valid) < 20:
        return pd.DataFrame()
        
    r_mean = valid.groupby("release_year")["vote_average"].transform("mean")
    r_std = valid.groupby("release_year")["vote_average"].transform("std").fillna(0)
    p_mean = valid.groupby("release_year")["popularity"].transform("mean")
    p_std = valid.groupby("release_year")["popularity"].transform("std").fillna(0)
    cohort_count = valid.groupby("release_year")["vote_average"].transform("count")

    valid["rating_z"] = np.where((cohort_count >= 5) & (r_std > 0), (valid["vote_average"] - r_mean) / r_std, np.nan)
    valid["pop_z"] = np.where((cohort_count >= 5) & (p_std > 0), (valid["popularity"] - p_mean) / p_std, np.nan)

    overhyped = valid[(valid["pop_z"] >= 1.28) & (valid["rating_z"] <= 0.0)].copy()
    if not overhyped.empty:
        overhyped.sort_values(by="pop_z", ascending=False, inplace=True)
        return overhyped.head(top_n)
    return pd.DataFrame()


def compute_director_consistency(
    movies_df: pd.DataFrame,
    director_bridge: pd.DataFrame,
    min_movies: int = MIN_DIRECTOR_MOVIES,
    min_votes: int = VOTE_COUNT_MIN,
    top_n: int = 20
) -> pd.DataFrame:
    """
    Calculate rating consistency across a director's filmography.
    Formula: 1 / (std(vote_average) / mean(vote_average))
    Higher score denotes more reliable quality across filmography.
    """
    if movies_df.empty or director_bridge.empty:
        return pd.DataFrame(columns=["person_name", "movie_count", "mean_rating", "rating_std", "consistency_score"])
        
    merged = director_bridge.merge(
        movies_df[["movie_id", "vote_average", "vote_count"]],
        on="movie_id",
        how="inner"
    )
    rated = merged[merged["vote_count"].fillna(0) >= min_votes]
    if rated.empty:
        return pd.DataFrame()
        
    records = []
    for p_name, grp in rated.groupby("person_name"):
        m_cnt = grp["movie_id"].nunique()
        if m_cnt < min_movies:
            continue
        m_rate = grp["vote_average"].mean()
        s_rate = grp["vote_average"].std()
        
        # Guard against zero or NaN std
        if np.isnan(s_rate) or s_rate < 0.01:
            cv = 0.01 / m_rate if m_rate > 0 else 1.0
        else:
            cv = s_rate / m_rate if m_rate > 0 else 1.0
            
        consistency = 1.0 / cv if cv > 0 else 0.0
        records.append({
            "person_name": p_name,
            "movie_count": m_cnt,
            "mean_rating": m_rate,
            "rating_std": s_rate if not np.isnan(s_rate) else 0.0,
            "consistency_score": consistency
        })
        
    res_df = pd.DataFrame(records)
    if not res_df.empty:
        res_df.sort_values(by="consistency_score", ascending=False, inplace=True)
        return res_df.head(top_n)
    return res_df


def compute_actor_consistency(
    movies_df: pd.DataFrame,
    actor_bridge: pd.DataFrame,
    min_movies: int = MIN_ACTOR_MOVIES,
    min_votes: int = VOTE_COUNT_MIN,
    top_n: int = 20
) -> pd.DataFrame:
    """Calculate rating consistency for actors."""
    if movies_df.empty or actor_bridge.empty:
        return pd.DataFrame(columns=["person_name", "movie_count", "mean_rating", "rating_std", "consistency_score"])
        
    merged = actor_bridge.merge(
        movies_df[["movie_id", "vote_average", "vote_count"]],
        on="movie_id",
        how="inner"
    )
    rated = merged[merged["vote_count"].fillna(0) >= min_votes]
    if rated.empty:
        return pd.DataFrame()
        
    records = []
    for p_name, grp in rated.groupby("person_name"):
        m_cnt = grp["movie_id"].nunique()
        if m_cnt < min_movies:
            continue
        m_rate = grp["vote_average"].mean()
        s_rate = grp["vote_average"].std()
        
        if np.isnan(s_rate) or s_rate < 0.01:
            cv = 0.01 / m_rate if m_rate > 0 else 1.0
        else:
            cv = s_rate / m_rate if m_rate > 0 else 1.0
            
        consistency = 1.0 / cv if cv > 0 else 0.0
        records.append({
            "person_name": p_name,
            "movie_count": m_cnt,
            "mean_rating": m_rate,
            "rating_std": s_rate if not np.isnan(s_rate) else 0.0,
            "consistency_score": consistency
        })
        
    res_df = pd.DataFrame(records)
    if not res_df.empty:
        res_df.sort_values(by="consistency_score", ascending=False, inplace=True)
        return res_df.head(top_n)
    return res_df


def calculate_correlations(movies_df: pd.DataFrame) -> Dict[str, float]:
    """Calculate Pearson correlation coefficients across valid numeric pairs."""
    corrs = {}
    
    # 1. Budget vs Revenue (both > 0)
    bud_rev = movies_df[movies_df["budget"].notna() & (movies_df["budget"] > 0) & movies_df["revenue"].notna() & (movies_df["revenue"] > 0)]
    corrs["budget_vs_revenue"] = float(bud_rev["budget"].corr(bud_rev["revenue"])) if len(bud_rev) > 5 else np.nan
    
    # 2. Budget vs Rating (budget > 0, vote_count >= VOTE_COUNT_MIN)
    bud_rate = movies_df[movies_df["budget"].notna() & (movies_df["budget"] > 0) & (movies_df["vote_count"].fillna(0) >= VOTE_COUNT_MIN)]
    corrs["budget_vs_rating"] = float(bud_rate["budget"].corr(bud_rate["vote_average"])) if len(bud_rate) > 5 else np.nan
    
    # 3. Budget vs Popularity (budget > 0)
    bud_pop = movies_df[movies_df["budget"].notna() & (movies_df["budget"] > 0) & movies_df["popularity"].notna()]
    corrs["budget_vs_popularity"] = float(bud_pop["budget"].corr(bud_pop["popularity"])) if len(bud_pop) > 5 else np.nan
    
    # 4. Revenue vs Popularity (revenue > 0)
    rev_pop = movies_df[movies_df["revenue"].notna() & (movies_df["revenue"] > 0) & movies_df["popularity"].notna()]
    corrs["revenue_vs_popularity"] = float(rev_pop["revenue"].corr(rev_pop["popularity"])) if len(rev_pop) > 5 else np.nan
    
    # 5. Rating vs Popularity (vote_count >= VOTE_COUNT_MIN)
    rate_pop = movies_df[(movies_df["vote_count"].fillna(0) >= VOTE_COUNT_MIN) & movies_df["popularity"].notna()]
    corrs["rating_vs_popularity"] = float(rate_pop["vote_average"].corr(rate_pop["popularity"])) if len(rate_pop) > 5 else np.nan
    
    # 6. Runtime vs Rating (runtime > 0, vote_count >= VOTE_COUNT_MIN)
    run_rate = movies_df[movies_df["runtime"].notna() & (movies_df["runtime"] > 0) & (movies_df["vote_count"].fillna(0) >= VOTE_COUNT_MIN)]
    corrs["runtime_vs_rating"] = float(run_rate["runtime"].corr(run_rate["vote_average"])) if len(run_rate) > 5 else np.nan
    
    return corrs

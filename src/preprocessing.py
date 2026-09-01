"""ETL Preprocessing Pipeline for raw movie dataset."""
import ast
import logging
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from src.transformations import add_financial_metrics, build_display_strings
from src.utils import MAIN_CAST_ORDER_LIMIT

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def safe_parse_json(val):
    """Safely parse stringified JSON/Python literals using ast.literal_eval."""
    if not isinstance(val, str) or not val.strip():
        return []
    try:
        parsed = ast.literal_eval(val)
        if isinstance(parsed, list):
            return parsed
        elif isinstance(parsed, dict):
            return [parsed]
        return []
    except (ValueError, SyntaxError, TypeError):
        return []


def clean_movies_metadata(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean movies_metadata raw dataframe:
    - Drop malformed rows where id is not numeric.
    - Cast id, budget, popularity, release_date, runtime, etc.
    - Treat 0 budget/revenue/runtime as NaN.
    - Filter status == 'Released' or 'Post Production'.
    - Deduplicate IDs using completeness-based heuristic.
    """
    logger.info(f"Initial movies_metadata rows: {len(raw_df)}")
    
    # 1. Identify & drop malformed rows where id is non-numeric (e.g. dates in id)
    raw_df["id_str"] = raw_df["id"].astype(str).str.strip()
    is_numeric_id = raw_df["id_str"].str.match(r"^\d+$", na=False)
    malformed_count = (~is_numeric_id).sum()
    logger.info(f"Dropped {malformed_count} malformed rows with corrupted id field.")
    df = raw_df[is_numeric_id].copy()
    df["id"] = df["id_str"].astype(np.int64)
    df.drop(columns=["id_str"], inplace=True)
    
    # 2. Cast numeric columns
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce")
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce")
    df["runtime"] = pd.to_numeric(df["runtime"], errors="coerce")
    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce")
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce")
    
    # 3. Convert 0 budget and 0 revenue to NaN (unreported)
    df.loc[df["budget"] == 0, "budget"] = np.nan
    df.loc[df["revenue"] == 0, "revenue"] = np.nan
    
    # 4. Convert 0 runtime to NaN and add runtime outlier flag (>300 min)
    df.loc[df["runtime"] == 0, "runtime"] = np.nan
    df["runtime_outlier"] = df["runtime"] > 300
    
    # 5. Parse release_date and derive release_year, release_decade
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year.astype("Int64")
    df["release_decade"] = (df["release_year"] // 10 * 10).astype("Int64")
    
    # 6. Filter status (keep Released and Post Production)
    initial_status_count = len(df)
    valid_statuses = {"Released", "Post Production"}
    status_mask = df["status"].fillna("Unknown").isin(valid_statuses)
    excluded_status_count = initial_status_count - status_mask.sum()
    logger.info(f"Excluded {excluded_status_count} movies with non-released status (Rumored, Planned, In Production, Canceled, Unknown).")
    df = df[status_mask].copy()
    
    # 7. Deduplicate id by completeness heuristic
    # Calculate null count across key analytics fields
    key_fields = ["budget", "revenue", "runtime", "vote_count", "overview", "tagline"]
    df["_null_count"] = df[key_fields].isnull().sum(axis=1)
    df.sort_values(by=["id", "_null_count"], ascending=[True, True], inplace=True)
    df.drop_duplicates(subset=["id"], keep="first", inplace=True)
    df.drop(columns=["_null_count"], inplace=True)
    
    df.rename(columns={"id": "movie_id"}, inplace=True)
    logger.info(f"Cleaned movies_metadata rows remaining: {len(df)}")
    return df


def clean_credits(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and deduplicate credits dataset."""
    logger.info(f"Initial credits rows: {len(raw_df)}")
    df = raw_df.copy()
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df.dropna(subset=["id"], inplace=True)
    df["id"] = df["id"].astype(np.int64)
    df.drop_duplicates(subset=["id"], keep="first", inplace=True)
    df.rename(columns={"id": "movie_id"}, inplace=True)
    logger.info(f"Cleaned credits rows remaining: {len(df)}")
    return df


def clean_keywords(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and deduplicate keywords dataset."""
    logger.info(f"Initial keywords rows: {len(raw_df)}")
    df = raw_df.copy()
    df.drop_duplicates(inplace=True)
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df.dropna(subset=["id"], inplace=True)
    df["id"] = df["id"].astype(np.int64)
    df.drop_duplicates(subset=["id"], keep="first", inplace=True)
    df.rename(columns={"id": "movie_id"}, inplace=True)
    logger.info(f"Cleaned keywords rows remaining: {len(df)}")
    return df


def build_bridge_tables(
    movies_df: pd.DataFrame, credits_df: pd.DataFrame, keywords_df: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Parse JSON fields and construct exploded bridge tables.
    Only keeps bridge rows referencing valid movie_ids in movies_df.
    """
    valid_movie_ids = set(movies_df["movie_id"])
    
    # 1. Genre Bridge
    logger.info("Building genre_bridge...")
    genre_rows = []
    for _, row in movies_df[["movie_id", "genres"]].iterrows():
        m_id = row["movie_id"]
        parsed = safe_parse_json(row["genres"])
        for item in parsed:
            if isinstance(item, dict) and "name" in item:
                genre_rows.append({
                    "movie_id": m_id,
                    "genre_id": item.get("id", np.nan),
                    "genre_name": str(item["name"]).strip()
                })
    genre_bridge = pd.DataFrame(genre_rows)
    if not genre_bridge.empty:
        genre_bridge = genre_bridge[genre_bridge["movie_id"].isin(valid_movie_ids)].drop_duplicates()
        genre_bridge["genre_name"] = genre_bridge["genre_name"].astype("category")
    logger.info(f"Genre bridge rows: {len(genre_bridge)}")

    # 2. Country Bridge
    logger.info("Building country_bridge...")
    from src.utils import ISO2_TO_ISO3
    country_rows = []
    for _, row in movies_df[["movie_id", "production_countries"]].iterrows():
        m_id = row["movie_id"]
        parsed = safe_parse_json(row["production_countries"])
        for item in parsed:
            if isinstance(item, dict) and "name" in item:
                iso2 = str(item.get("iso_3166_1", "")).strip().upper()
                iso3 = ISO2_TO_ISO3.get(iso2, iso2)
                country_rows.append({
                    "movie_id": m_id,
                    "iso_3166_1": iso2,
                    "iso_3166_1_alpha3": iso3,
                    "country_name": str(item["name"]).strip()
                })
    country_bridge = pd.DataFrame(country_rows)
    if not country_bridge.empty:
        country_bridge = country_bridge[country_bridge["movie_id"].isin(valid_movie_ids)].drop_duplicates()
        country_bridge["country_name"] = country_bridge["country_name"].astype("category")
        country_bridge["iso_3166_1"] = country_bridge["iso_3166_1"].astype("category")
        country_bridge["iso_3166_1_alpha3"] = country_bridge["iso_3166_1_alpha3"].astype("category")
    logger.info(f"Country bridge rows: {len(country_bridge)}")

    # 3. Keyword Bridge
    logger.info("Building keyword_bridge...")
    kw_subset = keywords_df[keywords_df["movie_id"].isin(valid_movie_ids)]
    kw_rows = []
    for _, row in kw_subset.iterrows():
        m_id = row["movie_id"]
        parsed = safe_parse_json(row["keywords"])
        for item in parsed:
            if isinstance(item, dict) and "name" in item:
                kw_rows.append({
                    "movie_id": m_id,
                    "keyword_id": item.get("id", np.nan),
                    "keyword_name": str(item["name"]).strip().lower()
                })
    keyword_bridge = pd.DataFrame(kw_rows)
    if not keyword_bridge.empty:
        keyword_bridge = keyword_bridge.drop_duplicates()
    logger.info(f"Keyword bridge rows: {len(keyword_bridge)}")

    # 4. Cast & Crew Bridges (Actor, Director, Extended Crew)
    logger.info("Building actor_bridge, director_bridge, crew_bridge_extended...")
    credits_subset = credits_df[credits_df["movie_id"].isin(valid_movie_ids)]
    
    actor_rows = []
    director_rows = []
    extended_crew_rows = []
    
    for _, row in credits_subset.iterrows():
        m_id = row["movie_id"]
        
        # Cast
        cast_list = safe_parse_json(row["cast"])
        for item in cast_list:
            if isinstance(item, dict) and "name" in item:
                order = item.get("order", 999)
                if order < MAIN_CAST_ORDER_LIMIT:
                    actor_rows.append({
                        "movie_id": m_id,
                        "person_id": item.get("id", np.nan),
                        "person_name": str(item["name"]).strip(),
                        "character": str(item.get("character", "")).strip(),
                        "cast_order": int(order)
                    })
                    
        # Crew
        crew_list = safe_parse_json(row["crew"])
        for item in crew_list:
            if isinstance(item, dict) and "name" in item:
                job = str(item.get("job", "")).strip()
                p_name = str(item["name"]).strip()
                p_id = item.get("id", np.nan)
                dept = str(item.get("department", "")).strip()
                
                if job == "Director":
                    director_rows.append({
                        "movie_id": m_id,
                        "person_id": p_id,
                        "person_name": p_name
                    })
                
                # Extended crew roles: Director, Screenplay, Writer, Producer, Composer, DP, Editor
                extended_crew_rows.append({
                    "movie_id": m_id,
                    "person_id": p_id,
                    "person_name": p_name,
                    "job": job,
                    "department": dept
                })

    actor_bridge = pd.DataFrame(actor_rows).drop_duplicates() if actor_rows else pd.DataFrame(columns=["movie_id", "person_id", "person_name", "character", "cast_order"])
    director_bridge = pd.DataFrame(director_rows).drop_duplicates() if director_rows else pd.DataFrame(columns=["movie_id", "person_id", "person_name"])
    crew_bridge_extended = pd.DataFrame(extended_crew_rows).drop_duplicates() if extended_crew_rows else pd.DataFrame(columns=["movie_id", "person_id", "person_name", "job", "department"])

    logger.info(f"Actor bridge (main cast < 10) rows: {len(actor_bridge)}")
    logger.info(f"Director bridge rows: {len(director_bridge)}")
    logger.info(f"Extended crew bridge rows: {len(crew_bridge_extended)}")

    return {
        "genre_bridge": genre_bridge,
        "country_bridge": country_bridge,
        "keyword_bridge": keyword_bridge,
        "actor_bridge": actor_bridge,
        "director_bridge": director_bridge,
        "crew_bridge_extended": crew_bridge_extended
    }


def finalize_fact_table(movies_df: pd.DataFrame, bridges: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Apply feature engineering and optimize fact table dtypes."""
    logger.info("Finalizing movies fact table...")
    df = add_financial_metrics(movies_df)
    df = build_display_strings(
        df,
        bridges["genre_bridge"],
        bridges["keyword_bridge"],
        bridges["director_bridge"],
        bridges["actor_bridge"]
    )
    
    # Derived count features
    genre_cnt = bridges["genre_bridge"].groupby("movie_id").size()
    kw_cnt = bridges["keyword_bridge"].groupby("movie_id").size()
    dir_cnt = bridges["director_bridge"].groupby("movie_id").size()
    actor_cnt = bridges["actor_bridge"].groupby("movie_id").size()
    
    df["n_genres"] = df["movie_id"].map(genre_cnt).fillna(0).astype("int16")
    df["n_keywords"] = df["movie_id"].map(kw_cnt).fillna(0).astype("int16")
    df["n_directors"] = df["movie_id"].map(dir_cnt).fillna(0).astype("int16")
    df["has_director"] = df["n_directors"] > 0
    df["main_cast_size"] = df["movie_id"].map(actor_cnt).fillna(0).astype("int16")
    
    # Drop raw unparsed stringified JSON columns to save disk & memory
    cols_to_drop = [
        "genres", "production_countries", "spoken_languages", "production_companies",
        "belongs_to_collection"
    ]
    df.drop(columns=[c for c in cols_to_drop if c in df.columns], inplace=True)
    
    # Optimize numeric dtypes (float32, Int64)
    float_cols = ["popularity", "vote_average", "budget", "revenue", "runtime", "profit", "roi"]
    for c in float_cols:
        if c in df.columns:
            df[c] = df[c].astype("float32")
            
    if "vote_count" in df.columns:
        df["vote_count"] = df["vote_count"].astype("Int64")
        
    if "original_language" in df.columns:
        df["original_language"] = df["original_language"].astype("category")
    if "status" in df.columns:
        df["status"] = df["status"].astype("category")
        
    return df

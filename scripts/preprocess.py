"""CLI script to run the offline preprocessing pipeline and precompute analytical summary tables."""
import logging
import sys
import time
from pathlib import Path

import pandas as pd

# Add repo root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.analytics import (
    country_financials,
    genre_financials,
    keyword_stats,
    top_actors,
    top_directors,
    yearly_financials
)
from src.preprocessing import (
    build_bridge_tables,
    clean_credits,
    clean_keywords,
    clean_movies_metadata,
    finalize_fact_table
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("preprocess_cli")

def run_preprocessing():
    start_time = time.time()
    logger.info("Starting CineLens offline preprocessing pipeline...")
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load raw files
    movies_csv = raw_dir / "movies_metadata.csv"
    credits_csv = raw_dir / "credits.csv"
    keywords_csv = raw_dir / "keywords.csv"
    
    if not movies_csv.exists() or not credits_csv.exists() or not keywords_csv.exists():
        logger.error(f"Raw CSV files not found in {raw_dir.resolve()}. Please ensure files exist.")
        sys.exit(1)
        
    logger.info("Loading movies_metadata.csv...")
    raw_movies = pd.read_csv(movies_csv, low_memory=False, dtype={"id": str})
    
    logger.info("Loading credits.csv...")
    raw_credits = pd.read_csv(credits_csv, low_memory=False, dtype={"id": str})
    
    logger.info("Loading keywords.csv...")
    raw_keywords = pd.read_csv(keywords_csv, low_memory=False, dtype={"id": str})
    
    # 2. Clean base dataframes
    clean_movies = clean_movies_metadata(raw_movies)
    clean_cred = clean_credits(raw_credits)
    clean_kw = clean_keywords(raw_keywords)
    
    # 3. Build bridge tables
    bridges = build_bridge_tables(clean_movies, clean_cred, clean_kw)
    
    # 4. Finalize Fact Table
    movies_fact = finalize_fact_table(clean_movies, bridges)
    
    # 5. Referential Integrity Checks
    logger.info("Performing referential integrity validation...")
    fact_ids = set(movies_fact["movie_id"])
    assert len(movies_fact) == len(fact_ids), "Duplicate movie_ids found in movies fact table!"
    
    for name, bridge_df in bridges.items():
        if not bridge_df.empty and "movie_id" in bridge_df.columns:
            bridge_ids = set(bridge_df["movie_id"])
            orphan_ids = bridge_ids - fact_ids
            assert len(orphan_ids) == 0, f"Found {len(orphan_ids)} orphan movie_ids in {name}!"
            logger.info(f"Integrity check passed for {name} ({len(bridge_df)} rows).")
            
    # 6. Precompute Analytical Summary Tables
    logger.info("Precomputing analytical summary tables for sub-second UI rendering...")
    genre_summary = genre_financials(movies_fact, bridges["genre_bridge"], min_sample=1)
    yearly_summary = yearly_financials(movies_fact)
    country_summary = country_financials(movies_fact, bridges["country_bridge"], min_sample=1)
    keyword_summary = keyword_stats(movies_fact, bridges["keyword_bridge"], min_support=10, top_n=100)
    actor_summary = top_actors(movies_fact, bridges["actor_bridge"], min_movies=3, top_n=200)
    director_summary = top_directors(movies_fact, bridges["director_bridge"], min_movies=2, top_n=200)
    
    # Overview KPI Summary (Single-row precomputed table)
    rev_valid = movies_fact[movies_fact["revenue"] > 0]
    rated_sub = movies_fact[movies_fact["vote_count"].fillna(0) >= 20]
    overview_kpis = pd.DataFrame([{
        "total_movies": int(len(movies_fact)),
        "total_revenue": float(rev_valid["revenue"].sum()) if not rev_valid.empty else 0.0,
        "avg_revenue": float(rev_valid["revenue"].mean()) if not rev_valid.empty else 0.0,
        "avg_rating": float(rated_sub["vote_average"].mean()) if not rated_sub.empty else 0.0,
        "avg_popularity": float(movies_fact["popularity"].mean()) if "popularity" in movies_fact.columns else 0.0,
        "avg_runtime": float(movies_fact.loc[movies_fact["runtime"] > 0, "runtime"].mean()) if not movies_fact.loc[movies_fact["runtime"] > 0].empty else 0.0
    }])

    # 7. Save Parquet Files
    logger.info("Writing output Parquet files...")
    movies_fact.to_parquet(processed_dir / "movies.parquet", index=False, engine="pyarrow")
    for name, bridge_df in bridges.items():
        bridge_df.to_parquet(processed_dir / f"{name}.parquet", index=False, engine="pyarrow")
        
    genre_summary.to_parquet(processed_dir / "genre_summary.parquet", index=False, engine="pyarrow")
    yearly_summary.to_parquet(processed_dir / "yearly_summary.parquet", index=False, engine="pyarrow")
    country_summary.to_parquet(processed_dir / "country_summary.parquet", index=False, engine="pyarrow")
    keyword_summary.to_parquet(processed_dir / "keyword_summary.parquet", index=False, engine="pyarrow")
    actor_summary.to_parquet(processed_dir / "actor_summary.parquet", index=False, engine="pyarrow")
    director_summary.to_parquet(processed_dir / "director_summary.parquet", index=False, engine="pyarrow")
    overview_kpis.to_parquet(processed_dir / "overview_kpis.parquet", index=False, engine="pyarrow")
        
    duration = time.time() - start_time
    logger.info(f"Preprocessing & precomputation completed successfully in {duration:.2f} seconds!")
    logger.info(f"Summary of processed data saved in {processed_dir.resolve()}:")
    logger.info(f"  - movies.parquet: {len(movies_fact):,} rows")
    for name, bridge_df in bridges.items():
        logger.info(f"  - {name}.parquet: {len(bridge_df):,} rows")
    logger.info("  - 7 Precomputed summary tables generated.")

if __name__ == "__main__":
    run_preprocessing()

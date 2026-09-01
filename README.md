# 🎬 CineLens Analytics

> **Enterprise Movie Intelligence & Box Office Analytics Dashboard**  
> An interactive multi-page Streamlit application delivering relational-integrity-safe aggregation, statistical thresholding, z-score outlier detection, and an automated rule-based insight engine across 45,000+ film records.

---

## 🌟 7 Streamlined Analytical Sections

### 1. Executive Overview (`pages/1_Overview.py`)
- **Macro KPIs**: Total unique titles, reported global box office, average revenue, catalog rating averages, and TMDB popularity scores.
- **Automated Insights**: Dynamic plain-language synthesis highlighting volume leaders, top-earning categories, and catalog distribution stats.
- **Macro Trends**: Movies released by year, annual box office trajectory, rating histogram, and popularity score distribution.

### 2. Movie Explorer (`pages/2_Movie_Explorer.py`)
- **Vectorized Search**: Instant substring search across titles and original titles with rating/popularity/year sliders.
- **Pagination & Inspector**: 25-item page slicing with rich movie detail cards (taglines, overviews, genres, themes, and financial breakdowns). Operates with zero runtime bridge table joins.

### 3. Performance, Financials & Ratings (`pages/3_Performance.py`)
- **Box Office & Profitability Leaderboards**: Highest grossing titles, net profits (`Revenue - Budget`), and high-ROI multipliers with verified budget guard (`Budget ≥ $1,000,000`).
- **Production Economics & Regressions**: WebGL-accelerated Budget vs. Revenue and Budget vs. Rating scatter plots with OLS trendlines and Pearson correlation coefficients.
- **Ratings & Engagement Dynamics**: Score distributions, vote-count reliability funnel, and runtime extreme records.

### 4. Talent Intelligence — Directors & Actors (`pages/4_People.py`)
- **Director Analytics**: Filtered rankings (`Credits ≥ 3`), career box office averages, and deep-dive director filmography explorer with scatter timelines.
- **Actor Analytics**: Main-cast billing leaderboards (`cast_order < 10`, `Credits ≥ 5`), career timelines, and genre specialization badges.

### 5. Genres & Thematic Keywords (`pages/5_Genres_and_Themes.py`)
- **Relational-Safe Genre Intelligence**: Zero double-counting across 20 closed genres, cross-genre box office benchmarks, and single-genre drilldown.
- **Thematic Plot Keywords**: Tag frequency ranking (`Support ≥ 20`), genre-clustered narrative tags, and box office revenue associations.

### 6. Historical & Geographic Trends (`pages/6_Trends.py`)
- **Longitudinal Evolution**: Annual release counts, box office trajectories, and decadal stacked genre proportion shares.
- **Global Cinema Production**: Interactive world choropleth map plotting film production volume and box office grosses by ISO-3166-1 country codes.

### 7. Automated Insights & Movie Comparison (`pages/7_Insights.py`)
- **Dynamic Rule Engine**: Plain-language analytical rules synthesizing catalog leaders and trends.
- **Cohort Z-Score Outlier Models**: Statistically Underrated (top 10% rating, bottom 50% popularity in release-year cohort) and Overhyped titles.
- **Side-by-Side Title Comparison**: Multi-select 2 to 3 films for direct metric benchmarking and dual-axis grouped charts.

---

## 🏗️ Architecture & Data Pipeline

```
Raw CSV Datasets (movies_metadata.csv, credits.csv, keywords.csv)
                                │
                                ▼
         scripts/preprocess.py (Offline One-Time ETL)
  ┌───────────────────────────────────────────────────────────┐
  │ - Drops 3 corrupted rows (dates in id)                     │
  │ - Converts 0 budget, revenue, and runtime to NaN          │
  │ - Filters unreleased statuses (Rumored, Planned, Canceled) │
  │ - Deduplicates IDs via completeness heuristics             │
  │ - Parses nested JSON cast, crew, genres, keywords, origin │
  │ - Precomputes display strings & financial features        │
  │ - Optimizes dtypes (float32, Int64, category)             │
  └─────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
                       data/processed/
  ├── movies.parquet               (Fact Table, 45,083 unique films)
  ├── genre_bridge.parquet         (90,425 records)
  ├── actor_bridge.parquet         (339,941 main-cast records)
  ├── director_bridge.parquet      (48,656 director records)
  ├── country_bridge.parquet       (49,086 country records)
  ├── keyword_bridge.parquet       (156,172 keyword records)
  └── crew_bridge_extended.parquet (462,215 extended crew records)
                                │
                                ▼
               Streamlit Application Runtime (app.py)
  - True lazy loading (loads only required bridge tables per page)
  - Zero runtime JSON parsing or ast.literal_eval
  - Fast sub-second response times with @st.cache_data
```

---

## 🚀 Quickstart & Local Installation

### Prerequisites
- Python 3.11+

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch Streamlit Dashboard
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🧪 Automated Testing

Run the test suite verifying data cleaning, referential integrity, many-to-many safety, and zero-runtime JSON parsing:

```bash
pytest -v
```

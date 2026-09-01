"""Page 2: Movie Explorer & Catalog Browser."""
import math
import streamlit as st
import pandas as pd

from src.components import empty_state, inject_custom_css, page_header
from src.data_loader import load_movies
from src.filters import apply_global_filters, render_global_filters
from src.utils import format_currency, format_number, format_pct

inject_custom_css()
page_header("🔍 Movie Explorer", "Search, filter, sort, and inspect granular details across the complete movie catalog.")

# 1. Lazy load fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

# 3. Search & Sort Controls
st.markdown("### 🔎 Catalog Search & Sorting")
c_search, c_sort, c_order = st.columns([2, 1.2, 0.8])

with c_search:
    search_query = st.text_input("Search Title or Substring", placeholder="e.g. Inception, Godfather, Avatar...").strip()

with c_sort:
    sort_field = st.selectbox(
        "Sort By",
        options=["vote_average", "popularity", "revenue", "release_year", "profit", "roi", "runtime"],
        format_func=lambda x: {
            "vote_average": "Rating ★",
            "popularity": "Popularity",
            "revenue": "Box Office Revenue",
            "release_year": "Release Year",
            "profit": "Net Profit",
            "roi": "ROI Multiplier",
            "runtime": "Runtime"
        }.get(x, x)
    )

with c_order:
    sort_order = st.radio("Order", ["Descending", "Ascending"], horizontal=True)

# 4. Apply Vectorized Text Search
if search_query:
    title_mask = filtered_df["title"].fillna("").str.contains(search_query, case=False, regex=False)
    orig_mask = (
        filtered_df["original_title"].fillna("").str.contains(search_query, case=False, regex=False)
        if "original_title" in filtered_df.columns else False
    )
    filtered_df = filtered_df[title_mask | orig_mask]

if filtered_df.empty:
    empty_state(title="No matching movies found", message="No movies match your current search and filter combination.")
    st.stop()

# 5. Sorting
ascending = (sort_order == "Ascending")
filtered_df = filtered_df.sort_values(by=sort_field, ascending=ascending, na_position="last")

# 6. Fast Pagination (25 items/page)
PAGE_SIZE = 25
total_items = len(filtered_df)
total_pages = max(1, math.ceil(total_items / PAGE_SIZE))

if "explorer_page" not in st.session_state:
    st.session_state["explorer_page"] = 1

col_pg_info, col_pg_nav = st.columns([2, 1])
with col_pg_info:
    st.caption(f"Showing {total_items:,} movies (Page {st.session_state['explorer_page']} of {total_pages})")
with col_pg_nav:
    page_num = st.number_input("Go to page", min_value=1, max_value=total_pages, value=st.session_state["explorer_page"], step=1)
    st.session_state["explorer_page"] = page_num

start_idx = (st.session_state["explorer_page"] - 1) * PAGE_SIZE
end_idx = min(start_idx + PAGE_SIZE, total_items)
page_items = filtered_df.iloc[start_idx:end_idx]

st.markdown("---")

# 7. Movie Detail Inspector
st.markdown("### 🎬 Movie Detail Inspector")
selected_title = st.selectbox(
    "Select a title from current page results for full breakdown:",
    options=page_items["title"].tolist(),
    index=0
)

selected_movie = page_items[page_items["title"] == selected_title].iloc[0]

with st.container():
    m_col1, m_col2 = st.columns([1.5, 1])
    
    with m_col1:
        st.markdown(f"## {selected_movie['title']} ({int(selected_movie['release_year']) if pd.notna(selected_movie['release_year']) else 'N/A'})")
        if pd.notna(selected_movie.get("tagline")) and selected_movie.get("tagline"):
            st.markdown(f"*\"{selected_movie['tagline']}\"*")
            
        st.markdown(f"**Overview:** {selected_movie.get('overview', 'No overview summary available.')}")
        st.markdown(f"**Director:** `{selected_movie.get('director_display', 'Not credited')}`")
        st.markdown(f"**Top Cast:** `{selected_movie.get('top_cast_display', 'Not credited')}`")
        
        genres_str = str(selected_movie.get("genres_display", ""))
        chips_html = "".join([f'<span class="genre-chip">{g.strip()}</span>' for g in genres_str.split(",") if g.strip()])
        st.markdown(f"**Genres:** {chips_html}", unsafe_allow_html=True)
        
        kw_str = str(selected_movie.get("keywords_display", ""))
        kw_html = "".join([f'<span class="keyword-chip">{k.strip()}</span>' for k in kw_str.split(",")[:8] if k.strip()])
        st.markdown(f"**Themes:** {kw_html}", unsafe_allow_html=True)
        
    with m_col2:
        st.markdown("#### 📊 Financial & Critical Profile")
        st.write(f"**Rating:** {selected_movie.get('vote_average', 'N/A')} ★ ({int(selected_movie.get('vote_count', 0)):,} votes)")
        st.write(f"**Popularity:** {selected_movie.get('popularity', 'N/A'):.2f}")
        st.write(f"**Budget:** {format_currency(selected_movie.get('budget'))}")
        st.write(f"**Box Office Revenue:** {format_currency(selected_movie.get('revenue'))}")
        st.write(f"**Net Profit:** {format_currency(selected_movie.get('profit'))}")
        st.write(f"**ROI Multiplier:** {format_pct(selected_movie.get('roi')) if pd.notna(selected_movie.get('roi')) else 'Not calculated'}")
        st.write(f"**Runtime:** {int(selected_movie.get('runtime')) if pd.notna(selected_movie.get('runtime')) and selected_movie.get('runtime') > 0 else 'Not reported'} min")
        st.write(f"**Language:** `{selected_movie.get('original_language', 'N/A')}`")

st.markdown("---")
st.markdown("### 📋 Page Catalog Table")
display_cols = ["title", "release_year", "genres_display", "vote_average", "vote_count", "revenue", "budget", "director_display"]
grid_view = page_items[[c for c in display_cols if c in page_items.columns]].copy()
grid_view.rename(columns={
    "title": "Title",
    "release_year": "Year",
    "genres_display": "Genres",
    "vote_average": "Rating ★",
    "vote_count": "Votes",
    "revenue": "Revenue ($)",
    "budget": "Budget ($)",
    "director_display": "Director"
}, inplace=True)

st.dataframe(grid_view, use_container_width=True, hide_index=True)

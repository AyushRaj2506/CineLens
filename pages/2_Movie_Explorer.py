"""Page 2: Movie Catalog Explorer (Redesigned SaaS Search & Profile Inspector)."""
import streamlit as st
import pandas as pd

from src.components import (
    empty_state,
    filter_status_bar,
    inject_custom_css,
    movie_profile_card,
    page_header
)
from src.data_loader import load_movies
from src.filters import apply_global_filters, render_global_filters

inject_custom_css()

# 1. Lazy load fact table
movies_df = load_movies()

# 2. Render sidebar filters & apply
filters = render_global_filters(movies_df)
filtered_df = apply_global_filters(movies_df, filters)

# 3. Page Header & Filter Status
page_header(
    title="Movie Catalog Explorer",
    subtitle="Vectorized substring search, multi-metric sorting, pagination, and structured film profile cards.",
    eyebrow="CATALOG EXPLORER"
)
filter_status_bar(filters, len(movies_df), len(filtered_df))

if filtered_df.empty:
    empty_state("No catalog titles found matching the active filter criteria.")
    st.stop()

# 4. Search & Sort Controls (Dominant Search Bar)
search_col, sort_col, order_col = st.columns([2.5, 1.2, 0.8])
with search_col:
    search_query = st.text_input(
        "Search by Title or Keyword",
        placeholder="Type a movie title (e.g. Inception, Godfather, Toy Story)...",
        label_visibility="collapsed"
    )
with sort_col:
    sort_by = st.selectbox(
        "Sort By",
        options=["popularity", "revenue", "vote_average", "profit", "release_year", "vote_count"],
        format_func=lambda x: {
            "popularity": "TMDB Popularity",
            "revenue": "Box Office Gross",
            "vote_average": "Audience Rating (★)",
            "profit": "Net Box Office Profit",
            "release_year": "Release Year",
            "vote_count": "Vote Count"
        }.get(x, x),
        label_visibility="collapsed"
    )
with order_col:
    sort_order = st.selectbox("Order", options=["Descending", "Ascending"], label_visibility="collapsed")

# 5. Vectorized Search & Sort
res_df = filtered_df
if search_query.strip():
    q = search_query.strip().lower()
    mask = res_df["title"].str.lower().str.contains(q, na=False)
    if "original_title" in res_df.columns:
        mask = mask | res_df["original_title"].str.lower().str.contains(q, na=False)
    res_df = res_df[mask]

if res_df.empty:
    empty_state(f"No movies found matching '{search_query}'", "Try checking for spelling or adjusting active filters.")
    st.stop()

ascending = (sort_order == "Ascending")
if sort_by in res_df.columns:
    res_df = res_df.sort_values(by=sort_by, ascending=ascending, na_position="last")

# 6. Pagination Controls (25 items/page)
PAGE_SIZE = 25
total_results = len(res_df)
total_pages = max(1, (total_results + PAGE_SIZE - 1) // PAGE_SIZE)

p_col1, p_col2 = st.columns([1, 4])
with p_col1:
    page_num = st.number_input(f"Page (of {total_pages})", min_value=1, max_value=total_pages, value=1, step=1)
with p_col2:
    st.markdown(
        f'<div style="font-size: 0.85rem; color: var(--text-muted); padding-top: 0.6rem;">Displaying <strong>{(page_num-1)*PAGE_SIZE + 1}</strong> – <strong>{min(page_num*PAGE_SIZE, total_results)}</strong> of <strong>{total_results:,}</strong> matching records</div>',
        unsafe_allow_html=True
    )

start_idx = (page_num - 1) * PAGE_SIZE
page_slice = res_df.iloc[start_idx : start_idx + PAGE_SIZE]

# 7. Split Layout: Catalog Table (Left) + Selected Movie Profile (Right)
col_table, col_profile = st.columns([1.1, 1.3])

with col_table:
    st.markdown('<div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Catalog Results</div>', unsafe_allow_html=True)
    
    # Selectable title list
    titles_in_page = page_slice["title"].fillna("Untitled").tolist()
    default_selected = titles_in_page[0] if titles_in_page else None
    
    selected_title = st.selectbox(
        "Select Movie to Inspect Profile:",
        options=titles_in_page,
        index=0,
        help="Select a title from this page to view its comprehensive intelligence profile."
    )
    
    # Summary Table for the page
    table_view = page_slice[["title", "release_year", "genres_display", "vote_average", "revenue"]].rename(columns={
        "title": "Title",
        "release_year": "Year",
        "genres_display": "Genres",
        "vote_average": "Rating ★",
        "revenue": "Gross ($)"
    })
    st.dataframe(table_view, use_container_width=True, hide_index=True)

with col_profile:
    st.markdown('<div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.5rem;">Film Intelligence Profile</div>', unsafe_allow_html=True)
    
    selected_row = page_slice[page_slice["title"] == selected_title]
    if not selected_row.empty:
        movie_profile_card(selected_row.iloc[0].to_dict())
    else:
        st.info("Select a title on the left to inspect its profile.")

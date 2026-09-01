"""Reusable UI components and design system tokens for CineLens Analytics."""
from pathlib import Path
from typing import Dict, List, Optional
import streamlit as st

from src.utils import format_currency, format_number, format_pct

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "css" / "main.css"


def inject_custom_css():
    """Inject the central stylesheet into the Streamlit session."""
    if CSS_PATH.exists():
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def render_sidebar_brand():
    """Render the cinematic SaaS brand mark at the top of the sidebar."""
    html = (
        '<div class="brand-container">'
        '<div class="brand-icon">CL</div>'
        '<div class="brand-text-wrapper">'
        '<div class="brand-title">CineLens</div>'
        '<div class="brand-subtitle">Movie Intelligence</div>'
        '</div>'
        '</div>'
    )
    st.sidebar.markdown(html, unsafe_allow_html=True)


def page_header(title: str, subtitle: Optional[str] = None, eyebrow: Optional[str] = None):
    """Render a standard header with category eyebrow, H1 title, and description."""
    eyebrow_html = f'<div class="header-eyebrow">{eyebrow}</div>' if eyebrow else ""
    sub_html = f'<div class="header-subtitle">{subtitle}</div>' if subtitle else ""
    html = f'<div class="header-container">{eyebrow_html}<div class="header-title">{title}</div>{sub_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def filter_status_bar(filters, total_count: int, filtered_count: int):
    """Render a compact active-filter status strip near the page header."""
    badges = []
    
    # Year Range
    if hasattr(filters, "year_range") and filters.year_range:
        badges.append(f'<span class="filter-badge">Release: {filters.year_range[0]}–{filters.year_range[1]}</span>')
        
    # Genres
    if hasattr(filters, "genres") and filters.genres:
        g_str = ", ".join(filters.genres[:3]) + (f" +{len(filters.genres)-3}" if len(filters.genres) > 3 else "")
        badges.append(f'<span class="filter-badge">Genres: {g_str}</span>')
        
    # Countries
    if hasattr(filters, "countries") and filters.countries:
        c_str = ", ".join(filters.countries[:2]) + (f" +{len(filters.countries)-2}" if len(filters.countries) > 2 else "")
        badges.append(f'<span class="filter-badge">Origin: {c_str}</span>')
        
    # Rating
    if hasattr(filters, "min_rating") and filters.min_rating > 0:
        badges.append(f'<span class="filter-badge">Rating ≥ {filters.min_rating:.1f} ★</span>')
        
    # Popularity
    if hasattr(filters, "min_popularity") and filters.min_popularity > 0:
        badges.append(f'<span class="filter-badge">Pop ≥ {filters.min_popularity:.0f}</span>')
        
    badge_content = "".join(badges) if badges else '<span class="filter-badge">Full Unfiltered Catalog</span>'
    scope_text = f'<span class="filter-strip-label">Scope:</span> {filtered_count:,} of {total_count:,} titles'
    
    html = f'<div class="filter-strip">{scope_text} &nbsp;|&nbsp; {badge_content}</div>'
    st.markdown(html, unsafe_allow_html=True)


def kpi_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    delta: Optional[str] = None,
    delta_type: str = "neutral",
    icon: str = ""
):
    """Render a premium KPI metric card with clean, single-line HTML."""
    icon_html = f"<span>{icon}</span> " if icon else ""
    delta_html = f'<div class="kpi-delta {delta_type}">{delta}</div>' if delta else ""
    sub_html = f'<div class="kpi-sub">{subtitle}</div>' if subtitle else ""
    html = f'<div class="kpi-card"><div class="kpi-title">{icon_html}{title}</div><div class="kpi-value">{value}</div>{delta_html}{sub_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def insight_card(number_str: str, text: str):
    """Render a numbered analytical insight card."""
    html = f'<div class="insight-card"><div class="insight-number">{number_str}</div><div class="insight-text">{text}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def insight_line(text: str, icon: str = "💡"):
    """Legacy alias for backward compatibility."""
    html = f'<div class="insight-card"><div class="insight-number">{icon}</div><div class="insight-text">{text}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def empty_state(
    title: str = "No movies match these filters",
    message: str = "Try widening the release period or clearing one of the active filters.",
    icon: str = "🎬"
):
    """Render a polished empty state UI."""
    html = f'<div class="empty-state"><div class="empty-state-icon">{icon}</div><div class="empty-state-title">{title}</div><div class="empty-state-msg">{message}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def movie_profile_card(row: Dict):
    """Render a rich, structured profile card for a selected movie."""
    title = str(row.get("title", "Untitled"))
    year = int(row.get("release_year", 0)) if row.get("release_year") and row.get("release_year") == row.get("release_year") else "Not reported"
    director = str(row.get("director_display", "Not credited"))
    genres = str(row.get("genres_display", "Not specified"))
    tagline = str(row.get("tagline", "")) if row.get("tagline") and row.get("tagline") == row.get("tagline") else ""
    overview = str(row.get("overview", "No synopsis available in catalog."))
    top_cast = str(row.get("top_cast_display", "Not reported"))
    runtime = f"{int(row['runtime'])} min" if row.get("runtime") and row.get("runtime") > 0 else "Not reported"
    
    # Financial metrics
    budget_str = format_currency(row.get("budget"))
    rev_str = format_currency(row.get("revenue"))
    profit_str = format_currency(row.get("profit"))
    roi_str = format_pct(row.get("roi")) if row.get("roi") and row.get("roi") == row.get("roi") else "Not reported"
    
    # Rating & sample size
    vote_avg = row.get("vote_average", 0.0)
    vote_cnt = int(row.get("vote_count", 0)) if row.get("vote_count") and row.get("vote_count") == row.get("vote_count") else 0
    
    rating_sample_note = ""
    if vote_cnt < 20:
        rating_sample_note = '<span class="low-sample-warning">(Low sample &lt; 20 votes)</span>'
        
    tagline_html = f'<div class="movie-tagline">“{tagline}”</div>' if tagline else ""
    
    # Format genre tags
    genre_chips = "".join([f'<span class="chip chip-genre">{g.strip()}</span>' for g in genres.split(",") if g.strip()])
    cast_chips = "".join([f'<span class="chip chip-actor">{a.strip()}</span>' for a in top_cast.split(",") if a.strip()])
    cast_html = cast_chips if cast_chips else '<span style="color: var(--text-muted); font-size: 0.85rem;">Not credited</span>'
    
    html = f"""
    <div class="movie-profile-card">
        <div class="movie-profile-header">
            <div class="movie-profile-title">{title}</div>
            <div class="movie-profile-meta">
                <span>{year}</span> &nbsp;•&nbsp; 
                <span>Directed by <strong>{director}</strong></span> &nbsp;•&nbsp; 
                <span>{runtime}</span>
            </div>
            {tagline_html}
            <div style="margin-top: 0.65rem;">
                <span class="rating-badge">★ {vote_avg:.1f}</span>
                <span style="font-size: 0.78rem; color: var(--text-muted); margin-left: 0.4rem;">{vote_cnt:,} votes {rating_sample_note}</span>
                <span style="font-size: 0.78rem; color: var(--text-muted); margin-left: 0.8rem;">Popularity: {row.get('popularity', 0.0):.1f}</span>
            </div>
            <div style="margin-top: 0.75rem;">{genre_chips}</div>
        </div>
        
        <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.35rem;">Overview</div>
        <div style="font-size: 0.92rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 1rem;">{overview}</div>
        
        <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.35rem;">Principal Cast</div>
        <div style="margin-bottom: 1rem;">{cast_html}</div>
        
        <div style="font-size: 0.78rem; font-weight: 700; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.05em; margin-bottom: 0.4rem;">Financial Performance</div>
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-box-label">Production Budget</div>
                <div class="metric-box-value">{budget_str}</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Box Office Gross</div>
                <div class="metric-box-value" style="color: var(--accent-finance);">{rev_str}</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">Net Profit</div>
                <div class="metric-box-value" style="color: var(--positive);">{profit_str}</div>
            </div>
            <div class="metric-box">
                <div class="metric-box-label">ROI Multiplier</div>
                <div class="metric-box-value">{roi_str}</div>
            </div>
        </div>
    </div>
    """
    # Clean indentation for markdown safety
    clean_lines = [line.strip() for line in html.strip().splitlines() if line.strip()]
    st.markdown("".join(clean_lines), unsafe_allow_html=True)

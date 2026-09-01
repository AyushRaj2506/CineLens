"""Centralized Plotly visualization wrappers with consistent dark cinematic theme and typography."""
from typing import List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Centralized Design Tokens
PRIMARY_COLOR = "#7C5CFC"
PRIMARY_LIGHT = "#9B87FF"
SECONDARY_COLOR = "#38BDF8"
ACCENT_FINANCE = "#F6B94A"
POSITIVE_COLOR = "#34D399"
NEGATIVE_COLOR = "#FB7185"
RATING_COLOR = "#A78BFA"

BG_COLOR = "#090B12"
SURFACE_COLOR = "#131722"
SURFACE_ELEVATED = "#171C2A"
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#A8B1C5"
TEXT_MUTED = "#737D92"
BORDER_COLOR = "rgba(148, 163, 184, 0.13)"

# Harmonious 8-color categorical palette (non-rainbow)
COLOR_SEQUENCE = [
    "#7C5CFC", "#38BDF8", "#F6B94A", "#34D399",
    "#FB7185", "#A78BFA", "#F472B6", "#818CF8"
]


def _apply_theme(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply consistent styling, typography, and dark theme layout to Plotly figures."""
    fig.update_layout(
        title={
            "text": title,
            "font": {"family": "Manrope, sans-serif", "size": 15, "color": TEXT_PRIMARY, "weight": "bold"},
            "x": 0.0,
            "xanchor": "left"
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Manrope, sans-serif", "color": TEXT_SECONDARY, "size": 12},
        height=height,
        margin=dict(l=15, r=15, t=45, b=15),
        legend=dict(
            bgcolor="rgba(19, 23, 34, 0.8)",
            bordercolor=BORDER_COLOR,
            borderwidth=1,
            font=dict(color=TEXT_SECONDARY, size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        colorway=COLOR_SEQUENCE,
        hoverlabel=dict(
            bgcolor=SURFACE_ELEVATED,
            font_size=12,
            font_family="Manrope, sans-serif",
            font_color=TEXT_PRIMARY,
            bordercolor=PRIMARY_COLOR
        )
    )
    fig.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.08)",
        zerolinecolor="rgba(148, 163, 184, 0.12)",
        tickfont=dict(family="Manrope, sans-serif", color=TEXT_MUTED, size=11),
        title_font=dict(family="Manrope, sans-serif", color=TEXT_SECONDARY, size=12)
    )
    fig.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.08)",
        zerolinecolor="rgba(148, 163, 184, 0.12)",
        tickfont=dict(family="Manrope, sans-serif", color=TEXT_MUTED, size=11),
        title_font=dict(family="Manrope, sans-serif", color=TEXT_SECONDARY, size=12)
    )
    return fig


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    orientation: str = "v",
    color: Optional[str] = None,
    text: Optional[str] = None,
    bar_color: Optional[str] = None,
    height: int = 400
) -> go.Figure:
    """Standardized bar chart with rounded corners and clean hover data."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    
    color_seq = [bar_color] if bar_color else COLOR_SEQUENCE
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation=orientation,
        color=color,
        text=text,
        color_discrete_sequence=color_seq
    )
    if orientation == "h":
        fig.update_layout(yaxis=dict(autorange="reversed"))
    fig.update_traces(marker_line_width=0, opacity=0.9)
    return _apply_theme(fig, title, height)


def line_chart(
    df: pd.DataFrame,
    x: str,
    y: str | List[str],
    title: str = "",
    color: Optional[str] = None,
    markers: bool = True,
    height: int = 400
) -> go.Figure:
    """Standardized line chart."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    fig = px.line(
        df,
        x=x,
        y=y,
        color=color,
        markers=markers,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    fig.update_traces(line=dict(width=2.5))
    return _apply_theme(fig, title, height)


def scatter_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    hover_name: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    trendline: Optional[str] = None,
    log_x: bool = False,
    log_y: bool = False,
    height: int = 450,
    use_webgl: bool = False
) -> go.Figure:
    """Standardized scatter plot with optional WebGL acceleration and OLS trendline."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    
    plot_df = df.copy()
    actual_size = None
    if size and size in plot_df.columns:
        valid_sizes = plot_df[size].dropna()
        if not valid_sizes.empty and (valid_sizes > 0).any():
            plot_df[size] = plot_df[size].fillna(0).clip(lower=0)
            actual_size = size

    try:
        fig = px.scatter(
            plot_df,
            x=x,
            y=y,
            hover_name=hover_name if hover_name and hover_name in plot_df.columns else None,
            color=color,
            size=actual_size,
            trendline=trendline,
            log_x=log_x,
            log_y=log_y,
            render_mode="webgl" if use_webgl else "auto",
            color_discrete_sequence=COLOR_SEQUENCE
        )
    except Exception:
        fig = px.scatter(
            plot_df,
            x=x,
            y=y,
            hover_name=hover_name if hover_name and hover_name in plot_df.columns else None,
            color=color,
            size=actual_size,
            log_x=log_x,
            log_y=log_y,
            render_mode="webgl" if use_webgl else "auto",
            color_discrete_sequence=COLOR_SEQUENCE
        )
        
    if actual_size:
        fig.update_traces(marker=dict(opacity=0.75, line=dict(width=0)))
    else:
        fig.update_traces(marker=dict(size=6, opacity=0.7, line=dict(width=0)))
    return _apply_theme(fig, title, height)


def histogram_chart(
    df: pd.DataFrame,
    x: str,
    title: str = "",
    nbins: int = 30,
    color: Optional[str] = None,
    log_x: bool = False,
    bar_color: str = PRIMARY_COLOR,
    height: int = 380
) -> go.Figure:
    """Standardized histogram."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    fig = px.histogram(
        df,
        x=x,
        nbins=nbins,
        color=color,
        log_x=log_x,
        color_discrete_sequence=[bar_color]
    )
    fig.update_traces(marker_line_width=0.5, marker_line_color=SURFACE_COLOR, opacity=0.85)
    return _apply_theme(fig, title, height)


def box_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: Optional[str] = None,
    height: int = 420
) -> go.Figure:
    """Standardized box plot."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    fig = px.box(
        df,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    fig.update_traces(marker_line_width=1, marker_line_color=SURFACE_COLOR, opacity=0.85)
    return _apply_theme(fig, title, height)


def stacked_area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
    height: int = 420
) -> go.Figure:
    """Stacked area chart for time-series proportions."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    fig = px.area(
        df,
        x=x,
        y=y,
        color=color,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    fig.update_traces(line=dict(width=0.5))
    return _apply_theme(fig, title, height)


def choropleth_map(
    df: pd.DataFrame,
    locations: str,
    z: str,
    title: str = "",
    hover_name: Optional[str] = None,
    height: int = 480
) -> go.Figure:
    """Choropleth world map based on ISO-3166-1 alpha-3 country codes."""
    if df.empty or z not in df.columns:
        return _apply_theme(go.Figure(), title, height)
    
    plot_df = df.copy()
    
    # If 2-letter codes were passed, automatically map to ISO-3 alpha-3
    from src.utils import ISO2_TO_ISO3
    if locations in plot_df.columns:
        sample_loc = plot_df[locations].dropna().iloc[0] if not plot_df[locations].dropna().empty else ""
        if len(str(sample_loc)) == 2:
            plot_df["iso_3_code"] = plot_df[locations].map(ISO2_TO_ISO3)
            loc_col = "iso_3_code"
        else:
            loc_col = locations
    else:
        loc_col = locations
        
    # Ensure metric is clean numeric and filter out NaNs for selected metric
    plot_df[z] = pd.to_numeric(plot_df[z], errors="coerce")
    valid_df = plot_df.dropna(subset=[loc_col, z])
    if valid_df.empty:
        return _apply_theme(go.Figure(), title, height)

    fig = px.choropleth(
        valid_df,
        locations=loc_col,
        locationmode="ISO-3",
        color=z,
        hover_name=hover_name if hover_name and hover_name in valid_df.columns else None,
        color_continuous_scale="Plasma",
        projection="natural earth"
    )
    fig.update_geos(
        bgcolor="rgba(0,0,0,0)",
        showocean=True,
        oceancolor=BG_COLOR,
        showland=True,
        landcolor="#1A1E29",
        showcountries=True,
        countrycolor="#2D3344",
        countrywidth=0.6,
        showlakes=True,
        lakecolor=BG_COLOR,
        framecolor=BORDER_COLOR
    )
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=dict(text=z.replace("_", " ").title(), font=dict(color=TEXT_PRIMARY, size=11)),
            tickfont=dict(color=TEXT_MUTED, size=10),
            len=0.75,
            thickness=14
        )
    )
    return _apply_theme(fig, title, height)


def grouped_bar_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: List[str],
    title: str = "",
    height: int = 400
) -> go.Figure:
    """Grouped bar chart for multiple metrics across items."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    fig = go.Figure()
    for idx, col in enumerate(y_cols):
        fig.add_trace(
            go.Bar(
                name=col,
                x=df[x],
                y=df[col],
                marker_color=COLOR_SEQUENCE[idx % len(COLOR_SEQUENCE)],
                opacity=0.9
            )
        )
    fig.update_layout(barmode="group")
    return _apply_theme(fig, title, height)

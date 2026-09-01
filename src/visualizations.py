"""Centralized Plotly visualization wrappers with consistent dark theme and typography."""
from typing import List, Optional
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Design theme color palette
PRIMARY_COLOR = "#6C5CE7"
SECONDARY_COLOR = "#00CEC9"
ACCENT_COLOR = "#FDCB6E"
BG_COLOR = "#0F1117"
SURFACE_COLOR = "#171A23"
TEXT_COLOR = "#EAECF0"
TEXT_MUTED = "#9AA1B1"
GRID_COLOR = "#262A38"

COLOR_SEQUENCE = [
    "#6C5CE7", "#00CEC9", "#FDCB6E", "#E17055", "#0984E3",
    "#00B894", "#E84393", "#A29BFE", "#FD79A8", "#FFEAA7",
    "#74B9FF", "#55EFC4", "#FAB1A0", "#DFE6E9", "#636E72"
]


def _apply_theme(fig: go.Figure, title: str = "", height: int = 420) -> go.Figure:
    """Apply consistent styling, fonts, and dark theme layout to Plotly figures."""
    fig.update_layout(
        title={
            "text": title,
            "font": {"family": "Manrope, sans-serif", "size": 16, "color": "#FFFFFF", "weight": "bold"},
            "x": 0.0,
            "xanchor": "left"
        },
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=SURFACE_COLOR,
        font={"family": "Manrope, sans-serif", "color": TEXT_COLOR, "size": 12},
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(
            bgcolor="rgba(23, 26, 35, 0.7)",
            bordercolor=GRID_COLOR,
            borderwidth=1,
            font=dict(color=TEXT_COLOR, size=11)
        ),
        colorway=COLOR_SEQUENCE,
        hoverlabel=dict(
            bgcolor="#1E2230",
            font_size=12,
            font_family="Manrope, sans-serif",
            bordercolor=PRIMARY_COLOR
        )
    )
    fig.update_xaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED)
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR,
        zerolinecolor=GRID_COLOR,
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED)
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
    height: int = 420
) -> go.Figure:
    """Standardized bar chart."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    fig = px.bar(
        df,
        x=x,
        y=y,
        orientation=orientation,
        color=color,
        text=text,
        color_discrete_sequence=COLOR_SEQUENCE
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
            hover_name=hover_name,
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
            hover_name=hover_name,
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
    log_x: bool = False,
    log_y: bool = False,
    color: Optional[str] = None,
    height: int = 380
) -> go.Figure:
    """Standardized histogram."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    fig = px.histogram(
        df,
        x=x,
        nbins=nbins,
        log_x=log_x,
        log_y=log_y,
        color=color,
        color_discrete_sequence=COLOR_SEQUENCE
    )
    fig.update_traces(marker_line_width=1, marker_line_color=SURFACE_COLOR, opacity=0.85)
    return _apply_theme(fig, title, height)


def heatmap_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    z: str,
    title: str = "",
    height: int = 450
) -> go.Figure:
    """Heatmap for 2D density/aggregates."""
    if df.empty:
        return _apply_theme(go.Figure(), title, height)
    pivot = df.pivot(index=y, columns=x, values=z)
    fig = px.imshow(
        pivot,
        color_continuous_scale="Purples",
        aspect="auto"
    )
    return _apply_theme(fig, title, height)


def stacked_area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str,
    title: str = "",
    height: int = 450
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
    height: int = 500
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
        oceancolor="#0F1117",
        showland=True,
        landcolor="#1A1E29",
        showcountries=True,
        countrycolor="#2D3344",
        countrywidth=0.6,
        showlakes=True,
        lakecolor="#0F1117",
        framecolor="#262A38"
    )
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=dict(text=z.replace("_", " ").title(), font=dict(color="#EAECF0", size=11)),
            tickfont=dict(color="#9AA1B1", size=10),
            len=0.75,
            thickness=15
        )
    )
    return _apply_theme(fig, title, height)


def grouped_bar_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: List[str],
    title: str = "",
    height: int = 420
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
                marker_color=COLOR_SEQUENCE[idx % len(COLOR_SEQUENCE)]
            )
        )
    fig.update_layout(barmode="group")
    return _apply_theme(fig, title, height)

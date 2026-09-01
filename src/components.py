"""Reusable UI components and design system tokens for Streamlit with zero HTML leakage."""
import streamlit as st

CUSTOM_CSS = """
<style>
/* Import Manrope and DM Sans fonts */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=Manrope:wght@300;400;500;600;700;800&display=swap');

:root {
    --color-bg: #0F1117;
    --color-surface: #171A23;
    --color-surface-hover: #1E2230;
    --color-primary: #6C5CE7;
    --color-primary-light: #8B7CF8;
    --color-secondary: #00CEC9;
    --color-accent: #FDCB6E;
    --color-text: #EAECF0;
    --color-text-muted: #9AA1B1;
    --color-border: #262A38;
    --color-success: #2ECC71;
    --color-warning: #F1C40F;
    --color-error: #E74C3C;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --shadow-card: 0 4px 12px rgba(0, 0, 0, 0.35);
}

html, body, [class*="css"] {
    font-family: 'Manrope', -apple-system, BlinkMacSystemFont, sans-serif;
    color: var(--color-text);
}

/* Section Header and Title Styling */
.main-title {
    font-size: 2.1rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FFFFFF 0%, #B2BEC3 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
    letter-spacing: -0.02em;
}

.page-subtitle {
    color: var(--color-text-muted);
    font-size: 0.95rem;
    margin-bottom: 1.25rem;
    line-height: 1.4;
}

/* KPI Card Styling with Hover Animation */
.kpi-card {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: 1rem 1.15rem;
    box-shadow: var(--shadow-card);
    transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
    margin-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
}

.kpi-card:hover {
    transform: translateY(-2px);
    border-color: var(--color-primary-light);
    box-shadow: 0 6px 20px rgba(108, 92, 231, 0.2);
}

.kpi-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--color-text-muted);
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

.kpi-value {
    font-family: 'DM Sans', sans-serif;
    font-size: 1.75rem;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.15;
}

.kpi-sub {
    font-size: 0.75rem;
    color: var(--color-text-muted);
    margin-top: 0.25rem;
}

.kpi-delta {
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 0.35rem;
}

.kpi-delta.pos { color: var(--color-success); }
.kpi-delta.neg { color: var(--color-error); }
.kpi-delta.neutral { color: var(--color-text-muted); }

/* Insight Line */
.insight-box {
    background: rgba(108, 92, 231, 0.08);
    border-left: 3px solid var(--color-primary);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    padding: 0.65rem 0.9rem;
    margin-bottom: 0.45rem;
    color: var(--color-text);
    font-size: 0.9rem;
    line-height: 1.45;
}

/* Empty State Card */
.empty-state {
    background: var(--color-surface);
    border: 1px dashed var(--color-border);
    border-radius: var(--radius-md);
    padding: 2rem 1.5rem;
    text-align: center;
    color: var(--color-text-muted);
    margin: 1.25rem 0;
}

.empty-state-icon {
    font-size: 2.2rem;
    margin-bottom: 0.4rem;
}

.empty-state-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--color-text);
    margin-bottom: 0.2rem;
}

.empty-state-msg {
    font-size: 0.88rem;
    color: var(--color-text-muted);
}

/* Chip tags */
.genre-chip {
    display: inline-block;
    background: rgba(108, 92, 231, 0.18);
    color: #A29BFE;
    border: 1px solid rgba(108, 92, 231, 0.35);
    padding: 0.12rem 0.5rem;
    border-radius: 20px;
    font-size: 0.73rem;
    font-weight: 600;
    margin-right: 0.25rem;
    margin-bottom: 0.25rem;
}

.keyword-chip {
    display: inline-block;
    background: rgba(0, 206, 201, 0.12);
    color: #81ECEC;
    border: 1px solid rgba(0, 206, 201, 0.25);
    padding: 0.12rem 0.45rem;
    border-radius: 12px;
    font-size: 0.7rem;
    margin-right: 0.2rem;
    margin-bottom: 0.2rem;
}

div[data-testid="stMetricValue"] {
    font-family: 'DM Sans', sans-serif !important;
}
</style>
"""


def inject_custom_css():
    """Inject custom styles and design tokens into the Streamlit session."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = None):
    """Render a standard header with typography (zero markdown indentation)."""
    sub_html = f'<div class="page-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(f'<div class="main-title">{title}</div>{sub_html}', unsafe_allow_html=True)


def kpi_card(title: str, value: str, subtitle: str = None, delta: str = None, delta_type: str = "neutral", icon: str = ""):
    """Render a rich KPI metric card with clean, single-line HTML (no raw markdown indentation)."""
    icon_html = f"<span>{icon}</span> " if icon else ""
    delta_html = f'<div class="kpi-delta {delta_type}">{delta}</div>' if delta else ""
    sub_html = f'<div class="kpi-sub">{subtitle}</div>' if subtitle else ""
    html = f'<div class="kpi-card"><div class="kpi-title">{icon_html}{title}</div><div class="kpi-value">{value}</div>{delta_html}{sub_html}</div>'
    st.markdown(html, unsafe_allow_html=True)


def empty_state(title: str = "No data found", message: str = "Try adjusting or clearing your global filters to see results.", icon: str = "🎬"):
    """Render an empty state UI when filtered selections yield zero records."""
    html = f'<div class="empty-state"><div class="empty-state-icon">{icon}</div><div class="empty-state-title">{title}</div><div class="empty-state-msg">{message}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def insight_line(text: str, icon: str = "💡"):
    """Render an automated insight row."""
    html = f'<div class="insight-box"><strong>{icon}</strong> {text}</div>'
    st.markdown(html, unsafe_allow_html=True)

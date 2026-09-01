"""Constants and formatting utilities for CineLens Analytics."""

# Key numeric constants (single source of truth)
VOTE_COUNT_MIN: int = 20
MIN_ACTOR_MOVIES: int = 5
MIN_DIRECTOR_MOVIES: int = 3
MIN_GENRE_SAMPLE: int = 5
MIN_GENRE_YEAR_MOVIES: int = 3
MIN_KEYWORD_SUPPORT: int = 20
ROI_MIN_BUDGET: float = 1_000_000.0
MAIN_CAST_ORDER_LIMIT: int = 10

# Closed genre taxonomy
VALID_GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary",
    "Drama", "Family", "Fantasy", "Foreign", "History", "Horror",
    "Music", "Mystery", "Romance", "Science Fiction", "TV Movie",
    "Thriller", "War", "Western"
]

# Standard ISO-3166-1 alpha-2 to alpha-3 mapping for choropleth mapping
ISO2_TO_ISO3 = {
    'AE': 'ARE', 'AF': 'AFG', 'AL': 'ALB', 'AM': 'ARM', 'AN': 'ANT', 'AO': 'AGO', 'AQ': 'ATA', 'AR': 'ARG',
    'AT': 'AUT', 'AU': 'AUS', 'AW': 'ABW', 'AZ': 'AZE', 'BA': 'BIH', 'BB': 'BRB', 'BD': 'BGD', 'BE': 'BEL',
    'BF': 'BFA', 'BG': 'BGR', 'BM': 'BMU', 'BN': 'BRN', 'BO': 'BOL', 'BR': 'BRA', 'BS': 'BHS', 'BT': 'BTN',
    'BW': 'BWA', 'BY': 'BLR', 'CA': 'CAN', 'CD': 'COD', 'CG': 'COG', 'CH': 'CHE', 'CI': 'CIV', 'CL': 'CHL',
    'CM': 'CMR', 'CN': 'CHN', 'CO': 'COL', 'CR': 'CRI', 'CS': 'SCG', 'CU': 'CUB', 'CY': 'CYP', 'CZ': 'CZE',
    'DE': 'DEU', 'DK': 'DNK', 'DO': 'DOM', 'DZ': 'DZA', 'EC': 'ECU', 'EE': 'EST', 'EG': 'EGY', 'ES': 'ESP',
    'ET': 'ETH', 'FI': 'FIN', 'FR': 'FRA', 'GB': 'GBR', 'GE': 'GEO', 'GH': 'GHA', 'GI': 'GIB', 'GN': 'GIN',
    'GR': 'GRC', 'GT': 'GTM', 'HK': 'HKG', 'HN': 'HND', 'HR': 'HRV', 'HU': 'HUN', 'ID': 'IDN', 'IE': 'IRL',
    'IL': 'ISR', 'IN': 'IND', 'IQ': 'IRQ', 'IR': 'IRN', 'IS': 'ISL', 'IT': 'ITA', 'JM': 'JAM', 'JO': 'JOR',
    'JP': 'JPN', 'KE': 'KEN', 'KG': 'KGZ', 'KH': 'KHM', 'KP': 'PRK', 'KR': 'KOR', 'KW': 'KWT', 'KY': 'CYM',
    'KZ': 'KAZ', 'LA': 'LAO', 'LB': 'LBN', 'LI': 'LIE', 'LK': 'LKA', 'LR': 'LBR', 'LT': 'LTU', 'LU': 'LUX',
    'LV': 'LVA', 'LY': 'LBY', 'MA': 'MAR', 'MC': 'MCO', 'MD': 'MDA', 'ME': 'MNE', 'MG': 'MDG', 'MK': 'MKD',
    'ML': 'MLI', 'MM': 'MMR', 'MN': 'MNG', 'MO': 'MAC', 'MQ': 'MTQ', 'MR': 'MRT', 'MT': 'MLT', 'MX': 'MEX',
    'MY': 'MYS', 'NA': 'NAM', 'NG': 'NGA', 'NI': 'NIC', 'NL': 'NLD', 'NO': 'NOR', 'NP': 'NPL', 'NZ': 'NZL',
    'PA': 'PAN', 'PE': 'PER', 'PF': 'PYF', 'PG': 'PNG', 'PH': 'PHL', 'PK': 'PAK', 'PL': 'POL', 'PR': 'PRI',
    'PS': 'PSE', 'PT': 'PRT', 'PY': 'PRY', 'QA': 'QAT', 'RO': 'ROU', 'RS': 'SRB', 'RU': 'RUS', 'RW': 'RWA',
    'SA': 'SAU', 'SE': 'SWE', 'SG': 'SGP', 'SI': 'SVN', 'SK': 'SVK', 'SN': 'SEN', 'SO': 'SOM', 'SU': 'RUS',
    'SV': 'SLV', 'SY': 'SYR', 'TD': 'TCD', 'TF': 'ATF', 'TH': 'THA', 'TJ': 'TJK', 'TN': 'TUN', 'TR': 'TUR',
    'TT': 'TTO', 'TW': 'TWN', 'TZ': 'TZA', 'UA': 'UKR', 'UG': 'UGA', 'UM': 'UMI', 'US': 'USA', 'UY': 'URY',
    'UZ': 'UZB', 'VE': 'VEN', 'VN': 'VNM', 'WS': 'WSM', 'XC': 'CZE', 'XG': 'DEU', 'YU': 'SRB', 'ZA': 'ZAF',
    'ZW': 'ZWE'
}


def format_currency(val: float | int | None) -> str:
    """Format numbers into human-readable currency strings (e.g. $1.2B, $45.6M, $120K)."""
    if val is None or (isinstance(val, float) and (val != val or val <= 0)):
        return "Not reported"
    val = float(val)
    if val >= 1_000_000_000:
        return f"${val / 1_000_000_000:.2f}B"
    if val >= 1_000_000:
        return f"${val / 1_000_000:.2f}M"
    if val >= 1_000:
        return f"${val / 1_000:.1f}K"
    return f"${val:,.0f}"


def format_number(val: float | int | None, precision: int = 0) -> str:
    """Format general numbers with comma separators."""
    if val is None or (isinstance(val, float) and val != val):
        return "N/A"
    if precision == 0:
        return f"{int(round(val)):,}"
    return f"{val:,.{precision}f}"


def format_pct(val: float | int | None, precision: int = 1) -> str:
    """Format ratios/percentages."""
    if val is None or (isinstance(val, float) and val != val):
        return "N/A"
    return f"{val * 100:.{precision}f}%"

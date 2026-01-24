# Recommendation Rules
# Color theory and seasonal color analysis rules

from .color_rules import (
    UndertoneColorRules,
    COLOR_DATABASE,
    ColorCategory,
    get_color_compatibility_score,
    find_closest_color_name,
    calculate_color_warmth,
    is_universal_color,
    UNIVERSAL_COLORS,
)

from .seasonal_rules import (
    SeasonType,
    SeasonSubtype,
    SEASONAL_PALETTES,
    SUBTYPE_PALETTES,
    determine_season,
    get_season_colors,
    get_subtype_details,
    is_color_in_season,
    get_seasonal_recommendations,
    calculate_seasonal_score,
)

__all__ = [
    # Color rules
    "UndertoneColorRules",
    "COLOR_DATABASE",
    "ColorCategory",
    "get_color_compatibility_score",
    "find_closest_color_name",
    "calculate_color_warmth",
    "is_universal_color",
    "UNIVERSAL_COLORS",
    
    # Seasonal rules
    "SeasonType",
    "SeasonSubtype",
    "SEASONAL_PALETTES",
    "SUBTYPE_PALETTES",
    "determine_season",
    "get_season_colors",
    "get_subtype_details",
    "is_color_in_season",
    "get_seasonal_recommendations",
    "calculate_seasonal_score",
]

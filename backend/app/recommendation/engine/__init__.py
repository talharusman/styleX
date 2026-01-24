# Recommendation Engine Components
# Core algorithms for color matching, style matching, and scoring

from .color_matcher import (
    ColorMatcher,
    rgb_to_hsl,
    hsl_to_rgb,
    get_complementary_color,
    calculate_color_distance,
)

from .style_matcher import (
    StyleMatcher,
    COMPATIBLE_STYLES,
    OCCASION_STYLES,
    OCCASION_FORMALITY,
)

from .scoring import (
    RecommendationScorer,
    BatchScorer,
    ScoringWeights,
    calibrate_score,
    normalize_scores,
)

__all__ = [
    # Color matcher
    "ColorMatcher",
    "rgb_to_hsl",
    "hsl_to_rgb",
    "get_complementary_color",
    "calculate_color_distance",
    
    # Style matcher
    "StyleMatcher",
    "COMPATIBLE_STYLES",
    "OCCASION_STYLES",
    "OCCASION_FORMALITY",
    
    # Scoring
    "RecommendationScorer",
    "BatchScorer",
    "ScoringWeights",
    "calibrate_score",
    "normalize_scores",
]

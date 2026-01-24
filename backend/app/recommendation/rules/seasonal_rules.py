# Seasonal Color Theory Rules
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# Based on the 12-Season Color Analysis system
# Combines undertone (warm/cool) with skin depth and contrast level

from typing import Dict, List, Tuple, Optional
from enum import Enum


# ============================================
# SEASONAL COLOR ANALYSIS
# ============================================

class SeasonType(str, Enum):
    """The four main seasonal color types"""
    SPRING = "spring"  # Warm + Light/Bright
    SUMMER = "summer"  # Cool + Light/Muted
    AUTUMN = "autumn"  # Warm + Deep/Muted
    WINTER = "winter"  # Cool + Deep/Bright


class SeasonSubtype(str, Enum):
    """12-season subtypes for more precise analysis"""
    # Spring subtypes
    LIGHT_SPRING = "light_spring"
    WARM_SPRING = "warm_spring"
    BRIGHT_SPRING = "bright_spring"
    
    # Summer subtypes
    LIGHT_SUMMER = "light_summer"
    COOL_SUMMER = "cool_summer"
    SOFT_SUMMER = "soft_summer"
    
    # Autumn subtypes
    SOFT_AUTUMN = "soft_autumn"
    WARM_AUTUMN = "warm_autumn"
    DEEP_AUTUMN = "deep_autumn"
    
    # Winter subtypes
    DEEP_WINTER = "deep_winter"
    COOL_WINTER = "cool_winter"
    BRIGHT_WINTER = "bright_winter"


# ============================================
# SEASON DETERMINATION RULES
# ============================================

def determine_season(
    undertone: str,
    skin_depth: str,
    lab_l: float = None,
    lab_a: float = None,
    lab_b: float = None
) -> Tuple[SeasonType, SeasonSubtype, str]:
    """
    Determine seasonal color type based on skin features
    
    Args:
        undertone: warm, cool, or neutral
        skin_depth: fair, light, medium, tan, deep
        lab_l: LAB lightness value (0-100)
        lab_a: LAB a channel value
        lab_b: LAB b channel value
    
    Returns:
        Tuple of (main season, subtype, reasoning)
    """
    undertone = undertone.lower()
    skin_depth = skin_depth.lower()
    
    # Calculate contrast level based on LAB values
    contrast = "medium"
    if lab_l is not None:
        if lab_l > 70:
            contrast = "low"  # Light skin = low contrast
        elif lab_l < 45:
            contrast = "high"  # Dark skin = high contrast
    
    # Determine season based on undertone and depth
    if undertone == "warm":
        if skin_depth in ["fair", "light"]:
            # Light + Warm = Spring
            if contrast == "high":
                return SeasonType.SPRING, SeasonSubtype.BRIGHT_SPRING, "Warm undertone with light skin and high contrast"
            else:
                return SeasonType.SPRING, SeasonSubtype.LIGHT_SPRING, "Warm undertone with light, soft coloring"
        else:
            # Deep + Warm = Autumn
            if skin_depth == "medium":
                return SeasonType.AUTUMN, SeasonSubtype.SOFT_AUTUMN, "Warm undertone with medium depth, muted coloring"
            elif skin_depth in ["tan", "deep"]:
                return SeasonType.AUTUMN, SeasonSubtype.DEEP_AUTUMN, "Warm undertone with deep, rich coloring"
            else:
                return SeasonType.AUTUMN, SeasonSubtype.WARM_AUTUMN, "Warm undertone with classic autumn characteristics"
    
    elif undertone == "cool":
        if skin_depth in ["fair", "light"]:
            # Light + Cool = Summer
            if contrast == "low":
                return SeasonType.SUMMER, SeasonSubtype.LIGHT_SUMMER, "Cool undertone with light, delicate coloring"
            else:
                return SeasonType.SUMMER, SeasonSubtype.COOL_SUMMER, "Cool undertone with light to medium coloring"
        else:
            # Deep + Cool = Winter
            if contrast == "high":
                return SeasonType.WINTER, SeasonSubtype.BRIGHT_WINTER, "Cool undertone with high contrast coloring"
            elif skin_depth in ["tan", "deep"]:
                return SeasonType.WINTER, SeasonSubtype.DEEP_WINTER, "Cool undertone with deep, dramatic coloring"
            else:
                return SeasonType.WINTER, SeasonSubtype.COOL_WINTER, "Cool undertone with classic winter characteristics"
    
    else:  # neutral undertone
        # Neutral can lean either way based on depth
        if skin_depth in ["fair", "light"]:
            if lab_b is not None and lab_b > 10:
                return SeasonType.SPRING, SeasonSubtype.LIGHT_SPRING, "Neutral-warm undertone with light coloring"
            else:
                return SeasonType.SUMMER, SeasonSubtype.SOFT_SUMMER, "Neutral-cool undertone with soft coloring"
        else:
            if lab_b is not None and lab_b > 10:
                return SeasonType.AUTUMN, SeasonSubtype.SOFT_AUTUMN, "Neutral-warm undertone with muted coloring"
            else:
                return SeasonType.WINTER, SeasonSubtype.COOL_WINTER, "Neutral-cool undertone with deeper coloring"


# ============================================
# SEASONAL COLOR PALETTES
# ============================================

SEASONAL_PALETTES: Dict[SeasonType, Dict[str, List[str]]] = {
    SeasonType.SPRING: {
        "best_colors": [
            # Warm, clear, bright colors
            "coral", "peach", "salmon", "warm pink", "apricot",
            "golden yellow", "warm yellow", "daffodil",
            "spring green", "lime", "mint",
            "turquoise", "aqua", "clear teal",
            "warm red", "poppy", "tomato red",
            "cream", "ivory", "camel", "warm beige",
            "gold", "copper", "bronze",
        ],
        "neutral_colors": [
            "warm white", "ivory", "cream",
            "camel", "warm gray", "chocolate brown",
            "navy", "warm navy",
        ],
        "accent_colors": [
            "coral", "turquoise", "lime green", "golden yellow",
        ],
        "colors_to_avoid": [
            "black", "pure white", "cool gray", "burgundy",
            "dusty colors", "muted tones", "dark brown",
        ],
        "metals": ["gold", "rose gold", "copper", "bronze"],
    },
    
    SeasonType.SUMMER: {
        "best_colors": [
            # Cool, soft, muted colors
            "dusty rose", "mauve", "soft pink", "lavender pink",
            "powder blue", "periwinkle", "soft blue", "sky blue",
            "lavender", "lilac", "soft purple", "wisteria",
            "sage", "seafoam", "soft teal", "dusty aqua",
            "raspberry", "soft burgundy", "dusty red",
            "cocoa", "rose brown", "taupe",
            "silver", "pewter", "platinum",
        ],
        "neutral_colors": [
            "soft white", "off-white", "rose beige",
            "cocoa", "taupe", "charcoal blue",
            "soft navy", "blue gray",
        ],
        "accent_colors": [
            "dusty rose", "soft teal", "lavender", "raspberry",
        ],
        "colors_to_avoid": [
            "bright orange", "bright yellow", "black",
            "stark white", "warm earth tones", "gold",
        ],
        "metals": ["silver", "platinum", "white gold", "rose gold"],
    },
    
    SeasonType.AUTUMN: {
        "best_colors": [
            # Warm, muted, earthy colors
            "rust", "terracotta", "burnt orange", "pumpkin",
            "mustard", "gold", "amber", "honey",
            "olive", "moss green", "forest green", "khaki",
            "teal", "deep turquoise", "petrol blue",
            "brick red", "tomato", "warm red", "paprika",
            "chocolate", "coffee", "camel", "tan",
            "cream", "warm beige", "oyster",
            "bronze", "copper", "antique gold",
        ],
        "neutral_colors": [
            "cream", "oyster", "warm beige",
            "camel", "chocolate brown", "olive",
            "warm gray", "charcoal brown",
        ],
        "accent_colors": [
            "rust", "teal", "mustard", "terracotta",
        ],
        "colors_to_avoid": [
            "black", "pure white", "bright pink", "fuchsia",
            "bright blue", "icy colors", "silver",
        ],
        "metals": ["gold", "bronze", "copper", "brass", "antique gold"],
    },
    
    SeasonType.WINTER: {
        "best_colors": [
            # Cool, clear, bright or dark colors
            "true red", "burgundy", "cherry", "wine",
            "hot pink", "magenta", "fuchsia", "shocking pink",
            "royal blue", "cobalt", "navy", "sapphire",
            "emerald", "pine green", "forest green", "bright teal",
            "purple", "violet", "royal purple", "plum",
            "true white", "bright white", "icy colors",
            "black", "charcoal", "cool gray",
            "silver", "platinum", "icy blue",
        ],
        "neutral_colors": [
            "pure white", "black", "charcoal",
            "navy", "cool gray", "icy gray",
            "taupe", "cool brown",
        ],
        "accent_colors": [
            "hot pink", "emerald", "royal blue", "true red",
        ],
        "colors_to_avoid": [
            "orange", "peach", "warm yellow", "rust",
            "warm earth tones", "muted colors", "gold",
        ],
        "metals": ["silver", "platinum", "white gold"],
    },
}


# ============================================
# SEASONAL SUBTYPE PALETTES (More specific)
# ============================================

SUBTYPE_PALETTES: Dict[SeasonSubtype, Dict[str, List[str]]] = {
    # SPRING SUBTYPES
    SeasonSubtype.LIGHT_SPRING: {
        "signature_colors": ["peach", "coral", "light turquoise", "warm pink"],
        "intensity": "light to medium",
        "avoid": ["very dark colors", "heavy earth tones"],
    },
    SeasonSubtype.WARM_SPRING: {
        "signature_colors": ["golden yellow", "warm coral", "amber", "warm green"],
        "intensity": "medium, warm",
        "avoid": ["cool colors", "blue-based colors"],
    },
    SeasonSubtype.BRIGHT_SPRING: {
        "signature_colors": ["bright coral", "turquoise", "bright yellow", "clear red"],
        "intensity": "bright, clear",
        "avoid": ["muted colors", "dusty tones"],
    },
    
    # SUMMER SUBTYPES
    SeasonSubtype.LIGHT_SUMMER: {
        "signature_colors": ["powder blue", "soft pink", "lavender", "light periwinkle"],
        "intensity": "light, soft",
        "avoid": ["very dark colors", "bright warm colors"],
    },
    SeasonSubtype.COOL_SUMMER: {
        "signature_colors": ["raspberry", "cool pink", "soft teal", "blue violet"],
        "intensity": "medium, cool",
        "avoid": ["warm colors", "orange tones"],
    },
    SeasonSubtype.SOFT_SUMMER: {
        "signature_colors": ["dusty rose", "soft blue gray", "sage", "mauve"],
        "intensity": "soft, muted",
        "avoid": ["bright colors", "stark contrasts"],
    },
    
    # AUTUMN SUBTYPES
    SeasonSubtype.SOFT_AUTUMN: {
        "signature_colors": ["soft coral", "olive", "soft teal", "warm taupe"],
        "intensity": "soft, muted",
        "avoid": ["bright colors", "stark contrasts", "cool colors"],
    },
    SeasonSubtype.WARM_AUTUMN: {
        "signature_colors": ["pumpkin", "gold", "olive green", "warm brown"],
        "intensity": "medium, warm",
        "avoid": ["cool colors", "black", "bright pink"],
    },
    SeasonSubtype.DEEP_AUTUMN: {
        "signature_colors": ["rust", "olive", "warm burgundy", "bronze"],
        "intensity": "deep, rich",
        "avoid": ["pastels", "light colors", "cool colors"],
    },
    
    # WINTER SUBTYPES
    SeasonSubtype.DEEP_WINTER: {
        "signature_colors": ["burgundy", "forest green", "navy", "plum"],
        "intensity": "deep, dramatic",
        "avoid": ["light pastels", "warm earth tones"],
    },
    SeasonSubtype.COOL_WINTER: {
        "signature_colors": ["magenta", "royal blue", "emerald", "icy pink"],
        "intensity": "cool, medium to deep",
        "avoid": ["warm colors", "orange", "gold"],
    },
    SeasonSubtype.BRIGHT_WINTER: {
        "signature_colors": ["hot pink", "true red", "cobalt", "emerald"],
        "intensity": "bright, clear, high contrast",
        "avoid": ["muted colors", "dusty tones", "warm earth tones"],
    },
}


# ============================================
# SEASONAL COLOR MATCHING FUNCTIONS
# ============================================

def get_season_colors(season: SeasonType) -> Dict[str, List[str]]:
    """Get full color palette for a season"""
    return SEASONAL_PALETTES.get(season, {})


def get_subtype_details(subtype: SeasonSubtype) -> Dict:
    """Get detailed color info for a season subtype"""
    return SUBTYPE_PALETTES.get(subtype, {})


def is_color_in_season(color_name: str, season: SeasonType) -> Tuple[bool, float, str]:
    """
    Check if a color belongs to a seasonal palette
    
    Returns:
        Tuple of (is_recommended, score, reason)
    """
    color_name = color_name.lower()
    palette = SEASONAL_PALETTES.get(season, {})
    
    # Check best colors
    if color_name in palette.get("best_colors", []):
        return True, 1.0, f"'{color_name}' is a perfect {season.value} color"
    
    # Check neutral colors
    if color_name in palette.get("neutral_colors", []):
        return True, 0.85, f"'{color_name}' is a great neutral for {season.value}"
    
    # Check accent colors
    if color_name in palette.get("accent_colors", []):
        return True, 0.9, f"'{color_name}' is a signature accent for {season.value}"
    
    # Check colors to avoid
    if color_name in palette.get("colors_to_avoid", []):
        return False, 0.2, f"'{color_name}' is typically avoided for {season.value}"
    
    # Not explicitly listed - moderate score
    return True, 0.5, f"'{color_name}' compatibility with {season.value} is moderate"


def get_seasonal_recommendations(
    season: SeasonType,
    subtype: Optional[SeasonSubtype] = None,
    category: str = "all"
) -> Dict[str, List[str]]:
    """
    Get color recommendations for a season
    
    Args:
        season: Main season type
        subtype: Optional subtype for more specific recommendations
        category: 'best', 'neutral', 'accent', 'avoid', or 'all'
    
    Returns:
        Dictionary of color recommendations
    """
    palette = SEASONAL_PALETTES.get(season, {})
    
    if category == "all":
        result = {
            "best_colors": palette.get("best_colors", []),
            "neutral_colors": palette.get("neutral_colors", []),
            "accent_colors": palette.get("accent_colors", []),
            "colors_to_avoid": palette.get("colors_to_avoid", []),
            "recommended_metals": palette.get("metals", []),
        }
    else:
        result = {category: palette.get(category, [])}
    
    # Add subtype-specific info if available
    if subtype and subtype in SUBTYPE_PALETTES:
        subtype_info = SUBTYPE_PALETTES[subtype]
        result["signature_colors"] = subtype_info.get("signature_colors", [])
        result["intensity"] = subtype_info.get("intensity", "medium")
    
    return result


def calculate_seasonal_score(
    color_name: str,
    cloth_rgb: List[int],
    season: SeasonType,
    undertone: str
) -> Tuple[float, str]:
    """
    Calculate how well a color fits a user's season
    
    Args:
        color_name: Name of the clothing color
        cloth_rgb: RGB values of the clothing
        season: User's seasonal color type
        undertone: User's undertone
    
    Returns:
        Tuple of (score 0-1, reasoning)
    """
    # Check by color name first
    is_good, name_score, reason = is_color_in_season(color_name.lower(), season)
    
    # If color name gives definitive answer, use it
    if name_score >= 0.8 or name_score <= 0.3:
        return name_score, reason
    
    # Otherwise, analyze RGB values
    r, g, b = cloth_rgb
    
    # Calculate color characteristics
    saturation = (max(r, g, b) - min(r, g, b)) / 255.0 if max(r, g, b) > 0 else 0
    brightness = max(r, g, b) / 255.0
    warmth = (r - b) / 255.0  # Positive = warm, negative = cool
    
    score = 0.5  # Start with neutral
    reasons = []
    
    if season == SeasonType.SPRING:
        # Spring likes warm, bright, clear colors
        if warmth > 0.1:
            score += 0.15
            reasons.append("warm tone")
        if brightness > 0.5 and saturation > 0.3:
            score += 0.15
            reasons.append("bright and clear")
        if brightness < 0.3:
            score -= 0.2
            reasons.append("too dark for spring")
            
    elif season == SeasonType.SUMMER:
        # Summer likes cool, soft, muted colors
        if warmth < 0:
            score += 0.15
            reasons.append("cool tone")
        if saturation < 0.5:
            score += 0.1
            reasons.append("soft and muted")
        if saturation > 0.7:
            score -= 0.15
            reasons.append("may be too bright")
            
    elif season == SeasonType.AUTUMN:
        # Autumn likes warm, muted, earthy colors
        if warmth > 0.1:
            score += 0.15
            reasons.append("warm tone")
        if saturation < 0.6 and brightness < 0.7:
            score += 0.1
            reasons.append("muted and earthy")
        if warmth < -0.1:
            score -= 0.15
            reasons.append("too cool for autumn")
            
    elif season == SeasonType.WINTER:
        # Winter likes cool, clear, bright or very dark colors
        if warmth < 0:
            score += 0.1
            reasons.append("cool tone")
        if saturation > 0.5 or brightness < 0.2 or brightness > 0.9:
            score += 0.15
            reasons.append("high contrast")
        if 0.3 < saturation < 0.6 and 0.3 < brightness < 0.7:
            score -= 0.1
            reasons.append("may be too muted")
    
    score = max(0, min(1, score))
    reason = f"Color analysis for {season.value}: " + ", ".join(reasons) if reasons else f"Moderate fit for {season.value}"
    
    return score, reason

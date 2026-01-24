# Color Recommendation Rules
# Author: Recommendation Team
# Last Updated: January 24, 2026
# 
# This module defines color rules for each undertone type based on 
# color theory and seasonal color analysis principles.

from typing import Dict, List, Set, Tuple
from enum import Enum


# ============================================
# COLOR DEFINITIONS
# ============================================

class ColorCategory(str, Enum):
    """Color temperature/harmony categories"""
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"
    UNIVERSAL = "universal"  # Works for everyone


# Master color database with RGB values and properties
COLOR_DATABASE: Dict[str, Dict] = {
    # ========== WARM COLORS ==========
    "coral": {"rgb": [255, 127, 80], "category": "warm", "warmth": 0.9},
    "peach": {"rgb": [255, 218, 185], "category": "warm", "warmth": 0.8},
    "salmon": {"rgb": [250, 128, 114], "category": "warm", "warmth": 0.85},
    "orange": {"rgb": [255, 165, 0], "category": "warm", "warmth": 1.0},
    "burnt orange": {"rgb": [204, 85, 0], "category": "warm", "warmth": 0.95},
    "terracotta": {"rgb": [226, 114, 91], "category": "warm", "warmth": 0.9},
    "rust": {"rgb": [183, 65, 14], "category": "warm", "warmth": 0.95},
    "gold": {"rgb": [255, 215, 0], "category": "warm", "warmth": 0.9},
    "mustard": {"rgb": [255, 219, 88], "category": "warm", "warmth": 0.85},
    "honey": {"rgb": [235, 177, 52], "category": "warm", "warmth": 0.85},
    "amber": {"rgb": [255, 191, 0], "category": "warm", "warmth": 0.9},
    "camel": {"rgb": [193, 154, 107], "category": "warm", "warmth": 0.7},
    "tan": {"rgb": [210, 180, 140], "category": "warm", "warmth": 0.6},
    "bronze": {"rgb": [205, 127, 50], "category": "warm", "warmth": 0.8},
    "copper": {"rgb": [184, 115, 51], "category": "warm", "warmth": 0.85},
    "warm red": {"rgb": [255, 69, 0], "category": "warm", "warmth": 0.9},
    "tomato red": {"rgb": [255, 99, 71], "category": "warm", "warmth": 0.85},
    "brick red": {"rgb": [203, 65, 84], "category": "warm", "warmth": 0.8},
    "warm brown": {"rgb": [150, 75, 0], "category": "warm", "warmth": 0.8},
    "chocolate": {"rgb": [123, 63, 0], "category": "warm", "warmth": 0.75},
    "olive": {"rgb": [128, 128, 0], "category": "warm", "warmth": 0.6},
    "olive green": {"rgb": [107, 142, 35], "category": "warm", "warmth": 0.55},
    "warm yellow": {"rgb": [255, 223, 0], "category": "warm", "warmth": 0.9},
    "golden yellow": {"rgb": [255, 223, 0], "category": "warm", "warmth": 0.9},
    "cream": {"rgb": [255, 253, 208], "category": "warm", "warmth": 0.5},
    "ivory": {"rgb": [255, 255, 240], "category": "warm", "warmth": 0.4},
    "beige": {"rgb": [245, 245, 220], "category": "warm", "warmth": 0.5},
    "warm pink": {"rgb": [255, 182, 193], "category": "warm", "warmth": 0.6},
    "peach pink": {"rgb": [255, 203, 164], "category": "warm", "warmth": 0.7},
    
    # ========== COOL COLORS ==========
    "navy": {"rgb": [0, 0, 128], "category": "cool", "warmth": 0.1},
    "navy blue": {"rgb": [0, 0, 128], "category": "cool", "warmth": 0.1},
    "royal blue": {"rgb": [65, 105, 225], "category": "cool", "warmth": 0.15},
    "cobalt": {"rgb": [0, 71, 171], "category": "cool", "warmth": 0.1},
    "sapphire": {"rgb": [15, 82, 186], "category": "cool", "warmth": 0.1},
    "sky blue": {"rgb": [135, 206, 235], "category": "cool", "warmth": 0.25},
    "powder blue": {"rgb": [176, 224, 230], "category": "cool", "warmth": 0.3},
    "ice blue": {"rgb": [153, 255, 255], "category": "cool", "warmth": 0.2},
    "teal": {"rgb": [0, 128, 128], "category": "cool", "warmth": 0.2},
    "turquoise": {"rgb": [64, 224, 208], "category": "cool", "warmth": 0.25},
    "aqua": {"rgb": [0, 255, 255], "category": "cool", "warmth": 0.2},
    "mint": {"rgb": [152, 255, 152], "category": "cool", "warmth": 0.3},
    "seafoam": {"rgb": [159, 226, 191], "category": "cool", "warmth": 0.3},
    "emerald": {"rgb": [80, 200, 120], "category": "cool", "warmth": 0.3},
    "forest green": {"rgb": [34, 139, 34], "category": "cool", "warmth": 0.25},
    "pine green": {"rgb": [1, 121, 111], "category": "cool", "warmth": 0.2},
    "cool pink": {"rgb": [255, 192, 203], "category": "cool", "warmth": 0.35},
    "rose": {"rgb": [255, 0, 127], "category": "cool", "warmth": 0.3},
    "hot pink": {"rgb": [255, 105, 180], "category": "cool", "warmth": 0.35},
    "magenta": {"rgb": [255, 0, 255], "category": "cool", "warmth": 0.25},
    "fuchsia": {"rgb": [255, 0, 128], "category": "cool", "warmth": 0.3},
    "raspberry": {"rgb": [227, 11, 92], "category": "cool", "warmth": 0.3},
    "burgundy": {"rgb": [128, 0, 32], "category": "cool", "warmth": 0.35},
    "wine": {"rgb": [114, 47, 55], "category": "cool", "warmth": 0.35},
    "plum": {"rgb": [142, 69, 133], "category": "cool", "warmth": 0.3},
    "purple": {"rgb": [128, 0, 128], "category": "cool", "warmth": 0.2},
    "violet": {"rgb": [138, 43, 226], "category": "cool", "warmth": 0.2},
    "lavender": {"rgb": [230, 230, 250], "category": "cool", "warmth": 0.3},
    "lilac": {"rgb": [200, 162, 200], "category": "cool", "warmth": 0.35},
    "mauve": {"rgb": [224, 176, 255], "category": "cool", "warmth": 0.35},
    "cool red": {"rgb": [220, 20, 60], "category": "cool", "warmth": 0.35},
    "cherry": {"rgb": [222, 49, 99], "category": "cool", "warmth": 0.35},
    "cool brown": {"rgb": [111, 78, 55], "category": "cool", "warmth": 0.4},
    "taupe": {"rgb": [72, 60, 50], "category": "cool", "warmth": 0.4},
    "charcoal": {"rgb": [54, 69, 79], "category": "cool", "warmth": 0.2},
    "slate": {"rgb": [112, 128, 144], "category": "cool", "warmth": 0.25},
    "steel blue": {"rgb": [70, 130, 180], "category": "cool", "warmth": 0.2},
    "silver": {"rgb": [192, 192, 192], "category": "cool", "warmth": 0.3},
    "pure white": {"rgb": [255, 255, 255], "category": "cool", "warmth": 0.35},
    "bright white": {"rgb": [255, 255, 255], "category": "cool", "warmth": 0.35},
    
    # ========== NEUTRAL COLORS ==========
    "white": {"rgb": [255, 255, 255], "category": "neutral", "warmth": 0.5},
    "off-white": {"rgb": [250, 250, 245], "category": "neutral", "warmth": 0.5},
    "black": {"rgb": [0, 0, 0], "category": "neutral", "warmth": 0.5},
    "gray": {"rgb": [128, 128, 128], "category": "neutral", "warmth": 0.5},
    "grey": {"rgb": [128, 128, 128], "category": "neutral", "warmth": 0.5},
    "light gray": {"rgb": [211, 211, 211], "category": "neutral", "warmth": 0.5},
    "dark gray": {"rgb": [64, 64, 64], "category": "neutral", "warmth": 0.5},
    "medium gray": {"rgb": [128, 128, 128], "category": "neutral", "warmth": 0.5},
    "greige": {"rgb": [169, 161, 149], "category": "neutral", "warmth": 0.5},
    "true red": {"rgb": [255, 0, 0], "category": "neutral", "warmth": 0.5},
    "red": {"rgb": [255, 0, 0], "category": "neutral", "warmth": 0.5},
    "blue": {"rgb": [0, 0, 255], "category": "neutral", "warmth": 0.5},
    "green": {"rgb": [0, 128, 0], "category": "neutral", "warmth": 0.5},
    "brown": {"rgb": [139, 69, 19], "category": "neutral", "warmth": 0.55},
    "khaki": {"rgb": [195, 176, 145], "category": "neutral", "warmth": 0.55},
    "denim": {"rgb": [21, 96, 189], "category": "neutral", "warmth": 0.4},
    "indigo": {"rgb": [75, 0, 130], "category": "neutral", "warmth": 0.4},
    "nude": {"rgb": [235, 200, 178], "category": "neutral", "warmth": 0.5},
    "blush": {"rgb": [222, 165, 164], "category": "neutral", "warmth": 0.55},
}


# ============================================
# UNDERTONE-BASED COLOR RULES
# ============================================

class UndertoneColorRules:
    """Color recommendations based on skin undertone"""
    
    # Best colors for WARM undertones (yellow/golden/peachy skin)
    WARM_BEST_COLORS: List[str] = [
        # Earth tones
        "coral", "peach", "salmon", "orange", "burnt orange", "terracotta", "rust",
        # Warm metallics
        "gold", "mustard", "honey", "amber", "bronze", "copper",
        # Warm neutrals
        "camel", "tan", "cream", "ivory", "beige", "warm brown", "chocolate",
        # Warm reds and pinks
        "warm red", "tomato red", "brick red", "warm pink", "peach pink",
        # Warm greens
        "olive", "olive green",
        # Warm yellows
        "warm yellow", "golden yellow",
        # Warm whites
        "cream", "ivory", "off-white",
    ]
    
    WARM_AVOID_COLORS: List[str] = [
        # Cool blues
        "navy", "royal blue", "cobalt", "sapphire", "ice blue",
        # Cool pinks and purples
        "hot pink", "magenta", "fuchsia", "purple", "violet", "lavender",
        # Cool whites
        "pure white", "bright white",
        # Cool silvers
        "silver", "charcoal", "slate",
        # Cool pinks
        "cool pink", "rose", "raspberry",
    ]
    
    # Best colors for COOL undertones (pink/red/bluish skin)
    COOL_BEST_COLORS: List[str] = [
        # Blues
        "navy", "navy blue", "royal blue", "cobalt", "sapphire", "sky blue", 
        "powder blue", "ice blue", "steel blue",
        # Blue-greens
        "teal", "turquoise", "aqua", "mint", "seafoam", "emerald",
        # Cool pinks and reds
        "cool pink", "rose", "hot pink", "magenta", "fuchsia", "raspberry",
        "burgundy", "wine", "cool red", "cherry",
        # Purples
        "plum", "purple", "violet", "lavender", "lilac", "mauve",
        # Cool neutrals
        "charcoal", "slate", "silver", "pure white", "bright white",
        # Cool greens
        "forest green", "pine green",
        # Cool browns
        "cool brown", "taupe",
    ]
    
    COOL_AVOID_COLORS: List[str] = [
        # Warm oranges and yellows
        "orange", "burnt orange", "terracotta", "rust", "mustard",
        "warm yellow", "golden yellow", "gold", "amber",
        # Warm neutrals
        "camel", "tan", "cream", "ivory", "beige",
        # Warm reds
        "coral", "peach", "salmon", "tomato red", "brick red",
        # Warm browns
        "bronze", "copper", "warm brown", "chocolate",
    ]
    
    # Best colors for NEUTRAL undertones (balanced, can wear both)
    NEUTRAL_BEST_COLORS: List[str] = [
        # Soft, muted versions work best
        "jade", "soft pink", "dusty rose", "mauve", "soft coral",
        "periwinkle", "soft blue", "sage", "dusty blue",
        # True neutrals
        "white", "off-white", "black", "gray", "grey", "greige",
        "true red", "red", "blue", "green",
        # Balanced tones
        "denim", "indigo", "nude", "blush", "khaki",
        # Medium intensity colors
        "teal", "burgundy", "forest green", "navy",
    ]
    
    NEUTRAL_AVOID_COLORS: List[str] = [
        # Very saturated warm colors
        "bright orange", "neon yellow",
        # Very saturated cool colors
        "neon pink", "electric blue",
        # Note: Neutrals can generally wear most colors
    ]
    
    @classmethod
    def get_best_colors(cls, undertone: str) -> List[str]:
        """Get best colors for an undertone"""
        undertone = undertone.lower()
        if undertone == "warm":
            return cls.WARM_BEST_COLORS.copy()
        elif undertone == "cool":
            return cls.COOL_BEST_COLORS.copy()
        else:  # neutral
            return cls.NEUTRAL_BEST_COLORS.copy()
    
    @classmethod
    def get_avoid_colors(cls, undertone: str) -> List[str]:
        """Get colors to avoid for an undertone"""
        undertone = undertone.lower()
        if undertone == "warm":
            return cls.WARM_AVOID_COLORS.copy()
        elif undertone == "cool":
            return cls.COOL_AVOID_COLORS.copy()
        else:  # neutral
            return cls.NEUTRAL_AVOID_COLORS.copy()
    
    @classmethod
    def is_color_recommended(cls, color_name: str, undertone: str) -> Tuple[bool, float, str]:
        """
        Check if a color is recommended for an undertone
        
        Returns:
            Tuple of (is_recommended, score, reason)
        """
        color_name = color_name.lower()
        undertone = undertone.lower()
        
        best_colors = cls.get_best_colors(undertone)
        avoid_colors = cls.get_avoid_colors(undertone)
        
        # Check if in best colors
        if color_name in best_colors:
            return True, 1.0, f"'{color_name}' is excellent for {undertone} undertones"
        
        # Check if in avoid colors
        if color_name in avoid_colors:
            return False, 0.2, f"'{color_name}' may clash with {undertone} undertones"
        
        # Check color database for category
        if color_name in COLOR_DATABASE:
            color_info = COLOR_DATABASE[color_name]
            color_category = color_info["category"]
            warmth = color_info["warmth"]
            
            if undertone == "warm" and warmth >= 0.6:
                return True, 0.8, f"'{color_name}' has warm undertones that complement your skin"
            elif undertone == "cool" and warmth <= 0.4:
                return True, 0.8, f"'{color_name}' has cool undertones that complement your skin"
            elif undertone == "neutral":
                return True, 0.7, f"'{color_name}' works well with neutral undertones"
            else:
                return True, 0.5, f"'{color_name}' is acceptable but not optimal"
        
        # Unknown color - neutral score
        return True, 0.5, f"'{color_name}' compatibility unknown, moderate match assumed"


# ============================================
# RGB COLOR MATCHING
# ============================================

def calculate_color_warmth(rgb: List[int]) -> float:
    """
    Calculate warmth score of a color (0=cool, 1=warm)
    Based on red-yellow vs blue-purple balance
    """
    r, g, b = rgb
    
    # Warm colors have more red/yellow, cool colors have more blue
    # Calculate warmth based on color balance
    
    # Red contribution (warm)
    red_warmth = r / 255.0
    
    # Yellow contribution (warm) - when R and G are high, B is low
    yellow_warmth = min(r, g) / 255.0 * (1 - b / 255.0)
    
    # Blue contribution (cool)
    blue_coolness = b / 255.0 * (1 - r / 255.0)
    
    # Purple contribution (cool) - when R and B are high, G is low
    purple_coolness = min(r, b) / 255.0 * (1 - g / 255.0) * 0.5
    
    warmth = (red_warmth * 0.4 + yellow_warmth * 0.4) - (blue_coolness * 0.5 + purple_coolness * 0.3)
    
    # Normalize to 0-1 range
    warmth = max(0, min(1, (warmth + 0.5)))
    
    return warmth


def get_color_compatibility_score(
    cloth_rgb: List[int],
    undertone: str,
    skin_rgb: List[int] = None
) -> Tuple[float, str]:
    """
    Calculate color compatibility score based on RGB values
    
    Args:
        cloth_rgb: RGB values of clothing color
        undertone: User's skin undertone
        skin_rgb: Optional RGB values of user's skin
    
    Returns:
        Tuple of (score 0-1, reasoning)
    """
    warmth = calculate_color_warmth(cloth_rgb)
    undertone = undertone.lower()
    
    # Determine if color matches undertone
    if undertone == "warm":
        if warmth >= 0.6:
            score = 0.8 + (warmth - 0.6) * 0.5  # 0.8 to 1.0
            reason = f"Warm color (warmth: {warmth:.2f}) complements warm undertone"
        elif warmth >= 0.4:
            score = 0.5 + (warmth - 0.4) * 1.5  # 0.5 to 0.8
            reason = f"Neutral-warm color (warmth: {warmth:.2f}) is acceptable"
        else:
            score = 0.2 + warmth * 0.75  # 0.2 to 0.5
            reason = f"Cool color (warmth: {warmth:.2f}) may clash with warm undertone"
            
    elif undertone == "cool":
        if warmth <= 0.4:
            score = 0.8 + (0.4 - warmth) * 0.5  # 0.8 to 1.0
            reason = f"Cool color (warmth: {warmth:.2f}) complements cool undertone"
        elif warmth <= 0.6:
            score = 0.5 + (0.6 - warmth) * 1.5  # 0.5 to 0.8
            reason = f"Neutral-cool color (warmth: {warmth:.2f}) is acceptable"
        else:
            score = 0.5 - (warmth - 0.6) * 0.75  # 0.2 to 0.5
            reason = f"Warm color (warmth: {warmth:.2f}) may clash with cool undertone"
            
    else:  # neutral
        # Neutral undertones work with most colors, slight preference for balanced
        distance_from_neutral = abs(warmth - 0.5)
        score = 0.7 + (0.5 - distance_from_neutral) * 0.6  # 0.7 to 1.0
        reason = f"Color (warmth: {warmth:.2f}) works well with neutral undertone"
    
    return max(0, min(1, score)), reason


def find_closest_color_name(rgb: List[int]) -> str:
    """Find the closest named color for RGB values"""
    min_distance = float('inf')
    closest_name = "unknown"
    
    for name, info in COLOR_DATABASE.items():
        db_rgb = info["rgb"]
        # Euclidean distance in RGB space
        distance = sum((a - b) ** 2 for a, b in zip(rgb, db_rgb)) ** 0.5
        
        if distance < min_distance:
            min_distance = distance
            closest_name = name
    
    return closest_name


# ============================================
# UNIVERSAL COLORS (Work for all undertones)
# ============================================

UNIVERSAL_COLORS: List[str] = [
    "true red",
    "black", 
    "white",
    "navy",
    "blush",
    "teal",
    "soft pink",
]

def is_universal_color(color_name: str) -> bool:
    """Check if a color works universally for all undertones"""
    return color_name.lower() in UNIVERSAL_COLORS

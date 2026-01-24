# Utility functions for recommendation engine
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# Helper functions for matching, filtering, sorting, and data conversion

from typing import List, Dict, Any, Tuple, Optional
import math
import colorsys

from .schemas import (
    SkinFeatures, ClothFeatures, ClothRecommendation,
    Undertone, SkinDepth, Season, StyleType, WeatherType
)


# ============================================
# COLOR CONVERSION UTILITIES
# ============================================

def rgb_to_hex(rgb: List[int]) -> str:
    """Convert RGB to hex color code"""
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def hex_to_rgb(hex_color: str) -> List[int]:
    """Convert hex color code to RGB"""
    hex_color = hex_color.lstrip('#')
    return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]


def rgb_to_lab(rgb: List[int]) -> Tuple[float, float, float]:
    """
    Convert RGB to LAB color space
    Uses D65 illuminant
    """
    # First convert to XYZ
    def pivot(n):
        n = n / 255.0
        return ((n + 0.055) / 1.055) ** 2.4 if n > 0.04045 else n / 12.92
    
    r, g, b = [pivot(c) for c in rgb]
    
    x = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) / 0.95047
    y = (r * 0.2126729 + g * 0.7151522 + b * 0.0721750) / 1.00000
    z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) / 1.08883
    
    def f(t):
        return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16 / 116)
    
    l = (116 * f(y)) - 16
    a = 500 * (f(x) - f(y))
    b_val = 200 * (f(y) - f(z))
    
    return l, a, b_val


def lab_to_rgb(lab: Tuple[float, float, float]) -> List[int]:
    """Convert LAB to RGB color space"""
    l, a, b = lab
    
    y = (l + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    
    def f_inv(t):
        return t ** 3 if t ** 3 > 0.008856 else (t - 16 / 116) / 7.787
    
    x = 0.95047 * f_inv(x)
    y = 1.00000 * f_inv(y)
    z = 1.08883 * f_inv(z)
    
    r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b_val = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
    
    def gamma(n):
        return 1.055 * (n ** (1/2.4)) - 0.055 if n > 0.0031308 else 12.92 * n
    
    return [
        max(0, min(255, int(gamma(r) * 255))),
        max(0, min(255, int(gamma(g) * 255))),
        max(0, min(255, int(gamma(b_val) * 255)))
    ]


def rgb_to_hsv(rgb: List[int]) -> Tuple[float, float, float]:
    """Convert RGB to HSV color space"""
    r, g, b = [x / 255.0 for x in rgb]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s, v


def hsv_to_rgb(hsv: Tuple[float, float, float]) -> List[int]:
    """Convert HSV to RGB"""
    h, s, v = hsv
    r, g, b = colorsys.hsv_to_rgb(h / 360, s, v)
    return [int(r * 255), int(g * 255), int(b * 255)]


# ============================================
# COLOR DISTANCE CALCULATIONS
# ============================================

def color_distance_euclidean(rgb1: List[int], rgb2: List[int]) -> float:
    """Simple Euclidean distance in RGB space"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))


def color_distance_lab(rgb1: List[int], rgb2: List[int]) -> float:
    """
    Perceptually uniform color distance using LAB color space (CIE76)
    More accurate for human perception
    """
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


def color_distance_ciede2000(rgb1: List[int], rgb2: List[int]) -> float:
    """
    CIEDE2000 color difference formula
    Most accurate perceptual color distance
    """
    lab1 = rgb_to_lab(rgb1)
    lab2 = rgb_to_lab(rgb2)
    
    L1, a1, b1 = lab1
    L2, a2, b2 = lab2
    
    # Calculate C and h
    C1 = math.sqrt(a1**2 + b1**2)
    C2 = math.sqrt(a2**2 + b2**2)
    C_avg = (C1 + C2) / 2
    
    G = 0.5 * (1 - math.sqrt(C_avg**7 / (C_avg**7 + 25**7)))
    
    a1_prime = a1 * (1 + G)
    a2_prime = a2 * (1 + G)
    
    C1_prime = math.sqrt(a1_prime**2 + b1**2)
    C2_prime = math.sqrt(a2_prime**2 + b2**2)
    
    h1_prime = math.degrees(math.atan2(b1, a1_prime)) % 360
    h2_prime = math.degrees(math.atan2(b2, a2_prime)) % 360
    
    # Calculate deltas
    delta_L = L2 - L1
    delta_C = C2_prime - C1_prime
    
    delta_h = h2_prime - h1_prime
    if abs(delta_h) > 180:
        delta_h = delta_h - 360 if delta_h > 180 else delta_h + 360
    
    delta_H = 2 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(delta_h / 2))
    
    # Calculate CIEDE2000
    L_avg = (L1 + L2) / 2
    C_avg_prime = (C1_prime + C2_prime) / 2
    
    h_avg = (h1_prime + h2_prime) / 2
    if abs(h1_prime - h2_prime) > 180:
        h_avg = h_avg + 180 if h_avg < 180 else h_avg - 180
    
    T = (1 - 0.17 * math.cos(math.radians(h_avg - 30)) +
         0.24 * math.cos(math.radians(2 * h_avg)) +
         0.32 * math.cos(math.radians(3 * h_avg + 6)) -
         0.20 * math.cos(math.radians(4 * h_avg - 63)))
    
    delta_theta = 30 * math.exp(-((h_avg - 275) / 25) ** 2)
    R_C = 2 * math.sqrt(C_avg_prime**7 / (C_avg_prime**7 + 25**7))
    S_L = 1 + (0.015 * (L_avg - 50)**2) / math.sqrt(20 + (L_avg - 50)**2)
    S_C = 1 + 0.045 * C_avg_prime
    S_H = 1 + 0.015 * C_avg_prime * T
    R_T = -math.sin(math.radians(2 * delta_theta)) * R_C
    
    delta_E = math.sqrt(
        (delta_L / S_L)**2 +
        (delta_C / S_C)**2 +
        (delta_H / S_H)**2 +
        R_T * (delta_C / S_C) * (delta_H / S_H)
    )
    
    return delta_E


# ============================================
# SKIN TONE ANALYSIS UTILITIES
# ============================================

def estimate_undertone_from_lab(lab_a: float, lab_b: float) -> str:
    """
    Estimate undertone from LAB a and b values
    
    a > 0: More red (warm)
    a < 0: More green (cool)
    b > 0: More yellow (warm)
    b < 0: More blue (cool)
    """
    warmth_score = (lab_a + lab_b) / 2
    
    if warmth_score > 10:
        return "warm"
    elif warmth_score < 0:
        return "cool"
    else:
        return "neutral"


def estimate_skin_depth_from_lab_l(lab_l: float) -> str:
    """Estimate skin depth from LAB L value"""
    if lab_l >= 75:
        return "fair"
    elif lab_l >= 65:
        return "light"
    elif lab_l >= 50:
        return "medium"
    elif lab_l >= 35:
        return "tan"
    else:
        return "deep"


# ============================================
# FILTERING UTILITIES
# ============================================

def filter_clothes_by_color_distance(
    clothes: List[ClothFeatures],
    target_rgb: List[int],
    max_distance: float = 100,
    use_lab: bool = True
) -> List[ClothFeatures]:
    """
    Filter clothing items by color distance from target
    """
    distance_fn = color_distance_lab if use_lab else color_distance_euclidean
    
    return [
        cloth for cloth in clothes
        if distance_fn(cloth.dominant_color_rgb, target_rgb) <= max_distance
    ]


def filter_clothes_by_formality_range(
    clothes: List[ClothFeatures],
    min_formality: int = 1,
    max_formality: int = 10
) -> List[ClothFeatures]:
    """Filter clothes by formality level range"""
    return [
        cloth for cloth in clothes
        if min_formality <= cloth.formality_level <= max_formality
    ]


def filter_by_weather(
    clothes: List[ClothFeatures],
    target_weather: WeatherType,
    include_all_season: bool = True
) -> List[ClothFeatures]:
    """Filter clothes by weather suitability"""
    results = [c for c in clothes if c.weather == target_weather]
    
    if include_all_season:
        results.extend([
            c for c in clothes 
            if c.weather == WeatherType.ALL_SEASON and c not in results
        ])
    
    return results


# ============================================
# SORTING UTILITIES
# ============================================

def sort_recommendations_by_score(
    recommendations: List[ClothRecommendation],
    descending: bool = True
) -> List[ClothRecommendation]:
    """Sort recommendations by overall score"""
    return sorted(
        recommendations,
        key=lambda r: r.overall_score,
        reverse=descending
    )


def sort_clothes_by_color_match(
    clothes: List[ClothFeatures],
    target_rgb: List[int]
) -> List[ClothFeatures]:
    """Sort clothes by how closely they match a target color"""
    return sorted(
        clothes,
        key=lambda c: color_distance_lab(c.dominant_color_rgb, target_rgb)
    )


# ============================================
# DATA TRANSFORMATION UTILITIES
# ============================================

def cloth_features_to_dict(cloth: ClothFeatures) -> Dict[str, Any]:
    """Convert ClothFeatures to dictionary"""
    return {
        "cloth_id": cloth.cloth_id,
        "image_url": cloth.image_url,
        "dominant_color": {
            "rgb": cloth.dominant_color_rgb,
            "name": cloth.dominant_color_name,
            "hex": cloth.color_hex
        },
        "category": cloth.category.value,
        "style": cloth.style.value,
        "gender": cloth.gender.value,
        "design": cloth.design,
        "fabric": cloth.fabric,
        "weather": cloth.weather.value,
        "formality_level": cloth.formality_level,
        "confidence": cloth.confidence
    }


def recommendation_to_summary(rec: ClothRecommendation) -> Dict[str, Any]:
    """Convert recommendation to summary dict for API response"""
    return {
        "cloth_id": rec.cloth_id,
        "rank": rec.rank,
        "score": rec.overall_score,
        "level": rec.recommendation_level,
        "color_score": rec.score_breakdown.color_score,
        "style_score": rec.score_breakdown.style_score,
        "reasoning": rec.score_breakdown.overall_reasoning
    }


def batch_convert_to_summary(
    recommendations: List[ClothRecommendation]
) -> List[Dict[str, Any]]:
    """Convert list of recommendations to summaries"""
    return [recommendation_to_summary(rec) for rec in recommendations]


# ============================================
# VALIDATION UTILITIES
# ============================================

def validate_rgb(rgb: List[int]) -> bool:
    """Validate RGB values are in correct range"""
    if len(rgb) != 3:
        return False
    return all(0 <= v <= 255 for v in rgb)


def validate_lab(lab_l: float, lab_a: float, lab_b: float) -> bool:
    """Validate LAB values are in correct range"""
    return (0 <= lab_l <= 100 and 
            -128 <= lab_a <= 127 and 
            -128 <= lab_b <= 127)


def validate_skin_features(skin: SkinFeatures) -> Tuple[bool, Optional[str]]:
    """Validate SkinFeatures object"""
    if not validate_rgb(skin.skin_rgb):
        return False, "Invalid RGB values"
    
    if not validate_lab(skin.lab_l, skin.lab_a, skin.lab_b):
        return False, "Invalid LAB values"
    
    if not 0 <= skin.confidence <= 1:
        return False, "Confidence must be between 0 and 1"
    
    return True, None


def validate_cloth_features(cloth: ClothFeatures) -> Tuple[bool, Optional[str]]:
    """Validate ClothFeatures object"""
    if not validate_rgb(cloth.dominant_color_rgb):
        return False, "Invalid RGB values"
    
    if not 1 <= cloth.formality_level <= 10:
        return False, "Formality must be between 1 and 10"
    
    if not 0 <= cloth.confidence <= 1:
        return False, "Confidence must be between 0 and 1"
    
    return True, None

# Color Matching Algorithm
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# Implements color matching between skin tone and clothing colors
# Uses undertone rules, seasonal color analysis, and color harmony principles

from typing import List, Tuple, Dict, Optional
import math

from ..schemas import (
    SkinFeatures, ClothFeatures, Undertone, SkinDepth, Season
)
from ..rules.color_rules import (
    UndertoneColorRules,
    get_color_compatibility_score,
    find_closest_color_name,
    calculate_color_warmth,
    COLOR_DATABASE,
)
from ..rules.seasonal_rules import (
    SeasonType, SeasonSubtype,
    determine_season,
    calculate_seasonal_score,
    get_seasonal_recommendations,
)


class ColorMatcher:
    """
    Main color matching engine
    Calculates compatibility between skin features and clothing colors
    """
    
    def __init__(self):
        self.undertone_rules = UndertoneColorRules()
    
    def calculate_color_score(
        self,
        skin_features: SkinFeatures,
        cloth_features: ClothFeatures
    ) -> Tuple[float, str]:
        """
        Calculate overall color compatibility score
        
        Args:
            skin_features: User's skin analysis results
            cloth_features: Clothing color features
        
        Returns:
            Tuple of (score 0-1, detailed reasoning)
        """
        scores = []
        reasons = []
        
        # 1. Undertone-based color matching (40% weight)
        undertone_score, undertone_reason = self._match_undertone(
            cloth_features.dominant_color_name,
            cloth_features.dominant_color_rgb,
            skin_features.undertone.value
        )
        scores.append(undertone_score * 0.4)
        reasons.append(f"Undertone: {undertone_reason}")
        
        # 2. Seasonal color matching (35% weight)
        season = self._get_user_season(skin_features)
        season_score, season_reason = calculate_seasonal_score(
            cloth_features.dominant_color_name,
            cloth_features.dominant_color_rgb,
            season,
            skin_features.undertone.value
        )
        scores.append(season_score * 0.35)
        reasons.append(f"Season: {season_reason}")
        
        # 3. Contrast/complement matching (25% weight)
        contrast_score, contrast_reason = self._calculate_contrast_score(
            skin_features.skin_rgb,
            cloth_features.dominant_color_rgb,
            skin_features.skin_depth.value
        )
        scores.append(contrast_score * 0.25)
        reasons.append(f"Contrast: {contrast_reason}")
        
        # Calculate final score
        final_score = sum(scores)
        final_reason = " | ".join(reasons)
        
        return final_score, final_reason
    
    def _match_undertone(
        self,
        color_name: str,
        color_rgb: List[int],
        undertone: str
    ) -> Tuple[float, str]:
        """Match clothing color to skin undertone"""
        
        # First check by color name
        is_recommended, name_score, name_reason = UndertoneColorRules.is_color_recommended(
            color_name, undertone
        )
        
        # Also check by RGB values
        rgb_score, rgb_reason = get_color_compatibility_score(
            color_rgb, undertone
        )
        
        # Combine scores (favor name match if confident)
        if name_score >= 0.8 or name_score <= 0.3:
            # Name gives strong signal
            final_score = name_score * 0.7 + rgb_score * 0.3
            reason = name_reason
        else:
            # Name is ambiguous, rely more on RGB
            final_score = name_score * 0.3 + rgb_score * 0.7
            reason = rgb_reason
        
        return final_score, reason
    
    def _get_user_season(self, skin_features: SkinFeatures) -> SeasonType:
        """Determine user's seasonal color type"""
        
        # If season is already provided
        if skin_features.season:
            return SeasonType(skin_features.season.value)
        
        # Calculate from features
        season, subtype, reason = determine_season(
            undertone=skin_features.undertone.value,
            skin_depth=skin_features.skin_depth.value,
            lab_l=skin_features.lab_l,
            lab_a=skin_features.lab_a,
            lab_b=skin_features.lab_b
        )
        
        return season
    
    def _calculate_contrast_score(
        self,
        skin_rgb: List[int],
        cloth_rgb: List[int],
        skin_depth: str
    ) -> Tuple[float, str]:
        """
        Calculate contrast/complement score
        Good contrast creates visual interest without overwhelming
        """
        # Calculate luminance values
        skin_luminance = self._calculate_luminance(skin_rgb)
        cloth_luminance = self._calculate_luminance(cloth_rgb)
        
        # Calculate contrast ratio
        contrast_ratio = self._contrast_ratio(skin_luminance, cloth_luminance)
        
        # Ideal contrast depends on skin depth
        if skin_depth in ["fair", "light"]:
            # Light skin: medium contrast is best (ratio 3-7)
            if 3 <= contrast_ratio <= 7:
                score = 1.0
                reason = f"Excellent contrast ({contrast_ratio:.1f}:1) for light skin"
            elif contrast_ratio < 3:
                score = 0.6
                reason = f"Low contrast ({contrast_ratio:.1f}:1), may wash out light skin"
            else:
                score = 0.7
                reason = f"High contrast ({contrast_ratio:.1f}:1), dramatic look"
                
        elif skin_depth in ["tan", "deep"]:
            # Deep skin: can handle higher contrast (ratio 4-10)
            if 4 <= contrast_ratio <= 10:
                score = 1.0
                reason = f"Great contrast ({contrast_ratio:.1f}:1) for deeper skin"
            elif contrast_ratio < 4:
                score = 0.7
                reason = f"Moderate contrast ({contrast_ratio:.1f}:1), subtle look"
            else:
                score = 0.8
                reason = f"High contrast ({contrast_ratio:.1f}:1), bold look"
                
        else:  # medium
            # Medium skin: versatile (ratio 3-8)
            if 3 <= contrast_ratio <= 8:
                score = 1.0
                reason = f"Good contrast ({contrast_ratio:.1f}:1) for medium skin"
            else:
                score = 0.7
                reason = f"Acceptable contrast ({contrast_ratio:.1f}:1)"
        
        return score, reason
    
    def _calculate_luminance(self, rgb: List[int]) -> float:
        """Calculate relative luminance of a color"""
        def adjust(channel):
            c = channel / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        
        r, g, b = rgb
        return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)
    
    def _contrast_ratio(self, lum1: float, lum2: float) -> float:
        """Calculate WCAG contrast ratio"""
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        return (lighter + 0.05) / (darker + 0.05)
    
    def get_best_colors_for_user(
        self,
        skin_features: SkinFeatures,
        include_hex: bool = False
    ) -> Dict[str, List]:
        """
        Get personalized color recommendations for a user
        
        Returns:
            Dictionary with 'best_colors', 'neutral_colors', 'accent_colors', 'colors_to_avoid'
        """
        undertone = skin_features.undertone.value
        season = self._get_user_season(skin_features)
        
        # Get undertone-based recommendations
        undertone_best = UndertoneColorRules.get_best_colors(undertone)
        undertone_avoid = UndertoneColorRules.get_avoid_colors(undertone)
        
        # Get seasonal recommendations
        seasonal_recs = get_seasonal_recommendations(season)
        
        # Combine recommendations (intersection of undertone + seasonal)
        best_colors = list(set(undertone_best) & set(seasonal_recs.get("best_colors", [])))
        
        # If intersection is too small, use union with priority
        if len(best_colors) < 10:
            best_colors = list(set(undertone_best[:15]) | set(seasonal_recs.get("best_colors", [])[:15]))
        
        # Get colors to avoid (union)
        avoid_colors = list(set(undertone_avoid) | set(seasonal_recs.get("colors_to_avoid", [])))
        
        result = {
            "best_colors": best_colors[:20],
            "neutral_colors": seasonal_recs.get("neutral_colors", []),
            "accent_colors": seasonal_recs.get("accent_colors", []),
            "colors_to_avoid": avoid_colors[:15],
            "recommended_metals": seasonal_recs.get("recommended_metals", []),
            "season": season.value,
            "undertone": undertone,
        }
        
        # Add hex codes if requested
        if include_hex:
            result["best_colors_hex"] = [
                COLOR_DATABASE.get(c, {}).get("rgb", [128, 128, 128])
                for c in result["best_colors"]
            ]
        
        return result
    
    def batch_score_colors(
        self,
        skin_features: SkinFeatures,
        clothes: List[ClothFeatures]
    ) -> List[Tuple[str, float, str]]:
        """
        Score multiple clothing items at once
        
        Returns:
            List of (cloth_id, score, reason) tuples sorted by score descending
        """
        results = []
        
        for cloth in clothes:
            score, reason = self.calculate_color_score(skin_features, cloth)
            results.append((cloth.cloth_id, score, reason))
        
        # Sort by score descending
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results


# ============================================
# COLOR HARMONY UTILITIES
# ============================================

def rgb_to_hsl(rgb: List[int]) -> Tuple[float, float, float]:
    """Convert RGB to HSL color space"""
    r, g, b = [x / 255.0 for x in rgb]
    
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0
    
    if max_c == min_c:
        h = s = 0.0
    else:
        d = max_c - min_c
        s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
        
        if max_c == r:
            h = (g - b) / d + (6.0 if g < b else 0.0)
        elif max_c == g:
            h = (b - r) / d + 2.0
        else:
            h = (r - g) / d + 4.0
        
        h /= 6.0
    
    return h * 360, s, l


def get_complementary_color(rgb: List[int]) -> List[int]:
    """Get complementary color (opposite on color wheel)"""
    h, s, l = rgb_to_hsl(rgb)
    new_h = (h + 180) % 360
    return hsl_to_rgb(new_h, s, l)


def hsl_to_rgb(h: float, s: float, l: float) -> List[int]:
    """Convert HSL to RGB"""
    h = h / 360.0
    
    if s == 0:
        r = g = b = l
    else:
        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p
        
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
    
    return [int(x * 255) for x in [r, g, b]]


def calculate_color_distance(rgb1: List[int], rgb2: List[int]) -> float:
    """Calculate perceptual color distance (CIE76 approximation)"""
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))

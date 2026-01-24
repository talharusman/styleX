# Style Matching Algorithm
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# Implements style-based recommendations based on user preferences,
# occasion filtering, and outfit coordination

from typing import List, Tuple, Dict, Optional, Set
from ..schemas import (
    ClothFeatures, UserPreferences, 
    StyleType, WeatherType, ClothingCategory, Gender
)


# ============================================
# STYLE COMPATIBILITY RULES
# ============================================

# Style combinations that work well together
COMPATIBLE_STYLES: Dict[StyleType, Set[StyleType]] = {
    StyleType.CASUAL: {
        StyleType.CASUAL, StyleType.SPORTY, StyleType.STREETWEAR, 
        StyleType.BOHEMIAN, StyleType.MINIMALIST
    },
    StyleType.FORMAL: {
        StyleType.FORMAL, StyleType.BUSINESS, StyleType.MINIMALIST
    },
    StyleType.BUSINESS: {
        StyleType.BUSINESS, StyleType.FORMAL, StyleType.MINIMALIST
    },
    StyleType.SPORTY: {
        StyleType.SPORTY, StyleType.CASUAL, StyleType.STREETWEAR
    },
    StyleType.BOHEMIAN: {
        StyleType.BOHEMIAN, StyleType.CASUAL, StyleType.VINTAGE
    },
    StyleType.VINTAGE: {
        StyleType.VINTAGE, StyleType.BOHEMIAN, StyleType.CASUAL
    },
    StyleType.STREETWEAR: {
        StyleType.STREETWEAR, StyleType.CASUAL, StyleType.SPORTY
    },
    StyleType.MINIMALIST: {
        StyleType.MINIMALIST, StyleType.CASUAL, StyleType.FORMAL, 
        StyleType.BUSINESS
    },
}

# Occasion to style mapping
OCCASION_STYLES: Dict[str, List[StyleType]] = {
    "work": [StyleType.BUSINESS, StyleType.FORMAL, StyleType.MINIMALIST],
    "office": [StyleType.BUSINESS, StyleType.FORMAL, StyleType.MINIMALIST],
    "meeting": [StyleType.BUSINESS, StyleType.FORMAL],
    "interview": [StyleType.FORMAL, StyleType.BUSINESS],
    "casual": [StyleType.CASUAL, StyleType.STREETWEAR, StyleType.MINIMALIST],
    "weekend": [StyleType.CASUAL, StyleType.SPORTY, StyleType.BOHEMIAN],
    "date": [StyleType.CASUAL, StyleType.MINIMALIST, StyleType.BOHEMIAN],
    "party": [StyleType.STREETWEAR, StyleType.BOHEMIAN, StyleType.CASUAL],
    "wedding": [StyleType.FORMAL],
    "workout": [StyleType.SPORTY],
    "gym": [StyleType.SPORTY],
    "travel": [StyleType.CASUAL, StyleType.SPORTY, StyleType.MINIMALIST],
    "vacation": [StyleType.CASUAL, StyleType.BOHEMIAN],
    "brunch": [StyleType.CASUAL, StyleType.BOHEMIAN, StyleType.MINIMALIST],
    "dinner": [StyleType.FORMAL, StyleType.BUSINESS, StyleType.MINIMALIST],
}

# Formality levels for occasions
OCCASION_FORMALITY: Dict[str, Tuple[int, int]] = {
    "work": (4, 7),
    "office": (4, 7),
    "meeting": (5, 8),
    "interview": (6, 9),
    "casual": (1, 4),
    "weekend": (1, 3),
    "date": (3, 6),
    "party": (2, 5),
    "wedding": (7, 10),
    "workout": (1, 2),
    "gym": (1, 2),
    "travel": (1, 4),
    "vacation": (1, 3),
    "brunch": (2, 5),
    "dinner": (5, 8),
}


class StyleMatcher:
    """
    Style matching engine
    Matches clothing items based on user preferences and occasion
    """
    
    def calculate_style_score(
        self,
        cloth: ClothFeatures,
        preferences: Optional[UserPreferences] = None
    ) -> Tuple[float, str]:
        """
        Calculate style compatibility score
        
        Args:
            cloth: Clothing features
            preferences: Optional user preferences
        
        Returns:
            Tuple of (score 0-1, reasoning)
        """
        if preferences is None:
            return 0.7, "No preferences specified, moderate match assumed"
        
        scores = []
        reasons = []
        
        # 1. Style preference matching (40%)
        style_score, style_reason = self._match_style_preference(
            cloth.style, preferences.preferred_styles
        )
        scores.append(style_score * 0.4)
        reasons.append(style_reason)
        
        # 2. Occasion matching (30%)
        occasion_score, occasion_reason = self._match_occasion(
            cloth, preferences.target_occasion
        )
        scores.append(occasion_score * 0.3)
        reasons.append(occasion_reason)
        
        # 3. Formality matching (20%)
        formality_score, formality_reason = self._match_formality(
            cloth.formality_level,
            preferences.min_formality,
            preferences.max_formality,
            preferences.target_occasion
        )
        scores.append(formality_score * 0.2)
        reasons.append(formality_reason)
        
        # 4. Weather/season matching (10%)
        weather_score, weather_reason = self._match_weather(
            cloth.weather, preferences.target_weather
        )
        scores.append(weather_score * 0.1)
        reasons.append(weather_reason)
        
        final_score = sum(scores)
        final_reason = " | ".join(reasons)
        
        return final_score, final_reason
    
    def _match_style_preference(
        self,
        cloth_style: StyleType,
        preferred_styles: List[StyleType]
    ) -> Tuple[float, str]:
        """Match clothing style against user preferences"""
        
        if not preferred_styles:
            return 0.7, "No style preference, neutral match"
        
        # Direct match
        if cloth_style in preferred_styles:
            return 1.0, f"Perfect match: {cloth_style.value} is preferred"
        
        # Check for compatible styles
        compatible = COMPATIBLE_STYLES.get(cloth_style, set())
        matching_compatible = [s for s in preferred_styles if s in compatible]
        
        if matching_compatible:
            return 0.75, f"{cloth_style.value} pairs well with preferred styles"
        
        return 0.4, f"{cloth_style.value} differs from preferred styles"
    
    def _match_occasion(
        self,
        cloth: ClothFeatures,
        occasion: Optional[str]
    ) -> Tuple[float, str]:
        """Match clothing to target occasion"""
        
        if not occasion:
            return 0.7, "No occasion specified"
        
        occasion = occasion.lower()
        appropriate_styles = OCCASION_STYLES.get(occasion, [])
        
        if not appropriate_styles:
            return 0.6, f"Unknown occasion '{occasion}', moderate match"
        
        if cloth.style in appropriate_styles:
            return 1.0, f"Perfect for {occasion}"
        
        # Check if style is at least compatible
        for app_style in appropriate_styles:
            if cloth.style in COMPATIBLE_STYLES.get(app_style, set()):
                return 0.7, f"Acceptable for {occasion}"
        
        return 0.3, f"May not be ideal for {occasion}"
    
    def _match_formality(
        self,
        cloth_formality: int,
        min_formality: int,
        max_formality: int,
        occasion: Optional[str] = None
    ) -> Tuple[float, str]:
        """Match formality level"""
        
        # If occasion is specified, use its formality range
        if occasion and occasion.lower() in OCCASION_FORMALITY:
            min_f, max_f = OCCASION_FORMALITY[occasion.lower()]
            min_formality = max(min_formality, min_f)
            max_formality = min(max_formality, max_f)
        
        # Check if within range
        if min_formality <= cloth_formality <= max_formality:
            return 1.0, f"Formality level {cloth_formality} is perfect"
        
        # Calculate distance from range
        if cloth_formality < min_formality:
            distance = min_formality - cloth_formality
            reason = f"Too casual (level {cloth_formality}, need {min_formality}+)"
        else:
            distance = cloth_formality - max_formality
            reason = f"Too formal (level {cloth_formality}, max {max_formality})"
        
        # Score decreases with distance
        score = max(0.2, 1.0 - (distance * 0.15))
        return score, reason
    
    def _match_weather(
        self,
        cloth_weather: WeatherType,
        target_weather: Optional[WeatherType]
    ) -> Tuple[float, str]:
        """Match weather suitability"""
        
        if not target_weather:
            return 0.8, "No weather filter"
        
        # All-season works for everything
        if cloth_weather == WeatherType.ALL_SEASON:
            return 0.9, "All-season item, versatile"
        
        # Perfect match
        if cloth_weather == target_weather:
            return 1.0, f"Perfect for {target_weather.value} weather"
        
        # Adjacent seasons
        season_order = [WeatherType.WINTER, WeatherType.SPRING, 
                       WeatherType.SUMMER, WeatherType.FALL]
        
        if cloth_weather in season_order and target_weather in season_order:
            idx1 = season_order.index(cloth_weather)
            idx2 = season_order.index(target_weather)
            distance = min(abs(idx1 - idx2), 4 - abs(idx1 - idx2))  # Circular
            
            if distance == 1:
                return 0.7, f"Suitable for transitional weather"
            elif distance == 2:
                return 0.4, f"May not be ideal for {target_weather.value}"
        
        return 0.3, f"Not recommended for {target_weather.value}"
    
    def filter_by_preferences(
        self,
        clothes: List[ClothFeatures],
        preferences: UserPreferences
    ) -> List[ClothFeatures]:
        """
        Filter clothing items based on user preferences
        
        Returns:
            Filtered list of clothing items
        """
        filtered = clothes.copy()
        
        # Filter by gender
        if preferences.gender_filter:
            filtered = [
                c for c in filtered 
                if c.gender == preferences.gender_filter or c.gender == Gender.UNISEX
            ]
        
        # Filter by category
        if preferences.category_filter:
            filtered = [
                c for c in filtered 
                if c.category in preferences.category_filter
            ]
        
        # Filter by weather
        if preferences.target_weather:
            filtered = [
                c for c in filtered
                if c.weather == preferences.target_weather or 
                   c.weather == WeatherType.ALL_SEASON
            ]
        
        # Filter by formality range
        filtered = [
            c for c in filtered
            if preferences.min_formality <= c.formality_level <= preferences.max_formality
        ]
        
        # Filter out avoided colors
        if preferences.avoided_colors:
            avoided_lower = [c.lower() for c in preferences.avoided_colors]
            filtered = [
                c for c in filtered
                if c.dominant_color_name.lower() not in avoided_lower
            ]
        
        return filtered
    
    def find_outfit_combinations(
        self,
        clothes: List[ClothFeatures],
        required_categories: List[ClothingCategory],
        max_combinations: int = 10
    ) -> List[List[ClothFeatures]]:
        """
        Find outfit combinations from available clothes
        
        Args:
            clothes: Available clothing items
            required_categories: Categories needed for complete outfit
            max_combinations: Maximum number of outfits to return
        
        Returns:
            List of outfit combinations (each outfit is a list of ClothFeatures)
        """
        # Group clothes by category
        by_category: Dict[ClothingCategory, List[ClothFeatures]] = {}
        for cloth in clothes:
            if cloth.category not in by_category:
                by_category[cloth.category] = []
            by_category[cloth.category].append(cloth)
        
        # Check if we have items in all required categories
        for cat in required_categories:
            if cat not in by_category or not by_category[cat]:
                return []  # Missing required category
        
        # Generate combinations
        outfits = []
        
        # Simple approach: pick top items from each category
        from itertools import product
        
        category_items = [
            by_category[cat][:5]  # Limit to top 5 per category
            for cat in required_categories
        ]
        
        for combination in product(*category_items):
            if len(outfits) >= max_combinations:
                break
            
            # Check style compatibility
            if self._is_outfit_compatible(list(combination)):
                outfits.append(list(combination))
        
        return outfits
    
    def _is_outfit_compatible(self, items: List[ClothFeatures]) -> bool:
        """Check if outfit items are style-compatible"""
        
        if len(items) < 2:
            return True
        
        styles = [item.style for item in items]
        base_style = styles[0]
        compatible_set = COMPATIBLE_STYLES.get(base_style, {base_style})
        
        return all(s in compatible_set or base_style in COMPATIBLE_STYLES.get(s, set()) 
                   for s in styles[1:])
    
    def score_outfit(
        self,
        outfit: List[ClothFeatures],
        preferences: Optional[UserPreferences] = None
    ) -> Tuple[float, str]:
        """
        Score an entire outfit combination
        
        Returns:
            Tuple of (score 0-1, reasoning)
        """
        if not outfit:
            return 0.0, "Empty outfit"
        
        # Score individual items
        item_scores = []
        for item in outfit:
            score, _ = self.calculate_style_score(item, preferences)
            item_scores.append(score)
        
        avg_score = sum(item_scores) / len(item_scores)
        
        # Bonus for style coherence
        if self._is_outfit_compatible(outfit):
            coherence_bonus = 0.1
            reason = "Cohesive outfit with matching styles"
        else:
            coherence_bonus = -0.1
            reason = "Mixed styles may not coordinate well"
        
        final_score = min(1.0, avg_score + coherence_bonus)
        
        return final_score, reason

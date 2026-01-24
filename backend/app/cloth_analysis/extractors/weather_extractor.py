"""
Weather Suitability Classification.
Derives weather appropriateness from clothing category and fabric.
No GPU required - rule-based inference.
"""

from typing import Tuple, Dict, Set
import logging

from ..schemas import ClothingCategory, WeatherType, FabricType

logger = logging.getLogger(__name__)


# Category to weather mapping
CATEGORY_WEATHER_MAP: Dict[ClothingCategory, WeatherType] = {
    # Summer items
    ClothingCategory.TSHIRT: WeatherType.SUMMER,
    ClothingCategory.TANK_TOP: WeatherType.SUMMER,
    ClothingCategory.SHORTS: WeatherType.SUMMER,
    ClothingCategory.SWIMWEAR: WeatherType.SUMMER,
    ClothingCategory.ROMPER: WeatherType.SUMMER,
    
    # Winter items
    ClothingCategory.COAT: WeatherType.WINTER,
    ClothingCategory.SWEATER: WeatherType.WINTER,
    ClothingCategory.HOODIE: WeatherType.FALL,  # Fall/transition
    ClothingCategory.CARDIGAN: WeatherType.FALL,
    
    # All-season items
    ClothingCategory.SHIRT: WeatherType.ALL_SEASON,
    ClothingCategory.BLOUSE: WeatherType.ALL_SEASON,
    ClothingCategory.POLO: WeatherType.ALL_SEASON,
    ClothingCategory.PANTS: WeatherType.ALL_SEASON,
    ClothingCategory.JEANS: WeatherType.ALL_SEASON,
    ClothingCategory.DRESS: WeatherType.ALL_SEASON,
    ClothingCategory.SKIRT: WeatherType.ALL_SEASON,
    ClothingCategory.LEGGINGS: WeatherType.ALL_SEASON,
    ClothingCategory.JUMPSUIT: WeatherType.ALL_SEASON,
    ClothingCategory.ACTIVEWEAR: WeatherType.ALL_SEASON,
    ClothingCategory.VEST: WeatherType.ALL_SEASON,
    
    # Outerwear - typically fall/spring
    ClothingCategory.JACKET: WeatherType.FALL,
    ClothingCategory.BLAZER: WeatherType.ALL_SEASON,
    
    # Unknown
    ClothingCategory.UNKNOWN: WeatherType.ALL_SEASON,
}

# Fabric modifiers for weather
WINTER_FABRICS: Set[FabricType] = {
    FabricType.WOOL,
    FabricType.VELVET,
    FabricType.LEATHER,
}

SUMMER_FABRICS: Set[FabricType] = {
    FabricType.LINEN,
    FabricType.COTTON,
    FabricType.SILK,
}

# Confidence values for different derivation methods
BASE_CONFIDENCE = 0.75  # When derived from category alone
FABRIC_BOOST = 0.15     # Additional confidence when fabric matches
HIGH_CONFIDENCE = 0.90  # For very clear cases


class WeatherExtractor:
    """
    Extracts weather suitability from clothing attributes.
    Uses rule-based inference - no GPU required.
    """
    
    def __init__(self):
        """Initialize the weather extractor."""
        logger.info("WeatherExtractor initialized (rule-based)")
    
    def extract(
        self,
        category: ClothingCategory,
        fabric: FabricType = FabricType.UNKNOWN
    ) -> Tuple[WeatherType, float]:
        """
        Extract weather suitability based on category and fabric.
        
        Args:
            category: Clothing category
            fabric: Fabric type (optional, for refinement)
            
        Returns:
            Tuple of (WeatherType, confidence_score)
        """
        try:
            # Get base weather from category
            base_weather = CATEGORY_WEATHER_MAP.get(category, WeatherType.ALL_SEASON)
            confidence = BASE_CONFIDENCE
            
            # Refine based on fabric if known
            if fabric != FabricType.UNKNOWN:
                weather, confidence = self._apply_fabric_modifier(
                    base_weather, fabric, confidence
                )
            else:
                weather = base_weather
            
            # Apply high confidence for very clear cases
            clear_winter = {ClothingCategory.COAT, ClothingCategory.SWEATER}
            clear_summer = {ClothingCategory.TANK_TOP, ClothingCategory.SHORTS, 
                          ClothingCategory.SWIMWEAR}
            
            if category in clear_winter and weather == WeatherType.WINTER:
                confidence = HIGH_CONFIDENCE
            elif category in clear_summer and weather == WeatherType.SUMMER:
                confidence = HIGH_CONFIDENCE
            
            logger.debug(f"Weather for {category.value}: {weather.value} ({confidence:.2%})")
            return weather, confidence
            
        except Exception as e:
            logger.error(f"Error extracting weather: {e}")
            return WeatherType.ALL_SEASON, 0.5
    
    def _apply_fabric_modifier(
        self,
        base_weather: WeatherType,
        fabric: FabricType,
        base_confidence: float
    ) -> Tuple[WeatherType, float]:
        """
        Apply fabric-based modifications to weather prediction.
        
        Args:
            base_weather: Initial weather prediction
            fabric: Detected fabric type
            base_confidence: Initial confidence score
            
        Returns:
            Tuple of (refined_weather, adjusted_confidence)
        """
        # Check if fabric reinforces or contradicts base weather
        if fabric in WINTER_FABRICS:
            if base_weather == WeatherType.WINTER:
                # Fabric confirms winter
                return base_weather, min(1.0, base_confidence + FABRIC_BOOST)
            elif base_weather == WeatherType.ALL_SEASON:
                # Shift towards winter
                return WeatherType.FALL, base_confidence
            elif base_weather == WeatherType.SUMMER:
                # Contradiction - fabric suggests cooler, reduce confidence
                return WeatherType.ALL_SEASON, base_confidence * 0.8
        
        elif fabric in SUMMER_FABRICS:
            if base_weather == WeatherType.SUMMER:
                # Fabric confirms summer
                return base_weather, min(1.0, base_confidence + FABRIC_BOOST)
            elif base_weather == WeatherType.ALL_SEASON:
                # Shift towards summer
                return WeatherType.SUMMER, base_confidence
            elif base_weather == WeatherType.WINTER:
                # Contradiction - reduce confidence
                return WeatherType.ALL_SEASON, base_confidence * 0.8
        
        return base_weather, base_confidence
    
    def get_temperature_range(self, weather: WeatherType) -> Tuple[int, int]:
        """
        Get approximate temperature range for a weather type.
        
        Args:
            weather: Weather type
            
        Returns:
            Tuple of (min_temp_celsius, max_temp_celsius)
        """
        ranges = {
            WeatherType.SUMMER: (25, 40),
            WeatherType.WINTER: (-10, 10),
            WeatherType.SPRING: (10, 22),
            WeatherType.FALL: (10, 22),
            WeatherType.ALL_SEASON: (10, 30),
        }
        return ranges.get(weather, (10, 30))


# Singleton instance
_weather_extractor: WeatherExtractor = None


def get_weather_extractor() -> WeatherExtractor:
    """Get or create the weather extractor singleton."""
    global _weather_extractor
    if _weather_extractor is None:
        _weather_extractor = WeatherExtractor()
    return _weather_extractor


def extract_weather(
    category: ClothingCategory,
    fabric: FabricType = FabricType.UNKNOWN
) -> Tuple[WeatherType, float]:
    """
    Convenience function to extract weather from category and fabric.
    
    Args:
        category: Clothing category
        fabric: Fabric type (optional)
        
    Returns:
        Tuple of (WeatherType, confidence_score)
    """
    extractor = get_weather_extractor()
    return extractor.extract(category, fabric)

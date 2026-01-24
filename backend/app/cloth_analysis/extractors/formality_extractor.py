"""
Formality Level Classification.
Derives formality from style and category.
No GPU required - rule-based inference.
"""

from typing import Tuple, Dict
import logging

from ..schemas import StyleType, ClothingCategory

logger = logging.getLogger(__name__)


# Style to formality level mapping (1-5 scale)
# 1 = very casual, 5 = very formal
STYLE_FORMALITY_MAP: Dict[StyleType, int] = {
    StyleType.CASUAL: 1,
    StyleType.SPORTY: 1,
    StyleType.STREETWEAR: 2,
    StyleType.BOHEMIAN: 2,
    StyleType.VINTAGE: 3,
    StyleType.MINIMALIST: 3,
    StyleType.BUSINESS: 4,
    StyleType.PARTY: 4,
    StyleType.FORMAL: 5,
}

# Category modifiers (adds/subtracts from base formality)
CATEGORY_FORMALITY_MODIFIER: Dict[ClothingCategory, int] = {
    # Very casual items
    ClothingCategory.TSHIRT: -1,
    ClothingCategory.TANK_TOP: -1,
    ClothingCategory.SHORTS: -1,
    ClothingCategory.HOODIE: -1,
    ClothingCategory.SWIMWEAR: -2,
    ClothingCategory.ACTIVEWEAR: -1,
    
    # Moderately casual
    ClothingCategory.JEANS: 0,
    ClothingCategory.POLO: 0,
    ClothingCategory.SWEATER: 0,
    ClothingCategory.CARDIGAN: 0,
    
    # Neutral to formal
    ClothingCategory.SHIRT: 1,
    ClothingCategory.PANTS: 0,
    ClothingCategory.SKIRT: 0,
    ClothingCategory.LEGGINGS: -1,
    
    # Formal items
    ClothingCategory.BLOUSE: 1,
    ClothingCategory.DRESS: 1,
    ClothingCategory.BLAZER: 2,
    ClothingCategory.COAT: 0,
    ClothingCategory.JACKET: 0,
    ClothingCategory.VEST: 1,
    ClothingCategory.JUMPSUIT: 0,
    ClothingCategory.ROMPER: -1,
}

# Confidence levels based on how clear the formality is
BASE_CONFIDENCE = 0.75
HIGH_CONFIDENCE = 0.90
LOW_CONFIDENCE = 0.60


class FormalityExtractor:
    """
    Extracts formality level from style and category.
    Uses rule-based inference - no GPU required.
    
    Formality Scale:
    1 = Very Casual (loungewear, sportswear)
    2 = Casual (everyday wear)
    3 = Smart Casual (business casual, neat)
    4 = Business/Semi-formal (office, events)
    5 = Formal (black tie, formal events)
    """
    
    def __init__(self):
        """Initialize the formality extractor."""
        logger.info("FormalityExtractor initialized (rule-based)")
    
    def extract(
        self,
        style: StyleType,
        category: ClothingCategory
    ) -> Tuple[int, float]:
        """
        Extract formality level based on style and category.
        
        Args:
            style: Detected style of the clothing
            category: Detected category of the clothing
            
        Returns:
            Tuple of (formality_level, confidence_score)
            formality_level is 1-5 (1=very casual, 5=very formal)
        """
        try:
            # Get base formality from style
            base_formality = STYLE_FORMALITY_MAP.get(style, 3)
            
            # Get modifier from category
            modifier = CATEGORY_FORMALITY_MODIFIER.get(category, 0)
            
            # Calculate final formality
            formality = base_formality + modifier
            
            # Clamp to valid range
            formality = max(1, min(5, formality))
            
            # Calculate confidence
            confidence = self._calculate_confidence(style, category, formality)
            
            logger.debug(
                f"Formality for {style.value}/{category.value}: "
                f"{formality} ({confidence:.2%})"
            )
            return formality, confidence
            
        except Exception as e:
            logger.error(f"Error extracting formality: {e}")
            return 3, 0.5  # Default to middle value
    
    def _calculate_confidence(
        self,
        style: StyleType,
        category: ClothingCategory,
        formality: int
    ) -> float:
        """
        Calculate confidence based on how clear the formality signals are.
        
        Args:
            style: Style type
            category: Category type
            formality: Calculated formality level
            
        Returns:
            Confidence score
        """
        # Clear formal signals
        clear_formal = {
            (StyleType.FORMAL, ClothingCategory.BLAZER),
            (StyleType.FORMAL, ClothingCategory.DRESS),
            (StyleType.BUSINESS, ClothingCategory.SHIRT),
            (StyleType.BUSINESS, ClothingCategory.PANTS),
        }
        
        # Clear casual signals
        clear_casual = {
            (StyleType.CASUAL, ClothingCategory.TSHIRT),
            (StyleType.CASUAL, ClothingCategory.SHORTS),
            (StyleType.SPORTY, ClothingCategory.ACTIVEWEAR),
            (StyleType.CASUAL, ClothingCategory.HOODIE),
        }
        
        if (style, category) in clear_formal or (style, category) in clear_casual:
            return HIGH_CONFIDENCE
        
        # Extreme formality values are more certain
        if formality in (1, 5):
            return HIGH_CONFIDENCE
        # Middle values are less certain
        elif formality == 3:
            return LOW_CONFIDENCE
        else:
            return BASE_CONFIDENCE
    
    def get_formality_label(self, formality: int) -> str:
        """
        Convert numeric formality to human-readable label.
        
        Args:
            formality: Formality level (1-5)
            
        Returns:
            Formality label string
        """
        labels = {
            1: "very_casual",
            2: "casual",
            3: "smart_casual",
            4: "business_casual",
            5: "formal",
        }
        return labels.get(formality, "unknown")
    
    def get_occasion_suggestions(self, formality: int) -> list:
        """
        Get suggested occasions for a formality level.
        
        Args:
            formality: Formality level (1-5)
            
        Returns:
            List of suggested occasions
        """
        suggestions = {
            1: ["gym", "home", "beach", "casual outing"],
            2: ["casual dinner", "shopping", "weekend activities", "brunch"],
            3: ["work", "casual meetings", "date night", "gallery visit"],
            4: ["office", "business meetings", "conferences", "dinners"],
            5: ["formal events", "galas", "weddings", "interviews"],
        }
        return suggestions.get(formality, ["general occasions"])


# Singleton instance
_formality_extractor: FormalityExtractor = None


def get_formality_extractor() -> FormalityExtractor:
    """Get or create the formality extractor singleton."""
    global _formality_extractor
    if _formality_extractor is None:
        _formality_extractor = FormalityExtractor()
    return _formality_extractor


def extract_formality(
    style: StyleType,
    category: ClothingCategory
) -> Tuple[int, float]:
    """
    Convenience function to extract formality.
    
    Args:
        style: Style type
        category: Category type
        
    Returns:
        Tuple of (formality_level, confidence_score)
    """
    extractor = get_formality_extractor()
    return extractor.extract(style, category)

"""
Confidence Scoring for Clothing Analysis.
Aggregates and normalizes confidence scores from all extractors.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FeatureConfidence:
    """Confidence score for a single feature."""
    feature_name: str
    confidence: float
    weight: float = 1.0


class ConfidenceScorer:
    """
    Calculates overall confidence score from individual feature confidences.
    Uses weighted averaging with configurable weights.
    """
    
    # Default weights for each feature
    DEFAULT_WEIGHTS = {
        "color": 1.0,      # Color detection is very reliable
        "design": 0.9,     # Design patterns can be ambiguous
        "category": 1.0,   # Category is usually clear
        "weather": 0.7,    # Derived feature, less certain
        "style": 0.85,     # Style is somewhat subjective
        "fabric": 0.6,     # Fabric is optional for MVP
        "formality": 0.75, # Derived from style/category
    }
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize the confidence scorer.
        
        Args:
            weights: Optional custom weights for each feature
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        logger.info("ConfidenceScorer initialized")
    
    def calculate_overall_confidence(
        self,
        feature_confidences: Dict[str, float]
    ) -> float:
        """
        Calculate overall confidence score using weighted average.
        
        Args:
            feature_confidences: Dictionary of feature_name -> confidence_score
            
        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        if not feature_confidences:
            return 0.0
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for feature_name, confidence in feature_confidences.items():
            weight = self.weights.get(feature_name, 1.0)
            
            # Skip features with zero or invalid confidence
            if confidence <= 0 or confidence > 1.0:
                continue
            
            weighted_sum += confidence * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        overall = weighted_sum / total_weight
        
        logger.debug(f"Overall confidence: {overall:.2%}")
        return min(1.0, max(0.0, overall))
    
    def normalize_confidence(self, raw_confidence: float) -> float:
        """
        Normalize a raw confidence score to a reasonable range.
        Handles cases where model outputs unrealistic confidences.
        
        Args:
            raw_confidence: Raw confidence score from model
            
        Returns:
            Normalized confidence (0.0 to 1.0)
        """
        # Clamp to valid range
        confidence = min(1.0, max(0.0, raw_confidence))
        
        # If confidence is suspiciously high for a pretrained model
        # without fine-tuning, apply a penalty
        if confidence > 0.95:
            # Reduce overconfident predictions
            confidence = 0.85 + (confidence - 0.95) * 0.3
        
        return confidence
    
    def apply_uncertainty_penalty(
        self,
        confidence: float,
        num_similar_classes: int,
        similarity_threshold: float = 0.1
    ) -> float:
        """
        Apply penalty when multiple classes have similar probabilities.
        
        Args:
            confidence: Original confidence score
            num_similar_classes: Number of classes within threshold of top class
            similarity_threshold: Threshold for considering classes similar
            
        Returns:
            Adjusted confidence score
        """
        if num_similar_classes <= 1:
            return confidence
        
        # Apply logarithmic penalty for confusion between classes
        penalty = 1.0 / (1.0 + 0.1 * (num_similar_classes - 1))
        adjusted = confidence * penalty
        
        return min(1.0, max(0.0, adjusted))
    
    def get_confidence_level(self, confidence: float) -> str:
        """
        Convert numeric confidence to human-readable level.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
            
        Returns:
            Confidence level string
        """
        if confidence >= 0.9:
            return "very_high"
        elif confidence >= 0.75:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        elif confidence >= 0.25:
            return "low"
        else:
            return "very_low"
    
    def combine_confidences(
        self,
        primary_confidence: float,
        secondary_confidence: float,
        primary_weight: float = 0.7
    ) -> float:
        """
        Combine two confidence scores with weighted average.
        Useful when combining model prediction with heuristics.
        
        Args:
            primary_confidence: Main confidence score
            secondary_confidence: Secondary/supporting confidence
            primary_weight: Weight for primary (0.0 to 1.0)
            
        Returns:
            Combined confidence score
        """
        secondary_weight = 1.0 - primary_weight
        combined = (primary_confidence * primary_weight + 
                   secondary_confidence * secondary_weight)
        return min(1.0, max(0.0, combined))


# Singleton instance
_confidence_scorer: ConfidenceScorer = None


def get_confidence_scorer() -> ConfidenceScorer:
    """Get or create the confidence scorer singleton."""
    global _confidence_scorer
    if _confidence_scorer is None:
        _confidence_scorer = ConfidenceScorer()
    return _confidence_scorer


def calculate_overall_confidence(feature_confidences: Dict[str, float]) -> float:
    """
    Convenience function to calculate overall confidence.
    
    Args:
        feature_confidences: Dictionary of feature_name -> confidence_score
        
    Returns:
        Overall confidence score (0.0 to 1.0)
    """
    scorer = get_confidence_scorer()
    return scorer.calculate_overall_confidence(feature_confidences)

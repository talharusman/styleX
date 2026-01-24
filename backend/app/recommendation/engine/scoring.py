# Recommendation Scoring System
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# Implements the weighted scoring algorithm that combines
# color, style, formality, and confidence scores

from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import time

from ..schemas import (
    SkinFeatures, ClothFeatures, UserPreferences,
    ClothRecommendation, ScoreBreakdown, RecommendationResponse,
    Season, Undertone, SkinDepth
)
from .color_matcher import ColorMatcher
from .style_matcher import StyleMatcher
from ..rules.seasonal_rules import determine_season, SeasonType


@dataclass
class ScoringWeights:
    """Configurable weights for scoring components"""
    color_weight: float = 0.40
    style_weight: float = 0.30
    formality_weight: float = 0.20
    confidence_weight: float = 0.10
    
    def normalize(self):
        """Ensure weights sum to 1.0"""
        total = self.color_weight + self.style_weight + self.formality_weight + self.confidence_weight
        if total != 1.0:
            self.color_weight /= total
            self.style_weight /= total
            self.formality_weight /= total
            self.confidence_weight /= total


class RecommendationScorer:
    """
    Main scoring engine that combines all factors into final recommendations
    """
    
    def __init__(self):
        self.color_matcher = ColorMatcher()
        self.style_matcher = StyleMatcher()
        self.default_weights = ScoringWeights()
    
    def score_single_item(
        self,
        skin_features: SkinFeatures,
        cloth: ClothFeatures,
        preferences: Optional[UserPreferences] = None
    ) -> Tuple[float, ScoreBreakdown]:
        """
        Calculate comprehensive score for a single clothing item
        
        Args:
            skin_features: User's skin analysis results
            cloth: Clothing features
            preferences: Optional user preferences
        
        Returns:
            Tuple of (overall_score, score_breakdown)
        """
        # Get weights from preferences or use defaults
        if preferences:
            weights = ScoringWeights(
                color_weight=preferences.color_weight,
                style_weight=preferences.style_weight,
                formality_weight=preferences.formality_weight,
                confidence_weight=preferences.confidence_weight
            )
        else:
            weights = self.default_weights
        
        weights.normalize()
        
        # 1. Color Score
        color_score, color_reasoning = self.color_matcher.calculate_color_score(
            skin_features, cloth
        )
        
        # 2. Style Score
        style_score, style_reasoning = self.style_matcher.calculate_style_score(
            cloth, preferences
        )
        
        # 3. Formality Score
        formality_score, formality_reasoning = self._calculate_formality_score(
            cloth, preferences
        )
        
        # 4. Confidence Score (from cloth analysis)
        confidence_score = cloth.confidence
        
        # Calculate weighted final score
        overall_score = (
            color_score * weights.color_weight +
            style_score * weights.style_weight +
            formality_score * weights.formality_weight +
            confidence_score * weights.confidence_weight
        )
        
        # Build reasoning
        overall_reasoning = self._build_overall_reasoning(
            overall_score, color_score, style_score, formality_score
        )
        
        breakdown = ScoreBreakdown(
            color_score=color_score,
            style_score=style_score,
            formality_score=formality_score,
            confidence_score=confidence_score,
            color_reasoning=color_reasoning,
            overall_reasoning=overall_reasoning
        )
        
        return overall_score, breakdown
    
    def _calculate_formality_score(
        self,
        cloth: ClothFeatures,
        preferences: Optional[UserPreferences]
    ) -> Tuple[float, str]:
        """Calculate formality match score"""
        
        if not preferences:
            return 0.7, "No formality preference, moderate match"
        
        cloth_formality = cloth.formality_level
        min_f = preferences.min_formality
        max_f = preferences.max_formality
        
        if min_f <= cloth_formality <= max_f:
            return 1.0, f"Perfect formality ({cloth_formality}/10)"
        
        # Calculate distance from acceptable range
        if cloth_formality < min_f:
            distance = min_f - cloth_formality
            reason = f"Too casual ({cloth_formality}/10, min: {min_f})"
        else:
            distance = cloth_formality - max_f
            reason = f"Too formal ({cloth_formality}/10, max: {max_f})"
        
        score = max(0.2, 1.0 - (distance * 0.15))
        return score, reason
    
    def _build_overall_reasoning(
        self,
        overall: float,
        color: float,
        style: float,
        formality: float
    ) -> str:
        """Build human-readable reasoning"""
        
        reasons = []
        
        # Highlight strengths
        if color >= 0.8:
            reasons.append("excellent color match")
        elif color >= 0.6:
            reasons.append("good color compatibility")
        elif color < 0.4:
            reasons.append("color may not be ideal")
        
        if style >= 0.8:
            reasons.append("matches your style")
        elif style < 0.4:
            reasons.append("different from preferred style")
        
        if formality >= 0.8:
            reasons.append("appropriate formality")
        elif formality < 0.4:
            reasons.append("formality mismatch")
        
        # Overall summary
        if overall >= 0.8:
            prefix = "Highly recommended"
        elif overall >= 0.6:
            prefix = "Good choice"
        elif overall >= 0.4:
            prefix = "Acceptable option"
        else:
            prefix = "May not be the best fit"
        
        if reasons:
            return f"{prefix}: {', '.join(reasons)}"
        return prefix
    
    def get_recommendation_level(self, score: float) -> str:
        """Convert score to recommendation level"""
        if score >= 0.8:
            return "Highly Recommended"
        elif score >= 0.6:
            return "Recommended"
        elif score >= 0.4:
            return "Consider"
        else:
            return "Not Recommended"
    
    def rank_clothes(
        self,
        skin_features: SkinFeatures,
        clothes: List[ClothFeatures],
        preferences: Optional[UserPreferences] = None,
        top_k: int = 10
    ) -> List[ClothRecommendation]:
        """
        Rank all clothing items and return top recommendations
        
        Args:
            skin_features: User's skin features
            clothes: List of available clothing items
            preferences: Optional user preferences
            top_k: Number of recommendations to return
        
        Returns:
            List of ClothRecommendation objects, sorted by score
        """
        # Filter clothes first if preferences provided
        if preferences:
            clothes = self.style_matcher.filter_by_preferences(clothes, preferences)
        
        # Score each item
        scored_items = []
        for cloth in clothes:
            score, breakdown = self.score_single_item(
                skin_features, cloth, preferences
            )
            scored_items.append((cloth, score, breakdown))
        
        # Sort by score descending
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # Build recommendations
        recommendations = []
        for rank, (cloth, score, breakdown) in enumerate(scored_items[:top_k], 1):
            rec = ClothRecommendation(
                cloth_id=cloth.cloth_id,
                image_url=cloth.image_url,
                overall_score=round(score, 3),
                score_breakdown=breakdown,
                rank=rank,
                cloth_features=cloth,
                recommendation_level=self.get_recommendation_level(score)
            )
            recommendations.append(rec)
        
        return recommendations
    
    def generate_full_response(
        self,
        skin_features: SkinFeatures,
        clothes: List[ClothFeatures],
        preferences: Optional[UserPreferences] = None,
        top_k: int = 10
    ) -> RecommendationResponse:
        """
        Generate complete recommendation response
        
        Returns:
            Full RecommendationResponse with all details
        """
        start_time = time.time()
        
        # Determine user's season
        season, subtype, _ = determine_season(
            undertone=skin_features.undertone.value,
            skin_depth=skin_features.skin_depth.value,
            lab_l=skin_features.lab_l,
            lab_a=skin_features.lab_a,
            lab_b=skin_features.lab_b
        )
        
        # Get color recommendations for user
        color_recs = self.color_matcher.get_best_colors_for_user(skin_features)
        
        # Rank clothes
        recommendations = self.rank_clothes(
            skin_features, clothes, preferences, top_k
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        response = RecommendationResponse(
            success=True,
            detected_season=Season(season.value),
            undertone=skin_features.undertone,
            skin_depth=skin_features.skin_depth,
            recommendations=recommendations,
            total_evaluated=len(clothes),
            best_colors=color_recs.get("best_colors", [])[:10],
            colors_to_avoid=color_recs.get("colors_to_avoid", [])[:10],
            processing_time_ms=round(processing_time, 2)
        )
        
        return response


# ============================================
# SCORE CALIBRATION UTILITIES
# ============================================

def calibrate_score(raw_score: float, curve: str = "linear") -> float:
    """
    Apply score calibration curve
    
    Args:
        raw_score: Original 0-1 score
        curve: 'linear', 'sigmoid', or 'ease'
    
    Returns:
        Calibrated score
    """
    raw_score = max(0, min(1, raw_score))
    
    if curve == "linear":
        return raw_score
    
    elif curve == "sigmoid":
        # S-curve: emphasizes differences in mid-range
        import math
        x = (raw_score - 0.5) * 10  # Scale to [-5, 5]
        return 1 / (1 + math.exp(-x))
    
    elif curve == "ease":
        # Ease out: more generous at top end
        return 1 - (1 - raw_score) ** 2
    
    return raw_score


def normalize_scores(scores: List[float]) -> List[float]:
    """Normalize scores to 0-1 range"""
    if not scores:
        return []
    
    min_s = min(scores)
    max_s = max(scores)
    
    if max_s == min_s:
        return [0.5] * len(scores)
    
    return [(s - min_s) / (max_s - min_s) for s in scores]


# ============================================
# BATCH SCORING
# ============================================

class BatchScorer:
    """Optimized scorer for large batches of clothing items"""
    
    def __init__(self):
        self.scorer = RecommendationScorer()
    
    def score_batch(
        self,
        skin_features: SkinFeatures,
        clothes: List[ClothFeatures],
        preferences: Optional[UserPreferences] = None,
        chunk_size: int = 100
    ) -> List[Tuple[str, float]]:
        """
        Score a large batch of items efficiently
        
        Returns:
            List of (cloth_id, score) tuples
        """
        results = []
        
        # Process in chunks for memory efficiency
        for i in range(0, len(clothes), chunk_size):
            chunk = clothes[i:i + chunk_size]
            
            for cloth in chunk:
                score, _ = self.scorer.score_single_item(
                    skin_features, cloth, preferences
                )
                results.append((cloth.cloth_id, score))
        
        return results
    
    def get_top_n(
        self,
        skin_features: SkinFeatures,
        clothes: List[ClothFeatures],
        n: int = 10,
        preferences: Optional[UserPreferences] = None
    ) -> List[ClothFeatures]:
        """
        Get top N items from a large batch
        
        Uses early stopping when enough high-scoring items are found
        """
        scores = self.score_batch(skin_features, clothes, preferences)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        top_ids = [s[0] for s in scores[:n]]
        
        # Map back to ClothFeatures
        id_to_cloth = {c.cloth_id: c for c in clothes}
        return [id_to_cloth[cid] for cid in top_ids if cid in id_to_cloth]

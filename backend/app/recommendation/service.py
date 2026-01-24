# Business logic for recommendation engine
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# Main recommendation service that orchestrates all components

from typing import List, Optional, Dict, Any
import logging

from .schemas import (
    SkinFeatures, ClothFeatures, UserPreferences,
    RecommendationRequest, RecommendationResponse,
    SingleClothRecommendationRequest, SingleClothRecommendationResponse,
    OutfitRecommendationRequest, OutfitRecommendationResponse,
    ClothRecommendation, ScoreBreakdown, OutfitRecommendation,
    TryOnRequest,
    Season, Undertone, SkinDepth, ClothingCategory
)
from .engine.scoring import RecommendationScorer, BatchScorer
from .engine.color_matcher import ColorMatcher
from .engine.style_matcher import StyleMatcher
from .rules.seasonal_rules import determine_season, SeasonType, get_seasonal_recommendations


logger = logging.getLogger(__name__)


class RecommendationService:
    """
    Main recommendation service
    Provides high-level API for generating clothing recommendations
    """
    
    def __init__(self):
        self.scorer = RecommendationScorer()
        self.batch_scorer = BatchScorer()
        self.color_matcher = ColorMatcher()
        self.style_matcher = StyleMatcher()
    
    async def get_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """
        Main recommendation endpoint
        Takes skin features and available clothes, returns ranked recommendations
        
        Integration Points:
        - INPUT: SkinFeatures from Face Analysis module
        - INPUT: ClothFeatures from Cloth Analysis module
        - OUTPUT: RecommendationResponse for Virtual Try-On module
        """
        logger.info(f"Generating recommendations for {len(request.available_clothes)} items")
        
        try:
            response = self.scorer.generate_full_response(
                skin_features=request.skin_features,
                clothes=request.available_clothes,
                preferences=request.preferences,
                top_k=request.top_k
            )
            
            logger.info(f"Generated {len(response.recommendations)} recommendations")
            return response
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise
    
    async def check_single_cloth(
        self,
        request: SingleClothRecommendationRequest
    ) -> SingleClothRecommendationResponse:
        """
        Check compatibility of a single clothing item
        Useful for quick lookups without ranking
        """
        score, breakdown = self.scorer.score_single_item(
            skin_features=request.skin_features,
            cloth=request.cloth_features,
            preferences=None
        )
        
        recommendation_level = self.scorer.get_recommendation_level(score)
        
        return SingleClothRecommendationResponse(
            cloth_id=request.cloth_features.cloth_id,
            is_recommended=score >= 0.5,
            overall_score=round(score, 3),
            score_breakdown=breakdown,
            recommendation_level=recommendation_level,
            reasoning=breakdown.overall_reasoning
        )
    
    async def get_outfit_recommendations(
        self,
        request: OutfitRecommendationRequest
    ) -> OutfitRecommendationResponse:
        """
        Generate complete outfit recommendations
        Combines multiple clothing items that work together
        """
        logger.info(f"Generating outfit recommendations from {len(request.available_clothes)} items")
        
        # Determine user's season
        season, subtype, _ = determine_season(
            undertone=request.skin_features.undertone.value,
            skin_depth=request.skin_features.skin_depth.value,
            lab_l=request.skin_features.lab_l,
            lab_a=request.skin_features.lab_a,
            lab_b=request.skin_features.lab_b
        )
        
        # First, rank all items by color compatibility
        ranked_items = self.scorer.rank_clothes(
            skin_features=request.skin_features,
            clothes=request.available_clothes,
            preferences=request.preferences,
            top_k=50  # Get more items for outfit building
        )
        
        # Convert back to ClothFeatures for outfit matching
        ranked_clothes = [rec.cloth_features for rec in ranked_items]
        
        # Find outfit combinations
        outfit_combinations = self.style_matcher.find_outfit_combinations(
            clothes=ranked_clothes,
            required_categories=request.include_categories,
            max_combinations=5
        )
        
        # Score and build outfit responses
        outfits = []
        for idx, combination in enumerate(outfit_combinations):
            # Get the ClothRecommendation for each item
            combo_recommendations = []
            for cloth in combination:
                for rec in ranked_items:
                    if rec.cloth_id == cloth.cloth_id:
                        combo_recommendations.append(rec)
                        break
            
            if len(combo_recommendations) == len(combination):
                outfit_score, outfit_reason = self.style_matcher.score_outfit(
                    combination, request.preferences
                )
                
                # Average color scores too
                avg_color_score = sum(r.score_breakdown.color_score for r in combo_recommendations) / len(combo_recommendations)
                combined_score = (outfit_score + avg_color_score) / 2
                
                outfit = OutfitRecommendation(
                    outfit_id=f"outfit_{idx + 1}",
                    items=combo_recommendations,
                    outfit_score=round(combined_score, 3),
                    outfit_reasoning=outfit_reason
                )
                outfits.append(outfit)
        
        # Sort by outfit score
        outfits.sort(key=lambda x: x.outfit_score, reverse=True)
        
        return OutfitRecommendationResponse(
            success=True,
            outfits=outfits,
            detected_season=Season(season.value),
            undertone=request.skin_features.undertone
        )
    
    async def get_color_analysis(
        self,
        skin_features: SkinFeatures
    ) -> Dict[str, Any]:
        """
        Get detailed color analysis for a user
        Returns personalized color palette recommendations
        """
        # Determine season
        season, subtype, reasoning = determine_season(
            undertone=skin_features.undertone.value,
            skin_depth=skin_features.skin_depth.value,
            lab_l=skin_features.lab_l,
            lab_a=skin_features.lab_a,
            lab_b=skin_features.lab_b
        )
        
        # Get seasonal recommendations
        seasonal_colors = get_seasonal_recommendations(season, subtype)
        
        # Get undertone-based colors
        best_colors = self.color_matcher.get_best_colors_for_user(
            skin_features, include_hex=True
        )
        
        return {
            "season": season.value,
            "season_subtype": subtype.value,
            "season_reasoning": reasoning,
            "undertone": skin_features.undertone.value,
            "skin_depth": skin_features.skin_depth.value,
            "color_recommendations": {
                "best_colors": best_colors.get("best_colors", []),
                "neutral_colors": best_colors.get("neutral_colors", []),
                "accent_colors": best_colors.get("accent_colors", []),
                "colors_to_avoid": best_colors.get("colors_to_avoid", []),
                "recommended_metals": seasonal_colors.get("recommended_metals", []),
            },
            "seasonal_palette": seasonal_colors,
        }
    
    def prepare_for_virtual_tryon(
        self,
        user_image_url: str,
        recommendations: List[ClothRecommendation],
        skin_features: SkinFeatures,
        max_items: int = 3
    ) -> TryOnRequest:
        """
        Prepare recommendation data for Virtual Try-On module
        
        This method packages the recommendations in the format
        expected by the Virtual Try-On service
        
        Integration: Virtual Try-On team should call their service
        with the returned TryOnRequest object
        """
        # Take top N recommendations
        top_recommendations = recommendations[:max_items]
        
        return TryOnRequest(
            user_image_url=user_image_url,
            recommended_clothes=top_recommendations,
            skin_features=skin_features,
            try_all=False,
            max_items=max_items
        )
    
    async def batch_score_inventory(
        self,
        skin_features: SkinFeatures,
        clothes: List[ClothFeatures],
        preferences: Optional[UserPreferences] = None
    ) -> List[Dict[str, Any]]:
        """
        Score a large inventory of clothing items
        Optimized for batch processing
        
        Returns simplified score data for large datasets
        """
        scores = self.batch_scorer.score_batch(
            skin_features, clothes, preferences
        )
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {
                "cloth_id": cloth_id,
                "score": round(score, 3),
                "recommendation_level": self.scorer.get_recommendation_level(score)
            }
            for cloth_id, score in scores
        ]


# ============================================
# FACTORY FUNCTION
# ============================================

_service_instance: Optional[RecommendationService] = None


def get_recommendation_service() -> RecommendationService:
    """
    Get singleton instance of RecommendationService
    Use this in FastAPI dependency injection
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = RecommendationService()
    return _service_instance

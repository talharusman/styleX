# API routes for recommendation endpoints
# Author: Recommendation Team
# Last Updated: January 24, 2026
#
# FastAPI router for all recommendation-related endpoints

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import logging

from .schemas import (
    RecommendationRequest, RecommendationResponse,
    SingleClothRecommendationRequest, SingleClothRecommendationResponse,
    OutfitRecommendationRequest, OutfitRecommendationResponse,
    SkinFeatures, ClothFeatures, UserPreferences,
    TryOnRequest,
    ClothingCategory
)
from .service import RecommendationService, get_recommendation_service


logger = logging.getLogger(__name__)

# Create router with prefix and tags
router = APIRouter(
    prefix="/recommendation",
    tags=["Recommendation"],
    responses={
        500: {"description": "Internal server error"},
        400: {"description": "Bad request"},
    }
)


# ============================================
# MAIN RECOMMENDATION ENDPOINTS
# ============================================

@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Get clothing recommendations",
    description="""
    Main recommendation endpoint.
    
    Takes user's skin features (from Face Analysis) and available clothing items
    (from Cloth Analysis), returns ranked recommendations based on color compatibility,
    style matching, and user preferences.
    
    **Integration Points:**
    - Receives SkinFeatures from Face Analysis module
    - Receives ClothFeatures from Cloth Analysis module
    - Output can be sent to Virtual Try-On module
    """
)
async def get_recommendations(
    request: RecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service)
) -> RecommendationResponse:
    """
    Generate personalized clothing recommendations
    """
    try:
        if not request.available_clothes:
            raise HTTPException(
                status_code=400,
                detail="No clothing items provided for recommendation"
            )
        
        response = await service.get_recommendations(request)
        return response
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.post(
    "/check-compatibility",
    response_model=SingleClothRecommendationResponse,
    summary="Check single item compatibility",
    description="""
    Quick compatibility check for a single clothing item.
    
    Use this endpoint to check if a specific item matches the user's skin tone
    without ranking against other items.
    """
)
async def check_cloth_compatibility(
    request: SingleClothRecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service)
) -> SingleClothRecommendationResponse:
    """
    Check if a single clothing item is compatible with user's skin features
    """
    try:
        return await service.check_single_cloth(request)
    except Exception as e:
        logger.error(f"Error checking compatibility: {e}")
        raise HTTPException(status_code=500, detail="Failed to check compatibility")


@router.post(
    "/outfits",
    response_model=OutfitRecommendationResponse,
    summary="Get outfit recommendations",
    description="""
    Generate complete outfit recommendations.
    
    Combines multiple clothing items that work well together based on:
    - Color compatibility with user's skin tone
    - Style coordination between items
    - User preferences and occasion
    """
)
async def get_outfit_recommendations(
    request: OutfitRecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service)
) -> OutfitRecommendationResponse:
    """
    Generate complete outfit combinations
    """
    try:
        return await service.get_outfit_recommendations(request)
    except Exception as e:
        logger.error(f"Error generating outfit recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate outfits")


# ============================================
# COLOR ANALYSIS ENDPOINTS
# ============================================

@router.post(
    "/color-analysis",
    summary="Get personalized color analysis",
    description="""
    Get detailed color analysis for a user based on their skin features.
    
    Returns:
    - Seasonal color type (Spring, Summer, Autumn, Winter)
    - Best colors for the user
    - Colors to avoid
    - Recommended metals for accessories
    """
)
async def get_color_analysis(
    skin_features: SkinFeatures,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get personalized color palette based on skin analysis
    """
    try:
        return await service.get_color_analysis(skin_features)
    except Exception as e:
        logger.error(f"Error in color analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze colors")


# ============================================
# VIRTUAL TRY-ON INTEGRATION ENDPOINT
# ============================================

@router.post(
    "/prepare-tryon",
    response_model=TryOnRequest,
    summary="Prepare data for virtual try-on",
    description="""
    Prepares recommendation data in the format expected by Virtual Try-On module.
    
    **For Virtual Try-On Team:**
    Call this endpoint after getting recommendations, then pass the response
    to your try-on service.
    """
)
async def prepare_for_tryon(
    user_image_url: str,
    recommendation_response: RecommendationResponse,
    skin_features: SkinFeatures,
    max_items: int = Query(default=3, ge=1, le=10),
    service: RecommendationService = Depends(get_recommendation_service)
) -> TryOnRequest:
    """
    Package recommendations for virtual try-on
    """
    return service.prepare_for_virtual_tryon(
        user_image_url=user_image_url,
        recommendations=recommendation_response.recommendations,
        skin_features=skin_features,
        max_items=max_items
    )


# ============================================
# BATCH PROCESSING ENDPOINT
# ============================================

@router.post(
    "/batch-score",
    summary="Batch score clothing inventory",
    description="""
    Score a large inventory of clothing items efficiently.
    
    Use this for:
    - Pre-computing scores for a product catalog
    - Database batch updates
    - Analytics on large datasets
    """
)
async def batch_score_inventory(
    skin_features: SkinFeatures,
    clothes: List[ClothFeatures],
    preferences: Optional[UserPreferences] = None,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Score large batches of clothing items
    """
    try:
        if len(clothes) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Maximum 1000 items per batch. Use pagination for larger datasets."
            )
        
        return await service.batch_score_inventory(
            skin_features, clothes, preferences
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch scoring: {e}")
        raise HTTPException(status_code=500, detail="Failed to score items")


# ============================================
# HEALTH CHECK
# ============================================

@router.get(
    "/health",
    summary="Health check",
    description="Check if recommendation service is running"
)
async def health_check():
    """
    Simple health check endpoint
    """
    return {
        "status": "healthy",
        "service": "recommendation",
        "version": "1.0.0"
    }


# ============================================
# DEBUG/TEST ENDPOINTS (Remove in production)
# ============================================

@router.post(
    "/test/sample-recommendation",
    summary="Test with sample data",
    description="Test the recommendation system with sample data (for development only)"
)
async def test_with_sample_data(
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Test endpoint with sample data
    """
    # Sample skin features (warm undertone, medium skin)
    sample_skin = SkinFeatures(
        undertone="warm",
        skin_depth="medium",
        lab_l=65.0,
        lab_a=12.0,
        lab_b=18.0,
        skin_rgb=[198, 166, 145],
        confidence=0.9
    )
    
    # Sample clothing items
    sample_clothes = [
        ClothFeatures(
            cloth_id="test_001",
            dominant_color_rgb=[70, 130, 180],
            dominant_color_name="steel blue",
            color_hex="#4682B4",
            color_palette=[],
            category="top",
            gender="unisex",
            style="casual",
            design="solid",
            fabric="cotton",
            weather="all_season",
            formality_level=4,
            confidence=0.85
        ),
        ClothFeatures(
            cloth_id="test_002",
            dominant_color_rgb=[255, 127, 80],
            dominant_color_name="coral",
            color_hex="#FF7F50",
            color_palette=[],
            category="top",
            gender="unisex",
            style="casual",
            design="solid",
            fabric="cotton",
            weather="summer",
            formality_level=3,
            confidence=0.9
        ),
        ClothFeatures(
            cloth_id="test_003",
            dominant_color_rgb=[139, 69, 19],
            dominant_color_name="saddle brown",
            color_hex="#8B4513",
            color_palette=[],
            category="bottom",
            gender="unisex",
            style="casual",
            design="solid",
            fabric="denim",
            weather="all_season",
            formality_level=3,
            confidence=0.88
        ),
    ]
    
    request = RecommendationRequest(
        skin_features=sample_skin,
        available_clothes=sample_clothes,
        preferences=None,
        top_k=10
    )
    
    response = await service.get_recommendations(request)
    
    return {
        "message": "Test completed successfully",
        "input": {
            "skin_undertone": sample_skin.undertone,
            "skin_depth": sample_skin.skin_depth,
            "num_clothes": len(sample_clothes)
        },
        "output": {
            "detected_season": response.detected_season,
            "best_colors": response.best_colors[:5],
            "num_recommendations": len(response.recommendations),
            "top_recommendation": response.recommendations[0].dict() if response.recommendations else None
        }
    }

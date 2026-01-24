"""
Face Analysis Router

API endpoints for face/skin feature extraction and color analysis.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, status
import base64
import logging

from .schemas import (
    FaceAnalysisInput, FaceAnalysisResponse,
    SkinFeatures, ColorRecommendations, SeasonalType
)
from .service import FaceAnalysisService, get_face_analysis_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/face-analysis",
    tags=["Face Analysis"],
    responses={
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"}
    }
)


@router.post(
    "/analyze",
    response_model=FaceAnalysisResponse,
    summary="Analyze face image",
    description="""
    Analyze a face image to extract skin features and generate color recommendations.
    
    Returns:
    - Skin undertone (warm, cool, neutral)
    - Skin depth (fair, light, medium, tan, deep)
    - Seasonal color type (spring, summer, autumn, winter)
    - Personalized color recommendations
    - Style tips based on analysis
    """
)
async def analyze_face(
    input_data: FaceAnalysisInput,
    service: FaceAnalysisService = Depends(get_face_analysis_service)
) -> FaceAnalysisResponse:
    """
    Analyze a face image and extract skin features.
    
    Provide either image_base64 or image_url.
    """
    if not input_data.image_base64 and not input_data.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either image_base64 or image_url must be provided"
        )
    
    try:
        response = await service.analyze_face(input_data)
        
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=response.error or "Face analysis failed"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Face analysis endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.post(
    "/analyze/upload",
    response_model=FaceAnalysisResponse,
    summary="Analyze uploaded face image",
    description="Upload an image file for face analysis."
)
async def analyze_uploaded_face(
    file: UploadFile = File(..., description="Image file to analyze"),
    service: FaceAnalysisService = Depends(get_face_analysis_service)
) -> FaceAnalysisResponse:
    """
    Analyze an uploaded face image file.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be an image"
        )
    
    try:
        # Read and encode file
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode("utf-8")
        
        # Create input
        input_data = FaceAnalysisInput(image_base64=image_base64)
        
        # Analyze
        response = await service.analyze_face(input_data)
        
        if not response.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=response.error or "Face analysis failed"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )


@router.get(
    "/color-palette/{seasonal_type}",
    response_model=ColorRecommendations,
    summary="Get color palette for seasonal type",
    description="Get recommended colors for a specific seasonal type."
)
async def get_color_palette(
    seasonal_type: SeasonalType,
    service: FaceAnalysisService = Depends(get_face_analysis_service)
) -> ColorRecommendations:
    """
    Get color recommendations for a seasonal type.
    
    - **seasonal_type**: spring, summer, autumn, or winter
    """
    return service._get_color_recommendations(seasonal_type)


@router.get(
    "/seasonal-types",
    summary="Get available seasonal types",
    description="List all available seasonal color analysis types."
)
async def get_seasonal_types() -> dict:
    """
    Get all seasonal types with descriptions.
    """
    return {
        "seasonal_types": [
            {
                "type": "spring",
                "description": "Warm undertone + Light skin depth",
                "characteristics": "Clear, warm, light colors"
            },
            {
                "type": "summer",
                "description": "Cool undertone + Light skin depth",
                "characteristics": "Soft, cool, muted colors"
            },
            {
                "type": "autumn",
                "description": "Warm undertone + Deep skin depth",
                "characteristics": "Rich, warm, earthy colors"
            },
            {
                "type": "winter",
                "description": "Cool undertone + Deep skin depth",
                "characteristics": "Bold, cool, high-contrast colors"
            }
        ]
    }


@router.get(
    "/undertones",
    summary="Get undertone information",
    description="Get information about skin undertones."
)
async def get_undertones() -> dict:
    """
    Get undertone types and how to identify them.
    """
    return {
        "undertones": [
            {
                "type": "warm",
                "vein_color": "Green/olive veins",
                "jewelry": "Gold looks better",
                "colors": "Yellow, orange, coral look good"
            },
            {
                "type": "cool",
                "vein_color": "Blue/purple veins",
                "jewelry": "Silver looks better",
                "colors": "Pink, blue, purple look good"
            },
            {
                "type": "neutral",
                "vein_color": "Mix of blue and green veins",
                "jewelry": "Both gold and silver look good",
                "colors": "Most colors work well"
            }
        ]
    }


@router.get(
    "/health",
    summary="Health check",
    description="Check face analysis service health."
)
async def health_check(
    service: FaceAnalysisService = Depends(get_face_analysis_service)
) -> dict:
    """
    Check the health of the face analysis service.
    """
    return {
        "status": "healthy",
        "service": "face_analysis",
        "mediapipe_available": service._initialized,
        "version": "1.0.0"
    }

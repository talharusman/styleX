"""
API routes for cloth analysis endpoints.
Provides endpoints for clothing feature extraction.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
import base64
import logging

from .schemas import ClothInput, ClothAnalysisResponse, ClothFeatures
from .service import get_cloth_analysis_service, analyze_clothing

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cloth-analysis",
    tags=["Clothing Analysis"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    }
)


@router.post(
    "/analyze",
    response_model=ClothAnalysisResponse,
    summary="Analyze clothing image",
    description="""
    Analyze a clothing image and extract all features including:
    - Dominant colors
    - Design pattern (plain, stripes, checks, etc.)
    - Gender classification (male, female, unisex)
    - Category (t-shirt, pants, dress, etc.)
    - Weather suitability (summer, winter, all-season)
    - Style (casual, formal, sporty, etc.)
    - Formality level (1-5 scale)
    
    Optimized for 4GB GPU with FP16 precision.
    """
)
async def analyze_clothing_endpoint(
    input_data: ClothInput,
    use_clip: bool = Query(
        default=True,
        description="Use CLIP for zero-shot style classification (more accurate but slower)"
    )
) -> ClothAnalysisResponse:
    """
    Analyze a clothing image and extract all features.
    
    Args:
        input_data: Contains either image_base64 or image_url
        use_clip: Whether to use CLIP for style detection
        
    Returns:
        ClothAnalysisResponse with extracted features
    """
    try:
        # Validate input
        if not input_data.image_base64 and not input_data.image_url:
            raise HTTPException(
                status_code=400,
                detail="Either image_base64 or image_url must be provided"
            )
        
        # Perform analysis
        response = await analyze_clothing(input_data, use_clip=use_clip)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=response.error or "Analysis failed"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/analyze/upload",
    response_model=ClothAnalysisResponse,
    summary="Analyze uploaded clothing image",
    description="Upload an image file for clothing analysis."
)
async def analyze_uploaded_image(
    file: UploadFile = File(..., description="Image file to analyze"),
    use_clip: bool = Query(
        default=True,
        description="Use CLIP for zero-shot style classification"
    )
) -> ClothAnalysisResponse:
    """
    Analyze an uploaded clothing image file.
    
    Args:
        file: Uploaded image file
        use_clip: Whether to use CLIP for style detection
        
    Returns:
        ClothAnalysisResponse with extracted features
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Uploaded file must be an image"
            )
        
        # Read and encode file
        contents = await file.read()
        image_base64 = base64.b64encode(contents).decode("utf-8")
        
        # Create input
        input_data = ClothInput(image_base64=image_base64)
        
        # Perform analysis
        response = await analyze_clothing(input_data, use_clip=use_clip)
        
        if not response.success:
            raise HTTPException(
                status_code=500,
                detail=response.error or "Analysis failed"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Check service health",
    description="Check if the cloth analysis service is running."
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Health status and GPU availability
    """
    from .utils import is_gpu_available, get_device
    
    return {
        "status": "healthy",
        "service": "cloth_analysis",
        "gpu_available": is_gpu_available(),
        "device": str(get_device()),
    }


@router.get(
    "/categories",
    summary="Get available categories",
    description="Get list of all supported clothing categories."
)
async def get_categories() -> dict:
    """
    Get all supported clothing categories.
    
    Returns:
        List of category values
    """
    from .schemas import ClothingCategory
    
    return {
        "categories": [c.value for c in ClothingCategory]
    }


@router.get(
    "/styles",
    summary="Get available styles",
    description="Get list of all supported clothing styles."
)
async def get_styles() -> dict:
    """
    Get all supported clothing styles.
    
    Returns:
        List of style values
    """
    from .schemas import StyleType
    
    return {
        "styles": [s.value for s in StyleType]
    }


@router.get(
    "/patterns",
    summary="Get available design patterns",
    description="Get list of all supported design patterns."
)
async def get_patterns() -> dict:
    """
    Get all supported design patterns.
    
    Returns:
        List of pattern values
    """
    from .schemas import DesignPattern
    
    return {
        "patterns": [p.value for p in DesignPattern]
    }

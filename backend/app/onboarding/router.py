"""
Onboarding Router - API endpoints for user onboarding wizard
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging

from .schemas import (
    OnboardingStep,
    OnboardingProgress,
    OnboardingSummary,
    OnboardingStepRequest,
    OnboardingStepResponse,
    SelfieStepData,
    BodyTypeStepData,
    SkinToneStepData,
    StyleStepData,
    CompleteStepData,
    AnalyzeSelfieRequest,
    AnalyzeSelfieResponse
)
from .service import OnboardingService, get_onboarding_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/onboarding",
    tags=["Onboarding"],
    responses={
        400: {"description": "Invalid request"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/progress/{user_id}",
    response_model=OnboardingProgress,
    summary="Get Onboarding Progress",
    description="Get user's current onboarding progress"
)
async def get_progress(
    user_id: str,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingProgress:
    """
    Get the current onboarding progress for a user.
    
    - **user_id**: User ID
    
    Returns current step, completed steps, and stored data.
    """
    return service.get_progress(user_id)


@router.get(
    "/summary/{user_id}",
    response_model=OnboardingSummary,
    summary="Get Onboarding Summary",
    description="Get summary of completed onboarding data"
)
async def get_summary(
    user_id: str,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingSummary:
    """
    Get the summary of user's onboarding data.
    
    - **user_id**: User ID
    
    Returns processed onboarding data including body type, skin tone,
    style preferences, and color recommendations.
    """
    return service.get_summary(user_id)


@router.post(
    "/step",
    response_model=OnboardingStepResponse,
    summary="Update Onboarding Step",
    description="Update data for a specific onboarding step"
)
async def update_step(
    user_id: str,
    request: OnboardingStepRequest,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingStepResponse:
    """
    Update a specific onboarding step.
    
    - **user_id**: User ID
    - **step**: The step being updated
    - **data**: Step-specific data (see individual step schemas)
    
    Returns success status and next step information.
    """
    try:
        result = await service.update_step(
            user_id=user_id,
            step=request.step,
            data=request.data
        )
        
        return OnboardingStepResponse(
            success=result["success"],
            step=result["step"],
            next_step=result["next_step"],
            progress_percentage=result["progress_percentage"],
            message="Step completed successfully"
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Update step error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update step: {str(e)}"
        )


# ============== Individual Step Endpoints ==============

@router.post(
    "/step/selfie/{user_id}",
    response_model=OnboardingStepResponse,
    summary="Submit Selfie Step",
    description="Submit selfie data for analysis"
)
async def submit_selfie_step(
    user_id: str,
    data: SelfieStepData,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingStepResponse:
    """
    Submit selfie step data.
    
    - **user_id**: User ID
    - **data**: Selfie analysis data or image for analysis
    """
    result = await service.update_step(
        user_id=user_id,
        step=OnboardingStep.SELFIE,
        data=data.model_dump()
    )
    
    return OnboardingStepResponse(
        success=result["success"],
        step=OnboardingStep.SELFIE,
        next_step=result["next_step"],
        progress_percentage=result["progress_percentage"],
        message="Selfie step completed"
    )


@router.post(
    "/step/body-type/{user_id}",
    response_model=OnboardingStepResponse,
    summary="Submit Body Type Step",
    description="Submit body type information"
)
async def submit_body_type_step(
    user_id: str,
    data: BodyTypeStepData,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingStepResponse:
    """
    Submit body type step data.
    
    - **user_id**: User ID
    - **data**: Body type and measurements
    """
    result = await service.update_step(
        user_id=user_id,
        step=OnboardingStep.BODY_TYPE,
        data=data.model_dump()
    )
    
    return OnboardingStepResponse(
        success=result["success"],
        step=OnboardingStep.BODY_TYPE,
        next_step=result["next_step"],
        progress_percentage=result["progress_percentage"],
        message="Body type step completed"
    )


@router.post(
    "/step/skin-tone/{user_id}",
    response_model=OnboardingStepResponse,
    summary="Submit Skin Tone Step",
    description="Submit skin tone and undertone information"
)
async def submit_skin_tone_step(
    user_id: str,
    data: SkinToneStepData,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingStepResponse:
    """
    Submit skin tone step data.
    
    - **user_id**: User ID
    - **data**: Skin tone and undertone
    """
    result = await service.update_step(
        user_id=user_id,
        step=OnboardingStep.SKIN_TONE,
        data=data.model_dump()
    )
    
    return OnboardingStepResponse(
        success=result["success"],
        step=OnboardingStep.SKIN_TONE,
        next_step=result["next_step"],
        progress_percentage=result["progress_percentage"],
        message="Skin tone step completed"
    )


@router.post(
    "/step/style/{user_id}",
    response_model=OnboardingStepResponse,
    summary="Submit Style Step",
    description="Submit style preferences"
)
async def submit_style_step(
    user_id: str,
    data: StyleStepData,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingStepResponse:
    """
    Submit style preferences step data.
    
    - **user_id**: User ID
    - **data**: Style preferences and favorite colors
    """
    result = await service.update_step(
        user_id=user_id,
        step=OnboardingStep.STYLE,
        data=data.model_dump()
    )
    
    return OnboardingStepResponse(
        success=result["success"],
        step=OnboardingStep.STYLE,
        next_step=result["next_step"],
        progress_percentage=result["progress_percentage"],
        message="Style step completed"
    )


@router.post(
    "/step/complete/{user_id}",
    response_model=OnboardingStepResponse,
    summary="Complete Onboarding",
    description="Complete the onboarding process"
)
async def complete_onboarding(
    user_id: str,
    data: CompleteStepData,
    service: OnboardingService = Depends(get_onboarding_service)
) -> OnboardingStepResponse:
    """
    Complete the onboarding process.
    
    - **user_id**: User ID
    - **data**: Final preferences and terms acceptance
    """
    result = await service.update_step(
        user_id=user_id,
        step=OnboardingStep.COMPLETE,
        data=data.model_dump()
    )
    
    return OnboardingStepResponse(
        success=result["success"],
        step=OnboardingStep.COMPLETE,
        next_step=None,
        progress_percentage=100.0,
        message="Onboarding completed successfully! Welcome to StyleX."
    )


# ============== Utility Endpoints ==============

@router.post(
    "/analyze-selfie",
    response_model=AnalyzeSelfieResponse,
    summary="Analyze Selfie",
    description="Analyze a selfie to detect face features"
)
async def analyze_selfie(
    request: AnalyzeSelfieRequest,
    service: OnboardingService = Depends(get_onboarding_service)
) -> AnalyzeSelfieResponse:
    """
    Analyze a selfie to detect face features.
    
    - **image_base64**: Base64 encoded image
    - **image_url**: URL to image
    
    Returns detected face shape, skin tone, and other features.
    """
    if not request.image_base64 and not request.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either image_base64 or image_url must be provided"
        )
    
    result = await service.analyze_selfie(
        image_base64=request.image_base64,
        image_url=request.image_url
    )
    
    return AnalyzeSelfieResponse(**result)


@router.get(
    "/color-recommendations",
    summary="Get Color Recommendations",
    description="Get color recommendations based on skin tone"
)
async def get_color_recommendations(
    skin_tone: str,
    undertone: str,
    service: OnboardingService = Depends(get_onboarding_service)
) -> dict:
    """
    Get color recommendations based on skin tone and undertone.
    
    - **skin_tone**: User's skin tone
    - **undertone**: User's undertone (warm, cool, neutral)
    """
    from .schemas import SkinTone, SkinUndertone
    
    try:
        tone = SkinTone(skin_tone.lower())
        under = SkinUndertone(undertone.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid skin tone or undertone value"
        )
    
    recommendations = service.get_color_recommendations(tone, under)
    
    return {
        "skin_tone": skin_tone,
        "undertone": undertone,
        "recommended_colors": recommendations["recommended"],
        "colors_to_avoid": recommendations["avoid"]
    }


@router.post(
    "/reset/{user_id}",
    summary="Reset Onboarding",
    description="Reset user's onboarding progress"
)
async def reset_onboarding(
    user_id: str,
    service: OnboardingService = Depends(get_onboarding_service)
) -> dict:
    """
    Reset onboarding progress for a user.
    
    - **user_id**: User ID
    
    Warning: This will delete all onboarding data.
    """
    service.reset_progress(user_id)
    return {"success": True, "message": "Onboarding progress reset"}


@router.get(
    "/steps",
    summary="Get Onboarding Steps",
    description="Get list of onboarding steps"
)
async def get_steps() -> dict:
    """Get the list of onboarding steps and their order."""
    return {
        "steps": [
            {
                "step": OnboardingStep.SELFIE.value,
                "name": "Selfie",
                "description": "Upload a selfie for face analysis",
                "order": 1
            },
            {
                "step": OnboardingStep.BODY_TYPE.value,
                "name": "Body Type",
                "description": "Select your body type and measurements",
                "order": 2
            },
            {
                "step": OnboardingStep.SKIN_TONE.value,
                "name": "Skin Tone",
                "description": "Confirm your skin tone and undertone",
                "order": 3
            },
            {
                "step": OnboardingStep.STYLE.value,
                "name": "Style Preferences",
                "description": "Select your style and color preferences",
                "order": 4
            },
            {
                "step": OnboardingStep.COMPLETE.value,
                "name": "Complete",
                "description": "Review and complete your profile",
                "order": 5
            }
        ]
    }

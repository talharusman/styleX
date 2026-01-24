"""
Profile Router - API endpoints for user profile management
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional
import logging

from .schemas import (
    UserProfile,
    ProfileUpdate,
    StyleProfile,
    ProfileStats,
    ProfileSummary,
    AvatarUpload,
    SubscriptionTier
)
from .service import ProfileService, get_profile_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/profile",
    tags=["Profile"],
    responses={
        404: {"description": "Profile not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "/{user_id}",
    response_model=UserProfile,
    summary="Get Profile",
    description="Get user profile by ID"
)
async def get_profile(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
) -> UserProfile:
    """
    Get complete user profile.
    
    - **user_id**: User ID
    
    Returns full profile with style information and preferences.
    """
    profile = await service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.patch(
    "/{user_id}",
    response_model=UserProfile,
    summary="Update Profile",
    description="Update user profile"
)
async def update_profile(
    user_id: str,
    update_data: ProfileUpdate,
    service: ProfileService = Depends(get_profile_service)
) -> UserProfile:
    """
    Update user profile.
    
    - **user_id**: User ID
    - **update_data**: Fields to update
    
    Returns updated profile.
    """
    profile = await service.update_profile(user_id, update_data)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Profile",
    description="Delete user profile"
)
async def delete_profile(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
):
    """
    Delete user profile.
    
    Warning: This action is irreversible.
    """
    success = await service.delete_profile(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )


@router.get(
    "/{user_id}/summary",
    response_model=ProfileSummary,
    summary="Get Profile Summary",
    description="Get compact profile summary"
)
async def get_profile_summary(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
) -> ProfileSummary:
    """
    Get compact profile summary for display.
    
    Returns essential profile info for UI display.
    """
    summary = await service.get_profile_summary(user_id)
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return summary


@router.get(
    "/{user_id}/style",
    response_model=StyleProfile,
    summary="Get Style Profile",
    description="Get user's style profile"
)
async def get_style_profile(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
) -> StyleProfile:
    """
    Get user's style profile.
    
    Returns style-related information including body type,
    skin tone, preferences, and recommended colors.
    """
    style = await service.get_style_profile(user_id)
    
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return style


@router.patch(
    "/{user_id}/style",
    response_model=StyleProfile,
    summary="Update Style Profile",
    description="Update user's style profile"
)
async def update_style_profile(
    user_id: str,
    style_data: dict,
    service: ProfileService = Depends(get_profile_service)
) -> StyleProfile:
    """
    Update user's style profile.
    
    - **style_data**: Style-related fields to update
    
    Returns updated style profile.
    """
    style = await service.update_style_profile(user_id, style_data)
    
    if not style:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return style


@router.get(
    "/{user_id}/stats",
    response_model=ProfileStats,
    summary="Get Profile Stats",
    description="Get user's profile statistics"
)
async def get_profile_stats(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
) -> ProfileStats:
    """
    Get user's profile statistics.
    
    Returns activity statistics and engagement metrics.
    """
    return await service.get_profile_stats(user_id)


@router.post(
    "/{user_id}/avatar",
    summary="Update Avatar",
    description="Update user's avatar"
)
async def update_avatar(
    user_id: str,
    avatar_data: AvatarUpload,
    service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Update user's avatar.
    
    - **avatar_data**: Image as base64 or URL
    
    Returns success status and avatar URL.
    """
    if not avatar_data.image_base64 and not avatar_data.image_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either image_base64 or image_url must be provided"
        )
    
    # In production, would upload to storage and get URL
    avatar_url = avatar_data.image_url or "https://storage.example.com/avatars/uploaded.jpg"
    
    success = await service.update_avatar(user_id, avatar_url)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {
        "success": True,
        "avatar_url": avatar_url
    }


@router.post(
    "/{user_id}/subscription",
    summary="Update Subscription",
    description="Update user's subscription tier"
)
async def update_subscription(
    user_id: str,
    tier: SubscriptionTier,
    service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Update user's subscription tier.
    
    - **tier**: New subscription tier (free, basic, premium, vip)
    """
    success = await service.update_subscription(user_id, tier)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {
        "success": True,
        "subscription_tier": tier.value,
        "message": f"Subscription updated to {tier.value}"
    }


@router.get(
    "/{user_id}/color-recommendations",
    summary="Get Color Recommendations",
    description="Get personalized color recommendations"
)
async def get_color_recommendations(
    user_id: str,
    service: ProfileService = Depends(get_profile_service)
) -> dict:
    """
    Get personalized color recommendations based on profile.
    
    Returns recommended colors and colors to avoid.
    """
    profile = await service.get_profile(user_id)
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    if not profile.skin_tone or not profile.undertone:
        return {
            "message": "Complete your skin tone analysis for personalized recommendations",
            "recommended_colors": ["navy", "white", "grey", "black"],
            "avoid_colors": []
        }
    
    recommended = service.get_recommended_colors(
        profile.skin_tone,
        profile.undertone
    )
    
    return {
        "skin_tone": profile.skin_tone,
        "undertone": profile.undertone,
        "seasonal_type": profile.seasonal_type,
        "recommended_colors": recommended,
        "avoid_colors": profile.avoid_colors,
        "favorite_colors": profile.favorite_colors
    }

"""
Settings Router - API endpoints for user settings management
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional
import logging

from .schemas import (
    AccountSettings,
    NotificationSettings,
    NotificationSettingsUpdate,
    PrivacySettings,
    PrivacySettingsUpdate,
    AppearanceSettings,
    AppearanceSettingsUpdate,
    CalendarSettings,
    CalendarSettingsUpdate,
    AISettings,
    AISettingsUpdate,
    AllSettings,
    HelpCategory,
    HelpArticle,
    ContactSupportRequest,
    FeedbackRequest
)
from .service import SettingsService, get_settings_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/settings",
    tags=["Settings"],
    responses={
        404: {"description": "Settings not found"},
        500: {"description": "Internal server error"}
    }
)


# ============== All Settings ==============

@router.get(
    "/{user_id}",
    response_model=AllSettings,
    summary="Get All Settings",
    description="Get all settings for a user"
)
async def get_all_settings(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> AllSettings:
    """
    Get all user settings in a single call.
    
    Returns account, notification, privacy, appearance, calendar, and AI settings.
    """
    return await service.get_all_settings(user_id)


@router.post(
    "/{user_id}/reset",
    summary="Reset Settings",
    description="Reset settings to defaults"
)
async def reset_settings(
    user_id: str,
    category: Optional[str] = Query(default=None, description="Specific category to reset"),
    service: SettingsService = Depends(get_settings_service)
) -> dict:
    """
    Reset settings to default values.
    
    - **category**: Optional specific category (notifications, privacy, etc.)
    
    If no category specified, resets all settings.
    """
    await service.reset_settings(user_id, category)
    return {
        "success": True,
        "message": f"{'All' if not category else category.capitalize()} settings reset to defaults"
    }


# ============== Account Settings ==============

@router.get(
    "/{user_id}/account",
    response_model=AccountSettings,
    summary="Get Account Settings",
    description="Get account-related settings"
)
async def get_account_settings(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> AccountSettings:
    """Get account settings including email, 2FA status, etc."""
    return await service.get_account_settings(user_id)


@router.post(
    "/{user_id}/account/two-factor",
    summary="Enable Two-Factor Auth",
    description="Enable two-factor authentication"
)
async def enable_two_factor(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> dict:
    """
    Enable two-factor authentication for the account.
    
    Returns setup information including secret key.
    """
    return await service.enable_two_factor(user_id)


# ============== Notification Settings ==============

@router.get(
    "/{user_id}/notifications",
    response_model=NotificationSettings,
    summary="Get Notification Settings",
    description="Get notification preferences"
)
async def get_notification_settings(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> NotificationSettings:
    """Get notification settings for push, email, and SMS."""
    return await service.get_notification_settings(user_id)


@router.patch(
    "/{user_id}/notifications",
    response_model=NotificationSettings,
    summary="Update Notification Settings",
    description="Update notification preferences"
)
async def update_notification_settings(
    user_id: str,
    update_data: NotificationSettingsUpdate,
    service: SettingsService = Depends(get_settings_service)
) -> NotificationSettings:
    """
    Update notification settings.
    
    Only include fields you want to change.
    """
    return await service.update_notification_settings(user_id, update_data)


# ============== Privacy Settings ==============

@router.get(
    "/{user_id}/privacy",
    response_model=PrivacySettings,
    summary="Get Privacy Settings",
    description="Get privacy preferences"
)
async def get_privacy_settings(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> PrivacySettings:
    """Get privacy settings including data collection and sharing preferences."""
    return await service.get_privacy_settings(user_id)


@router.patch(
    "/{user_id}/privacy",
    response_model=PrivacySettings,
    summary="Update Privacy Settings",
    description="Update privacy preferences"
)
async def update_privacy_settings(
    user_id: str,
    update_data: PrivacySettingsUpdate,
    service: SettingsService = Depends(get_settings_service)
) -> PrivacySettings:
    """
    Update privacy settings.
    
    Only include fields you want to change.
    """
    return await service.update_privacy_settings(user_id, update_data)


# ============== Appearance Settings ==============

@router.get(
    "/{user_id}/appearance",
    response_model=AppearanceSettings,
    summary="Get Appearance Settings",
    description="Get appearance/UI preferences"
)
async def get_appearance_settings(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> AppearanceSettings:
    """Get appearance settings including theme, language, and accessibility options."""
    return await service.get_appearance_settings(user_id)


@router.patch(
    "/{user_id}/appearance",
    response_model=AppearanceSettings,
    summary="Update Appearance Settings",
    description="Update appearance/UI preferences"
)
async def update_appearance_settings(
    user_id: str,
    update_data: AppearanceSettingsUpdate,
    service: SettingsService = Depends(get_settings_service)
) -> AppearanceSettings:
    """
    Update appearance settings.
    
    Only include fields you want to change.
    """
    return await service.update_appearance_settings(user_id, update_data)


# ============== Calendar Settings ==============

@router.get(
    "/{user_id}/calendar",
    response_model=CalendarSettings,
    summary="Get Calendar Settings",
    description="Get calendar integration settings"
)
async def get_calendar_settings(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> CalendarSettings:
    """Get calendar settings including Google connection and sync preferences."""
    return await service.get_calendar_settings(user_id)


@router.patch(
    "/{user_id}/calendar",
    response_model=CalendarSettings,
    summary="Update Calendar Settings",
    description="Update calendar integration settings"
)
async def update_calendar_settings(
    user_id: str,
    update_data: CalendarSettingsUpdate,
    service: SettingsService = Depends(get_settings_service)
) -> CalendarSettings:
    """
    Update calendar settings.
    
    Only include fields you want to change.
    """
    return await service.update_calendar_settings(user_id, update_data)


@router.post(
    "/{user_id}/calendar/disconnect",
    summary="Disconnect Google Calendar",
    description="Disconnect Google Calendar integration"
)
async def disconnect_google_calendar(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> dict:
    """Disconnect Google Calendar and remove synced data."""
    await service.disconnect_google_calendar(user_id)
    return {
        "success": True,
        "message": "Google Calendar disconnected"
    }


# ============== AI Settings ==============

@router.get(
    "/{user_id}/ai",
    response_model=AISettings,
    summary="Get AI Settings",
    description="Get AI assistant settings"
)
async def get_ai_settings(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> AISettings:
    """Get AI settings including recommendation and learning preferences."""
    return await service.get_ai_settings(user_id)


@router.patch(
    "/{user_id}/ai",
    response_model=AISettings,
    summary="Update AI Settings",
    description="Update AI assistant settings"
)
async def update_ai_settings(
    user_id: str,
    update_data: AISettingsUpdate,
    service: SettingsService = Depends(get_settings_service)
) -> AISettings:
    """
    Update AI settings.
    
    Only include fields you want to change.
    """
    return await service.update_ai_settings(user_id, update_data)


# ============== Help & Support ==============

@router.get(
    "/help/categories",
    response_model=list[HelpCategory],
    summary="Get Help Categories",
    description="Get list of help/FAQ categories"
)
async def get_help_categories(
    service: SettingsService = Depends(get_settings_service)
) -> list[HelpCategory]:
    """Get available help categories."""
    return service.get_help_categories()


@router.get(
    "/help/articles/{category_id}",
    response_model=list[HelpArticle],
    summary="Get Help Articles",
    description="Get help articles for a category"
)
async def get_help_articles(
    category_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> list[HelpArticle]:
    """Get help articles for a specific category."""
    return service.get_help_articles(category_id)


@router.post(
    "/{user_id}/support",
    summary="Contact Support",
    description="Submit a support request"
)
async def contact_support(
    user_id: str,
    request: ContactSupportRequest,
    service: SettingsService = Depends(get_settings_service)
) -> dict:
    """
    Submit a support request.
    
    Creates a support ticket and returns ticket ID.
    """
    return await service.submit_support_request(
        user_id=user_id,
        subject=request.subject,
        message=request.message,
        category=request.category
    )


@router.post(
    "/{user_id}/feedback",
    summary="Submit Feedback",
    description="Submit user feedback"
)
async def submit_feedback(
    user_id: str,
    request: FeedbackRequest,
    service: SettingsService = Depends(get_settings_service)
) -> dict:
    """
    Submit feedback about the app.
    
    - **rating**: 1-5 star rating
    - **feedback**: Optional text feedback
    - **feature**: Optional specific feature being rated
    """
    return await service.submit_feedback(
        user_id=user_id,
        rating=request.rating,
        feedback=request.feedback,
        feature=request.feature
    )


# ============== Data Management (GDPR) ==============

@router.get(
    "/{user_id}/export",
    summary="Export User Data",
    description="Export all user data (GDPR)"
)
async def export_user_data(
    user_id: str,
    service: SettingsService = Depends(get_settings_service)
) -> dict:
    """
    Export all user data for GDPR compliance.
    
    Returns all stored user data in JSON format.
    """
    return await service.export_user_data(user_id)


@router.delete(
    "/{user_id}/data",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User Data",
    description="Delete all user data (GDPR)"
)
async def delete_user_data(
    user_id: str,
    confirm: bool = Query(..., description="Confirm deletion"),
    service: SettingsService = Depends(get_settings_service)
):
    """
    Delete all user data for GDPR compliance.
    
    Warning: This action is irreversible.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must confirm deletion with confirm=true"
        )
    
    await service.delete_user_data(user_id)

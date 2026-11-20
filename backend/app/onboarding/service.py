"""
Onboarding Service - Handles user onboarding logic with MongoDB backend
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from beanie import PydanticObjectId

from .schemas import (
    OnboardingStep,
    OnboardingProgress,
    OnboardingSummary,
    SelfieStepData,
    BodyTypeStepData,
    SkinToneStepData,
    StyleStepData,
    CompleteStepData,
    BodyType,
    SkinTone,
    SkinUndertone,
    StylePreference
)
from app.database import (
    user_repository,
    get_user_repository,
    OnboardingProgress as DbOnboardingProgress,
)

logger = logging.getLogger(__name__)


# Color recommendations based on skin tone and undertone
COLOR_RECOMMENDATIONS = {
    (SkinTone.FAIR, SkinUndertone.COOL): {
        "recommended": ["navy", "burgundy", "forest green", "plum", "silver", "charcoal", "rose"],
        "avoid": ["orange", "mustard", "camel", "warm brown"]
    },
    (SkinTone.FAIR, SkinUndertone.WARM): {
        "recommended": ["peach", "coral", "gold", "cream", "olive", "warm brown", "turquoise"],
        "avoid": ["black", "neon colors", "silver"]
    },
    (SkinTone.LIGHT, SkinUndertone.COOL): {
        "recommended": ["lavender", "soft pink", "powder blue", "silver", "grey", "mauve"],
        "avoid": ["orange", "bright yellow", "rust"]
    },
    (SkinTone.LIGHT, SkinUndertone.WARM): {
        "recommended": ["camel", "peach", "gold", "warm red", "olive", "ivory"],
        "avoid": ["pure white", "black", "fuchsia"]
    },
    (SkinTone.MEDIUM, SkinUndertone.COOL): {
        "recommended": ["burgundy", "teal", "purple", "raspberry", "grey", "navy"],
        "avoid": ["orange", "mustard", "beige"]
    },
    (SkinTone.MEDIUM, SkinUndertone.WARM): {
        "recommended": ["orange", "coral", "gold", "teal", "olive", "bronze"],
        "avoid": ["pastel pink", "silver", "pure white"]
    },
    (SkinTone.OLIVE, SkinUndertone.NEUTRAL): {
        "recommended": ["emerald", "turquoise", "coral", "cream", "burgundy", "orange"],
        "avoid": ["neon colors", "pure white", "black near face"]
    },
    (SkinTone.TAN, SkinUndertone.WARM): {
        "recommended": ["white", "coral", "orange", "gold", "turquoise", "cream"],
        "avoid": ["brown", "dull colors", "grey"]
    },
    (SkinTone.BROWN, SkinUndertone.WARM): {
        "recommended": ["orange", "gold", "coral", "emerald", "turquoise", "cream"],
        "avoid": ["brown near face", "dull greys"]
    },
    (SkinTone.DARK, SkinUndertone.COOL): {
        "recommended": ["royal blue", "purple", "silver", "pink", "white", "red"],
        "avoid": ["brown", "navy near face"]
    },
    (SkinTone.DARK, SkinUndertone.WARM): {
        "recommended": ["orange", "yellow", "gold", "coral", "white", "emerald"],
        "avoid": ["dark brown", "khaki", "muted colors"]
    }
}


# Face-analysis skin depth -> onboarding SkinTone
_DEPTH_TO_TONE = {
    "fair": SkinTone.FAIR,
    "light": SkinTone.LIGHT,
    "medium": SkinTone.MEDIUM,
    "tan": SkinTone.TAN,
    "deep": SkinTone.DARK,
}


class OnboardingService:
    """Service for managing user onboarding with MongoDB"""
    
    STEP_ORDER = [
        OnboardingStep.SELFIE,
        OnboardingStep.BODY_TYPE,
        OnboardingStep.SKIN_TONE,
        OnboardingStep.STYLE,
        OnboardingStep.COMPLETE
    ]
    
    def __init__(self):
        """Initialize onboarding service"""
        self._repo = get_user_repository()
    
    async def get_progress(self, user_id: str) -> OnboardingProgress:
        """Get onboarding progress for a user"""
        db_progress = await self._repo.get_onboarding_progress(user_id)
        
        if not db_progress:
            # Create new progress if not exists
            user_id_obj = PydanticObjectId(user_id) if isinstance(user_id, str) else user_id
            db_progress = await self._repo.create_onboarding_progress(user_id_obj)
        
        # Convert DB model to schema
        return OnboardingProgress(
            user_id=user_id,
            current_step=OnboardingStep(db_progress.current_step) if db_progress.current_step else OnboardingStep.SELFIE,
            completed_steps=[OnboardingStep(s) for s in db_progress.completed_steps],
            step_data=db_progress.step_data or {},
            is_complete=db_progress.is_complete,
            started_at=db_progress.created_at,
            completed_at=db_progress.completed_at,
            updated_at=db_progress.updated_at
        )
    
    def get_progress_percentage(self, progress: OnboardingProgress) -> float:
        """Calculate progress percentage"""
        total_steps = len(self.STEP_ORDER)
        completed = len(progress.completed_steps)
        return (completed / total_steps) * 100
    
    def get_next_step(self, current_step: OnboardingStep) -> Optional[OnboardingStep]:
        """Get the next step after the current one"""
        try:
            current_index = self.STEP_ORDER.index(current_step)
            if current_index < len(self.STEP_ORDER) - 1:
                return self.STEP_ORDER[current_index + 1]
        except ValueError:
            pass
        return None
    
    async def update_step(
        self,
        user_id: str,
        step: OnboardingStep,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a specific onboarding step
        
        Args:
            user_id: User ID
            step: Step to update
            data: Step-specific data
            
        Returns:
            Dict with success status and next step info
        """
        progress = await self.get_progress(user_id)
        
        # Validate and process step data
        processed_data = await self._process_step_data(step, data)
        
        # Update progress
        progress.step_data[step.value] = processed_data
        
        # Mark step as completed if not already
        if step not in progress.completed_steps:
            progress.completed_steps.append(step)
        
        # Move to next step
        next_step = self.get_next_step(step)
        if next_step:
            progress.current_step = next_step
        
        # Check if onboarding is complete
        is_complete = step == OnboardingStep.COMPLETE
        
        # Save to database
        updates = {
            "current_step": progress.current_step.value,
            "completed_steps": [s.value for s in progress.completed_steps],
            "step_data": progress.step_data,
            "is_complete": is_complete
        }
        
        if is_complete:
            updates["completed_at"] = datetime.utcnow()
            # Also mark user as onboarded
            await self._repo.update_user(user_id, onboarding_completed=True)
        
        await self._repo.update_onboarding_progress(user_id, **updates)
        
        return {
            "success": True,
            "step": step,
            "next_step": next_step,
            "progress_percentage": self.get_progress_percentage(progress),
            "is_complete": is_complete
        }
    
    async def _process_step_data(
        self,
        step: OnboardingStep,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process and validate step-specific data"""
        
        if step == OnboardingStep.SELFIE:
            selfie_data = SelfieStepData(**data)
            dumped = selfie_data.model_dump()
            # Never persist the raw selfie in the onboarding document
            dumped.pop("image_base64", None)
            return dumped
        
        elif step == OnboardingStep.BODY_TYPE:
            body_data = BodyTypeStepData(**data)
            return body_data.model_dump()
        
        elif step == OnboardingStep.SKIN_TONE:
            skin_data = SkinToneStepData(**data)
            # Determine seasonal color type
            skin_data.seasonal_color_type = self._determine_seasonal_type(
                skin_data.skin_tone,
                skin_data.undertone
            )
            return skin_data.model_dump()
        
        elif step == OnboardingStep.STYLE:
            style_data = StyleStepData(**data)
            return style_data.model_dump()
        
        elif step == OnboardingStep.COMPLETE:
            complete_data = CompleteStepData(**data)
            return complete_data.model_dump()
        
        return data
    
    def _determine_seasonal_type(
        self,
        skin_tone: SkinTone,
        undertone: SkinUndertone
    ) -> str:
        """Determine seasonal color type based on skin tone and undertone"""
        if undertone == SkinUndertone.WARM:
            if skin_tone in [SkinTone.FAIR, SkinTone.LIGHT]:
                return "Spring"
            else:
                return "Autumn"
        else:  # Cool or neutral
            if skin_tone in [SkinTone.FAIR, SkinTone.LIGHT]:
                return "Summer"
            else:
                return "Winter"
    
    async def get_summary(self, user_id: str) -> OnboardingSummary:
        """Get onboarding summary for a user"""
        progress = await self.get_progress(user_id)
        
        summary = OnboardingSummary(user_id=user_id)
        
        # Extract data from completed steps
        if OnboardingStep.SELFIE.value in progress.step_data:
            selfie = progress.step_data[OnboardingStep.SELFIE.value]
            summary.face_shape = selfie.get("face_shape")
        
        if OnboardingStep.BODY_TYPE.value in progress.step_data:
            body = progress.step_data[OnboardingStep.BODY_TYPE.value]
            if body.get("body_type"):
                summary.body_type = BodyType(body["body_type"])
            if body.get("gender"):
                summary.gender = body["gender"]
        
        if OnboardingStep.SKIN_TONE.value in progress.step_data:
            skin = progress.step_data[OnboardingStep.SKIN_TONE.value]
            if skin.get("skin_tone"):
                summary.skin_tone = SkinTone(skin["skin_tone"])
            if skin.get("undertone"):
                summary.undertone = SkinUndertone(skin["undertone"])
            summary.seasonal_type = skin.get("seasonal_color_type")
            
            # Get color recommendations
            if summary.skin_tone and summary.undertone:
                colors = self.get_color_recommendations(
                    summary.skin_tone,
                    summary.undertone
                )
                summary.recommended_colors = colors["recommended"]
                summary.avoid_colors = colors["avoid"]
        
        if OnboardingStep.STYLE.value in progress.step_data:
            style = progress.step_data[OnboardingStep.STYLE.value]
            if style.get("primary_style"):
                summary.primary_style = StylePreference(style["primary_style"])
            if style.get("secondary_styles"):
                summary.secondary_styles = [
                    StylePreference(s) for s in style["secondary_styles"]
                ]
            summary.favorite_colors = style.get("favorite_colors", [])
        
        return summary
    
    def get_color_recommendations(
        self,
        skin_tone: SkinTone,
        undertone: SkinUndertone
    ) -> Dict[str, List[str]]:
        """Get color recommendations based on skin tone and undertone"""
        key = (skin_tone, undertone)
        
        if key in COLOR_RECOMMENDATIONS:
            return COLOR_RECOMMENDATIONS[key]
        
        # Fallback for neutral undertone
        if undertone == SkinUndertone.NEUTRAL:
            # Combine warm and cool recommendations
            warm_key = (skin_tone, SkinUndertone.WARM)
            cool_key = (skin_tone, SkinUndertone.COOL)
            
            warm_colors = COLOR_RECOMMENDATIONS.get(warm_key, {})
            cool_colors = COLOR_RECOMMENDATIONS.get(cool_key, {})
            
            return {
                "recommended": list(set(
                    warm_colors.get("recommended", []) + 
                    cool_colors.get("recommended", [])
                ))[:8],
                "avoid": []  # Neutral can wear most colors
            }
        
        # Default recommendations
        return {
            "recommended": ["navy", "white", "grey", "burgundy", "forest green"],
            "avoid": []
        }
    
    async def analyze_selfie(
        self,
        user_id: str,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a selfie with the face-analysis module and persist the result
        to the user's profile. Failures (no face, bad image) are reported as
        success=False and nothing is stored.
        """
        from app.face_analysis.service import get_face_analysis_service
        from app.face_analysis.schemas import FaceAnalysisInput
        from app.face_analysis.persistence import persist_face_analysis

        response = await get_face_analysis_service().analyze_face(
            FaceAnalysisInput(image_base64=image_base64, image_url=image_url)
        )

        if not response.success:
            return {
                "success": False,
                "face_detected": False,
                "confidence": 0.0,
                "message": response.error or "Face analysis failed",
                "error_code": response.error_code,
            }

        await persist_face_analysis(user_id, response)

        sf = response.skin_features
        return {
            "success": True,
            "face_detected": True,
            "face_shape": response.facial_features.face_shape.value if response.facial_features else None,
            "skin_tone": _DEPTH_TO_TONE.get(sf.skin_depth.value),
            "undertone": SkinUndertone(sf.undertone.value),
            "confidence": sf.confidence,
            "message": "Face analysis complete",
        }
    
    async def reset_progress(self, user_id: str):
        """Reset onboarding progress for a user"""
        user_id_obj = PydanticObjectId(user_id) if isinstance(user_id, str) else user_id
        
        # Delete existing progress
        await DbOnboardingProgress.find(DbOnboardingProgress.user_id == user_id_obj).delete()
        
        # Create fresh progress
        await self._repo.create_onboarding_progress(user_id_obj)
        
        # Mark user as not onboarded
        await self._repo.update_user(user_id, onboarding_completed=False)
    
    async def skip_to_step(self, user_id: str, step: OnboardingStep):
        """Skip to a specific step (for testing/admin)"""
        await self._repo.update_onboarding_progress(user_id, current_step=step.value)


# Singleton instance
_service_instance: Optional[OnboardingService] = None


def get_onboarding_service() -> OnboardingService:
    """Get or create the Onboarding service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = OnboardingService()
    return _service_instance

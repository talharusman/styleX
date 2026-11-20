"""
Persistence for face analysis results.

Only successful analyses are stored. The uploaded image itself is never stored;
only the derived skin features, palette and metadata are kept.
"""

import logging
from datetime import datetime

from beanie import PydanticObjectId

from app.database.models import (
    AnalysisResult,
    Season,
    SkinDepth as DbSkinDepth,
    SkinFeatures as DbSkinFeatures,
    Undertone,
    UserProfile,
)
from .schemas import FaceAnalysisResponse

logger = logging.getLogger(__name__)


async def persist_face_analysis(user_id: str, response: FaceAnalysisResponse) -> None:
    """Save a successful analysis: update the profile's skin features and log the result."""
    if not response.success:
        raise ValueError("Refusing to persist a failed face analysis")

    uid = PydanticObjectId(user_id)
    sf = response.skin_features

    db_skin = DbSkinFeatures(
        undertone=Undertone(sf.undertone.value),
        depth=DbSkinDepth(sf.skin_depth.value),
        skin_depth=DbSkinDepth(sf.skin_depth.value),
        season=Season(sf.seasonal_type.value),
        seasonal_type=Season(sf.seasonal_type.value),
        lab_l=sf.lab_l,
        lab_a=sf.lab_a,
        lab_b=sf.lab_b,
        skin_rgb=list(sf.skin_rgb),
        confidence_score=sf.confidence,
    )

    profile = await UserProfile.find_one(UserProfile.user_id == uid)
    if profile is None:
        profile = UserProfile(user_id=uid)
        await profile.insert()

    recs = response.color_recommendations
    updates = {
        "skin_features": db_skin.model_dump(mode="json"),
        "updated_at": datetime.utcnow(),
    }
    if recs is not None:
        updates["style_preferences.recommended_colors"] = list(recs.best_colors)
        updates["style_preferences.avoid_colors"] = list(recs.avoid_colors)
    await profile.update({"$set": updates})

    await AnalysisResult(
        user_id=uid,
        analysis_type="face",
        results=response.model_dump(mode="json", exclude={"success", "error", "error_code"}),
        confidence_score=sf.confidence,
        processing_time_ms=response.processing_time_ms,
    ).insert()

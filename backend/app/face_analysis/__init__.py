"""
Face Analysis Module

Handles skin feature extraction from face images.
Provides color recommendations based on skin tone analysis.
"""

from .router import router
from .service import FaceAnalysisService, get_face_analysis_service
from .schemas import (
    FaceAnalysisInput,
    FaceAnalysisResponse,
    SkinFeatures,
    FacialFeatures,
    ColorRecommendations,
    SkinUndertone,
    SkinDepth,
    SeasonalType,
    FaceShape
)

__all__ = [
    "router",
    "FaceAnalysisService",
    "get_face_analysis_service",
    "FaceAnalysisInput",
    "FaceAnalysisResponse",
    "SkinFeatures",
    "FacialFeatures",
    "ColorRecommendations",
    "SkinUndertone",
    "SkinDepth",
    "SeasonalType",
    "FaceShape"
]

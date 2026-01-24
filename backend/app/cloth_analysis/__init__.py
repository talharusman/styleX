"""
Cloth Analysis Module.

Handles clothing feature extraction from images.
Optimized for 4GB RTX 3050 GPU with FP16 precision.

Features extracted:
- Colors: Dominant colors using KMeans clustering
- Design: Pattern detection (plain, stripes, checks, etc.)
- Gender: Male, female, or unisex classification
- Category: Garment type (shirt, pants, dress, etc.)
- Weather: Seasonal suitability (summer, winter, etc.)
- Style: Casual, formal, sporty, etc.
- Fabric: Fabric type (optional for MVP)
- Formality: Formality level (1-5 scale)

Usage:
    from app.cloth_analysis import router
    from app.cloth_analysis.service import analyze_clothing
    from app.cloth_analysis.schemas import ClothInput, ClothAnalysisResponse
"""

from .router import router
from .schemas import (
    ClothInput,
    ClothFeatures,
    ClothAnalysisResponse,
    ColorInfo,
    DesignPattern,
    ClothingCategory,
    WeatherType,
    StyleType,
    FabricType,
)
from .service import (
    ClothAnalysisService,
    get_cloth_analysis_service,
    analyze_clothing,
)


__all__ = [
    # Router
    "router",
    # Schemas
    "ClothInput",
    "ClothFeatures",
    "ClothAnalysisResponse",
    "ColorInfo",
    "DesignPattern",
    "ClothingCategory",
    "WeatherType",
    "StyleType",
    "FabricType",
    # Service
    "ClothAnalysisService",
    "get_cloth_analysis_service",
    "analyze_clothing",
]

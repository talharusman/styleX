"""
Cloth Feature Extractors.

This module provides all clothing feature extractors optimized for 4GB RTX 3050 GPU.

Features:
- Color: OpenCV + KMeans clustering (CPU-based)
- Design: MobileNetV3-Small (GPU, FP16)
- Gender: MobileNetV3-Small (GPU, FP16)
- Category: MobileNetV3-Small (GPU, FP16)
- Weather: Rule-based from category (CPU)
- Style: CLIP zero-shot or CNN fallback (GPU, FP16)
- Fabric: Heuristic-based (CPU, optional for MVP)
- Formality: Rule-based from style+category (CPU)
- Confidence: Weighted score aggregation (CPU)
"""

from .color_extractor import (
    ColorExtractor,
    extract_colors,
    get_color_extractor,
)

from .design_extractor import (
    DesignExtractor,
    extract_design,
    get_design_extractor,
)

from .category_extractor import (
    CategoryExtractor,
    extract_category,
    get_category_extractor,
)

from .weather_extractor import (
    WeatherExtractor,
    extract_weather,
    get_weather_extractor,
)

from .style_extractor import (
    StyleExtractor,
    extract_style,
    get_style_extractor,
)

from .fabric_extractor import (
    FabricExtractor,
    extract_fabric,
    get_fabric_extractor,
)

from .formality_extractor import (
    FormalityExtractor,
    extract_formality,
    get_formality_extractor,
)

from .confidence_scorer import (
    ConfidenceScorer,
    calculate_overall_confidence,
    get_confidence_scorer,
)


__all__ = [
    # Color
    "ColorExtractor",
    "extract_colors",
    "get_color_extractor",
    # Design
    "DesignExtractor",
    "extract_design",
    "get_design_extractor",
    # Category
    "CategoryExtractor",
    "extract_category",
    "get_category_extractor",
    # Weather
    "WeatherExtractor",
    "extract_weather",
    "get_weather_extractor",
    # Style
    "StyleExtractor",
    "extract_style",
    "get_style_extractor",
    # Fabric
    "FabricExtractor",
    "extract_fabric",
    "get_fabric_extractor",
    # Formality
    "FormalityExtractor",
    "extract_formality",
    "get_formality_extractor",
    # Confidence
    "ConfidenceScorer",
    "calculate_overall_confidence",
    "get_confidence_scorer",
]

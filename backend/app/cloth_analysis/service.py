"""
Clothing Analysis Service.
Orchestrates all clothing feature extractors for complete analysis.
Optimized for 4GB RTX 3050 GPU with FP16 precision.
"""

import time
import logging
from typing import Optional

from .schemas import (
    ClothInput,
    ClothFeatures,
    ClothAnalysisResponse,
    FabricType,
)
from .utils import load_image, clear_gpu_memory

from .extractors.color_extractor import extract_colors
from .extractors.design_extractor import extract_design
from .extractors.category_extractor import extract_category
from .extractors.weather_extractor import extract_weather
from .extractors.style_extractor import extract_style
from .extractors.fabric_extractor import extract_fabric
from .extractors.formality_extractor import extract_formality
from .extractors.confidence_scorer import calculate_overall_confidence

logger = logging.getLogger(__name__)


class ClothAnalysisService:
    """
    Main service for clothing feature extraction.
    Orchestrates all extractors and combines results.
    
    Optimized for:
    - 4GB RTX 3050 GPU
    - FP16 precision for all PyTorch models
    - 224x224 image input size
    - Batch size = 1
    """
    
    def __init__(self):
        """Initialize the clothing analysis service."""
        logger.info("ClothAnalysisService initialized")
    
    async def analyze(
        self,
        input_data: ClothInput,
        use_clip: bool = True
    ) -> ClothAnalysisResponse:
        """
        Perform complete clothing analysis on an image.
        
        Args:
            input_data: Input containing image base64 or URL
            use_clip: Whether to use CLIP for style classification
            
        Returns:
            ClothAnalysisResponse with all extracted features
        """
        start_time = time.time()
        
        try:
            # Load image
            image = load_image(
                image_base64=input_data.image_base64,
                image_url=input_data.image_url
            )
            
            # Extract all features (pass base64 for RGBA color handling)
            features = await self._extract_all_features(
                image, 
                use_clip,
                image_base64=input_data.image_base64
            )
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Clothing analysis completed in {processing_time_ms:.2f}ms")
            
            return ClothAnalysisResponse(
                success=True,
                features=features,
                error=None,
                processing_time_ms=round(processing_time_ms, 2)
            )
            
        except ValueError as e:
            logger.error(f"Input validation error: {e}")
            return ClothAnalysisResponse(
                success=False,
                features=None,
                error=str(e),
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            return ClothAnalysisResponse(
                success=False,
                features=None,
                error=f"Analysis failed: {str(e)}",
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
        finally:
            # Clean up GPU memory
            clear_gpu_memory()
    
    async def _extract_all_features(
        self,
        image,
        use_clip: bool = True,
        image_base64: str = None
    ) -> ClothFeatures:
        """
        Extract all clothing features from an image.
        
        Args:
            image: Input image in BGR format (numpy array)
            use_clip: Whether to use CLIP for style
            image_base64: Original base64 data for RGBA color extraction
            
        Returns:
            ClothFeatures object with all extracted features
        """
        # 1. Extract colors (CPU-based, no GPU needed)
        # Pass base64 for proper RGBA handling
        logger.debug("Extracting colors...")
        colors = extract_colors(image, image_base64=image_base64)
        
        # 2. Extract category (GPU)
        logger.debug("Extracting category...")
        category, category_conf = extract_category(image)
        
        # 3. Extract design pattern (GPU)
        logger.debug("Extracting design pattern...")
        design, design_conf = extract_design(image)
        
        # 4. Extract style (GPU, possibly CLIP)
        logger.debug("Extracting style...")
        style, style_conf = extract_style(image, use_clip=use_clip)
        
        # 5. Derive weather from category (CPU)
        logger.debug("Deriving weather...")
        fabric = FabricType.UNKNOWN  # MVP: fabric not reliably detected
        weather, weather_conf = extract_weather(category, fabric)
        
        # 6. Extract fabric (CPU, heuristic-based in MVP)
        logger.debug("Extracting fabric hint...")
        fabric, fabric_conf = extract_fabric(image, category)
        
        # 7. Derive formality from style and category (CPU)
        logger.debug("Deriving formality...")
        formality, formality_conf = extract_formality(style, category)
        
        # 8. Calculate overall confidence
        feature_confidences = {
            "color": 0.9 if colors else 0.0,  # Colors always detected
            "design": design_conf,
            "category": category_conf,
            "weather": weather_conf,
            "style": style_conf,
            "fabric": fabric_conf,
            "formality": formality_conf,
        }
        overall_conf = calculate_overall_confidence(feature_confidences)
        
        # Build result
        features = ClothFeatures(
            dominant_colors=colors,
            design_pattern=design,
            design_confidence=round(design_conf, 4),
            category=category,
            category_confidence=round(category_conf, 4),
            weather=weather,
            weather_confidence=round(weather_conf, 4),
            style=style,
            style_confidence=round(style_conf, 4),
            fabric=fabric,
            fabric_confidence=round(fabric_conf, 4),
            formality_level=formality,
            formality_confidence=round(formality_conf, 4),
            overall_confidence=round(overall_conf, 4),
        )
        
        return features
    
    def analyze_sync(
        self,
        input_data: ClothInput,
        use_clip: bool = True
    ) -> ClothAnalysisResponse:
        """
        Synchronous version of analyze for non-async contexts.
        
        Args:
            input_data: Input containing image base64 or URL
            use_clip: Whether to use CLIP for style classification
            
        Returns:
            ClothAnalysisResponse with all extracted features
        """
        import asyncio
        return asyncio.run(self.analyze(input_data, use_clip))


# Singleton service instance
_service: Optional[ClothAnalysisService] = None


def get_cloth_analysis_service() -> ClothAnalysisService:
    """Get or create the cloth analysis service singleton."""
    global _service
    if _service is None:
        _service = ClothAnalysisService()
    return _service


async def analyze_clothing(
    input_data: ClothInput,
    use_clip: bool = True
) -> ClothAnalysisResponse:
    """
    Convenience function to analyze clothing.
    
    Args:
        input_data: Input containing image base64 or URL
        use_clip: Whether to use CLIP for style classification
        
    Returns:
        ClothAnalysisResponse with all extracted features
    """
    service = get_cloth_analysis_service()
    return await service.analyze(input_data, use_clip)

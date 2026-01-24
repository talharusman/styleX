"""
Gender Classification for Clothing.
Uses MobileNetV3-Small for lightweight classification.
Optimized for 4GB RTX 3050 GPU with FP16 precision.
"""

import torch
import torch.nn as nn
from torchvision import models
from typing import Tuple
import numpy as np
import logging

from ..schemas import GenderType
from ..utils import (
    preprocess_image_pytorch,
    get_device,
    ensure_model_on_device,
    run_inference,
    softmax_to_confidence,
    model_cache,
    IMAGE_SIZE
)

logger = logging.getLogger(__name__)

# Gender labels in order
GENDER_LABELS = [
    GenderType.MALE,
    GenderType.FEMALE,
    GenderType.UNISEX,
]

MODEL_CACHE_KEY = "gender_extractor_model"


class GenderClassifier(nn.Module):
    """
    Lightweight gender classifier based on MobileNetV3-Small.
    Classifies clothing as male, female, or unisex.
    """
    
    def __init__(self, num_classes: int = len(GENDER_LABELS), pretrained: bool = True):
        super().__init__()
        
        # Load MobileNetV3-Small backbone
        if pretrained:
            weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
            self.backbone = models.mobilenet_v3_small(weights=weights)
        else:
            self.backbone = models.mobilenet_v3_small(weights=None)
        
        # Replace the classifier head for gender classification
        in_features = self.backbone.classifier[0].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Linear(in_features, 128),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


def _create_gender_model() -> nn.Module:
    """Create and initialize the gender model."""
    model = GenderClassifier(num_classes=len(GENDER_LABELS), pretrained=True)
    model = ensure_model_on_device(model)
    logger.info(f"Gender classification model loaded on {get_device()}")
    return model


def _get_model() -> nn.Module:
    """Get the gender model from cache or create it."""
    model = model_cache.get(MODEL_CACHE_KEY)
    if model is None:
        model = _create_gender_model()
        model_cache.set(MODEL_CACHE_KEY, model)
    return model


class GenderExtractor:
    """
    Extracts gender classification from clothing images.
    Uses MobileNetV3-Small for efficient GPU inference.
    """
    
    def __init__(self):
        """Initialize the gender extractor."""
        self._model = None
        logger.info("GenderExtractor initialized")
    
    @property
    def model(self) -> nn.Module:
        """Lazy load the model on first use."""
        if self._model is None:
            self._model = _get_model()
        return self._model
    
    def extract(self, image: np.ndarray) -> Tuple[GenderType, float]:
        """
        Extract gender classification from a clothing image.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Tuple of (GenderType, confidence_score)
        """
        try:
            # Preprocess image for PyTorch
            input_tensor = preprocess_image_pytorch(image, IMAGE_SIZE)
            
            # Run inference
            with torch.no_grad():
                logits = run_inference(self.model, input_tensor)
            
            # Get prediction and confidence
            class_idx, confidence = softmax_to_confidence(logits)
            
            # Map to gender type
            if 0 <= class_idx < len(GENDER_LABELS):
                gender = GENDER_LABELS[class_idx]
            else:
                gender = GenderType.UNISEX
                confidence = 0.5
            
            logger.debug(f"Detected gender: {gender.value} ({confidence:.2%})")
            return gender, confidence
            
        except Exception as e:
            logger.error(f"Error extracting gender: {e}")
            return GenderType.UNISEX, 0.0
    
    def apply_heuristics(
        self,
        image: np.ndarray,
        detected_colors: list,
        detected_category: str
    ) -> Tuple[GenderType, float]:
        """
        Apply color and category heuristics to refine gender prediction.
        
        Args:
            image: Input image
            detected_colors: List of detected colors
            detected_category: Detected clothing category
            
        Returns:
            Tuple of (GenderType, confidence_adjustment)
        """
        # Color-based heuristics
        color_names = [c.name.lower() if hasattr(c, 'name') else str(c).lower() 
                       for c in detected_colors[:3]]
        
        female_colors = {'pink', 'coral', 'purple', 'lavender', 'rose'}
        male_colors = {'navy', 'dark_blue', 'olive', 'maroon', 'dark_green'}
        
        female_score = sum(1 for c in color_names if c in female_colors)
        male_score = sum(1 for c in color_names if c in male_colors)
        
        # Category-based heuristics
        category = detected_category.lower() if detected_category else ""
        
        female_categories = {'dress', 'skirt', 'blouse', 'romper'}
        male_categories = set()  # Most categories are unisex
        
        if category in female_categories:
            female_score += 2
        if category in male_categories:
            male_score += 2
        
        # Determine gender based on scores
        if female_score > male_score and female_score >= 2:
            return GenderType.FEMALE, 0.1
        elif male_score > female_score and male_score >= 2:
            return GenderType.MALE, 0.1
        else:
            return GenderType.UNISEX, 0.0


# Singleton instance
_gender_extractor: GenderExtractor = None


def get_gender_extractor() -> GenderExtractor:
    """Get or create the gender extractor singleton."""
    global _gender_extractor
    if _gender_extractor is None:
        _gender_extractor = GenderExtractor()
    return _gender_extractor


def extract_gender(image: np.ndarray) -> Tuple[GenderType, float]:
    """
    Convenience function to extract gender from an image.
    
    Args:
        image: Input image in BGR format
        
    Returns:
        Tuple of (GenderType, confidence_score)
    """
    extractor = get_gender_extractor()
    return extractor.extract(image)

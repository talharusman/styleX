"""
Design Pattern Extraction.
Uses MobileNetV3-Small pretrained model with custom classification head.
Optimized for 4GB RTX 3050 GPU with FP16 precision.
"""

import torch
import torch.nn as nn
from torchvision import models
from typing import Tuple
import numpy as np
import logging

from ..schemas import DesignPattern
from ..utils import (
    preprocess_image_pytorch,
    get_device,
    get_dtype,
    ensure_model_on_device,
    run_inference,
    softmax_to_confidence,
    model_cache,
    IMAGE_SIZE
)

logger = logging.getLogger(__name__)

# Design pattern labels in order
DESIGN_LABELS = [
    DesignPattern.PLAIN,
    DesignPattern.STRIPES,
    DesignPattern.CHECKS,
    DesignPattern.POLKA_DOT,
    DesignPattern.FLORAL,
    DesignPattern.GEOMETRIC,
    DesignPattern.ABSTRACT,
    DesignPattern.ANIMAL_PRINT,
    DesignPattern.CAMO,
    DesignPattern.TIE_DYE,
]

MODEL_CACHE_KEY = "design_extractor_model"


class DesignPatternClassifier(nn.Module):
    """
    Lightweight design pattern classifier based on MobileNetV3-Small.
    Optimized for low VRAM usage with FP16 support.
    """
    
    def __init__(self, num_classes: int = len(DESIGN_LABELS), pretrained: bool = True):
        super().__init__()
        
        # Load MobileNetV3-Small backbone (very lightweight ~2.5M params)
        if pretrained:
            weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
            self.backbone = models.mobilenet_v3_small(weights=weights)
        else:
            self.backbone = models.mobilenet_v3_small(weights=None)
        
        # Replace the classifier head
        in_features = self.backbone.classifier[0].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


def _create_design_model() -> nn.Module:
    """Create and initialize the design pattern model."""
    model = DesignPatternClassifier(num_classes=len(DESIGN_LABELS), pretrained=True)
    model = ensure_model_on_device(model)
    logger.info(f"Design pattern model loaded on {get_device()}")
    return model


def _get_model() -> nn.Module:
    """Get the design pattern model from cache or create it."""
    model = model_cache.get(MODEL_CACHE_KEY)
    if model is None:
        model = _create_design_model()
        model_cache.set(MODEL_CACHE_KEY, model)
    return model


class DesignExtractor:
    """
    Extracts design patterns from clothing images.
    Uses MobileNetV3-Small for efficient GPU inference.
    """
    
    def __init__(self):
        """Initialize the design extractor."""
        self._model = None
        logger.info("DesignExtractor initialized")
    
    @property
    def model(self) -> nn.Module:
        """Lazy load the model on first use."""
        if self._model is None:
            self._model = _get_model()
        return self._model
    
    def extract(self, image: np.ndarray) -> Tuple[DesignPattern, float]:
        """
        Extract design pattern from a clothing image.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Tuple of (DesignPattern, confidence_score)
        """
        try:
            # Preprocess image for PyTorch
            input_tensor = preprocess_image_pytorch(image, IMAGE_SIZE)
            
            # Run inference
            with torch.no_grad():
                logits = run_inference(self.model, input_tensor)
            
            # Get prediction and confidence
            class_idx, confidence = softmax_to_confidence(logits)
            
            # Map to design pattern
            if 0 <= class_idx < len(DESIGN_LABELS):
                pattern = DESIGN_LABELS[class_idx]
            else:
                pattern = DesignPattern.PLAIN
                confidence = 0.5
            
            logger.debug(f"Detected design pattern: {pattern.value} ({confidence:.2%})")
            return pattern, confidence
            
        except Exception as e:
            logger.error(f"Error extracting design pattern: {e}")
            return DesignPattern.PLAIN, 0.0
    
    def analyze_texture_variance(self, image: np.ndarray) -> float:
        """
        Analyze texture variance to help distinguish plain vs patterned.
        Higher variance suggests patterns.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Variance score (0-1), higher = more pattern
        """
        import cv2
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize to standard size
        gray = cv2.resize(gray, IMAGE_SIZE)
        
        # Calculate Laplacian variance (edge detection)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()
        
        # Normalize to 0-1 range (empirically determined thresholds)
        # Low variance (< 100) = plain, High variance (> 2000) = highly patterned
        normalized = min(1.0, variance / 2000)
        
        return normalized


# Singleton instance
_design_extractor: DesignExtractor = None


def get_design_extractor() -> DesignExtractor:
    """Get or create the design extractor singleton."""
    global _design_extractor
    if _design_extractor is None:
        _design_extractor = DesignExtractor()
    return _design_extractor


def extract_design(image: np.ndarray) -> Tuple[DesignPattern, float]:
    """
    Convenience function to extract design pattern from an image.
    
    Args:
        image: Input image in BGR format
        
    Returns:
        Tuple of (DesignPattern, confidence_score)
    """
    extractor = get_design_extractor()
    return extractor.extract(image)

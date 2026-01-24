"""
Style Classification for Clothing.
Uses CLIP for zero-shot style classification or lightweight CNN fallback.
Optimized for 4GB RTX 3050 GPU with FP16 precision.
"""

import torch
import torch.nn as nn
from torchvision import models
from typing import Tuple, List, Optional
import numpy as np
import logging

from ..schemas import StyleType
from ..utils import (
    preprocess_image_pytorch,
    preprocess_image_pil,
    get_device,
    get_dtype,
    ensure_model_on_device,
    run_inference,
    softmax_to_confidence,
    model_cache,
    IMAGE_SIZE
)

logger = logging.getLogger(__name__)

# Style labels for classification
STYLE_LABELS = [
    StyleType.CASUAL,
    StyleType.FORMAL,
    StyleType.BUSINESS,
    StyleType.SPORTY,
    StyleType.PARTY,
    StyleType.BOHEMIAN,
    StyleType.STREETWEAR,
    StyleType.VINTAGE,
    StyleType.MINIMALIST,
]

# CLIP-style text prompts for zero-shot classification
STYLE_PROMPTS = {
    StyleType.CASUAL: "casual everyday clothing, relaxed comfortable wear",
    StyleType.FORMAL: "formal elegant clothing, sophisticated dressy attire",
    StyleType.BUSINESS: "business professional clothing, office work attire",
    StyleType.SPORTY: "sporty athletic clothing, activewear sportswear",
    StyleType.PARTY: "party glamorous clothing, evening cocktail attire",
    StyleType.BOHEMIAN: "bohemian boho clothing, artistic free-spirited wear",
    StyleType.STREETWEAR: "streetwear urban clothing, trendy hip hop style",
    StyleType.VINTAGE: "vintage retro clothing, classic timeless style",
    StyleType.MINIMALIST: "minimalist simple clothing, clean modern design",
}

MODEL_CACHE_KEY = "style_extractor_model"
CLIP_CACHE_KEY = "style_clip_model"


class StyleClassifierCNN(nn.Module):
    """
    Lightweight style classifier based on MobileNetV3-Small.
    Used as fallback when CLIP is not available.
    """
    
    def __init__(self, num_classes: int = len(STYLE_LABELS), pretrained: bool = True):
        super().__init__()
        
        if pretrained:
            weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
            self.backbone = models.mobilenet_v3_small(weights=weights)
        else:
            self.backbone = models.mobilenet_v3_small(weights=None)
        
        in_features = self.backbone.classifier[0].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Linear(in_features, 256),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


def _create_cnn_model() -> nn.Module:
    """Create and initialize the CNN style model."""
    model = StyleClassifierCNN(num_classes=len(STYLE_LABELS), pretrained=True)
    model = ensure_model_on_device(model)
    logger.info(f"Style CNN model loaded on {get_device()}")
    return model


def _load_clip_model():
    """
    Attempt to load CLIP model for zero-shot classification.
    Returns None if CLIP is not available (will use CNN fallback).
    """
    try:
        # Try to import and load lightweight CLIP
        import clip
        
        device = get_device()
        # Use ViT-B/32 - smallest CLIP model (~340MB)
        model, preprocess = clip.load("ViT-B/32", device=device)
        
        if torch.cuda.is_available():
            model = model.half()  # FP16 for GPU
        
        model.eval()
        logger.info("CLIP model loaded successfully for zero-shot style classification")
        return model, preprocess
        
    except ImportError:
        logger.warning("CLIP not available, using CNN fallback for style classification")
        return None
    except Exception as e:
        logger.warning(f"Failed to load CLIP: {e}, using CNN fallback")
        return None


class StyleExtractor:
    """
    Extracts style classification from clothing images.
    Uses CLIP for zero-shot classification or CNN fallback.
    """
    
    def __init__(self, use_clip: bool = True):
        """
        Initialize the style extractor.
        
        Args:
            use_clip: Whether to attempt using CLIP for zero-shot classification
        """
        self._cnn_model = None
        self._clip_model = None
        self._clip_preprocess = None
        self._clip_available = False
        self._use_clip = use_clip
        self._text_features = None
        
        logger.info("StyleExtractor initialized")
    
    @property
    def cnn_model(self) -> nn.Module:
        """Lazy load CNN model."""
        if self._cnn_model is None:
            cached = model_cache.get(MODEL_CACHE_KEY)
            if cached is not None:
                self._cnn_model = cached
            else:
                self._cnn_model = _create_cnn_model()
                model_cache.set(MODEL_CACHE_KEY, self._cnn_model)
        return self._cnn_model
    
    def _init_clip(self):
        """Initialize CLIP model if available."""
        if not self._use_clip or self._clip_model is not None:
            return
        
        cached = model_cache.get(CLIP_CACHE_KEY)
        if cached is not None:
            self._clip_model, self._clip_preprocess = cached
            self._clip_available = True
        else:
            result = _load_clip_model()
            if result is not None:
                self._clip_model, self._clip_preprocess = result
                self._clip_available = True
                model_cache.set(CLIP_CACHE_KEY, result)
                
                # Pre-compute text features for all styles
                self._compute_text_features()
    
    def _compute_text_features(self):
        """Pre-compute CLIP text features for all style prompts."""
        if not self._clip_available:
            return
        
        try:
            import clip
            
            device = get_device()
            text_inputs = [STYLE_PROMPTS[style] for style in STYLE_LABELS]
            text_tokens = clip.tokenize(text_inputs).to(device)
            
            with torch.no_grad():
                self._text_features = self._clip_model.encode_text(text_tokens)
                self._text_features /= self._text_features.norm(dim=-1, keepdim=True)
            
            logger.debug("Pre-computed CLIP text features for styles")
            
        except Exception as e:
            logger.warning(f"Failed to compute CLIP text features: {e}")
            self._clip_available = False
    
    def extract(self, image: np.ndarray) -> Tuple[StyleType, float]:
        """
        Extract style classification from a clothing image.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Tuple of (StyleType, confidence_score)
        """
        try:
            # Try CLIP zero-shot first
            self._init_clip()
            if self._clip_available and self._text_features is not None:
                return self._extract_with_clip(image)
            
            # Fall back to CNN
            return self._extract_with_cnn(image)
            
        except Exception as e:
            logger.error(f"Error extracting style: {e}")
            return StyleType.CASUAL, 0.0
    
    def _extract_with_clip(self, image: np.ndarray) -> Tuple[StyleType, float]:
        """Extract style using CLIP zero-shot classification."""
        try:
            import cv2
            from PIL import Image
            
            # Convert BGR to RGB PIL Image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            # Preprocess and encode image
            device = get_device()
            image_input = self._clip_preprocess(pil_image).unsqueeze(0).to(device)
            
            if torch.cuda.is_available():
                image_input = image_input.half()
            
            with torch.no_grad():
                image_features = self._clip_model.encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                
                # Calculate similarity with text features
                similarity = (100.0 * image_features @ self._text_features.T).softmax(dim=-1)
                
                # Get best match
                confidence, class_idx = similarity[0].max(dim=0)
                
                style = STYLE_LABELS[class_idx.item()]
                conf_value = confidence.item()
            
            logger.debug(f"CLIP detected style: {style.value} ({conf_value:.2%})")
            return style, conf_value
            
        except Exception as e:
            logger.warning(f"CLIP inference failed: {e}, falling back to CNN")
            return self._extract_with_cnn(image)
    
    def _extract_with_cnn(self, image: np.ndarray) -> Tuple[StyleType, float]:
        """Extract style using CNN classifier."""
        input_tensor = preprocess_image_pytorch(image, IMAGE_SIZE)
        
        with torch.no_grad():
            logits = run_inference(self.cnn_model, input_tensor)
        
        class_idx, confidence = softmax_to_confidence(logits)
        
        if 0 <= class_idx < len(STYLE_LABELS):
            style = STYLE_LABELS[class_idx]
        else:
            style = StyleType.CASUAL
            confidence = 0.5
        
        logger.debug(f"CNN detected style: {style.value} ({confidence:.2%})")
        return style, confidence


# Singleton instance
_style_extractor: StyleExtractor = None


def get_style_extractor(use_clip: bool = True) -> StyleExtractor:
    """Get or create the style extractor singleton."""
    global _style_extractor
    if _style_extractor is None:
        _style_extractor = StyleExtractor(use_clip=use_clip)
    return _style_extractor


def extract_style(image: np.ndarray, use_clip: bool = True) -> Tuple[StyleType, float]:
    """
    Convenience function to extract style from an image.
    
    Args:
        image: Input image in BGR format
        use_clip: Whether to use CLIP for zero-shot classification
        
    Returns:
        Tuple of (StyleType, confidence_score)
    """
    extractor = get_style_extractor(use_clip=use_clip)
    return extractor.extract(image)

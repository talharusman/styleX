"""
Clothing Category Classification.
Uses CLIP for zero-shot category detection with CNN fallback.
Optimized for 4GB RTX 3050 GPU with FP16 precision.
"""

import torch
import torch.nn as nn
from torchvision import models
from typing import Tuple, Dict
import numpy as np
import cv2
from PIL import Image
import logging

from ..schemas import ClothingCategory
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

# Category labels with CLIP-friendly descriptions
CATEGORY_PROMPTS: Dict[ClothingCategory, str] = {
    ClothingCategory.TSHIRT: "a t-shirt, casual cotton tee",
    ClothingCategory.SHIRT: "a button-up shirt, collared dress shirt",
    ClothingCategory.BLOUSE: "a blouse, elegant flowy top",
    ClothingCategory.SWEATER: "a sweater, knitted pullover",
    ClothingCategory.HOODIE: "a hoodie, hooded sweatshirt",
    ClothingCategory.TANK_TOP: "a tank top, sleeveless top",
    ClothingCategory.POLO: "a polo shirt, collared t-shirt",
    ClothingCategory.PANTS: "pants, trousers",
    ClothingCategory.JEANS: "jeans, denim pants",
    ClothingCategory.SHORTS: "shorts, short pants",
    ClothingCategory.SKIRT: "a skirt",
    ClothingCategory.LEGGINGS: "leggings, tight-fitting pants",
    ClothingCategory.DRESS: "a dress",
    ClothingCategory.JUMPSUIT: "a jumpsuit, one-piece outfit",
    ClothingCategory.ROMPER: "a romper, short jumpsuit",
    ClothingCategory.JACKET: "a jacket",
    ClothingCategory.COAT: "a coat, long outerwear",
    ClothingCategory.BLAZER: "a blazer, formal jacket",
    ClothingCategory.CARDIGAN: "a cardigan, open-front sweater",
    ClothingCategory.VEST: "a vest, sleeveless jacket",
    ClothingCategory.SWIMWEAR: "swimwear, bikini or swimsuit",
    ClothingCategory.ACTIVEWEAR: "activewear, sports clothing",
}

CATEGORY_LABELS = list(CATEGORY_PROMPTS.keys())

MODEL_CACHE_KEY = "category_extractor_model"
CLIP_CACHE_KEY = "category_clip_model"


def _load_clip_model():
    """Load CLIP model for zero-shot category classification."""
    try:
        import clip
        
        device = get_device()
        model, preprocess = clip.load("ViT-B/32", device=device)
        
        if torch.cuda.is_available():
            model = model.half()
        
        model.eval()
        logger.info("CLIP model loaded for category classification")
        return model, preprocess
        
    except ImportError:
        logger.warning("CLIP not available, using CNN fallback")
        return None
    except Exception as e:
        logger.warning(f"Failed to load CLIP: {e}")
        return None


class CategoryClassifier(nn.Module):
    """
    Clothing category classifier based on MobileNetV3-Small.
    Used as fallback when CLIP is not available.
    """
    
    def __init__(self, num_classes: int = len(CATEGORY_LABELS), pretrained: bool = True):
        super().__init__()
        
        if pretrained:
            weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
            self.backbone = models.mobilenet_v3_small(weights=weights)
        else:
            self.backbone = models.mobilenet_v3_small(weights=None)
        
        in_features = self.backbone.classifier[0].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.Hardswish(),
            nn.Dropout(p=0.3),
            nn.Linear(512, 256),
            nn.Hardswish(),
            nn.Dropout(p=0.2),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


def _create_category_model() -> nn.Module:
    """Create and initialize the category model."""
    model = CategoryClassifier(num_classes=len(CATEGORY_LABELS), pretrained=True)
    model = ensure_model_on_device(model)
    logger.info(f"Category CNN model loaded on {get_device()}")
    return model


def _get_model() -> nn.Module:
    """Get the category model from cache or create it."""
    model = model_cache.get(MODEL_CACHE_KEY)
    if model is None:
        model = _create_category_model()
        model_cache.set(MODEL_CACHE_KEY, model)
    return model


class CategoryExtractor:
    """
    Extracts clothing category from images.
    Uses CLIP for zero-shot classification (primary) or MobileNetV3 fallback.
    """
    
    def __init__(self):
        """Initialize the category extractor."""
        self._cnn_model = None
        self._clip_model = None
        self._clip_preprocess = None
        self._clip_available = False
        self._text_features = None
        logger.info("CategoryExtractor initialized")
    
    @property
    def cnn_model(self) -> nn.Module:
        """Lazy load CNN model."""
        if self._cnn_model is None:
            self._cnn_model = _get_model()
        return self._cnn_model
    
    def _init_clip(self):
        """Initialize CLIP model if available."""
        if self._clip_model is not None:
            return
        
        cached = model_cache.get(CLIP_CACHE_KEY)
        if cached is not None:
            self._clip_model, self._clip_preprocess = cached
            self._clip_available = True
            self._compute_text_features()
        else:
            result = _load_clip_model()
            if result is not None:
                self._clip_model, self._clip_preprocess = result
                self._clip_available = True
                model_cache.set(CLIP_CACHE_KEY, result)
                self._compute_text_features()
    
    def _compute_text_features(self):
        """Pre-compute CLIP text features for all categories."""
        if not self._clip_available or self._text_features is not None:
            return
        
        try:
            import clip
            
            device = get_device()
            text_inputs = [f"a photo of {CATEGORY_PROMPTS[cat]}" for cat in CATEGORY_LABELS]
            text_tokens = clip.tokenize(text_inputs).to(device)
            
            with torch.no_grad():
                self._text_features = self._clip_model.encode_text(text_tokens)
                self._text_features /= self._text_features.norm(dim=-1, keepdim=True)
            
            logger.debug("Pre-computed CLIP text features for categories")
            
        except Exception as e:
            logger.warning(f"Failed to compute CLIP text features: {e}")
            self._clip_available = False
    
    def extract(self, image: np.ndarray) -> Tuple[ClothingCategory, float]:
        """
        Extract clothing category from an image using CLIP or CNN fallback.
        
        Args:
            image: Input image in BGR format
            
        Returns:
            Tuple of (ClothingCategory, confidence_score)
        """
        try:
            # Try CLIP first
            self._init_clip()
            if self._clip_available and self._text_features is not None:
                return self._extract_with_clip(image)
            
            # Fall back to CNN
            return self._extract_with_cnn(image)
            
        except Exception as e:
            logger.error(f"Error extracting category: {e}")
            return ClothingCategory.UNKNOWN, 0.0
    
    def _extract_with_clip(self, image: np.ndarray) -> Tuple[ClothingCategory, float]:
        """Extract category using CLIP zero-shot classification."""
        try:
            # Convert BGR to RGB PIL Image
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_image)
            
            device = get_device()
            image_input = self._clip_preprocess(pil_image).unsqueeze(0).to(device)
            
            if torch.cuda.is_available():
                image_input = image_input.half()
            
            with torch.no_grad():
                image_features = self._clip_model.encode_image(image_input)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                
                similarity = (100.0 * image_features @ self._text_features.T).softmax(dim=-1)
                confidence, class_idx = similarity[0].max(dim=0)
                
                category = CATEGORY_LABELS[class_idx.item()]
                conf_value = confidence.item()
            
            logger.debug(f"CLIP detected category: {category.value} ({conf_value:.2%})")
            return category, conf_value
            
        except Exception as e:
            logger.warning(f"CLIP category failed: {e}, using CNN fallback")
            return self._extract_with_cnn(image)
    
    def _extract_with_cnn(self, image: np.ndarray) -> Tuple[ClothingCategory, float]:
        """Extract category using CNN classifier."""
        input_tensor = preprocess_image_pytorch(image, IMAGE_SIZE)
        
        with torch.no_grad():
            logits = run_inference(self.cnn_model, input_tensor)
        
        class_idx, confidence = softmax_to_confidence(logits)
        
        if 0 <= class_idx < len(CATEGORY_LABELS):
            category = CATEGORY_LABELS[class_idx]
        else:
            category = ClothingCategory.UNKNOWN
            confidence = 0.0
        
        logger.debug(f"CNN detected category: {category.value} ({confidence:.2%})")
        return category, confidence
    
    def get_category_group(self, category: ClothingCategory) -> str:
        """
        Get the broad category group for a specific category.
        
        Args:
            category: Clothing category
            
        Returns:
            Category group string ('tops', 'bottoms', 'full_body', 'outerwear', 'other')
        """
        tops = {
            ClothingCategory.TSHIRT, ClothingCategory.SHIRT, ClothingCategory.BLOUSE,
            ClothingCategory.SWEATER, ClothingCategory.HOODIE, ClothingCategory.TANK_TOP,
            ClothingCategory.POLO
        }
        bottoms = {
            ClothingCategory.PANTS, ClothingCategory.JEANS, ClothingCategory.SHORTS,
            ClothingCategory.SKIRT, ClothingCategory.LEGGINGS
        }
        full_body = {
            ClothingCategory.DRESS, ClothingCategory.JUMPSUIT, ClothingCategory.ROMPER
        }
        outerwear = {
            ClothingCategory.JACKET, ClothingCategory.COAT, ClothingCategory.BLAZER,
            ClothingCategory.CARDIGAN, ClothingCategory.VEST
        }
        
        if category in tops:
            return "tops"
        elif category in bottoms:
            return "bottoms"
        elif category in full_body:
            return "full_body"
        elif category in outerwear:
            return "outerwear"
        else:
            return "other"


# Singleton instance
_category_extractor: CategoryExtractor = None


def get_category_extractor() -> CategoryExtractor:
    """Get or create the category extractor singleton."""
    global _category_extractor
    if _category_extractor is None:
        _category_extractor = CategoryExtractor()
    return _category_extractor


def extract_category(image: np.ndarray) -> Tuple[ClothingCategory, float]:
    """
    Convenience function to extract category from an image.
    
    Args:
        image: Input image in BGR format
        
    Returns:
        Tuple of (ClothingCategory, confidence_score)
    """
    extractor = get_category_extractor()
    return extractor.extract(image)

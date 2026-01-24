"""
Utility functions for cloth analysis.
Optimized for 4GB RTX 3050 GPU with FP16 precision.
"""

import cv2
import numpy as np
import torch
import base64
import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)

# GPU Configuration for 4GB VRAM optimization
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_FP16 = torch.cuda.is_available()  # Use FP16 only on GPU
IMAGE_SIZE = (224, 224)  # Standard size for efficient processing
BATCH_SIZE = 1  # Single image inference to save memory


def get_device() -> torch.device:
    """Get the appropriate device for inference."""
    return DEVICE


def is_gpu_available() -> bool:
    """Check if GPU is available."""
    return torch.cuda.is_available()


def get_dtype() -> torch.dtype:
    """Get appropriate dtype for inference (FP16 on GPU, FP32 on CPU)."""
    return torch.float16 if USE_FP16 else torch.float32


def decode_base64_image(base64_string: str) -> np.ndarray:
    """
    Decode a base64 encoded image string to numpy array.
    Handles RGBA images by converting transparent pixels to white background.
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        numpy array in BGR format (OpenCV format)
    """
    try:
        # Remove header if present (data:image/jpeg;base64,...)
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        
        image_data = base64.b64decode(base64_string)
        
        # Use PIL to properly handle RGBA/transparency
        pil_image = Image.open(BytesIO(image_data))
        
        # Handle RGBA images (with transparency)
        if pil_image.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', pil_image.size, (255, 255, 255))
            # Get alpha channel as mask
            alpha = pil_image.split()[3]
            # Paste RGB onto white background using alpha
            background.paste(pil_image.convert('RGB'), mask=alpha)
            pil_image = background
        elif pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert to numpy and BGR for OpenCV
        rgb_array = np.array(pil_image)
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        
        if bgr_array is None:
            raise ValueError("Failed to decode image from base64")
            
        return bgr_array
    except Exception as e:
        logger.error(f"Error decoding base64 image: {e}")
        raise ValueError(f"Invalid base64 image: {e}")


def load_image_from_url(url: str) -> np.ndarray:
    """
    Load an image from URL.
    
    Args:
        url: Image URL
        
    Returns:
        numpy array in BGR format (OpenCV format)
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        image_array = np.frombuffer(response.content, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image from URL")
            
        return image
    except requests.RequestException as e:
        logger.error(f"Error loading image from URL: {e}")
        raise ValueError(f"Failed to load image from URL: {e}")


def preprocess_image_cv2(
    image: np.ndarray,
    target_size: Tuple[int, int] = IMAGE_SIZE
) -> np.ndarray:
    """
    Preprocess image for OpenCV-based processing.
    
    Args:
        image: Input image in BGR format
        target_size: Target size (width, height)
        
    Returns:
        Preprocessed image resized to target size
    """
    if image is None:
        raise ValueError("Input image is None")
    
    # Resize to target size
    resized = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
    
    return resized


def preprocess_image_pytorch(
    image: np.ndarray,
    target_size: Tuple[int, int] = IMAGE_SIZE
) -> torch.Tensor:
    """
    Preprocess image for PyTorch model inference.
    Optimized for 4GB GPU with FP16 precision.
    
    Args:
        image: Input image in BGR format (OpenCV)
        target_size: Target size (width, height)
        
    Returns:
        PyTorch tensor ready for inference [1, 3, H, W]
    """
    # Convert BGR to RGB
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Resize
    resized = cv2.resize(rgb_image, target_size, interpolation=cv2.INTER_AREA)
    
    # Convert to float and normalize to [0, 1]
    normalized = resized.astype(np.float32) / 255.0
    
    # ImageNet normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    normalized = (normalized - mean) / std
    
    # Convert to tensor [H, W, C] -> [C, H, W]
    tensor = torch.from_numpy(normalized.transpose(2, 0, 1))
    
    # Add batch dimension [C, H, W] -> [1, C, H, W]
    tensor = tensor.unsqueeze(0)
    
    # Convert to appropriate dtype and move to device
    dtype = get_dtype()
    tensor = tensor.to(dtype=dtype, device=DEVICE)
    
    return tensor


def preprocess_image_pil(
    image: np.ndarray,
    target_size: Tuple[int, int] = IMAGE_SIZE
) -> Image.Image:
    """
    Preprocess image for PIL-based processing.
    
    Args:
        image: Input image in BGR format (OpenCV)
        target_size: Target size (width, height)
        
    Returns:
        PIL Image in RGB format
    """
    # Convert BGR to RGB
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    
    # Convert to PIL
    pil_image = Image.fromarray(rgb_image)
    
    # Resize
    pil_image = pil_image.resize(target_size, Image.Resampling.LANCZOS)
    
    return pil_image


def load_image(
    image_base64: Optional[str] = None,
    image_url: Optional[str] = None
) -> np.ndarray:
    """
    Load image from either base64 string or URL.
    
    Args:
        image_base64: Base64 encoded image string
        image_url: Image URL
        
    Returns:
        numpy array in BGR format
    """
    if image_base64:
        return decode_base64_image(image_base64)
    elif image_url:
        return load_image_from_url(image_url)
    else:
        raise ValueError("Either image_base64 or image_url must be provided")


def clear_gpu_memory():
    """Clear GPU memory cache."""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


class ModelCache:
    """
    Simple model cache to avoid reloading models.
    Manages memory efficiently for 4GB GPU.
    """
    _instance = None
    _models = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get(self, model_name: str):
        """Get cached model by name."""
        return self._models.get(model_name)
    
    def set(self, model_name: str, model):
        """Cache a model."""
        self._models[model_name] = model
    
    def remove(self, model_name: str):
        """Remove model from cache and free memory."""
        if model_name in self._models:
            del self._models[model_name]
            clear_gpu_memory()
    
    def clear_all(self):
        """Clear all cached models."""
        self._models.clear()
        clear_gpu_memory()


# Global model cache instance
model_cache = ModelCache()


def softmax_to_confidence(logits: torch.Tensor) -> Tuple[int, float]:
    """
    Convert logits to class prediction and confidence score.
    
    Args:
        logits: Model output logits [1, num_classes]
        
    Returns:
        Tuple of (predicted_class_index, confidence_score)
    """
    probabilities = torch.softmax(logits, dim=-1)
    confidence, predicted_class = torch.max(probabilities, dim=-1)
    
    return predicted_class.item(), confidence.item()


def ensure_model_on_device(model: torch.nn.Module) -> torch.nn.Module:
    """
    Ensure model is on correct device with appropriate precision.
    
    Args:
        model: PyTorch model
        
    Returns:
        Model on correct device with FP16 if GPU available
    """
    model = model.to(DEVICE)
    
    if USE_FP16:
        model = model.half()
    
    model.eval()
    
    return model


@torch.no_grad()
def run_inference(
    model: torch.nn.Module,
    input_tensor: torch.Tensor
) -> torch.Tensor:
    """
    Run inference with memory optimization.
    
    Args:
        model: PyTorch model
        input_tensor: Input tensor
        
    Returns:
        Model output
    """
    try:
        output = model(input_tensor)
        return output
    finally:
        # Help garbage collection
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

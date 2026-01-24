"""
Color Extraction from Clothing.
Uses OpenCV with KMeans clustering to detect dominant colors.
Handles RGBA images with transparency properly.
Optimized for 4GB GPU - runs on CPU (no GPU needed for this task).
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Optional
from sklearn.cluster import KMeans
from PIL import Image
import logging

from ..schemas import ColorInfo
from ..utils import IMAGE_SIZE

logger = logging.getLogger(__name__)


# Extended color mapping with HSV ranges for better accuracy
# Format: color_name -> (H_min, H_max, S_min, S_max, V_min, V_max)
HSV_COLOR_RANGES = {
    # Achromatic colors (low saturation)
    "white": (0, 180, 0, 30, 200, 255),
    "light_gray": (0, 180, 0, 30, 150, 200),
    "gray": (0, 180, 0, 30, 80, 150),
    "dark_gray": (0, 180, 0, 30, 40, 80),
    "black": (0, 180, 0, 30, 0, 40),
    
    # Chromatic colors
    "red": (0, 10, 50, 255, 50, 255),
    "red2": (170, 180, 50, 255, 50, 255),  # Red wraps around
    "orange": (10, 25, 50, 255, 50, 255),
    "yellow": (25, 35, 50, 255, 50, 255),
    "lime": (35, 50, 50, 255, 50, 255),
    "green": (50, 80, 50, 255, 50, 255),
    "cyan": (80, 100, 50, 255, 50, 255),
    "blue": (100, 130, 50, 255, 50, 255),
    "purple": (130, 150, 50, 255, 50, 255),
    "magenta": (150, 170, 50, 255, 50, 255),
    
    # Special colors
    "pink": (150, 180, 20, 150, 150, 255),
    "beige": (15, 35, 20, 80, 180, 255),
    "cream": (20, 40, 10, 50, 200, 255),
    "brown": (10, 30, 50, 200, 30, 150),
    "tan": (15, 30, 30, 100, 150, 220),
    "navy": (100, 130, 50, 255, 20, 100),
    "maroon": (0, 10, 50, 200, 30, 100),
    "olive": (35, 60, 30, 150, 50, 150),
    "teal": (80, 100, 50, 200, 50, 150),
    "coral": (0, 20, 50, 150, 150, 255),
    "gold": (20, 35, 100, 255, 150, 255),
    "silver": (0, 180, 0, 20, 150, 220),
    "lavender": (130, 160, 20, 80, 150, 255),
    "burgundy": (0, 10, 80, 255, 30, 100),
}


def rgb_to_hex(rgb: List[int]) -> str:
    """Convert RGB values to hex color code."""
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))


def get_color_name_hsv(rgb: List[int]) -> str:
    """
    Get color name using HSV color space for better accuracy.
    
    Args:
        rgb: [R, G, B] values (0-255)
        
    Returns:
        Color name string
    """
    # Convert RGB to HSV
    rgb_pixel = np.uint8([[rgb]])
    hsv_pixel = cv2.cvtColor(rgb_pixel, cv2.COLOR_RGB2HSV)
    h, s, v = hsv_pixel[0][0]
    
    # Check achromatic colors first (low saturation)
    if s < 30:
        if v > 200:
            return "white"
        elif v > 150:
            return "light gray"
        elif v > 80:
            return "gray"
        elif v > 40:
            return "dark gray"
        else:
            return "black"
    
    # Check chromatic colors
    for color_name, (h_min, h_max, s_min, s_max, v_min, v_max) in HSV_COLOR_RANGES.items():
        if color_name in ["white", "light_gray", "gray", "dark_gray", "black"]:
            continue
        if h_min <= h <= h_max and s_min <= s <= s_max and v_min <= v <= v_max:
            # Handle red2 (wraps around)
            if color_name == "red2":
                return "red"
            return color_name.replace("_", " ")
    
    # Fallback based on hue
    if h < 10 or h > 170:
        return "red"
    elif h < 25:
        return "orange"
    elif h < 35:
        return "yellow"
    elif h < 80:
        return "green"
    elif h < 100:
        return "cyan"
    elif h < 130:
        return "blue"
    elif h < 150:
        return "purple"
    else:
        return "pink"


def extract_rgba_from_base64(base64_string: str, min_alpha: int = 128) -> Optional[np.ndarray]:
    """
    Extract non-transparent pixels from a base64 encoded RGBA image.
    
    Args:
        base64_string: Base64 encoded image
        min_alpha: Minimum alpha value to consider pixel as non-transparent
        
    Returns:
        RGB pixels as 2D numpy array (N x 3), or None if all transparent
    """
    try:
        from io import BytesIO
        import base64
        
        # Remove header if present
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        
        image_data = base64.b64decode(base64_string)
        img = Image.open(BytesIO(image_data))
        
        # Convert to RGBA to handle transparency
        if img.mode != 'RGBA':
            if img.mode == 'RGB':
                # No transparency - return all pixels
                arr = np.array(img)
                return arr.reshape(-1, 3)
            img = img.convert('RGBA')
        
        arr = np.array(img)
        
        # Get non-transparent pixels
        mask = arr[:, :, 3] >= min_alpha
        if mask.sum() == 0:
            logger.warning("All pixels are transparent in image")
            return None
        
        rgb_pixels = arr[:, :, :3][mask]  # Shape: (N, 3)
        logger.debug(f"Extracted {len(rgb_pixels)} non-transparent pixels from base64")
        return rgb_pixels
        
    except Exception as e:
        logger.warning(f"Error extracting RGBA from base64: {e}")
        return None


def extract_rgba_pixels(image_path_or_array, min_alpha: int = 128) -> Optional[np.ndarray]:
    """
    Extract only non-transparent pixels from an RGBA image.
    
    Args:
        image_path_or_array: Either file path or numpy array
        min_alpha: Minimum alpha value to consider pixel as non-transparent
        
    Returns:
        RGB pixels as 2D numpy array (N x 3), or None if all transparent
    """
    try:
        if isinstance(image_path_or_array, str):
            img = Image.open(image_path_or_array).convert('RGBA')
            arr = np.array(img)
            # Get non-transparent pixels
            mask = arr[:, :, 3] >= min_alpha
            if mask.sum() == 0:
                return None
            rgb_pixels = arr[:, :, :3][mask]  # Shape: (N, 3)
            return rgb_pixels
            
        elif isinstance(image_path_or_array, np.ndarray):
            arr = image_path_or_array
            
            if len(arr.shape) == 3:
                if arr.shape[2] == 4:
                    # BGRA from OpenCV - get non-transparent pixels
                    mask = arr[:, :, 3] >= min_alpha
                    if mask.sum() == 0:
                        return None
                    # Convert BGRA to RGB for the masked pixels
                    bgra_pixels = arr[mask]  # Shape: (N, 4)
                    rgb_pixels = bgra_pixels[:, [2, 1, 0]]  # BGR to RGB
                    return rgb_pixels
                elif arr.shape[2] == 3:
                    # BGR without alpha - convert and reshape
                    rgb_image = cv2.cvtColor(arr, cv2.COLOR_BGR2RGB)
                    rgb_pixels = rgb_image.reshape(-1, 3)  # Shape: (H*W, 3)
                    return rgb_pixels
            elif len(arr.shape) == 2:
                # Grayscale - expand to RGB
                rgb_pixels = np.stack([arr.ravel(), arr.ravel(), arr.ravel()], axis=1)
                return rgb_pixels
        
        return None
            
    except Exception as e:
        logger.warning(f"Error extracting RGBA pixels: {e}")
        return None


class ColorExtractor:
    """
    Extracts dominant colors from clothing images using KMeans clustering.
    Handles transparent backgrounds properly.
    Runs on CPU - no GPU required.
    """
    
    def __init__(self, n_colors: int = 5, min_percentage: float = 5.0):
        """
        Initialize the color extractor.
        
        Args:
            n_colors: Number of dominant colors to extract
            min_percentage: Minimum percentage for a color to be included
        """
        self.n_colors = n_colors
        self.min_percentage = min_percentage
        logger.info(f"ColorExtractor initialized with {n_colors} colors")
    
    def extract(self, image: np.ndarray, image_path: Optional[str] = None, image_base64: Optional[str] = None) -> List[ColorInfo]:
        """
        Extract dominant colors from a clothing image.
        Handles transparent backgrounds by excluding transparent pixels.
        
        Args:
            image: Input image in BGR/BGRA format
            image_path: Optional path for loading RGBA properly
            image_base64: Optional base64 data for RGBA handling
            
        Returns:
            List of ColorInfo objects with dominant colors
        """
        try:
            rgb_pixels = None
            
            # Priority 1: Use base64 for proper RGBA handling
            if image_base64:
                rgb_pixels = extract_rgba_from_base64(image_base64)
            
            # Priority 2: Use file path
            if rgb_pixels is None and image_path:
                rgb_pixels = extract_rgba_pixels(image_path)
            
            # Priority 3: Use numpy array
            if rgb_pixels is None:
                rgb_pixels = extract_rgba_pixels(image)
            
            if rgb_pixels is None or len(rgb_pixels) < 100:
                # Fall back to regular processing
                if len(image.shape) == 3 and image.shape[2] == 4:
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
                else:
                    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                rgb_image = cv2.resize(rgb_image, IMAGE_SIZE)
                rgb_pixels = rgb_image.reshape(-1, 3)
            
            # Limit number of pixels for performance
            if len(rgb_pixels) > 50000:
                indices = np.random.choice(len(rgb_pixels), 50000, replace=False)
                rgb_pixels = rgb_pixels[indices]
            
            # Apply KMeans clustering
            n_clusters = min(self.n_colors, len(rgb_pixels) // 10)
            n_clusters = max(2, n_clusters)
            
            kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10,
                max_iter=100
            )
            kmeans.fit(rgb_pixels)
            
            # Get cluster centers and counts
            centers = kmeans.cluster_centers_.astype(int)
            labels = kmeans.labels_
            
            # Calculate percentage for each color
            unique, counts = np.unique(labels, return_counts=True)
            total_pixels = len(labels)
            
            colors = []
            for idx, count in zip(unique, counts):
                percentage = (count / total_pixels) * 100
                
                # Skip colors below threshold
                if percentage < self.min_percentage:
                    continue
                
                rgb = centers[idx].tolist()
                color_name = get_color_name_hsv(rgb)
                hex_code = rgb_to_hex(rgb)
                
                colors.append(ColorInfo(
                    name=color_name,
                    hex_code=hex_code,
                    rgb=rgb,
                    percentage=round(percentage, 2)
                ))
            
            # Sort by percentage (highest first)
            colors.sort(key=lambda x: x.percentage, reverse=True)
            
            # Merge similar colors
            colors = self._merge_similar_colors(colors)
            
            logger.debug(f"Extracted {len(colors)} dominant colors")
            return colors if colors else [ColorInfo(
                name="unknown",
                hex_code="#808080",
                rgb=[128, 128, 128],
                percentage=100.0
            )]
            
        except Exception as e:
            logger.error(f"Error extracting colors: {e}")
            return [ColorInfo(
                name="unknown",
                hex_code="#808080",
                rgb=[128, 128, 128],
                percentage=100.0
            )]
    
    def _merge_similar_colors(self, colors: List[ColorInfo], threshold: float = 30) -> List[ColorInfo]:
        """Merge colors with similar names or RGB values."""
        if len(colors) <= 1:
            return colors
        
        merged = []
        used = set()
        
        for i, c1 in enumerate(colors):
            if i in used:
                continue
            
            total_pct = c1.percentage
            combined_rgb = [c1.rgb[0] * c1.percentage, 
                           c1.rgb[1] * c1.percentage, 
                           c1.rgb[2] * c1.percentage]
            
            for j, c2 in enumerate(colors[i+1:], i+1):
                if j in used:
                    continue
                
                # Check if same color name or very similar RGB
                same_name = c1.name.lower() == c2.name.lower()
                rgb_dist = np.sqrt(sum((c1.rgb[k] - c2.rgb[k])**2 for k in range(3)))
                
                if same_name or rgb_dist < threshold:
                    used.add(j)
                    total_pct += c2.percentage
                    for k in range(3):
                        combined_rgb[k] += c2.rgb[k] * c2.percentage
            
            # Calculate weighted average RGB
            avg_rgb = [int(combined_rgb[k] / total_pct) for k in range(3)]
            
            merged.append(ColorInfo(
                name=c1.name,
                hex_code=rgb_to_hex(avg_rgb),
                rgb=avg_rgb,
                percentage=round(total_pct, 2)
            ))
        
        return sorted(merged, key=lambda x: x.percentage, reverse=True)


# Singleton instance for reuse
_color_extractor: ColorExtractor = None


def get_color_extractor() -> ColorExtractor:
    """Get or create the color extractor singleton."""
    global _color_extractor
    if _color_extractor is None:
        _color_extractor = ColorExtractor()
    return _color_extractor


def extract_colors(image: np.ndarray, image_path: Optional[str] = None, image_base64: Optional[str] = None) -> List[ColorInfo]:
    """
    Convenience function to extract colors from an image.
    
    Args:
        image: Input image in BGR format
        image_path: Optional path for proper RGBA handling
        image_base64: Optional base64 data for proper RGBA handling
        
    Returns:
        List of ColorInfo objects
    """
    extractor = get_color_extractor()
    return extractor.extract(image, image_path=image_path, image_base64=image_base64)

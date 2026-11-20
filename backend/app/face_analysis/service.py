"""
Face Analysis Service

Orchestrates face detection, skin analysis, and color recommendations.
Uses MediaPipe for face detection and custom algorithms for color analysis.
"""

import time
import logging
import numpy as np
from typing import Optional, Tuple, List
import base64
from io import BytesIO

from .schemas import (
    FaceAnalysisInput, FaceAnalysisResponse,
    SkinFeatures, FacialFeatures, ColorRecommendations,
    SkinUndertone, SkinDepth, SeasonalType, FaceShape
)
from app.config import settings

logger = logging.getLogger(__name__)

MAX_IMAGE_BYTES = 10 * 1024 * 1024   # 10 MB decoded
MAX_IMAGE_SIDE = 1024                # downscale large photos before analysis
MIN_SKIN_PIXELS = 60


class FaceAnalysisError(Exception):
    """Expected, user-facing analysis failure (never persisted as a result)."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _is_public_http_url(url: str) -> bool:
    """Only allow http(s) URLs that resolve to public addresses (SSRF guard)."""
    import ipaddress
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return False
    try:
        for info in socket.getaddrinfo(parsed.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return False
    except (socket.gaierror, ValueError):
        return False
    return True


# Color palettes for different seasonal types
SEASONAL_PALETTES = {
    SeasonalType.SPRING: {
        "best_colors": ["coral", "peach", "warm pink", "golden yellow", "light orange", "aqua", "turquoise"],
        "avoid_colors": ["black", "dark gray", "burgundy", "deep purple", "cool pink"],
        "neutral_colors": ["ivory", "camel", "warm beige", "light brown"],
        "accent_colors": ["bright coral", "clear red", "lime green"],
        "metals": ["gold", "rose gold", "brass"]
    },
    SeasonalType.SUMMER: {
        "best_colors": ["lavender", "dusty rose", "powder blue", "soft pink", "mauve", "slate blue"],
        "avoid_colors": ["orange", "bright yellow", "black", "warm brown"],
        "neutral_colors": ["soft white", "dove gray", "blue-gray", "cocoa"],
        "accent_colors": ["raspberry", "soft fuchsia", "blue-red"],
        "metals": ["silver", "platinum", "white gold"]
    },
    SeasonalType.AUTUMN: {
        "best_colors": ["burnt orange", "olive", "rust", "gold", "terracotta", "warm brown", "teal"],
        "avoid_colors": ["pink", "fuchsia", "bright blue", "silver gray"],
        "neutral_colors": ["cream", "camel", "warm gray", "chocolate"],
        "accent_colors": ["turquoise", "tomato red", "forest green"],
        "metals": ["gold", "brass", "copper", "bronze"]
    },
    SeasonalType.WINTER: {
        "best_colors": ["black", "white", "navy", "true red", "emerald", "royal blue", "fuchsia"],
        "avoid_colors": ["orange", "gold", "beige", "warm brown"],
        "neutral_colors": ["black", "white", "charcoal", "navy"],
        "accent_colors": ["icy pink", "bright blue", "magenta"],
        "metals": ["silver", "platinum", "white gold"]
    }
}


class FaceAnalysisService:
    """Service for analyzing facial features and skin tone"""
    
    def __init__(self):
        self._face_mesh = None
        self._initialized = False
        
    def _ensure_initialized(self):
        """Lazy initialization of MediaPipe"""
        if not self._initialized:
            try:
                import mediapipe as mp
                self._mp_face_mesh = mp.solutions.face_mesh
                self._face_mesh = self._mp_face_mesh.FaceMesh(
                    static_image_mode=True,
                    max_num_faces=1,
                    refine_landmarks=True,
                    min_detection_confidence=0.5
                )
                self._initialized = True
                logger.info("Face analysis initialized successfully")
            except (ImportError, AttributeError) as e:
                # AttributeError: mediapipe installed without the legacy mp.solutions API
                logger.error(f"MediaPipe Face Mesh unavailable: {e}")
                self._face_mesh = None
                self._initialized = True
    
    async def analyze_face(self, input_data: FaceAnalysisInput) -> FaceAnalysisResponse:
        """
        Analyze face image and extract features.
        
        Args:
            input_data: FaceAnalysisInput with image data
            
        Returns:
            FaceAnalysisResponse with skin features and recommendations
        """
        start_time = time.time()
        
        try:
            self._ensure_initialized()
            
            # Load image
            if self._face_mesh is None:
                raise FaceAnalysisError(
                    "analyzer_unavailable",
                    "Face analysis is currently unavailable on the server."
                )

            image = await self._load_image(input_data)
            if image is None:
                raise FaceAnalysisError(
                    "invalid_image",
                    "The image could not be read. Upload a JPEG or PNG photo."
                )

            # Extract skin features
            skin_features = await self._extract_skin_features(image)
            
            # Extract facial features (optional)
            facial_features = await self._extract_facial_features(image)
            
            # Generate color recommendations
            color_recs = self._get_color_recommendations(skin_features.seasonal_type)
            
            # Generate style tips
            style_tips = self._generate_style_tips(skin_features, facial_features)
            
            processing_time = (time.time() - start_time) * 1000
            
            return FaceAnalysisResponse(
                success=True,
                skin_features=skin_features,
                facial_features=facial_features,
                color_recommendations=color_recs,
                style_tips=style_tips,
                processing_time_ms=round(processing_time, 2)
            )
            
        except FaceAnalysisError as e:
            return FaceAnalysisResponse(
                success=False,
                error=e.message,
                error_code=e.code,
                skin_features=self._get_default_skin_features(),
                color_recommendations=self._get_default_recommendations(),
                processing_time_ms=round((time.time() - start_time) * 1000, 2)
            )
        except Exception as e:
            logger.error(f"Face analysis error: {str(e)}")
            processing_time = (time.time() - start_time) * 1000
            return FaceAnalysisResponse(
                success=False,
                error="Face analysis failed unexpectedly.",
                error_code="analysis_failed",
                skin_features=self._get_default_skin_features(),
                color_recommendations=self._get_default_recommendations(),
                processing_time_ms=round(processing_time, 2)
            )
    
    async def _load_image(self, input_data: FaceAnalysisInput) -> Optional[np.ndarray]:
        """Load image from base64 or URL"""
        try:
            from PIL import Image
            import cv2
            
            if input_data.image_base64:
                payload = input_data.image_base64
                if payload.startswith("data:") and "," in payload:
                    payload = payload.split(",", 1)[1]  # strip data-URL prefix
                image_data = base64.b64decode(payload)
            elif input_data.image_url:
                if not _is_public_http_url(input_data.image_url):
                    raise FaceAnalysisError("invalid_image", "Image URL is not allowed.")
                import httpx
                async with httpx.AsyncClient(timeout=10, follow_redirects=False) as client:
                    response = await client.get(input_data.image_url)
                    response.raise_for_status()
                    image_data = response.content
            else:
                return None

            if len(image_data) > MAX_IMAGE_BYTES:
                raise FaceAnalysisError("invalid_image", "Image is too large (max 10 MB).")

            from PIL import ImageOps
            pil_image = Image.open(BytesIO(image_data))
            pil_image = ImageOps.exif_transpose(pil_image)  # honour phone-camera rotation
            pil_image.thumbnail((MAX_IMAGE_SIDE, MAX_IMAGE_SIDE))

            # Convert to RGB if needed
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')

            # Convert to numpy array
            return np.array(pil_image)
            
        except FaceAnalysisError:
            raise
        except Exception as e:
            logger.error(f"Failed to load image: {str(e)}")
            return None
    
    async def _extract_skin_features(self, image: np.ndarray) -> SkinFeatures:
        """Extract skin features from face image"""
        try:
            # Get face region
            skin_pixels = self._get_skin_pixels(image)

            if skin_pixels is None or len(skin_pixels) < MIN_SKIN_PIXELS:
                raise FaceAnalysisError(
                    "insufficient_skin_pixels",
                    "Could not sample enough skin from the photo. Use a clear, well-lit, front-facing selfie."
                )

            # Calculate average skin color
            avg_rgb = np.mean(skin_pixels, axis=0).astype(int).tolist()
            
            # Convert to LAB for undertone analysis
            lab = self._rgb_to_lab(avg_rgb)
            
            # Determine undertone from LAB values
            undertone = self._determine_undertone(lab)
            
            # Determine skin depth
            skin_depth = self._determine_skin_depth(lab[0])
            
            # Determine seasonal type
            seasonal_type = self._determine_seasonal_type(undertone, skin_depth)
            
            # Calculate hex color
            skin_hex = '#{:02x}{:02x}{:02x}'.format(*avg_rgb)
            
            return SkinFeatures(
                undertone=undertone,
                skin_depth=skin_depth,
                seasonal_type=seasonal_type,
                lab_l=round(lab[0], 2),
                lab_a=round(lab[1], 2),
                lab_b=round(lab[2], 2),
                skin_rgb=avg_rgb,
                skin_hex=skin_hex,
                # Heuristic: how uniform the sampled cheek pixels are (not a model probability)
                confidence=round(float(np.clip(1.0 - np.mean(np.std(skin_pixels, axis=0)) / 60.0, 0.3, 0.9)), 2)
            )

        except FaceAnalysisError:
            raise
        except Exception as e:
            logger.error(f"Skin feature extraction error: {str(e)}")
            raise FaceAnalysisError("analysis_failed", "Skin analysis failed.") from e
    
    def _get_skin_pixels(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extract skin region pixels using face detection"""
        try:
            if self._face_mesh:
                # Use MediaPipe for accurate face region
                results = self._face_mesh.process(image)  # image is already RGB

                if not results.multi_face_landmarks:
                    raise FaceAnalysisError(
                        "no_face_detected",
                        "No face detected. Use a clear, well-lit, front-facing selfie with your face fully visible."
                    )

                if results.multi_face_landmarks:
                    landmarks = results.multi_face_landmarks[0]
                    h, w = image.shape[:2]
                    
                    # Get cheek region landmarks (approximate skin area)
                    cheek_indices = [234, 93, 132, 361, 323, 454]
                    
                    points = []
                    for idx in cheek_indices:
                        lm = landmarks.landmark[idx]
                        x, y = int(lm.x * w), int(lm.y * h)
                        points.append([x, y])
                    
                    # Sample pixels from cheek regions
                    skin_pixels = []
                    for x, y in points:
                        # Sample 5x5 region around each point
                        for dx in range(-2, 3):
                            for dy in range(-2, 3):
                                px, py = x + dx, y + dy
                                if 0 <= px < w and 0 <= py < h:
                                    skin_pixels.append(image[py, px])
                    
                    return np.array(skin_pixels) if skin_pixels else None
            
            return None

        except FaceAnalysisError:
            raise
        except Exception as e:
            logger.error(f"Error extracting skin pixels: {str(e)}")
            return None
    
    def _rgb_to_lab(self, rgb: List[int]) -> Tuple[float, float, float]:
        """Convert RGB to LAB color space"""
        # Normalize RGB
        r, g, b = [x / 255.0 for x in rgb]
        
        # sRGB to Linear RGB
        def linearize(c):
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        
        r, g, b = linearize(r), linearize(g), linearize(b)
        
        # Linear RGB to XYZ
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
        
        # XYZ to LAB (D65 illuminant)
        xn, yn, zn = 0.95047, 1.0, 1.08883
        
        def f(t):
            return t ** (1/3) if t > 0.008856 else (7.787 * t) + (16/116)
        
        fx, fy, fz = f(x/xn), f(y/yn), f(z/zn)
        
        L = (116 * fy) - 16
        a = 500 * (fx - fy)
        b = 200 * (fy - fz)
        
        return (L, a, b)
    
    def _determine_undertone(self, lab: Tuple[float, float, float]) -> SkinUndertone:
        """Determine skin undertone from LAB values"""
        _, a, b = lab
        
        # a > 0 indicates more red/yellow (warm)
        # b > 0 indicates more yellow (warm)
        warm_score = a + b * 0.5
        
        if warm_score > 8:
            return SkinUndertone.WARM
        elif warm_score < -5:
            return SkinUndertone.COOL
        else:
            return SkinUndertone.NEUTRAL
    
    def _determine_skin_depth(self, lightness: float) -> SkinDepth:
        """Determine skin depth from LAB lightness"""
        if lightness >= 75:
            return SkinDepth.FAIR
        elif lightness >= 65:
            return SkinDepth.LIGHT
        elif lightness >= 55:
            return SkinDepth.MEDIUM
        elif lightness >= 45:
            return SkinDepth.TAN
        else:
            return SkinDepth.DEEP
    
    def _determine_seasonal_type(
        self,
        undertone: SkinUndertone,
        depth: SkinDepth
    ) -> SeasonalType:
        """Determine seasonal type from undertone and depth"""
        is_warm = undertone == SkinUndertone.WARM
        is_light = depth in [SkinDepth.FAIR, SkinDepth.LIGHT]
        
        if is_warm and is_light:
            return SeasonalType.SPRING
        elif not is_warm and is_light:
            return SeasonalType.SUMMER
        elif is_warm and not is_light:
            return SeasonalType.AUTUMN
        else:
            return SeasonalType.WINTER
    
    async def _extract_facial_features(
        self,
        image: np.ndarray
    ) -> Optional[FacialFeatures]:
        """Extract facial structure features"""
        try:
            if not self._face_mesh:
                return None
            
            import cv2
            results = self._face_mesh.process(image)
            
            if not results.multi_face_landmarks:
                return None
            
            landmarks = results.multi_face_landmarks[0]
            h, w = image.shape[:2]
            
            # Calculate face dimensions
            # Face width (ear to ear)
            left_ear = landmarks.landmark[234]
            right_ear = landmarks.landmark[454]
            face_width = abs(right_ear.x - left_ear.x) * w
            
            # Face height (forehead to chin)
            forehead = landmarks.landmark[10]
            chin = landmarks.landmark[152]
            face_height = abs(chin.y - forehead.y) * h
            
            # Eye distance
            left_eye = landmarks.landmark[33]
            right_eye = landmarks.landmark[263]
            eye_distance = abs(right_eye.x - left_eye.x) * w
            
            # Determine face shape
            ratio = face_width / face_height if face_height > 0 else 1
            face_shape = self._determine_face_shape(ratio, landmarks, w, h)
            
            return FacialFeatures(
                face_shape=face_shape,
                face_width=round(face_width, 2),
                face_height=round(face_height, 2),
                eye_distance=round(eye_distance, 2),
                jawline_angle=90.0,  # Simplified
                forehead_ratio=0.33,  # Simplified
                confidence=0.8
            )
            
        except Exception as e:
            logger.error(f"Facial feature extraction error: {str(e)}")
            return None
    
    def _determine_face_shape(
        self,
        ratio: float,
        landmarks,
        w: int,
        h: int
    ) -> FaceShape:
        """Determine face shape from measurements"""
        if ratio > 0.9:
            return FaceShape.ROUND
        elif ratio < 0.7:
            return FaceShape.OBLONG
        elif ratio > 0.85:
            return FaceShape.SQUARE
        else:
            return FaceShape.OVAL
    
    def _get_color_recommendations(
        self,
        seasonal_type: SeasonalType
    ) -> ColorRecommendations:
        """Get color recommendations for seasonal type"""
        palette = SEASONAL_PALETTES.get(
            seasonal_type,
            SEASONAL_PALETTES[SeasonalType.AUTUMN]
        )
        
        return ColorRecommendations(**palette)
    
    def _generate_style_tips(
        self,
        skin: SkinFeatures,
        face: Optional[FacialFeatures]
    ) -> List[str]:
        """Generate personalized style tips"""
        tips = []
        
        # Undertone-based tips
        if skin.undertone == SkinUndertone.WARM:
            tips.append("Warm earthy tones like olive, rust, and gold enhance your complexion")
            tips.append("Gold jewelry will complement your warm undertones beautifully")
        elif skin.undertone == SkinUndertone.COOL:
            tips.append("Cool tones like navy, lavender, and silver flatter your skin")
            tips.append("Silver and platinum accessories work best for you")
        else:
            tips.append("You're lucky! Both warm and cool tones work well for you")
            tips.append("Experiment with both gold and silver accessories")
        
        # Seasonal tips
        if skin.seasonal_type == SeasonalType.SPRING:
            tips.append("Bright, warm colors with yellow undertones are your best friend")
        elif skin.seasonal_type == SeasonalType.SUMMER:
            tips.append("Soft, muted colors with blue undertones complement you well")
        elif skin.seasonal_type == SeasonalType.AUTUMN:
            tips.append("Rich, warm colors like burnt orange and olive suit you perfectly")
        else:
            tips.append("High contrast and bold colors like true red and emerald look stunning on you")
        
        # Face shape tips (if available)
        if face:
            if face.face_shape == FaceShape.ROUND:
                tips.append("V-neck tops and angular frames can add definition")
            elif face.face_shape == FaceShape.SQUARE:
                tips.append("Round necklines and soft curves balance your strong features")
            elif face.face_shape == FaceShape.OVAL:
                tips.append("Most styles work well for your balanced face shape")
        
        return tips
    
    def _get_default_skin_features(self) -> SkinFeatures:
        """Return default skin features for error cases"""
        return SkinFeatures(
            undertone=SkinUndertone.NEUTRAL,
            skin_depth=SkinDepth.MEDIUM,
            seasonal_type=SeasonalType.AUTUMN,
            lab_l=60.0,
            lab_a=10.0,
            lab_b=15.0,
            skin_rgb=[180, 150, 130],
            skin_hex="#B49682",
            confidence=0.0
        )
    
    def _get_default_recommendations(self) -> ColorRecommendations:
        """Return default recommendations"""
        return self._get_color_recommendations(SeasonalType.AUTUMN)


# Singleton instance
_service_instance: Optional[FaceAnalysisService] = None


def get_face_analysis_service() -> FaceAnalysisService:
    """Get or create face analysis service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = FaceAnalysisService()
    return _service_instance

# 🎯 Recommendation Module - Integration Guide

> **Author:** Recommendation Team  
> **Last Updated:** January 24, 2026  
> **Version:** 1.0.0

This document explains how to integrate the Recommendation module with other modules in the StyleX project.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Endpoints](#api-endpoints)
4. [For Face Analysis Team](#for-face-analysis-team)
5. [For Cloth Analysis Team](#for-cloth-analysis-team)
6. [For Virtual Try-On Team](#for-virtual-try-on-team)
7. [Schema Reference](#schema-reference)
8. [Testing](#testing)
9. [Error Handling](#error-handling)

---

## 🔍 Overview

The Recommendation module takes:
- **Skin features** (from Face Analysis) 
- **Clothing features** (from Cloth Analysis)

And produces:
- **Ranked recommendations** with scores
- **Color analysis** for the user
- **Outfit combinations**

The output can then be sent to Virtual Try-On for visualization.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     RECOMMENDATION MODULE                     │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────┐     ┌─────────────────┐               │
│   │   router.py     │────▶│   service.py    │               │
│   │  (API Routes)   │     │ (Business Logic)│               │
│   └─────────────────┘     └────────┬────────┘               │
│                                    │                         │
│          ┌─────────────────────────┼─────────────────────┐   │
│          │                         │                     │   │
│          ▼                         ▼                     ▼   │
│   ┌─────────────┐         ┌─────────────┐       ┌───────────┐│
│   │color_matcher│         │style_matcher│       │  scoring  ││
│   └──────┬──────┘         └──────┬──────┘       └─────┬─────┘│
│          │                       │                    │      │
│          ▼                       ▼                    ▼      │
│   ┌─────────────┐         ┌─────────────┐                    │
│   │ color_rules │         │seasonal_rules│                   │
│   └─────────────┘         └─────────────┘                    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🌐 API Endpoints

Base URL: `/api/v1/recommendation`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/recommend` | Get ranked clothing recommendations |
| POST | `/check-compatibility` | Check single item compatibility |
| POST | `/outfits` | Get complete outfit recommendations |
| POST | `/color-analysis` | Get personalized color palette |
| POST | `/prepare-tryon` | Prepare data for virtual try-on |
| POST | `/batch-score` | Score large inventory batches |
| GET | `/health` | Health check |

---

## 👤 For Face Analysis Team

### What We Need From You

The `SkinFeatures` schema that you should return:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class Undertone(str, Enum):
    WARM = "warm"
    COOL = "cool"
    NEUTRAL = "neutral"

class SkinDepth(str, Enum):
    FAIR = "fair"
    LIGHT = "light"
    MEDIUM = "medium"
    TAN = "tan"
    DEEP = "deep"

class SkinFeatures(BaseModel):
    """
    Schema for Face Analysis output
    """
    # REQUIRED: Undertone classification
    undertone: Undertone  # "warm", "cool", or "neutral"
    
    # REQUIRED: Skin depth/darkness
    skin_depth: SkinDepth  # "fair", "light", "medium", "tan", "deep"
    
    # REQUIRED: LAB color values (from your color analysis)
    lab_l: float  # Lightness 0-100
    lab_a: float  # Green-Red axis -128 to 127
    lab_b: float  # Blue-Yellow axis -128 to 127
    
    # REQUIRED: RGB skin color
    skin_rgb: List[int]  # [R, G, B] values 0-255
    
    # OPTIONAL: Season (we can calculate if not provided)
    season: Optional[str] = None  # "spring", "summer", "autumn", "winter"
    
    # REQUIRED: Confidence score
    confidence: float = 1.0  # 0.0 to 1.0
```

### How to Determine Values

#### Undertone Detection
Based on your LAB-based analysis:
- **Warm**: `lab_a > 5` AND `lab_b > 10` (yellow/golden/peachy)
- **Cool**: `lab_a < 0` OR `lab_b < 5` (pink/red/bluish)
- **Neutral**: In between

#### Skin Depth Detection
Based on LAB L (lightness) value:
- **Fair**: `lab_l >= 75`
- **Light**: `65 <= lab_l < 75`
- **Medium**: `50 <= lab_l < 65`
- **Tan**: `35 <= lab_l < 50`
- **Deep**: `lab_l < 35`

### Example Output

```json
{
    "undertone": "warm",
    "skin_depth": "medium",
    "lab_l": 65.5,
    "lab_a": 12.3,
    "lab_b": 18.7,
    "skin_rgb": [198, 166, 145],
    "season": null,
    "confidence": 0.92
}
```

### Integration Code Example

```python
# In your face_analysis/service.py

from recommendation.schemas import SkinFeatures, Undertone, SkinDepth

async def analyze_face(image) -> SkinFeatures:
    # Your face mesh detection
    face_regions = detect_face_mesh(image)
    
    # Your LAB color extraction
    lab_values = extract_lab_colors(face_regions)
    
    # Your undertone detection
    undertone = detect_undertone(lab_values)
    
    # Build the schema we need
    return SkinFeatures(
        undertone=Undertone(undertone),
        skin_depth=determine_skin_depth(lab_values['L']),
        lab_l=lab_values['L'],
        lab_a=lab_values['a'],
        lab_b=lab_values['b'],
        skin_rgb=lab_to_rgb(lab_values),
        confidence=calculate_confidence()
    )
```

---

## 👕 For Cloth Analysis Team

### What We Need From You

The `ClothFeatures` schema that you should return:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ClothingCategory(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    ACCESSORY = "accessory"
    FOOTWEAR = "footwear"

class StyleType(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    BUSINESS = "business"
    SPORTY = "sporty"
    BOHEMIAN = "bohemian"
    VINTAGE = "vintage"
    STREETWEAR = "streetwear"
    MINIMALIST = "minimalist"

class WeatherType(str, Enum):
    SUMMER = "summer"
    WINTER = "winter"
    SPRING = "spring"
    FALL = "fall"
    ALL_SEASON = "all_season"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"

class ClothFeatures(BaseModel):
    """
    Schema for Cloth Analysis output
    """
    # REQUIRED: Unique ID
    cloth_id: str
    
    # OPTIONAL: Image URL for virtual try-on
    image_url: Optional[str] = None
    
    # REQUIRED: Color features
    dominant_color_rgb: List[int]  # [R, G, B]
    dominant_color_name: str       # "navy blue", "coral", etc.
    color_palette: List[List[int]] = []  # Additional colors
    color_hex: str                 # "#4682B4"
    
    # REQUIRED: Classification
    category: ClothingCategory     # "top", "bottom", etc.
    gender: Gender                 # "male", "female", "unisex"
    style: StyleType               # "casual", "formal", etc.
    
    # REQUIRED: Design/Pattern
    design: str                    # "solid", "striped", "floral", etc.
    
    # REQUIRED: Material
    fabric: str                    # "cotton", "silk", "denim", etc.
    
    # REQUIRED: Context
    weather: WeatherType           # "summer", "winter", "all_season"
    formality_level: int           # 1-10 (1=very casual, 10=black tie)
    
    # REQUIRED: Confidence
    confidence: float = 1.0        # 0.0 to 1.0
```

### Feature Extraction Guidelines

#### Color Extraction
- Extract dominant color using K-means clustering
- Map RGB to human-readable color names
- Calculate hex code

#### Category Detection
Map your detections to our categories:
- **top**: t-shirt, shirt, blouse, sweater, tank top, polo
- **bottom**: pants, jeans, shorts, skirt, trousers
- **dress**: dress, gown, romper, jumpsuit
- **outerwear**: jacket, coat, blazer, hoodie, cardigan
- **accessory**: scarf, hat, belt, tie, jewelry
- **footwear**: shoes, sneakers, boots, sandals

#### Style Classification
- **casual**: everyday wear, relaxed fit
- **formal**: suits, evening wear, dress clothes
- **business**: office appropriate, smart casual
- **sporty**: athletic wear, activewear
- **bohemian**: flowy, ethnic, artistic
- **vintage**: retro styles, classic cuts
- **streetwear**: urban, trendy, graphic
- **minimalist**: clean lines, neutral colors

#### Formality Level Guide
| Level | Description | Examples |
|-------|-------------|----------|
| 1-2 | Very Casual | Gym clothes, pajamas, tank tops |
| 3-4 | Casual | Jeans, t-shirts, sneakers |
| 5-6 | Smart Casual | Chinos, polo shirts, loafers |
| 7-8 | Business | Dress shirts, blazers, dress shoes |
| 9-10 | Formal | Suits, evening gowns, tuxedos |

### Example Output

```json
{
    "cloth_id": "cloth_001",
    "image_url": "/images/blue_shirt.jpg",
    "dominant_color_rgb": [70, 130, 180],
    "dominant_color_name": "steel blue",
    "color_palette": [[70, 130, 180], [100, 149, 237]],
    "color_hex": "#4682B4",
    "category": "top",
    "gender": "unisex",
    "style": "casual",
    "design": "solid",
    "fabric": "cotton",
    "weather": "all_season",
    "formality_level": 4,
    "confidence": 0.88
}
```

### Integration Code Example

```python
# In your cloth_analysis/service.py

from recommendation.schemas import (
    ClothFeatures, ClothingCategory, StyleType, 
    WeatherType, Gender
)

async def analyze_clothing(image, cloth_id: str) -> ClothFeatures:
    # Your color extraction
    colors = extract_colors(image)
    
    # Your category detection
    category = detect_category(image)
    
    # Your style classification
    style = classify_style(image)
    
    # Build the schema we need
    return ClothFeatures(
        cloth_id=cloth_id,
        image_url=f"/images/{cloth_id}.jpg",
        dominant_color_rgb=colors['dominant'],
        dominant_color_name=colors['name'],
        color_palette=colors['palette'],
        color_hex=rgb_to_hex(colors['dominant']),
        category=ClothingCategory(category),
        gender=detect_gender(image),
        style=StyleType(style),
        design=detect_pattern(image),
        fabric=detect_fabric(image),
        weather=determine_weather_suitability(category, fabric),
        formality_level=calculate_formality(category, style),
        confidence=calculate_confidence()
    )
```

---

## 👔 For Virtual Try-On Team

### What You Receive From Us

The `TryOnRequest` schema:

```python
class TryOnRequest(BaseModel):
    """
    Data package for Virtual Try-On
    """
    # User's full body image
    user_image_url: str
    
    # Recommended clothing items with scores
    recommended_clothes: List[ClothRecommendation]
    
    # User's skin features (for color reference)
    skin_features: SkinFeatures
    
    # Options
    try_all: bool = False
    max_items: int = 3
```

Each `ClothRecommendation` contains:

```python
class ClothRecommendation(BaseModel):
    cloth_id: str
    image_url: Optional[str]        # Clothing image for warping
    overall_score: float            # 0-1 compatibility score
    score_breakdown: ScoreBreakdown  # Detailed scores
    rank: int                       # Recommendation rank
    cloth_features: ClothFeatures   # Full clothing features
    recommendation_level: str       # "Highly Recommended", etc.
```

### Integration Flow

```
1. User uploads face image + body image
                │
                ▼
2. Face Analysis extracts SkinFeatures
                │
                ▼
3. Cloth Analysis processes clothing inventory
                │
                ▼
4. Recommendation ranks clothes ──────────────┐
                │                             │
                ▼                             │
5. Call /prepare-tryon endpoint               │
                │                             │
                ▼                             │
6. TryOnRequest is created ◄──────────────────┘
                │
                ▼
7. Virtual Try-On receives TryOnRequest
                │
                ▼
8. Generate try-on images for top items
```

### API Call Example

```python
# In your virtual_tryon/service.py

import httpx
from recommendation.schemas import TryOnRequest, RecommendationResponse

async def process_tryon(
    user_image_url: str,
    recommendations: RecommendationResponse,
    skin_features: SkinFeatures
):
    # Option 1: Call the prepare endpoint
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/recommendation/prepare-tryon",
            params={"user_image_url": user_image_url, "max_items": 3},
            json={
                "recommendation_response": recommendations.dict(),
                "skin_features": skin_features.dict()
            }
        )
        tryon_request = TryOnRequest(**response.json())
    
    # Option 2: Create TryOnRequest directly
    tryon_request = TryOnRequest(
        user_image_url=user_image_url,
        recommended_clothes=recommendations.recommendations[:3],
        skin_features=skin_features,
        max_items=3
    )
    
    # Process each recommended item
    results = []
    for rec in tryon_request.recommended_clothes:
        # Get clothing image
        cloth_image = load_image(rec.image_url)
        
        # Your garment warping
        warped = warp_garment(cloth_image, user_pose)
        
        # Your image synthesis
        result = synthesize_image(user_image, warped)
        
        results.append({
            "cloth_id": rec.cloth_id,
            "generated_image": result,
            "recommendation_score": rec.overall_score
        })
    
    return results
```

### What You Should Return

```python
class TryOnResult(BaseModel):
    cloth_id: str
    generated_image_url: str
    fit_score: Optional[float] = None
    processing_time_ms: float

class TryOnResponse(BaseModel):
    success: bool
    results: List[TryOnResult]
    total_processing_time_ms: float
```

---

## 📖 Schema Reference

### Complete Type Definitions

All schemas are defined in `recommendation/schemas.py`:

```python
# Import all schemas
from recommendation import (
    # Enums
    Undertone,          # warm, cool, neutral
    SkinDepth,          # fair, light, medium, tan, deep
    Season,             # spring, summer, autumn, winter
    ClothingCategory,   # top, bottom, dress, outerwear, accessory, footwear
    StyleType,          # casual, formal, business, sporty, etc.
    WeatherType,        # summer, winter, spring, fall, all_season
    Gender,             # male, female, unisex
    
    # Input schemas
    SkinFeatures,
    ClothFeatures,
    UserPreferences,
    
    # Request schemas
    RecommendationRequest,
    SingleClothRecommendationRequest,
    OutfitRecommendationRequest,
    
    # Response schemas
    RecommendationResponse,
    SingleClothRecommendationResponse,
    OutfitRecommendationResponse,
    ClothRecommendation,
    ScoreBreakdown,
    OutfitRecommendation,
    
    # Virtual Try-On schemas
    TryOnRequest,
    TryOnResponse,
    TryOnResult,
)
```

---

## 🧪 Testing

### Test Endpoint

Use the test endpoint for development:

```bash
POST /api/v1/recommendation/test/sample-recommendation
```

This runs a full recommendation cycle with sample data.

### Manual Testing

```python
import httpx
import asyncio

async def test_recommendation():
    # Sample skin features
    skin_features = {
        "undertone": "warm",
        "skin_depth": "medium",
        "lab_l": 65.5,
        "lab_a": 12.3,
        "lab_b": 18.7,
        "skin_rgb": [198, 166, 145],
        "confidence": 0.92
    }
    
    # Sample clothing items
    clothes = [
        {
            "cloth_id": "shirt_001",
            "dominant_color_rgb": [70, 130, 180],
            "dominant_color_name": "steel blue",
            "color_hex": "#4682B4",
            "color_palette": [],
            "category": "top",
            "gender": "unisex",
            "style": "casual",
            "design": "solid",
            "fabric": "cotton",
            "weather": "all_season",
            "formality_level": 4,
            "confidence": 0.85
        }
    ]
    
    request_data = {
        "skin_features": skin_features,
        "available_clothes": clothes,
        "top_k": 10
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/recommendation/recommend",
            json=request_data
        )
        print(response.json())

asyncio.run(test_recommendation())
```

---

## ⚠️ Error Handling

### Common Errors

| Error Code | Cause | Solution |
|------------|-------|----------|
| 400 | Invalid schema data | Check field types and ranges |
| 400 | Empty clothes list | Provide at least one clothing item |
| 400 | Invalid RGB values | Ensure values are 0-255 |
| 400 | Invalid LAB values | Ensure L is 0-100, a/b are -128 to 127 |
| 500 | Internal error | Check server logs |

### Validation Example

```python
from recommendation.utils import validate_skin_features, validate_cloth_features

# Validate before sending
is_valid, error = validate_skin_features(skin_features)
if not is_valid:
    raise ValueError(f"Invalid skin features: {error}")

for cloth in clothes:
    is_valid, error = validate_cloth_features(cloth)
    if not is_valid:
        raise ValueError(f"Invalid cloth {cloth.cloth_id}: {error}")
```

---

## 📞 Contact

For questions about integration:
- **Recommendation Module Issues**: Create issue with `recommendation` label
- **API Changes**: Check this document for updates
- **Schema Changes**: We will notify all teams before breaking changes

---

## 📝 Changelog

### v1.0.0 (January 24, 2026)
- Initial release
- Complete recommendation engine
- Color matching with undertone and seasonal rules
- Style matching with occasion filtering
- Virtual Try-On integration schemas
- Batch processing support

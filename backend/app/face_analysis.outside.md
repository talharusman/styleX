# Face Analysis External Dependencies

This document lists the external dependencies and integrations that need to be implemented outside the `cloth_analysis` folder after integrating all models from other developers.

## Required Dependencies for Cloth Analysis

### Python Packages

Add these dependencies to `requirements.txt`:

```txt
# Core dependencies
fastapi>=0.100.0
pydantic>=2.0.0
uvicorn>=0.22.0

# Image processing
opencv-python>=4.8.0
Pillow>=10.0.0
numpy>=1.24.0

# Machine Learning
torch>=2.0.0
torchvision>=0.15.0
scikit-learn>=1.3.0

# Optional: CLIP for zero-shot style classification
# Adds ~340MB model download, but improves style detection accuracy
# Comment out if VRAM is insufficient
# ftfy
# regex
# git+https://github.com/openai/CLIP.git

# HTTP requests for image URLs
requests>=2.31.0
```

### GPU Configuration

For 4GB RTX 3050, ensure PyTorch is installed with CUDA support:

```bash
# Install PyTorch with CUDA 11.8 (or your CUDA version)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## Integration Points

### 1. Main Application (`app/main.py`)

Add the cloth analysis router to the main FastAPI app:

```python
from fastapi import FastAPI
from app.cloth_analysis import router as cloth_analysis_router

app = FastAPI(title="StyleX API", version="1.0.0")

# Include cloth analysis router
app.include_router(cloth_analysis_router)
```

### 2. Configuration (`app/config.py`)

If you have a central config, add these settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Cloth Analysis Settings
    CLOTH_ANALYSIS_USE_CLIP: bool = True
    CLOTH_ANALYSIS_IMAGE_SIZE: int = 224
    CLOTH_ANALYSIS_USE_FP16: bool = True
    CLOTH_ANALYSIS_BATCH_SIZE: int = 1
    
    # Model paths (if using custom trained models)
    CLOTH_MODEL_PATH: str = "models/cloth_analysis/"
    
    class Config:
        env_file = ".env"
```

### 3. Model Downloads (`scripts/download_models.py`)

Add model download script for custom trained models (if applicable):

```python
def download_cloth_analysis_models():
    """Download pre-trained models for cloth analysis."""
    # MobileNetV3 weights are downloaded automatically by torchvision
    # CLIP model is downloaded on first use
    
    # If you have custom fine-tuned models, download them here:
    # download_model("category_classifier.pth", "models/cloth_analysis/")
    # download_model("design_classifier.pth", "models/cloth_analysis/")
    pass
```

### 4. Database Integration (`app/database/`)

If storing analysis results:

```python
# app/database/models.py
from sqlalchemy import Column, Integer, String, Float, JSON
from .connection import Base

class ClothingAnalysisResult(Base):
    __tablename__ = "clothing_analysis_results"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)
    image_hash = Column(String, index=True)
    dominant_colors = Column(JSON)
    category = Column(String)
    design_pattern = Column(String)
    gender = Column(String)
    style = Column(String)
    weather = Column(String)
    formality_level = Column(Integer)
    overall_confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 5. Face Analysis Integration

When integrating with face analysis for recommendation:

```python
# In recommendation service
from app.cloth_analysis import analyze_clothing
from app.face_analysis import analyze_face  # From other developer

async def get_outfit_recommendation(user_image, clothing_images):
    # Get user skin tone from face analysis
    face_result = await analyze_face(user_image)
    skin_undertone = face_result.undertone
    
    # Analyze clothing items
    clothing_features = []
    for img in clothing_images:
        result = await analyze_clothing(ClothInput(image_base64=img))
        clothing_features.append(result.features)
    
    # Match colors based on skin undertone and clothing colors
    recommendations = match_colors(skin_undertone, clothing_features)
    return recommendations
```

## Custom Model Training (Post-MVP)

If you want to fine-tune models on your own dataset:

### 1. Design Pattern Model

```python
# Fine-tune MobileNetV3 on your pattern dataset
# Dataset structure:
# data/patterns/
#   plain/
#   stripes/
#   checks/
#   floral/
#   ...

# Use transfer learning from pretrained ImageNet weights
```

### 2. Category Model

```python
# Fine-tune on fashion dataset like DeepFashion or your custom data
# data/categories/
#   t-shirt/
#   shirt/
#   pants/
#   dress/
#   ...
```

### 3. CLIP Fine-tuning (Advanced)

For better style detection, fine-tune CLIP on fashion-specific prompts.

## Memory Optimization Notes

For 4GB GPU:
1. All models use FP16 precision
2. Image size is 224x224
3. Batch size is 1
4. Models are loaded lazily and cached
5. GPU memory is cleared after each inference

If running multiple models simultaneously causes OOM:
1. Unload models between different feature extractions
2. Use CPU for some features (color, weather, formality)
3. Process one image at a time

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/cloth-analysis/analyze` | POST | Analyze clothing by base64/URL |
| `/cloth-analysis/analyze/upload` | POST | Analyze uploaded image file |
| `/cloth-analysis/health` | GET | Service health check |
| `/cloth-analysis/categories` | GET | List supported categories |
| `/cloth-analysis/styles` | GET | List supported styles |
| `/cloth-analysis/patterns` | GET | List supported patterns |

## Testing

Run tests with:

```bash
pytest tests/test_cloth_analysis/ -v
```

## Environment Variables

```env
# .env file
CUDA_VISIBLE_DEVICES=0
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
USE_CLIP=true
DEBUG=false
```

# StyleX Backend

Fashion recommendation system backend with face analysis, clothing analysis, and virtual try-on capabilities.

## Project Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI entry point
│   ├── config.py                   # Configuration settings
│   │
│   ├── face_analysis/              # 🧑 FACE/SKIN ANALYSIS MODULE
│   │   ├── router.py               # API endpoints
│   │   ├── schemas.py              # Request/Response models
│   │   ├── service.py              # Business logic
│   │   ├── utils.py                # Helper functions
│   │   └── models/
│   │       ├── face_mesh.py        # MediaPipe Face Mesh
│   │       ├── color_analysis.py   # LAB-based color extraction
│   │       └── undertone_detection.py  # Rule-based undertone
│   │
│   ├── cloth_analysis/             # 👕 CLOTHING ANALYSIS MODULE
│   │   ├── router.py               # API endpoints
│   │   ├── schemas.py              # Request/Response models
│   │   ├── service.py              # Business logic
│   │   ├── utils.py                # Helper functions
│   │   └── extractors/
│   │       ├── color_extractor.py      # Clothing color
│   │       ├── design_extractor.py     # Pattern/design
│   │       ├── gender_extractor.py     # Gender classification
│   │       ├── category_extractor.py   # Clothing category
│   │       ├── weather_extractor.py    # Weather suitability
│   │       ├── style_extractor.py      # Style classification
│   │       ├── fabric_extractor.py     # Fabric type
│   │       ├── formality_extractor.py  # Formality level
│   │       └── confidence_scorer.py    # Confidence scores
│   │
│   ├── recommendation/             # 🎯 RECOMMENDATION ENGINE
│   │   ├── router.py               # API endpoints
│   │   ├── schemas.py              # Request/Response models
│   │   ├── service.py              # Business logic
│   │   ├── utils.py                # Helper functions
│   │   ├── engine/
│   │   │   ├── color_matcher.py    # Color matching algorithm
│   │   │   ├── style_matcher.py    # Style matching
│   │   │   └── scoring.py          # Recommendation scoring
│   │   └── rules/
│   │       ├── color_rules.py      # Undertone color rules
│   │       └── seasonal_rules.py   # Seasonal color theory
│   │
│   ├── virtual_tryon/              # 👔 VIRTUAL TRY-ON MODULE
│   │   ├── router.py               # API endpoints
│   │   ├── schemas.py              # Request/Response models
│   │   ├── service.py              # Business logic
│   │   ├── utils.py                # Helper functions
│   │   └── models/
│   │       ├── pose_estimation.py  # Body pose detection
│   │       ├── garment_warping.py  # Clothing warping
│   │       └── image_synthesis.py  # Final image generation
│   │
│   ├── common/                     # 🔧 SHARED UTILITIES
│   │   ├── image_utils.py          # Image processing
│   │   ├── color_utils.py          # Color utilities
│   │   ├── exceptions.py           # Custom exceptions
│   │   └── constants.py            # Constants & enums
│   │
│   └── database/                   # 💾 DATABASE
│       ├── connection.py           # DB connection
│       ├── models.py               # DB models
│       └── repositories/           # Data access layer
│
├── models/                         # 🤖 ML Model weights (git-ignored)
├── data/                           # 📁 Data files
├── tests/                          # 🧪 Unit tests
├── scripts/                        # 🛠️ Utility scripts
├── requirements.txt                # Dependencies
└── .env.example                    # Environment template
```

## Developer Assignments

Each developer should work in their assigned module:

| Module | Developer | Directory |
|--------|-----------|-----------|
| Face Analysis | Developer 1 | `app/face_analysis/` |
| Cloth Analysis | Developer 2 | `app/cloth_analysis/` |
| Recommendation | Developer 3 | `app/recommendation/` |
| Virtual Try-On | Developer 4 | `app/virtual_tryon/` |
| Common/Database | Shared | `app/common/`, `app/database/` |

## Setup

See the [root README](../README.md) for the full guide. Short version:

```bash
python scripts/setup.py          # creates .venv, installs deps, writes .env
docker compose up -d mongo       # run from the repo root (MongoDB is required)
.venv/Scripts/uvicorn app.main:app --reload   # Windows; use .venv/bin/uvicorn on Linux/Mac
```

The API refuses to start if MongoDB is unreachable. Check `http://localhost:8000/health`
and `http://localhost:8000/docs`.

## API Endpoints

See `/docs` (Swagger UI) for the authoritative, live list. Examples:

- `POST /api/face/analyze` - Analyze face and extract skin features
- `POST /api/cloth/analyze` - Extract clothing features
- `POST /api/recommend` - Get clothing recommendations
- `POST /api/tryon` - Generate virtual try-on image

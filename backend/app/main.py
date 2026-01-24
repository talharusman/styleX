# Main FastAPI application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.recommendation.router import router as recommendation_router

app = FastAPI(
    title="StyleX API",
    description="Fashion recommendation system with face analysis, cloth analysis, and virtual try-on",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommendation_router)

# TODO: Add other routers when ready
# from app.face_analysis.router import router as face_router
# from app.cloth_analysis.router import router as cloth_router
# from app.virtual_tryon.router import router as tryon_router
# app.include_router(face_router)
# app.include_router(cloth_router)
# app.include_router(tryon_router)

@app.get("/")
async def root():
    return {"message": "Welcome to StyleX API", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

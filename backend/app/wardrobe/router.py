"""Wardrobe routes. Every route requires authentication and only touches the caller's data."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.auth.jwt_handler import get_current_user
from app.auth.schemas import UserAuth

from .schemas import (
    OutfitSuggestions,
    SaveOutfitRequest,
    SavedOutfit,
    SavedOutfitList,
    WardrobeItem,
    WardrobeItemList,
    WardrobeItemUpdate,
    WardrobeRecommendations,
)
from .service import WardrobeService, get_wardrobe_service, to_view

router = APIRouter(prefix="/api/wardrobe", tags=["Wardrobe"])

CATEGORIES = "^(top|bottom|dress|outerwear|accessory|footwear|unknown)$"


@router.post("/items", response_model=WardrobeItem, status_code=status.HTTP_201_CREATED,
             summary="Upload and analyze a clothing photo")
async def add_item(
    file: UploadFile = File(...),
    name: Optional[str] = Form(default=None, max_length=100),
    user: UserAuth = Depends(get_current_user),
    service: WardrobeService = Depends(get_wardrobe_service),
) -> WardrobeItem:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file must be an image")
    data = await file.read()
    return to_view(await service.add_item(user.user_id, data, name))


@router.get("/items", response_model=WardrobeItemList, summary="List my wardrobe")
async def list_items(
    category: Optional[str] = Query(default=None, pattern=CATEGORIES),
    favorite: Optional[bool] = None,
    needs_review: Optional[bool] = None,
    user: UserAuth = Depends(get_current_user),
    service: WardrobeService = Depends(get_wardrobe_service),
) -> WardrobeItemList:
    items = await service.list_items(user.user_id, category, favorite, needs_review)
    return WardrobeItemList(items=[to_view(i) for i in items], total=len(items))


@router.get("/items/{item_id}", response_model=WardrobeItem)
async def get_item(item_id: str, user: UserAuth = Depends(get_current_user),
                   service: WardrobeService = Depends(get_wardrobe_service)) -> WardrobeItem:
    return to_view(await service.get_owned(user.user_id, item_id))


@router.patch("/items/{item_id}", response_model=WardrobeItem, summary="Correct analysis results")
async def update_item(item_id: str, update: WardrobeItemUpdate, user: UserAuth = Depends(get_current_user),
                      service: WardrobeService = Depends(get_wardrobe_service)) -> WardrobeItem:
    return to_view(await service.update_item(user.user_id, item_id, update))


@router.post("/items/{item_id}/favorite", response_model=WardrobeItem, summary="Toggle favorite")
async def toggle_favorite(item_id: str, user: UserAuth = Depends(get_current_user),
                          service: WardrobeService = Depends(get_wardrobe_service)) -> WardrobeItem:
    return to_view(await service.toggle_favorite(user.user_id, item_id))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str, user: UserAuth = Depends(get_current_user),
                      service: WardrobeService = Depends(get_wardrobe_service)) -> None:
    await service.delete_item(user.user_id, item_id)


@router.get("/items/{item_id}/image", summary="Item photo (owner only)")
async def item_image(item_id: str, user: UserAuth = Depends(get_current_user),
                     service: WardrobeService = Depends(get_wardrobe_service)) -> FileResponse:
    item = await service.get_owned(user.user_id, item_id)
    if not item.image_path or not Path(item.image_path).is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    return FileResponse(item.image_path, media_type="image/jpeg",
                        headers={"Cache-Control": "private, max-age=3600"})


@router.get("/recommendations", response_model=WardrobeRecommendations,
            summary="Rank my wardrobe against my skin profile")
async def recommendations(
    top_k: int = Query(default=20, ge=1, le=100),
    occasion: Optional[str] = Query(default=None, max_length=40),
    user: UserAuth = Depends(get_current_user),
    service: WardrobeService = Depends(get_wardrobe_service),
) -> WardrobeRecommendations:
    return await service.recommendations(user.user_id, top_k, occasion)


@router.get("/outfits", response_model=OutfitSuggestions, summary="Complete outfit combinations from my wardrobe")
async def outfits(
    occasion: Optional[str] = Query(default=None, max_length=40),
    user: UserAuth = Depends(get_current_user),
    service: WardrobeService = Depends(get_wardrobe_service),
) -> OutfitSuggestions:
    return await service.outfits(user.user_id, occasion)


@router.post("/outfits/saved", response_model=SavedOutfit, status_code=status.HTTP_201_CREATED,
             summary="Save an outfit")
async def save_outfit(body: SaveOutfitRequest, user: UserAuth = Depends(get_current_user),
                      service: WardrobeService = Depends(get_wardrobe_service)) -> SavedOutfit:
    return await service.save_outfit(user.user_id, body.name, body.item_ids, body.score, body.reasoning, body.occasion)


@router.get("/outfits/saved", response_model=SavedOutfitList, summary="My saved outfits")
async def saved_outfits(user: UserAuth = Depends(get_current_user),
                        service: WardrobeService = Depends(get_wardrobe_service)) -> SavedOutfitList:
    return SavedOutfitList(outfits=await service.saved_outfits(user.user_id))


@router.delete("/outfits/saved/{outfit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_outfit(outfit_id: str, user: UserAuth = Depends(get_current_user),
                              service: WardrobeService = Depends(get_wardrobe_service)) -> None:
    await service.delete_saved_outfit(user.user_id, outfit_id)

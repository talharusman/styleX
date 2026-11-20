"""
Wardrobe service.

Turns uploaded clothing photos into persisted ClothingItem documents (using the
cloth-analysis module), and ranks the user's real wardrobe against their stored
skin profile with the recommendation engine.

Design notes:
- Classifiers are imperfect, so low-confidence items are flagged `needs_review`
  and every key field can be corrected by the user (PATCH).
- Items whose category is unknown are stored but never ranked.
- Images are stored on disk under UPLOAD_DIR/<user_id>/ and served only to their owner.
"""

import base64
import io
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from beanie import PydanticObjectId
from fastapi import HTTPException, status
from PIL import Image, ImageOps

from app.config import settings
from app.database.models import (
    ClothingCategory as DbCategory,
    ClothingFeatures,
    ClothingItem,
    ColorInfo,
    DesignPattern,
    OutfitRecommendation as DbOutfit,
    StyleType as DbStyle,
    UserProfile,
    WeatherType as DbWeather,
)
from app.cloth_analysis.schemas import ClothInput
from app.cloth_analysis.service import analyze_clothing
from app.recommendation import schemas as rec
from app.recommendation.service import get_recommendation_service

from .schemas import (
    OutfitSuggestions,
    OutfitView,
    PrimaryColor,
    RankedItem,
    SavedOutfit,
    WardrobeItem,
    WardrobeItemUpdate,
    WardrobeRecommendations,
)

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
STORED_IMAGE_SIDE = 800
CATEGORY_REVIEW_THRESHOLD = 0.35
STYLE_REVIEW_THRESHOLD = 0.25

# Fine-grained analyzer category -> coarse wardrobe group used by the recommender
CATEGORY_GROUP = {
    "t-shirt": "top", "shirt": "top", "blouse": "top", "sweater": "top",
    "hoodie": "top", "tank_top": "top", "polo": "top",
    "pants": "bottom", "jeans": "bottom", "shorts": "bottom",
    "skirt": "bottom", "leggings": "bottom",
    "dress": "dress", "jumpsuit": "dress", "romper": "dress",
    "jacket": "outerwear", "coat": "outerwear", "blazer": "outerwear",
    "cardigan": "outerwear", "vest": "outerwear",
}
RECO_STYLES = {s.value for s in rec.StyleType}


def _upload_root() -> Path:
    root = Path(settings.UPLOAD_DIR)
    if not root.is_absolute():
        root = Path(__file__).resolve().parents[2] / root
    return root


# ---------------------------------------------------------------- images

def _prepare_image(data: bytes) -> bytes:
    """Validate, orient and downscale an upload. Returns JPEG bytes."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "Image is too large (max 10 MB)")
    try:
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        img.thumbnail((STORED_IMAGE_SIDE, STORED_IMAGE_SIDE))
        if img.mode in ("RGBA", "LA", "P"):
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, (255, 255, 255))
            background.paste(rgba, mask=rgba.split()[-1])
            img = background
        else:
            img = img.convert("RGB")
    except Exception:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "The file is not a readable image")
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=88)
    return out.getvalue()


def _store_image(user_id: str, jpeg: bytes) -> str:
    folder = _upload_root() / user_id
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex}.jpg"
    path.write_bytes(jpeg)
    return str(path)


def _delete_image(path: Optional[str]) -> None:
    if not path:
        return
    try:
        p = Path(path).resolve()
        if _upload_root().resolve() in p.parents:  # never delete outside the upload dir
            p.unlink(missing_ok=True)
    except OSError as e:
        logger.warning(f"Could not delete image {path}: {e}")


# ---------------------------------------------------------------- colours

def _is_background(rgb: List[int]) -> bool:
    return all(c >= 235 for c in rgb)


def _order_colors(colors: List[ColorInfo]) -> List[ColorInfo]:
    """Put the garment colour first. Plain white studio backgrounds are skipped
    when another colour covers a meaningful part (>=10%) of the image."""
    ordered = sorted(colors, key=lambda c: c.percentage, reverse=True)
    for i, c in enumerate(ordered):
        if not _is_background(c.rgb) and c.percentage >= 10:
            return [c] + ordered[:i] + ordered[i + 1:]
    return ordered


# ---------------------------------------------------------------- mapping

def _group_of(features: ClothingFeatures) -> str:
    if features.category != DbCategory.UNKNOWN:
        return features.category.value
    return "unknown"


def to_view(item: ClothingItem) -> WardrobeItem:
    f = item.features
    colors = [PrimaryColor(name=c.name, hex_code=c.hex_code, rgb=c.rgb) for c in f.dominant_colors]
    primary = colors[0] if colors else PrimaryColor(name="unknown", hex_code="#808080", rgb=[128, 128, 128])
    return WardrobeItem(
        id=str(item.id),
        name=item.name,
        image_url=f"/api/wardrobe/items/{item.id}/image",
        category=_group_of(f),
        subcategory=f.subcategory,
        style=f.style.value,
        formality_level=f.formality_level,
        weather=f.weather.value,
        pattern=f.design_pattern.value,
        gender=f.gender,
        fabric=f.fabric_type,
        primary_color=primary,
        colors=colors,
        confidence=item.analysis_confidence,
        needs_review=f.needs_review,
        user_corrected=f.user_corrected,
        is_favorite=item.is_favorite,
        tags=item.tags,
        created_at=item.created_at,
    )


def to_reco_cloth(item: ClothingItem) -> rec.ClothFeatures:
    f = item.features
    colors = f.dominant_colors
    p = colors[0]
    style = f.style.value if f.style.value in RECO_STYLES else "formal"  # "party" has no engine equivalent
    return rec.ClothFeatures(
        cloth_id=str(item.id),
        image_url=f"/api/wardrobe/items/{item.id}/image",
        dominant_color_rgb=p.rgb,
        dominant_color_name=p.name,
        color_palette=[c.rgb for c in colors],
        color_hex=p.hex_code,
        category=rec.ClothingCategory(f.category.value),
        gender=rec.Gender(f.gender if f.gender in ("male", "female", "unisex") else "unisex"),
        style=rec.StyleType(style),
        design=f.design_pattern.value,
        fabric=f.fabric_type or "unknown",
        weather=rec.WeatherType(f.weather.value),
        formality_level=f.formality_level,
        confidence=item.analysis_confidence,
    )


def _reco_skin(profile: Optional[UserProfile]) -> rec.SkinFeatures:
    sf = profile.skin_features if profile else None
    depth = (sf.depth or sf.skin_depth) if sf else None
    if not sf or not sf.undertone or not depth or sf.lab_l is None or sf.lab_a is None or sf.lab_b is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={"message": "Complete the selfie analysis before getting recommendations", "code": "profile_incomplete"},
        )
    season = sf.season or sf.seasonal_type
    return rec.SkinFeatures(
        undertone=rec.Undertone(sf.undertone.value),
        skin_depth=rec.SkinDepth(depth.value),
        lab_l=sf.lab_l, lab_a=sf.lab_a, lab_b=sf.lab_b,
        skin_rgb=sf.skin_rgb,
        season=rec.Season(season.value) if season else None,
        confidence=sf.confidence_score or 0.5,
    )


def _reco_preferences(profile: Optional[UserProfile], occasion: Optional[str]) -> rec.UserPreferences:
    sp = profile.style_preferences if profile else None
    styles: List[rec.StyleType] = []
    if sp:
        for s in ([sp.primary_style] if sp.primary_style else []) + list(sp.secondary_styles):
            value = s.value if s.value in RECO_STYLES else None
            if value and rec.StyleType(value) not in styles:
                styles.append(rec.StyleType(value))
    return rec.UserPreferences(
        preferred_styles=styles,
        preferred_colors=list(dict.fromkeys((sp.favorite_colors + sp.preferred_colors) if sp else [])),
        avoided_colors=list(dict.fromkeys((sp.avoided_colors + sp.avoid_colors) if sp else [])),
        target_occasion=occasion,
    )


def _ranked(r: rec.ClothRecommendation, items: Dict[str, ClothingItem]) -> Optional[RankedItem]:
    item = items.get(r.cloth_id)
    if item is None:
        return None
    b = r.score_breakdown
    return RankedItem(
        rank=r.rank,
        item=to_view(item),
        overall_score=r.overall_score,
        recommendation_level=r.recommendation_level,
        color_score=b.color_score,
        style_score=b.style_score,
        formality_score=b.formality_score,
        confidence_score=b.confidence_score,
        reasoning=b.overall_reasoning,
    )


# ---------------------------------------------------------------- service

class WardrobeService:

    async def add_item(self, user_id: str, data: bytes, name: Optional[str]) -> ClothingItem:
        jpeg = _prepare_image(data)

        result = await analyze_clothing(
            ClothInput(image_base64=base64.b64encode(jpeg).decode()),
            use_clip=settings.USE_CLIP,
        )
        if not result.success or result.features is None:
            logger.error(f"Clothing analysis failed: {result.error}")
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Could not analyze this photo. Try a clear picture of one garment.", "code": "analysis_failed"},
            )
        a = result.features

        group = CATEGORY_GROUP.get(a.category.value)
        colors = _order_colors([
            ColorInfo(name=c.name, hex_code=c.hex_code, rgb=c.rgb, percentage=c.percentage)
            for c in a.dominant_colors
        ])
        if not colors:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "No clothing colours could be detected in this photo", "code": "analysis_failed"},
            )

        needs_review = (
            group is None
            or a.category_confidence < CATEGORY_REVIEW_THRESHOLD
            or a.style_confidence < STYLE_REVIEW_THRESHOLD
        )
        features = ClothingFeatures(
            dominant_colors=colors,
            design_pattern=DesignPattern(a.design_pattern.value),
            category=DbCategory(group) if group else DbCategory.UNKNOWN,
            weather=DbWeather(a.weather.value),
            style=DbStyle(a.style.value),
            formality_level=min(10, max(1, a.formality_level * 2)),  # analyzer scale is 1-5
            fabric_type=None if a.fabric.value == "unknown" else a.fabric.value,
            subcategory=a.category.value if a.category.value != "unknown" else None,
            needs_review=needs_review,
            confidence_scores={
                "category": a.category_confidence, "style": a.style_confidence,
                "design": a.design_confidence, "weather": a.weather_confidence,
                "formality": a.formality_confidence,
            },
        )

        path = _store_image(user_id, jpeg)
        try:
            item = ClothingItem(
                user_id=PydanticObjectId(user_id),
                name=(name or "").strip() or (a.category.value.replace("_", " ").title() if group else "New item"),
                image_path=path,
                features=features,
                analysis_confidence=a.overall_confidence,
            )
            await item.insert()
            item.image_url = f"/api/wardrobe/items/{item.id}/image"
            await item.save()
        except Exception:
            _delete_image(path)
            raise
        return item

    async def get_owned(self, user_id: str, item_id: str) -> ClothingItem:
        try:
            item = await ClothingItem.get(PydanticObjectId(item_id))
        except Exception:
            item = None
        if item is None or str(item.user_id) != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found")
        return item

    async def list_items(self, user_id: str, category=None, favorite=None, needs_review=None) -> List[ClothingItem]:
        query = {"user_id": PydanticObjectId(user_id)}
        if category:
            query["features.category"] = category
        if favorite is not None:
            query["is_favorite"] = favorite
        if needs_review is not None:
            query["features.needs_review"] = needs_review
        return await ClothingItem.find(query).sort("-created_at").to_list()

    async def update_item(self, user_id: str, item_id: str, upd: WardrobeItemUpdate) -> ClothingItem:
        item = await self.get_owned(user_id, item_id)
        f = item.features
        if upd.name is not None:
            item.name = upd.name.strip() or item.name
        if upd.category is not None:
            f.category = DbCategory(upd.category)
        if upd.style is not None:
            f.style = DbStyle(upd.style)
        if upd.formality_level is not None:
            f.formality_level = upd.formality_level
        if upd.primary_color_name or upd.primary_color_hex:
            primary = f.dominant_colors[0].model_copy()
            if upd.primary_color_name:
                primary.name = upd.primary_color_name.strip().lower()
            if upd.primary_color_hex:
                h = upd.primary_color_hex.lstrip("#")
                primary.hex_code = "#" + h.lower()
                primary.rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
            f.dominant_colors = [primary] + f.dominant_colors[1:]
        if upd.tags is not None:
            item.tags = [t.strip() for t in upd.tags if t.strip()][:20]
        if any(v is not None for v in (upd.category, upd.style, upd.formality_level)):
            f.user_corrected = True
            f.needs_review = False
        item.updated_at = datetime.utcnow()
        await item.save()
        return item

    async def toggle_favorite(self, user_id: str, item_id: str) -> ClothingItem:
        item = await self.get_owned(user_id, item_id)
        item.is_favorite = not item.is_favorite
        item.updated_at = datetime.utcnow()
        await item.save()
        return item

    async def delete_item(self, user_id: str, item_id: str) -> None:
        item = await self.get_owned(user_id, item_id)
        _delete_image(item.image_path)
        await item.delete()

    # ------------------------------------------------ recommendations

    async def _load_context(self, user_id: str, occasion: Optional[str]):
        profile = await UserProfile.find_one(UserProfile.user_id == PydanticObjectId(user_id))
        skin = _reco_skin(profile)  # raises 409 when the selfie analysis is missing
        prefs = _reco_preferences(profile, occasion)
        all_items = await self.list_items(user_id)
        rankable = [i for i in all_items if i.features.category != DbCategory.UNKNOWN and i.features.dominant_colors]
        return skin, prefs, rankable, len(all_items) - len(rankable)

    async def recommendations(self, user_id: str, top_k: int, occasion: Optional[str]) -> WardrobeRecommendations:
        skin, prefs, items, excluded = await self._load_context(user_id, occasion)
        if not items:
            return WardrobeRecommendations(
                excluded_needs_review=excluded,
                reason="empty_wardrobe" if excluded == 0 else "no_categorised_items",
            )
        by_id = {str(i.id): i for i in items}
        resp = await get_recommendation_service().get_recommendations(
            rec.RecommendationRequest(
                skin_features=skin,
                available_clothes=[to_reco_cloth(i) for i in items],
                preferences=prefs,
                top_k=top_k,
            )
        )
        ranked = [r for r in (_ranked(x, by_id) for x in resp.recommendations) if r]
        return WardrobeRecommendations(
            detected_season=resp.detected_season.value,
            undertone=resp.undertone.value,
            best_colors=resp.best_colors,
            colors_to_avoid=resp.colors_to_avoid,
            recommendations=ranked,
            total_evaluated=resp.total_evaluated,
            excluded_needs_review=excluded,
        )

    async def outfits(self, user_id: str, occasion: Optional[str]) -> OutfitSuggestions:
        skin, prefs, items, _ = await self._load_context(user_id, occasion)
        by_id = {str(i.id): i for i in items}
        clothes = [to_reco_cloth(i) for i in items]
        service = get_recommendation_service()

        outfits: List[OutfitView] = []
        for label, cats in (("tb", [rec.ClothingCategory.TOP, rec.ClothingCategory.BOTTOM]),
                            ("dr", [rec.ClothingCategory.DRESS])):
            if not any(c.category in cats for c in clothes):
                continue
            resp = await service.get_outfit_recommendations(
                rec.OutfitRecommendationRequest(
                    skin_features=skin, available_clothes=clothes,
                    preferences=prefs, include_categories=cats,
                )
            )
            for o in resp.outfits:
                ranked = [r for r in (_ranked(x, by_id) for x in o.items) if r]
                if len(ranked) == len(o.items) and ranked:
                    outfits.append(OutfitView(
                        outfit_id=f"{label}-" + "-".join(sorted(r.item.id[-6:] for r in ranked)),
                        items=ranked, outfit_score=o.outfit_score, reasoning=o.outfit_reasoning,
                    ))
        outfits.sort(key=lambda o: o.outfit_score, reverse=True)
        if not outfits:
            return OutfitSuggestions(reason="need_top_and_bottom_or_dress")
        return OutfitSuggestions(outfits=outfits[:10])

    # ------------------------------------------------ saved outfits

    async def save_outfit(self, user_id: str, name: str, item_ids: List[str], score: float,
                          reasoning: Optional[str], occasion: Optional[str]) -> SavedOutfit:
        uid = PydanticObjectId(user_id)
        ids = list(dict.fromkeys(item_ids))
        if len(ids) < 2:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "An outfit needs at least two different items")
        items = [await self.get_owned(user_id, i) for i in ids]  # 404 for foreign/missing items

        wanted = {i.id for i in items}
        for existing in await DbOutfit.find(DbOutfit.user_id == uid, DbOutfit.is_saved == True).to_list():  # noqa: E712
            if set(existing.clothing_item_ids) == wanted:
                return self._saved_view(existing, items)  # idempotent

        doc = DbOutfit(
            user_id=uid, outfit_name=name, clothing_item_ids=[i.id for i in items],
            overall_score=score, reasoning=reasoning, occasion=occasion, is_saved=True,
        )
        await doc.insert()
        return self._saved_view(doc, items)

    def _saved_view(self, doc: DbOutfit, items: List[ClothingItem]) -> SavedOutfit:
        return SavedOutfit(
            id=str(doc.id), name=doc.outfit_name, items=[to_view(i) for i in items],
            score=doc.overall_score, reasoning=doc.reasoning, occasion=doc.occasion, created_at=doc.created_at,
        )

    async def saved_outfits(self, user_id: str) -> List[SavedOutfit]:
        uid = PydanticObjectId(user_id)
        docs = await DbOutfit.find(DbOutfit.user_id == uid, DbOutfit.is_saved == True).sort("-created_at").to_list()  # noqa: E712
        result: List[SavedOutfit] = []
        for d in docs:
            found = [i for i in [await ClothingItem.get(x) for x in d.clothing_item_ids]
                     if i is not None and i.user_id == uid]
            if len(found) >= 2:  # hide outfits whose items were deleted
                result.append(self._saved_view(d, found))
        return result

    async def delete_saved_outfit(self, user_id: str, outfit_id: str) -> None:
        try:
            doc = await DbOutfit.get(PydanticObjectId(outfit_id))
        except Exception:
            doc = None
        if doc is None or str(doc.user_id) != user_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Saved outfit not found")
        await doc.delete()


_service: Optional[WardrobeService] = None


def get_wardrobe_service() -> WardrobeService:
    global _service
    if _service is None:
        _service = WardrobeService()
    return _service

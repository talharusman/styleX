"""
Clothing Repository - MongoDB operations for clothing items.

Provides CRUD operations for ClothingItem, AnalysisResult, and OutfitRecommendation documents.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from beanie import PydanticObjectId

from app.database.models import (
    ClothingItem, AnalysisResult, OutfitRecommendation,
    ClothingFeatures, ClothingCategory, StyleType
)

logger = logging.getLogger(__name__)


class ClothingRepository:
    """Repository for ClothingItem CRUD operations."""
    
    # ==========================================
    # CLOTHING ITEM OPERATIONS
    # ==========================================
    
    async def create_clothing_item(
        self,
        user_id: str | PydanticObjectId,
        image_url: str,
        features: Optional[ClothingFeatures] = None,
        **kwargs
    ) -> ClothingItem:
        """
        Create a new clothing item.
        
        Args:
            user_id: Owner user ID
            image_url: URL or path to clothing image
            features: Extracted clothing features
            **kwargs: Additional fields (name, brand, price, etc.)
            
        Returns:
            Created ClothingItem document
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        item = ClothingItem(
            user_id=user_id,
            image_url=image_url,
            features=features or ClothingFeatures(),
            **kwargs
        )
        await item.insert()
        
        logger.info(f"Created clothing item for user: {user_id}")
        return item
    
    async def get_clothing_item(self, item_id: str | PydanticObjectId) -> Optional[ClothingItem]:
        """Get clothing item by ID."""
        if isinstance(item_id, str):
            try:
                item_id = PydanticObjectId(item_id)
            except Exception:
                return None
        return await ClothingItem.get(item_id)
    
    async def get_user_clothing(
        self,
        user_id: str | PydanticObjectId,
        category: Optional[ClothingCategory] = None,
        style: Optional[StyleType] = None,
        is_favorite: Optional[bool] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[ClothingItem]:
        """
        Get user's clothing items with optional filters.
        
        Args:
            user_id: User ID
            category: Filter by clothing category
            style: Filter by style type
            is_favorite: Filter by favorite status
            limit: Maximum items to return
            skip: Number of items to skip
            
        Returns:
            List of ClothingItem documents
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        # Build query
        query = ClothingItem.find(ClothingItem.user_id == user_id)
        
        if category:
            query = query.find({"features.category": category.value})
        if style:
            query = query.find({"features.style": style.value})
        if is_favorite is not None:
            query = query.find(ClothingItem.is_favorite == is_favorite)
        
        return await query.skip(skip).limit(limit).to_list()
    
    async def update_clothing_item(
        self,
        item_id: str | PydanticObjectId,
        **updates
    ) -> Optional[ClothingItem]:
        """Update clothing item fields."""
        item = await self.get_clothing_item(item_id)
        if not item:
            return None
        
        updates['updated_at'] = datetime.utcnow()
        await item.update({"$set": updates})
        return await self.get_clothing_item(item_id)
    
    async def delete_clothing_item(self, item_id: str | PydanticObjectId) -> bool:
        """Delete a clothing item."""
        item = await self.get_clothing_item(item_id)
        if not item:
            return False
        
        await item.delete()
        logger.info(f"Deleted clothing item: {item_id}")
        return True
    
    async def toggle_favorite(self, item_id: str | PydanticObjectId) -> Optional[ClothingItem]:
        """Toggle favorite status of a clothing item."""
        item = await self.get_clothing_item(item_id)
        if not item:
            return None
        
        await item.update({"$set": {
            "is_favorite": not item.is_favorite,
            "updated_at": datetime.utcnow()
        }})
        return await self.get_clothing_item(item_id)
    
    async def record_wear(self, item_id: str | PydanticObjectId) -> Optional[ClothingItem]:
        """Record that an item was worn."""
        item = await self.get_clothing_item(item_id)
        if not item:
            return None
        
        await item.update({"$set": {
            "times_worn": item.times_worn + 1,
            "last_worn": datetime.utcnow().date(),
            "updated_at": datetime.utcnow()
        }})
        return await self.get_clothing_item(item_id)
    
    async def get_wardrobe_stats(self, user_id: str | PydanticObjectId) -> Dict[str, Any]:
        """Get wardrobe statistics for a user."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$group": {
                "_id": None,
                "total_items": {"$sum": 1},
                "favorites": {"$sum": {"$cond": ["$is_favorite", 1, 0]}},
                "total_worn": {"$sum": "$times_worn"},
                "categories": {"$addToSet": "$features.category"},
                "styles": {"$addToSet": "$features.style"}
            }}
        ]
        
        result = await ClothingItem.aggregate(pipeline).to_list()
        if result:
            return result[0]
        return {
            "total_items": 0,
            "favorites": 0,
            "total_worn": 0,
            "categories": [],
            "styles": []
        }
    
    async def search_clothing(
        self,
        user_id: str | PydanticObjectId,
        query: str = None,
        filters: Dict[str, Any] = None,
        limit: int = 20
    ) -> List[ClothingItem]:
        """
        Search clothing items with text query and filters.
        
        Args:
            user_id: User ID
            query: Text search query
            filters: Additional filters
            limit: Maximum results
            
        Returns:
            Matching clothing items
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        match_conditions = {"user_id": user_id}
        
        if query:
            match_conditions["$or"] = [
                {"name": {"$regex": query, "$options": "i"}},
                {"brand": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query.lower()]}}
            ]
        
        if filters:
            if 'categories' in filters:
                match_conditions["features.category"] = {"$in": filters['categories']}
            if 'styles' in filters:
                match_conditions["features.style"] = {"$in": filters['styles']}
            if 'min_formality' in filters:
                match_conditions["features.formality_level"] = {"$gte": filters['min_formality']}
            if 'max_formality' in filters:
                match_conditions.setdefault("features.formality_level", {})
                match_conditions["features.formality_level"]["$lte"] = filters['max_formality']
        
        return await ClothingItem.find(match_conditions).limit(limit).to_list()
    
    # ==========================================
    # ANALYSIS RESULT OPERATIONS
    # ==========================================
    
    async def save_analysis_result(
        self,
        analysis_type: str,
        results: Dict[str, Any],
        user_id: Optional[str | PydanticObjectId] = None,
        image_url: Optional[str] = None,
        image_hash: Optional[str] = None,
        confidence_score: float = 0.0,
        processing_time_ms: float = 0.0,
        **kwargs
    ) -> AnalysisResult:
        """Save an analysis result."""
        if user_id and isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        result = AnalysisResult(
            user_id=user_id,
            analysis_type=analysis_type,
            results=results,
            image_url=image_url,
            image_hash=image_hash,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            **kwargs
        )
        await result.insert()
        return result
    
    async def get_analysis_by_hash(self, image_hash: str) -> Optional[AnalysisResult]:
        """Get cached analysis result by image hash."""
        return await AnalysisResult.find_one(AnalysisResult.image_hash == image_hash)
    
    async def get_user_analysis_history(
        self,
        user_id: str | PydanticObjectId,
        analysis_type: Optional[str] = None,
        limit: int = 20
    ) -> List[AnalysisResult]:
        """Get user's analysis history."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        query = AnalysisResult.find(AnalysisResult.user_id == user_id)
        
        if analysis_type:
            query = query.find(AnalysisResult.analysis_type == analysis_type)
        
        return await query.sort(-AnalysisResult.created_at).limit(limit).to_list()
    
    # ==========================================
    # OUTFIT RECOMMENDATION OPERATIONS
    # ==========================================
    
    async def save_outfit_recommendation(
        self,
        user_id: str | PydanticObjectId,
        outfit_name: str,
        clothing_item_ids: List[str | PydanticObjectId],
        overall_score: float = 0.0,
        **kwargs
    ) -> OutfitRecommendation:
        """Save an outfit recommendation."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        # Convert item IDs
        item_ids = [
            PydanticObjectId(id) if isinstance(id, str) else id
            for id in clothing_item_ids
        ]
        
        recommendation = OutfitRecommendation(
            user_id=user_id,
            outfit_name=outfit_name,
            clothing_item_ids=item_ids,
            overall_score=overall_score,
            **kwargs
        )
        await recommendation.insert()
        return recommendation
    
    async def get_outfit_recommendation(
        self,
        recommendation_id: str | PydanticObjectId
    ) -> Optional[OutfitRecommendation]:
        """Get outfit recommendation by ID."""
        if isinstance(recommendation_id, str):
            try:
                recommendation_id = PydanticObjectId(recommendation_id)
            except Exception:
                return None
        return await OutfitRecommendation.get(recommendation_id)
    
    async def get_user_recommendations(
        self,
        user_id: str | PydanticObjectId,
        is_saved: Optional[bool] = None,
        limit: int = 20
    ) -> List[OutfitRecommendation]:
        """Get user's outfit recommendations."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        query = OutfitRecommendation.find(OutfitRecommendation.user_id == user_id)
        
        if is_saved is not None:
            query = query.find(OutfitRecommendation.is_saved == is_saved)
        
        return await query.sort(-OutfitRecommendation.created_at).limit(limit).to_list()
    
    async def toggle_save_recommendation(
        self,
        recommendation_id: str | PydanticObjectId
    ) -> Optional[OutfitRecommendation]:
        """Toggle saved status of a recommendation."""
        rec = await self.get_outfit_recommendation(recommendation_id)
        if not rec:
            return None
        
        await rec.update({"$set": {
            "is_saved": not rec.is_saved,
            "updated_at": datetime.utcnow()
        }})
        return await self.get_outfit_recommendation(recommendation_id)
    
    async def rate_recommendation(
        self,
        recommendation_id: str | PydanticObjectId,
        rating: int
    ) -> Optional[OutfitRecommendation]:
        """Rate an outfit recommendation."""
        rec = await self.get_outfit_recommendation(recommendation_id)
        if not rec:
            return None
        
        await rec.update({"$set": {
            "user_rating": rating,
            "updated_at": datetime.utcnow()
        }})
        return await self.get_outfit_recommendation(recommendation_id)


# Singleton repository instance
clothing_repository = ClothingRepository()


def get_clothing_repository() -> ClothingRepository:
    """Get the clothing repository instance."""
    return clothing_repository

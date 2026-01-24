"""
Chat Repository - MongoDB operations for Chat message management.

Provides CRUD operations for ChatMessage documents.
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from beanie import PydanticObjectId
import uuid

from app.database.models import ChatMessage

logger = logging.getLogger(__name__)


class ChatRepository:
    """Repository for Chat CRUD operations."""
    
    async def create_message(
        self,
        user_id: str | PydanticObjectId,
        message: str,
        message_type: str = "user",
        session_id: Optional[str] = None,
        response: Optional[str] = None,
        context: Optional[dict] = None,
        model: Optional[str] = None,
        tokens_used: Optional[int] = None,
        processing_time_ms: Optional[float] = None
    ) -> ChatMessage:
        """
        Create a new chat message.
        
        Args:
            user_id: User ID
            message: User message content
            message_type: Type of message ("user", "assistant", "system")
            session_id: Conversation session ID
            response: AI response (if assistant message)
            context: Additional context data
            model: AI model used
            tokens_used: Tokens consumed
            processing_time_ms: Processing time
            
        Returns:
            Created ChatMessage document
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        chat_message = ChatMessage(
            user_id=user_id,
            session_id=session_id,
            message_type=message_type,
            message=message,
            response=response,
            context=context or {},
            model=model,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms
        )
        
        await chat_message.insert()
        logger.debug(f"Created chat message for user: {user_id}")
        return chat_message
    
    async def get_conversation_history(
        self,
        user_id: str | PydanticObjectId,
        session_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Get conversation history for a user.
        
        Args:
            user_id: User ID
            session_id: Optional session ID to filter by
            limit: Maximum number of messages
            offset: Number of messages to skip
            
        Returns:
            List of ChatMessage documents
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        query = ChatMessage.find(ChatMessage.user_id == user_id)
        
        if session_id:
            query = ChatMessage.find(
                ChatMessage.user_id == user_id,
                ChatMessage.session_id == session_id
            )
        
        messages = await query.sort(-ChatMessage.created_at).skip(offset).limit(limit).to_list()
        
        # Return in chronological order
        return list(reversed(messages))
    
    async def get_recent_sessions(
        self,
        user_id: str | PydanticObjectId,
        limit: int = 10
    ) -> List[dict]:
        """
        Get recent chat sessions for a user.
        
        Returns list of session summaries with first message and message count.
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        # Aggregate to get unique sessions with counts
        pipeline = [
            {"$match": {"user_id": user_id}},
            {"$sort": {"created_at": -1}},
            {"$group": {
                "_id": "$session_id",
                "first_message": {"$last": "$message"},
                "last_message_at": {"$first": "$created_at"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_message_at": -1}},
            {"$limit": limit}
        ]
        
        results = await ChatMessage.aggregate(pipeline).to_list()
        
        return [
            {
                "session_id": r["_id"],
                "first_message": r["first_message"][:100] + "..." if len(r["first_message"]) > 100 else r["first_message"],
                "last_message_at": r["last_message_at"],
                "message_count": r["message_count"]
            }
            for r in results
        ]
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[ChatMessage]:
        """Get all messages for a specific session."""
        messages = await ChatMessage.find(
            ChatMessage.session_id == session_id
        ).sort(ChatMessage.created_at).limit(limit).to_list()
        
        return messages
    
    async def delete_session(
        self,
        user_id: str | PydanticObjectId,
        session_id: str
    ) -> int:
        """
        Delete all messages in a session.
        
        Returns number of deleted messages.
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        result = await ChatMessage.find(
            ChatMessage.user_id == user_id,
            ChatMessage.session_id == session_id
        ).delete()
        
        return result.deleted_count if result else 0
    
    async def delete_user_chat_history(
        self,
        user_id: str | PydanticObjectId
    ) -> int:
        """
        Delete all chat history for a user.
        
        Returns number of deleted messages.
        """
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        result = await ChatMessage.find(
            ChatMessage.user_id == user_id
        ).delete()
        
        logger.info(f"Deleted chat history for user: {user_id}")
        return result.deleted_count if result else 0
    
    async def get_message_count(
        self,
        user_id: str | PydanticObjectId,
        since: Optional[datetime] = None
    ) -> int:
        """Get total message count for a user."""
        if isinstance(user_id, str):
            user_id = PydanticObjectId(user_id)
        
        query = ChatMessage.find(ChatMessage.user_id == user_id)
        
        if since:
            query = ChatMessage.find(
                ChatMessage.user_id == user_id,
                ChatMessage.created_at >= since
            )
        
        return await query.count()
    
    async def cleanup_old_messages(
        self,
        days_old: int = 90
    ) -> int:
        """
        Delete messages older than specified days.
        
        Returns number of deleted messages.
        """
        cutoff = datetime.utcnow() - timedelta(days=days_old)
        
        result = await ChatMessage.find(
            ChatMessage.created_at < cutoff
        ).delete()
        
        deleted = result.deleted_count if result else 0
        logger.info(f"Cleaned up {deleted} old chat messages")
        return deleted


# Singleton repository instance
chat_repository = ChatRepository()


def get_chat_repository() -> ChatRepository:
    """Get the chat repository instance."""
    return chat_repository

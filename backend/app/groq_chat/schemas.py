"""
Pydantic schemas for Groq Chat endpoints
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Single message in a conversation"""
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    message: str = Field(..., min_length=1, max_length=4000, description="User's message")
    conversation_history: Optional[List[ChatMessage]] = Field(
        default=None,
        description="Previous messages for context"
    )
    context_type: Optional[str] = Field(
        default=None,
        description="Type of context: 'style', 'weather', 'calendar', 'general'"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalized responses"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID for conversation continuity"
    )


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    response: str
    tokens_used: Optional[int] = None
    model: str = "llama-3.3-70b-versatile"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StyleAdviceRequest(BaseModel):
    """Request for AI-powered style advice"""
    query: str = Field(..., description="Style-related question")
    body_type: Optional[str] = None
    skin_tone: Optional[str] = None
    style_preference: Optional[str] = None
    weather_condition: Optional[str] = None
    occasion: Optional[str] = None


class StyleAdviceResponse(BaseModel):
    """Response with style recommendations"""
    advice: str
    outfit_suggestions: Optional[List[str]] = None
    color_palette: Optional[List[str]] = None
    confidence_score: Optional[float] = None


class ConversationContext(BaseModel):
    """Context for maintaining conversation state"""
    user_id: str
    messages: List[ChatMessage]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None

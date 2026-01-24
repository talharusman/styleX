"""
Groq Chat Router - API endpoints for AI chatbot functionality with MongoDB persistence
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
import logging
import uuid

from .schemas import (
    ChatRequest,
    ChatResponse,
    StyleAdviceRequest,
    StyleAdviceResponse,
    ChatMessage
)
from .service import GroqChatService, get_groq_service
from app.database import (
    chat_repository,
    get_chat_repository,
    user_repository,
    get_user_repository,
)
from app.auth.jwt_handler import get_current_user, get_current_user_optional, UserAuth

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["AI Chat"],
    responses={
        500: {"description": "Internal server error"},
        503: {"description": "AI service unavailable"}
    }
)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with AI",
    description="Send a message to the AI assistant and receive a response"
)
async def chat(
    request: ChatRequest,
    service: GroqChatService = Depends(get_groq_service),
    current_user: Optional[UserAuth] = Depends(get_current_user_optional)
) -> ChatResponse:
    """
    Chat with the AI assistant.
    
    - **message**: The user's message to the AI
    - **conversation_history**: Optional previous messages for context
    - **context_type**: Type of conversation ('general', 'style', 'weather', 'calendar')
    - **session_id**: Optional session ID for conversation continuity
    
    Returns the AI's response with metadata.
    """
    try:
        chat_repo = get_chat_repository()
        user_repo = get_user_repository()
        
        # Get user context if authenticated
        user_context = None
        user_id = current_user.user_id if current_user else request.user_id
        
        if user_id:
            # Fetch user profile for personalized responses
            profile = await user_repo.get_user_profile(user_id)
            if profile:
                user_context = {
                    "body_type": profile.body_measurements.body_type if profile.body_measurements else None,
                    "skin_tone": profile.skin_features.depth.value if profile.skin_features and profile.skin_features.depth else None,
                    "style_preference": profile.style_preferences.primary_style.value if profile.style_preferences and profile.style_preferences.primary_style else None
                }
        
        # Get or create session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # Call AI service
        import time
        start_time = time.time()
        
        response = await service.chat(
            user_message=request.message,
            conversation_history=request.conversation_history,
            context_type=request.context_type or "general",
            user_context=user_context
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        # Persist chat to database if user is authenticated
        if user_id:
            await chat_repo.create_message(
                user_id=user_id,
                message=request.message,
                message_type="user",
                session_id=session_id,
                response=response.response,
                context=user_context,
                model=response.model,
                tokens_used=response.tokens_used,
                processing_time_ms=processing_time
            )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )


@router.get(
    "/history",
    summary="Get Chat History",
    description="Retrieve conversation history for the authenticated user"
)
async def get_chat_history(
    session_id: Optional[str] = None,
    limit: int = 50,
    current_user: UserAuth = Depends(get_current_user)
) -> dict:
    """
    Get chat history for the authenticated user.
    
    - **session_id**: Optional filter by specific conversation session
    - **limit**: Maximum number of messages to return
    """
    chat_repo = get_chat_repository()
    
    messages = await chat_repo.get_conversation_history(
        user_id=current_user.user_id,
        session_id=session_id,
        limit=limit
    )
    
    return {
        "messages": [
            {
                "id": str(msg.id),
                "message": msg.message,
                "response": msg.response,
                "message_type": msg.message_type,
                "session_id": msg.session_id,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "count": len(messages)
    }


@router.get(
    "/sessions",
    summary="Get Chat Sessions",
    description="Get list of recent chat sessions"
)
async def get_chat_sessions(
    limit: int = 10,
    current_user: UserAuth = Depends(get_current_user)
) -> dict:
    """Get recent chat sessions for the user."""
    chat_repo = get_chat_repository()
    
    sessions = await chat_repo.get_recent_sessions(
        user_id=current_user.user_id,
        limit=limit
    )
    
    return {"sessions": sessions}


@router.delete(
    "/sessions/{session_id}",
    summary="Delete Chat Session",
    description="Delete a specific chat session"
)
async def delete_chat_session(
    session_id: str,
    current_user: UserAuth = Depends(get_current_user)
) -> dict:
    """Delete a chat session and all its messages."""
    chat_repo = get_chat_repository()
    
    deleted = await chat_repo.delete_session(
        user_id=current_user.user_id,
        session_id=session_id
    )
    
    return {"deleted": deleted, "session_id": session_id}


@router.post(
    "/style-advice",
    response_model=StyleAdviceResponse,
    summary="Get Style Advice",
    description="Get personalized fashion and style advice from the AI"
)
async def get_style_advice(
    request: StyleAdviceRequest,
    service: GroqChatService = Depends(get_groq_service)
) -> StyleAdviceResponse:
    """
    Get personalized style advice.
    
    - **query**: The style question or request
    - **body_type**: User's body type for personalized advice
    - **skin_tone**: User's skin tone for color recommendations
    - **style_preference**: User's preferred style (casual, formal, etc.)
    - **weather_condition**: Current weather for practical suggestions
    - **occasion**: The occasion for the outfit
    
    Returns detailed style advice with outfit suggestions and color palettes.
    """
    try:
        response = await service.get_style_advice(
            query=request.query,
            body_type=request.body_type,
            skin_tone=request.skin_tone,
            style_preference=request.style_preference,
            weather_condition=request.weather_condition,
            occasion=request.occasion
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Style advice endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )


@router.post(
    "/weather-outfit",
    summary="Get Weather-Based Outfit",
    description="Get outfit recommendation based on current weather"
)
async def get_weather_outfit(
    temperature: float,
    condition: str,
    humidity: Optional[int] = None,
    style_preference: Optional[str] = None,
    service: GroqChatService = Depends(get_groq_service)
) -> dict:
    """
    Get outfit recommendation based on weather conditions.
    
    - **temperature**: Current temperature
    - **condition**: Weather condition (sunny, rainy, cloudy, etc.)
    - **humidity**: Optional humidity percentage
    - **style_preference**: User's style preference
    
    Returns outfit recommendation for the weather.
    """
    try:
        weather_data = {
            "temperature": temperature,
            "condition": condition,
            "humidity": humidity or 50
        }
        
        recommendation = await service.get_outfit_for_weather(
            weather_data=weather_data,
            style_preference=style_preference
        )
        
        return {
            "recommendation": recommendation,
            "weather": weather_data
        }
        
    except Exception as e:
        logger.error(f"Weather outfit endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )


@router.post(
    "/event-outfit",
    summary="Get Event-Based Outfit",
    description="Get outfit recommendation for a specific event"
)
async def get_event_outfit(
    event_title: str,
    event_time: str,
    location: Optional[str] = None,
    body_type: Optional[str] = None,
    skin_tone: Optional[str] = None,
    style_preference: Optional[str] = None,
    service: GroqChatService = Depends(get_groq_service)
) -> dict:
    """
    Get outfit recommendation for a calendar event.
    
    - **event_title**: Name/title of the event
    - **event_time**: When the event is scheduled
    - **location**: Optional event location
    - **body_type**: User's body type
    - **skin_tone**: User's skin tone
    - **style_preference**: User's style preference
    
    Returns outfit recommendation for the event.
    """
    try:
        user_context = {
            "body_type": body_type,
            "skin_tone": skin_tone,
            "style_preference": style_preference
        }
        
        recommendation = await service.get_outfit_for_event(
            event_title=event_title,
            event_time=event_time,
            location=location,
            user_context=user_context
        )
        
        return {
            "recommendation": recommendation,
            "event": {
                "title": event_title,
                "time": event_time,
                "location": location
            }
        }
        
    except Exception as e:
        logger.error(f"Event outfit endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI service error: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health Check",
    description="Check if the AI chat service is available"
)
async def health_check(
    service: GroqChatService = Depends(get_groq_service)
) -> dict:
    """
    Check the health of the AI chat service.
    
    Returns service status and model information.
    """
    try:
        # Quick test to verify the service is working
        return {
            "status": "healthy",
            "model": service.model,
            "service": "groq"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

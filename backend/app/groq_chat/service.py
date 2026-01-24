"""
Groq Chat Service - Handles interactions with Groq LLM API
"""

import os
import logging
from typing import Optional, List, Dict, Any
from groq import Groq
from .schemas import ChatMessage, MessageRole, ChatResponse, StyleAdviceResponse

logger = logging.getLogger(__name__)


class GroqChatService:
    """Service for interacting with Groq LLM API"""
    
    # System prompts for different contexts
    SYSTEM_PROMPTS = {
        "general": """You are StyleX AI, a friendly and knowledgeable personal styling assistant. 
You help users with fashion advice, outfit recommendations, and lifestyle tips. 
Be concise, helpful, and personalized in your responses.""",
        
        "style": """You are StyleX AI, an expert fashion stylist and personal shopper. 
You provide personalized outfit recommendations based on body type, skin tone, weather, and occasion.
Consider color theory, seasonal trends, and individual preferences.
Give specific, actionable advice with outfit combinations.""",
        
        "weather": """You are StyleX AI, helping users dress appropriately for the weather.
Consider temperature, precipitation, humidity, and wind conditions.
Suggest practical yet stylish outfit choices for the weather conditions.""",
        
        "calendar": """You are StyleX AI, helping users plan outfits for their scheduled events.
Consider the type of event, dress code, time of day, and venue.
Provide outfit suggestions that are appropriate and stylish for each occasion."""
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq client
        
        Args:
            api_key: Groq API key. If not provided, uses environment variable.
        """
        self.api_key = api_key or os.getenv(
            "GROQ_API_KEY", 
        )
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"
        
    async def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[ChatMessage]] = None,
        context_type: str = "general",
        user_context: Optional[Dict[str, Any]] = None
    ) -> ChatResponse:
        """
        Send a message to Groq LLM and get a response
        
        Args:
            user_message: The user's input message
            conversation_history: Previous messages for context
            context_type: Type of context ('general', 'style', 'weather', 'calendar')
            user_context: Additional user context (preferences, profile data)
            
        Returns:
            ChatResponse with the AI's response
        """
        try:
            messages = self._build_messages(
                user_message, 
                conversation_history, 
                context_type,
                user_context
            )
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                top_p=0.9,
                stream=False
            )
            
            response_content = completion.choices[0].message.content
            tokens_used = getattr(completion.usage, 'total_tokens', None)
            
            return ChatResponse(
                response=response_content,
                tokens_used=tokens_used,
                model=self.model
            )
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {str(e)}")
            raise Exception(f"Failed to get response from AI: {str(e)}")
    
    def _build_messages(
        self,
        user_message: str,
        conversation_history: Optional[List[ChatMessage]],
        context_type: str,
        user_context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Build the messages array for the API call"""
        messages = []
        
        # Add system prompt based on context type
        system_prompt = self.SYSTEM_PROMPTS.get(context_type, self.SYSTEM_PROMPTS["general"])
        
        # Enhance system prompt with user context
        if user_context:
            context_info = self._format_user_context(user_context)
            system_prompt += f"\n\nUser Profile:\n{context_info}"
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        if conversation_history:
            for msg in conversation_history[-10:]:  # Keep last 10 messages for context
                messages.append({"role": msg.role, "content": msg.content})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _format_user_context(self, user_context: Dict[str, Any]) -> str:
        """Format user context into a readable string for the prompt"""
        context_parts = []
        
        if user_context.get("body_type"):
            context_parts.append(f"- Body Type: {user_context['body_type']}")
        if user_context.get("skin_tone"):
            context_parts.append(f"- Skin Tone: {user_context['skin_tone']}")
        if user_context.get("style_preference"):
            context_parts.append(f"- Style Preference: {user_context['style_preference']}")
        if user_context.get("gender"):
            context_parts.append(f"- Gender: {user_context['gender']}")
        if user_context.get("weather"):
            context_parts.append(f"- Current Weather: {user_context['weather']}")
        if user_context.get("occasion"):
            context_parts.append(f"- Occasion: {user_context['occasion']}")
            
        return "\n".join(context_parts) if context_parts else "No additional context"
    
    async def get_style_advice(
        self,
        query: str,
        body_type: Optional[str] = None,
        skin_tone: Optional[str] = None,
        style_preference: Optional[str] = None,
        weather_condition: Optional[str] = None,
        occasion: Optional[str] = None
    ) -> StyleAdviceResponse:
        """
        Get personalized style advice from the AI
        
        Args:
            query: User's style-related question
            body_type: User's body type
            skin_tone: User's skin tone
            style_preference: User's style preference
            weather_condition: Current weather condition
            occasion: The occasion for the outfit
            
        Returns:
            StyleAdviceResponse with personalized advice
        """
        user_context = {
            "body_type": body_type,
            "skin_tone": skin_tone,
            "style_preference": style_preference,
            "weather": weather_condition,
            "occasion": occasion
        }
        
        enhanced_query = f"""
Based on the user's profile and current conditions, provide style advice for: {query}

Please include:
1. Specific outfit recommendation
2. Color palette suggestions (list 3-5 colors)
3. Any styling tips

Format your response clearly with these sections.
"""
        
        chat_response = await self.chat(
            user_message=enhanced_query,
            context_type="style",
            user_context=user_context
        )
        
        # Parse response to extract structured data
        return StyleAdviceResponse(
            advice=chat_response.response,
            outfit_suggestions=self._extract_outfit_suggestions(chat_response.response),
            color_palette=self._extract_color_palette(chat_response.response),
            confidence_score=0.85  # Placeholder - could implement confidence scoring
        )
    
    def _extract_outfit_suggestions(self, response: str) -> List[str]:
        """Extract outfit suggestions from AI response"""
        # Simple extraction - could be enhanced with NLP
        suggestions = []
        lines = response.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['wear', 'pair', 'outfit', 'suggest', 'recommend']):
                clean_line = line.strip('- •*').strip()
                if clean_line and len(clean_line) > 10:
                    suggestions.append(clean_line)
        return suggestions[:5]  # Return top 5 suggestions
    
    def _extract_color_palette(self, response: str) -> List[str]:
        """Extract color mentions from AI response"""
        common_colors = [
            'black', 'white', 'navy', 'beige', 'gray', 'charcoal', 'cream',
            'burgundy', 'olive', 'tan', 'brown', 'blue', 'green', 'red',
            'pink', 'purple', 'yellow', 'orange', 'coral', 'teal', 'maroon'
        ]
        
        response_lower = response.lower()
        found_colors = []
        
        for color in common_colors:
            if color in response_lower and color not in found_colors:
                found_colors.append(color.capitalize())
        
        return found_colors[:5]  # Return up to 5 colors
    
    async def get_outfit_for_weather(
        self,
        weather_data: Dict[str, Any],
        style_preference: Optional[str] = None
    ) -> str:
        """
        Get outfit recommendation based on weather conditions
        
        Args:
            weather_data: Weather information dict
            style_preference: User's style preference
            
        Returns:
            String with outfit recommendation
        """
        query = f"""
The current weather is:
- Temperature: {weather_data.get('temperature', 'Unknown')}°
- Condition: {weather_data.get('condition', 'Unknown')}
- Humidity: {weather_data.get('humidity', 'Unknown')}%

What should I wear today that's both practical and stylish?
"""
        
        user_context = {"style_preference": style_preference} if style_preference else None
        
        response = await self.chat(
            user_message=query,
            context_type="weather",
            user_context=user_context
        )
        
        return response.response
    
    async def get_outfit_for_event(
        self,
        event_title: str,
        event_time: str,
        location: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get outfit recommendation for a calendar event
        
        Args:
            event_title: Title of the event
            event_time: Time of the event
            location: Event location
            user_context: User's profile data
            
        Returns:
            String with outfit recommendation
        """
        query = f"""
I have an event coming up:
- Event: {event_title}
- Time: {event_time}
{f'- Location: {location}' if location else ''}

What should I wear for this event?
"""
        
        response = await self.chat(
            user_message=query,
            context_type="calendar",
            user_context=user_context
        )
        
        return response.response


# Singleton instance for easy import
_service_instance: Optional[GroqChatService] = None


def get_groq_service() -> GroqChatService:
    """Get or create the Groq service singleton"""
    global _service_instance
    if _service_instance is None:
        _service_instance = GroqChatService()
    return _service_instance

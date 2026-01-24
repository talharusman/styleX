"""
Weather Router - API endpoints for weather data and outfit suggestions
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import Optional
import logging

from .schemas import (
    WeatherRequest,
    WeatherResponse,
    ForecastResponse,
    LocationSearchResult,
    TemperatureUnit
)
from .service import WeatherService, get_weather_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/weather",
    tags=["Weather"],
    responses={
        404: {"description": "Location not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get(
    "",
    response_model=WeatherResponse,
    summary="Get Current Weather",
    description="Get current weather with outfit suggestions for a location"
)
async def get_weather(
    location: str = Query(..., description="City name (e.g., 'London' or 'New York,US')"),
    units: TemperatureUnit = Query(
        default=TemperatureUnit.CELSIUS,
        description="Temperature unit"
    ),
    service: WeatherService = Depends(get_weather_service)
) -> WeatherResponse:
    """
    Get current weather for a location with personalized outfit suggestions.
    
    - **location**: City name, optionally with country code (e.g., "London,UK")
    - **units**: Temperature unit (celsius or fahrenheit)
    
    Returns weather data along with:
    - Outfit suggestions based on temperature and conditions
    - Weather-appropriate color recommendations
    - General weather advice
    """
    try:
        response = await service.get_weather(location=location, units=units)
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Weather endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch weather: {str(e)}"
        )


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get Weather Forecast",
    description="Get multi-day weather forecast for a location"
)
async def get_forecast(
    location: str = Query(..., description="City name"),
    days: int = Query(default=5, ge=1, le=7, description="Number of days (1-7)"),
    units: TemperatureUnit = Query(
        default=TemperatureUnit.CELSIUS,
        description="Temperature unit"
    ),
    service: WeatherService = Depends(get_weather_service)
) -> ForecastResponse:
    """
    Get weather forecast for upcoming days.
    
    - **location**: City name, optionally with country code
    - **days**: Number of forecast days (1-7)
    - **units**: Temperature unit
    
    Returns daily forecasts with high/low temperatures and conditions.
    """
    try:
        response = await service.get_forecast(
            location=location,
            days=days,
            units=units
        )
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Forecast endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch forecast: {str(e)}"
        )


@router.get(
    "/search",
    response_model=list[LocationSearchResult],
    summary="Search Locations",
    description="Search for locations by name"
)
async def search_locations(
    query: str = Query(..., min_length=2, description="Location search query"),
    limit: int = Query(default=5, ge=1, le=10, description="Maximum results"),
    service: WeatherService = Depends(get_weather_service)
) -> list[LocationSearchResult]:
    """
    Search for locations by name.
    
    - **query**: Search term (city name)
    - **limit**: Maximum number of results
    
    Returns matching locations with coordinates.
    """
    try:
        results = await service.search_location(query=query, limit=limit)
        return results
        
    except Exception as e:
        logger.error(f"Location search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search locations: {str(e)}"
        )


@router.get(
    "/outfit-suggestion",
    summary="Get Outfit for Weather",
    description="Get outfit recommendation for specific weather conditions"
)
async def get_outfit_for_weather(
    temperature: float = Query(..., description="Temperature in Celsius"),
    condition: str = Query(..., description="Weather condition (e.g., sunny, rainy)"),
    humidity: Optional[int] = Query(default=50, ge=0, le=100, description="Humidity percentage"),
    wind_speed: Optional[float] = Query(default=0, ge=0, description="Wind speed in m/s"),
    service: WeatherService = Depends(get_weather_service)
) -> dict:
    """
    Get outfit recommendation for specific weather conditions.
    
    Useful for manual weather input or planning for future weather.
    
    - **temperature**: Temperature in Celsius
    - **condition**: Weather condition description
    - **humidity**: Humidity percentage
    - **wind_speed**: Wind speed in m/s
    
    Returns outfit suggestions tailored to the conditions.
    """
    from .schemas import WeatherData
    
    # Create weather data from parameters
    weather_data = WeatherData(
        location="Custom",
        temperature=temperature,
        feels_like=temperature,
        condition=condition,
        description=condition.lower(),
        humidity=humidity,
        wind_speed=wind_speed
    )
    
    suggestions = service._generate_outfit_suggestions(weather_data)
    advice = service._generate_weather_advice(weather_data)
    colors = service._get_recommended_colors(weather_data)
    
    return {
        "weather_summary": {
            "temperature": temperature,
            "condition": condition,
            "humidity": humidity,
            "wind_speed": wind_speed
        },
        "outfit_suggestions": [s.model_dump() for s in suggestions],
        "weather_advice": advice,
        "recommended_colors": colors
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Check if the weather service is available"
)
async def health_check(
    service: WeatherService = Depends(get_weather_service)
) -> dict:
    """
    Check the health of the weather service.
    
    Returns service status and API key configuration status.
    """
    api_configured = bool(service.api_key)
    
    return {
        "status": "healthy" if api_configured else "limited",
        "api_configured": api_configured,
        "message": "Full functionality" if api_configured else "Using mock data - configure OPENWEATHER_API_KEY"
    }

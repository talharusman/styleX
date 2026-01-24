"""
Weather Module - Real-time weather integration with outfit suggestions
"""

from .router import router
from .service import WeatherService

__all__ = ["router", "WeatherService"]

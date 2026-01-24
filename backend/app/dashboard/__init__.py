"""
Dashboard Module - Combined view of weather, events, and outfit recommendations
"""

from .router import router
from .service import DashboardService

__all__ = ["router", "DashboardService"]

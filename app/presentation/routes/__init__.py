"""Routes Module - HTTP endpoints for all API operations"""
import logging

from app.presentation.routes.search_routes import create_search_router
from app.presentation.routes.health_routes import create_health_router

logger = logging.getLogger(__name__)

# Export all router factories
__all__ = ["create_search_router", "create_health_router"]

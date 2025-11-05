"""Health Check Routes - Application health monitoring endpoints"""
import logging
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import db_connection

logger = logging.getLogger(__name__)


def create_health_router() -> APIRouter:
    """
    Factory function to create health check router.
    
    Returns:
        APIRouter configured with health monitoring endpoints
    """
    router = APIRouter(prefix="", tags=["health"])

    @router.get("/health")
    async def health_check() -> dict:
        """
        Health check endpoint for monitoring.
        
        Verifies database connectivity and basic application status.
        """
        db_healthy = await db_connection.health_check()
        
        status_code = status.HTTP_200_OK if db_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if db_healthy else "degraded",
                "database": "connected" if db_healthy else "disconnected",
            },
        )

    @router.get("/ready")
    async def ready_check() -> dict:
        """
        Readiness check - indicates if app is ready to receive traffic.
        """
        return {
            "ready": True,
            "version": settings.APP_VERSION,
        }

    return router

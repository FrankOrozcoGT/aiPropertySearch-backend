"""Main Application - FastAPI Setup and Startup"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import db_connection
from app.di import ServiceContainer
from app.presentation.routes import create_search_router
from app.infrastructure.repositories.mysql_property_repo import MySQLPropertyRepository
from app.infrastructure.llm.ollama_adapter import OllamaLLMAdapter

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global service container (initialized in lifespan)
service_container: ServiceContainer | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    
    Handles:
    - Database connections
    - Service initialization
    - Graceful shutdown
    """
    # Startup
    logger.info("🚀 Starting PropTech API...")
    
    try:
        # Connect to database
        await db_connection.connect()
        
        # Initialize adapters
        logger.info("Initializing adapters...")
        property_repository = MySQLPropertyRepository()
        llm_service = OllamaLLMAdapter(timeout=settings.OLLAMA_TIMEOUT)
        
        # Initialize service container with adapters
        service_container_instance = ServiceContainer(
            property_repository=property_repository,
            llm_service=llm_service,
        )
        
        # Store in global for use in routes
        global service_container
        service_container = service_container_instance
        
        logger.info("✓ Service container initialized with adapters")
        logger.info("✓ MySQL repository ready")
        logger.info(f"✓ Ollama LLM ready ({settings.OLLAMA_MODEL})")
        
        logger.info("✅ Application started successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down PropTech API...")
    
    try:
        await db_connection.disconnect()
        logger.info("✓ Resources cleaned up")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {str(e)}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Property search API using natural language queries with Ollama LLM",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configure CORS
allowed_origins = (
    ["*"]
    if settings.CORS_ORIGINS == "*"
    else settings.CORS_ORIGINS.split(",")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info(f"✓ CORS configured for origins: {allowed_origins}")


# Health Check Endpoint
@app.get("/health", tags=["health"])
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


# Ready Endpoint
@app.get("/ready", tags=["health"])
async def ready_check() -> dict:
    """
    Readiness check - indicates if app is ready to receive traffic.
    """
    return {
        "ready": True,
        "version": settings.APP_VERSION,
    }


# Include routers
if service_container:
    search_use_case = service_container.get_search_property_use_case()
    search_router = create_search_router(search_use_case)
    app.include_router(search_router, prefix=settings.API_PREFIX)
    logger.info(f"✓ Search router registered at {settings.API_PREFIX}/search")
else:
    logger.warning("⚠️ Service container not initialized - routers not registered")

logger.info(f"✓ FastAPI app initialized: {settings.APP_NAME} v{settings.APP_VERSION}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

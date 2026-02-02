"""
FastAPI Application Entry Point.

ScamShield AI - Agentic Honeypot for Scam Detection and Intelligence Extraction.

This module creates and configures the FastAPI application with:
- API routes for honeypot endpoints
- CORS middleware
- Exception handlers
- Startup/shutdown events
"""

from contextlib import asynccontextmanager
from datetime import datetime
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.api.endpoints import router
from app.utils.logger import setup_logging, get_logger

# Initialize logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Track startup time for uptime calculation
_startup_time: float = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    global _startup_time
    
    # Startup
    logger.info("Starting ScamShield AI...")
    _startup_time = time.time()
    
    # Pre-load ML models (prevents cold-start delays)
    logger.info("Loading ML models...")
    try:
        from app.models.detector import get_detector
        from app.models.extractor import get_extractor
        
        # Pre-initialize detector (loads IndicBERT)
        detector = get_detector()
        logger.info(f"Detector ready (model loaded: {detector._model_loaded})")
        
        # Pre-initialize extractor (loads spaCy)
        extractor = get_extractor()
        logger.info(f"Extractor ready (spaCy loaded: {extractor.nlp is not None})")
        
        logger.info("All ML models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load ML models: {e}")
        logger.warning("Application will continue but may have degraded functionality")
    
    # Initialize PostgreSQL database
    if settings.POSTGRES_URL:
        try:
            from app.database.postgres import init_engine, init_database, verify_schema
            
            logger.info("Initializing PostgreSQL connection...")
            init_engine()
            
            # Initialize database schema if needed
            if not verify_schema():
                logger.info("Database schema not found, initializing...")
                init_database()
            else:
                logger.info("Database schema verified")
                
            logger.info("PostgreSQL initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {e}")
            logger.warning("PostgreSQL operations will fail. Application will continue with Redis only.")
    else:
        logger.warning("POSTGRES_URL not configured. PostgreSQL features disabled.")
    
    # Initialize Redis connection
    if settings.REDIS_URL:
        try:
            from app.database.redis_client import init_redis_client, is_redis_available
            
            logger.info("Initializing Redis connection...")
            init_redis_client()
            
            if is_redis_available():
                logger.info("Redis initialized successfully")
            else:
                logger.warning("Redis connection failed. Will use in-memory fallback.")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            logger.warning("Redis operations will fail. Will use in-memory fallback.")
    else:
        logger.warning("REDIS_URL not configured. Will use in-memory session storage.")
    
    logger.info(f"ScamShield AI started in {settings.ENVIRONMENT} mode")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ScamShield AI...")
    
    # Cleanup resources
    try:
        from app.database.postgres import engine
        if engine:
            engine.dispose()
            logger.info("PostgreSQL connections closed")
    except Exception as e:
        logger.warning(f"Error closing PostgreSQL connections: {e}")
    
    try:
        from app.database.redis_client import redis_client
        if redis_client:
            redis_client.close()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Error closing Redis connection: {e}")
    
    logger.info("ScamShield AI shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ScamShield AI",
    description="Agentic Honeypot System for Scam Detection & Intelligence Extraction",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Mount static files for UI
ui_path = Path(__file__).parent.parent / "ui"
if ui_path.exists():
    app.mount("/ui", StaticFiles(directory=str(ui_path), html=True), name="ui")
    logger.info(f"UI mounted at /ui (from {ui_path})")
    
    # Serve index.html at root
    @app.get("/", include_in_schema=False)
    async def serve_ui():
        """Serve the UI dashboard at root."""
        from fastapi.responses import FileResponse
        index_file = ui_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"message": "UI files not found"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Args:
        request: FastAPI request
        exc: Exception that was raised
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred while processing your request",
                "details": {
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                },
            },
        },
    )


# Root endpoint moved to serve UI (see above)


def get_uptime_seconds() -> int:
    """
    Get application uptime in seconds.
    
    Returns:
        Uptime in seconds
    """
    if _startup_time == 0:
        return 0
    return int(time.time() - _startup_time)


# Export for uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.is_development,
    )

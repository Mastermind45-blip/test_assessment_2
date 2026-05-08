"""FastAPI application entry point.

This module initializes the FastAPI application with:
- Router registration for all API endpoints
- OpenAPI documentation configuration
- Global error handlers (using custom exception handlers)
- Startup/shutdown lifecycle events
- CORS middleware
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import close_db, init_db
from app.core.error_handlers import register_exception_handlers
from app.routers import export, weather

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("Starting up Weather App Backend...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Weather App Backend...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


# Initialize FastAPI application with OpenAPI configuration
app = FastAPI(
    title="Weather App Backend API",
    description="""
    ## Overview
    A RESTful API for managing weather records with external API integration.

    ### Features
    - **Weather Records Management**: Create, read, update, and delete weather records
    - **External API Integration**: Automatically fetches weather forecasts, YouTube videos, and map data
    - **Data Export**: Export weather data in multiple formats (JSON, CSV, Excel)
    - **Input Validation**: Comprehensive validation for coordinates, dates, and input data

    ### Architecture
    This API follows Clean Architecture principles with the following layers:
    - **Routes/Routers**: HTTP endpoint definitions
    - **Controllers**: HTTP request/response handling
    - **Services**: Business logic orchestration
    - **Repositories**: Data access abstraction
    - **Models**: Database ORM models

    """,
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "Weather Records",
            "description": "Operations with weather records including creation, retrieval, update, and deletion.",
        },
        {
            "name": "Data Export",
            "description": "Export weather data in various formats (JSON, CSV, Excel).",
        },
    ],
    contact={
        "name": "Weather App Team",
        "email": "support@weatherapp.com",
    },
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(weather.router)
app.include_router(export.router)


@app.get("/", tags=["Health Check"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Weather App Backend API is running",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
    }


@app.get("/health", tags=["Health Check"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB health check
        "timestamp": "2024-01-01T00:00:00Z",  # TODO: Add actual timestamp
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

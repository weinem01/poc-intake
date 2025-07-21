"""
Main FastAPI application for POC Intake
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import get_settings, LogConfig
from app.core.token_manager import charm_token_manager
from app.routers import intake, chat

# Configure logging
logging.config.dictConfig(LogConfig().model_dump())
logger = logging.getLogger("poc_intake")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting POC Intake application")
    logger.info("Token manager initialized with Supabase storage")
  
    yield
    
    # Shutdown
    logger.info("Shutting down POC Intake application")


# Initialize FastAPI app
settings = get_settings()

app = FastAPI(
    title="POC Intake API",
    description="Patient intake system for Pound of Cure Weight Loss",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.debug
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.poundofcure.com", "localhost", "127.0.0.1"]
    )

# Include routers
app.include_router(intake.router, prefix="/api/v1", tags=["intake"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "POC Intake API",
        "version": "1.0.0",
        "environment": settings.environment,
        "project": settings.gcp_project_id
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "project": settings.gcp_project_id
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_config=LogConfig().dict()
    )
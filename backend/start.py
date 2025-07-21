#!/usr/bin/env python
"""Startup script with better error handling for Cloud Run"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    logger.info("Starting application...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"PORT environment variable: {os.getenv('PORT', 'Not set')}")
    logger.info(f"GCP_PROJECT_ID: {os.getenv('GCP_PROJECT_ID', 'Not set')}")
    
    # Try importing the application
    logger.info("Importing FastAPI application...")
    from app.main import app
    logger.info("Application imported successfully")
    
    # Start uvicorn
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
    
except Exception as e:
    logger.error(f"Failed to start application: {e}")
    logger.exception("Full traceback:")
    sys.exit(1)
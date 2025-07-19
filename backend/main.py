"""
Entry point for the POC Intake FastAPI application
"""

if __name__ == "__main__":
    import uvicorn
    from app.core.config import get_settings, LogConfig
    
    settings = get_settings()
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level="debug"
    )
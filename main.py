"""
main.py: FastAPI application entry point

- Exposes the FastAPI app instance for Uvicorn/Gunicorn (app = FastAPI(...))
- Does NOT perform environment checks, DB setup, or model imports
- For robust startup (env checks, DB setup, model imports), use run_server.py
"""

import logging
import os
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional portfolios analytics API for high-net-worth individuals",
    openapi_url=f"/api/{settings.API_PREFIX}/openapi.json",
    docs_url=f"/api/{settings.API_PREFIX}/docs",
    redoc_url=f"/api/{settings.API_PREFIX}/redoc",
    swagger_favicon_url="favicon.ico",
)


# Favicon endpoint
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = "favicon.ico"
    if os.path.exists(favicon_path):
        return FileResponse(favicon_path)
    return JSONResponse({"error": "Favicon not found"}, status_code=404)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "detail": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and deployment."""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": f"/api/{settings.API_PREFIX}/docs",
        "status": "online",
    }


# Only include API router after all models are properly defined
try:
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix=f"/api/{settings.API_PREFIX}")
    logger.info("✅ API routes loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load API routes: {e}")
    logger.error("The server will start but API endpoints may not be available")


# Also include auth routes at the application root for backward compatibility
# This makes endpoints like /register, /login available for tests and legacy clients
try:
    import app.auth.router as auth_router_module

    # auth_router_module.router defines paths like /register, /login relative to the router
    app.include_router(auth_router_module.router)
    logger.info("✅ Auth routes loaded at root (backward compatibility)")
except Exception as e:
    logger.warning(f"Could not include root auth routes: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

"""
Web2JSON Agent - 简化版 Web API
FastAPI application entry point

核心功能：
1. 接收HTML内容
2. 接收字段定义
3. 调用agent生成XPath
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Web2JSON Agent API",
    description="Web interface for web2json-agent - AI-powered XPath generator",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from web2json_api.routers import xpath

# Register routers
app.include_router(xpath.router, prefix="/api/xpath", tags=["xpath"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Web2JSON Agent API - Simplified",
        "version": "1.0.0",
        "docs": "/api/docs",
        "description": "AI-powered XPath generator"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "web2json-api"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


# Application startup/shutdown events
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("Starting Web2JSON Agent API (Simplified)...")
    logger.info("API Documentation: http://localhost:8000/api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down Web2JSON Agent API...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web2json_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

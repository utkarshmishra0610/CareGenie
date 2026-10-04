import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import api_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
PUBLIC_DIR = os.path.join(ROOT_DIR, "public")
FRONTEND_DIR = PUBLIC_DIR if os.path.exists(os.path.join(PUBLIC_DIR, "index.html")) else os.path.join(ROOT_DIR, "frontend")
FRONTEND_INDEX = os.path.join(FRONTEND_DIR, "index.html")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Personalized AI Health Assistant for Disease Risk Assessment.\n\n"
        "**DISCLAIMER**: This application is an academic/research prototype intended "
        "for preliminary health-risk assessment and healthcare navigation assistance ONLY. "
        "It is NOT a medical device, does not provide definitive medical diagnosis, "
        "and does not prescribe medication or treatments. Consult a licensed healthcare "
        "professional for medical concerns or emergencies."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS if isinstance(settings.BACKEND_CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api
app.include_router(api_router, prefix=settings.API_V1_STR)

from app.core.database import Base, engine
from app import models  # noqa: F401

try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database init: {e}")



# Mount frontend static assets if available
if os.path.exists(FRONTEND_DIR):
    css_dir = os.path.join(FRONTEND_DIR, "css")
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")


@app.get("/app", response_class=FileResponse, tags=["Web App"])
def web_app():
    """Serves the Single-Page Application web interface directly."""
    if os.path.exists(FRONTEND_INDEX):
        return FileResponse(FRONTEND_INDEX)
    return {"message": "Frontend assets not found."}


@app.get("/", tags=["Root"])
def root(request: Request):
    """Root entry point: serves Single-Page App for browser navigation or API metadata."""
    accept = request.headers.get("accept", "")
    # Serve UI if requested by browser navigation without JSON explicitly requested
    if "text/html" in accept and "application/json" not in accept and os.path.exists(FRONTEND_INDEX):
        return FileResponse(FRONTEND_INDEX)
    return {
        "name": settings.PROJECT_NAME,
        "version": "0.1.0",
        "health_check": f"{settings.API_V1_STR}/health",
        "web_app": "/app",
        "docs": "/docs",
        "disclaimer": "Preliminary health-risk assessment & healthcare navigation prototype only."
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )

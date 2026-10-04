import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.routes import api_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

# Locate static index.html with priority: static package dir, root dir, frontend dir
FRONTEND_INDEX = None
FRONTEND_DIR = STATIC_DIR
for candidate in [
    os.path.join(STATIC_DIR, "index.html"),
    os.path.join(ROOT_DIR, "index.html"),
    os.path.join(ROOT_DIR, "frontend", "index.html"),
    os.path.join(ROOT_DIR, "public", "index.html"),
]:
    if os.path.exists(candidate):
        FRONTEND_INDEX = candidate
        FRONTEND_DIR = os.path.dirname(candidate)
        break

if not FRONTEND_INDEX:
    FRONTEND_INDEX = os.path.join(STATIC_DIR, "index.html")

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



# Mount frontend static assets
mounted_css = False
mounted_js = False

for candidate_dir in [STATIC_DIR, FRONTEND_DIR, os.path.join(ROOT_DIR, "frontend"), os.path.join(ROOT_DIR, "public")]:
    css_path = os.path.join(candidate_dir, "css")
    js_path = os.path.join(candidate_dir, "js")
    if not mounted_css and os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
        mounted_css = True
    if not mounted_js and os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
        mounted_js = True


@app.get("/app", response_class=FileResponse, tags=["Web App"])
def web_app():
    """Serves the Single-Page Application web interface directly."""
    if FRONTEND_INDEX and os.path.exists(FRONTEND_INDEX):
        return FileResponse(FRONTEND_INDEX)
    return {"message": "Frontend assets not found."}


@app.get("/", tags=["Root"])
def root(request: Request):
    """Root entry point: serves Single-Page App for browser navigation or API metadata."""
    accept = request.headers.get("accept", "")
    # Serve UI if requested by browser navigation without JSON explicitly requested
    if "text/html" in accept and "application/json" not in accept and FRONTEND_INDEX and os.path.exists(FRONTEND_INDEX):
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

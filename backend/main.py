"""Application entry point for the AI Chatbot Platform backend."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api.chat_routes import router as chat_router
from backend.api.upload_routes import router as upload_router
from backend.api.faq_routes import router as faq_router
from backend.api.client_routes import router as client_router
from backend.api.agent_routes import router as agent_router
from backend.api.auth_routes import router as auth_router
from backend.api.widget_routes import router as widget_router
from backend.api.analytics_routes import router as analytics_router

from backend.database.mongodb import (
    connect_to_mongodb,
    close_mongodb_connection,
    create_database_indexes,
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"
DASHBOARD_DIR = BASE_DIR / "dashboard"


# =========================================================
# APPLICATION LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    await connect_to_mongodb()
    await create_database_indexes()

    yield

    await close_mongodb_connection()


# =========================================================
# APPLICATION
# =========================================================

app = FastAPI(
    title="AI Chatbot Platform",
    version="0.1.0",
    description=(
        "Modular backend for AI chatbot, "
        "RAG, authentication, widget, and analytics services."
    ),
    lifespan=lifespan,
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STATIC FRONTEND FILES
# =========================================================

if (FRONTEND_DIR / "css").exists():
    app.mount(
        "/css",
        StaticFiles(directory=str(FRONTEND_DIR / "css")),
        name="frontend-css",
    )

if (FRONTEND_DIR / "js").exists():
    app.mount(
        "/js",
        StaticFiles(directory=str(FRONTEND_DIR / "js")),
        name="frontend-js",
    )

if (FRONTEND_DIR / "assets").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIR / "assets")),
        name="frontend-assets",
    )

if (FRONTEND_DIR / "widget").exists():
    app.mount(
        "/frontend-widget",
        StaticFiles(directory=str(FRONTEND_DIR / "widget")),
        name="frontend-widget",
    )


# =========================================================
# ROUTERS
# =========================================================

app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(faq_router)
app.include_router(client_router)
app.include_router(agent_router)
app.include_router(auth_router)
app.include_router(widget_router)
app.include_router(analytics_router)


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "ai-chatbot-platform",
    }


# =========================================================
# DASHBOARD PAGES
# =========================================================

@app.get("/dashboard")
@app.get("/dashboard/")
async def dashboard_home():
    return FileResponse(
        DASHBOARD_DIR / "index.html"
    )


@app.get("/dashboard/{page_name}")
async def dashboard_page(page_name: str):
    page_path = DASHBOARD_DIR / page_name

    if page_path.suffix.lower() != ".html":
        page_path = DASHBOARD_DIR / f"{page_name}.html"

    if not page_path.is_file():
        return FileResponse(
            DASHBOARD_DIR / "index.html"
        )

    return FileResponse(page_path)


# =========================================================
# FAVICON
# =========================================================

@app.get("/favicon.ico")
async def favicon():
    favicon_path = FRONTEND_DIR / "favicon.ico"

    if favicon_path.is_file():
        return FileResponse(favicon_path)

    return {
        "message": "favicon not found"
    }


# =========================================================
# FRONTEND
# =========================================================

@app.get("/")
async def frontend_home():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )
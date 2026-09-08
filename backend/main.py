"""Application entry point for the AI Chatbot Platform backend."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
# APPLICATION LIFESPAN
# =========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""

    # Startup
    await connect_to_mongodb()
    await create_database_indexes()

    yield

    # Shutdown
    await close_mongodb_connection()


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
# ROOT
# =========================================================

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "AI Chatbot Platform is running",
    }
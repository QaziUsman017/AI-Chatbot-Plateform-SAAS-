"""Application configuration placeholders."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = os.getenv("APP_NAME", "AI Chatbot Platform")
APP_ENV = os.getenv("APP_ENV", "development")
APP_DEBUG = os.getenv("APP_DEBUG", "true").lower() == "true"
APP_PORT = int(os.getenv("APP_PORT", "8000"))

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
VECTOR_DB_URI = os.getenv("VECTOR_DB_URI", "http://localhost:6333")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "knowledge_base" / "uploads")))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", str(BASE_DIR / "knowledge_base" / "processed")))
TEMP_DIR = Path(os.getenv("TEMP_DIR", str(BASE_DIR / "knowledge_base" / "temporary")))

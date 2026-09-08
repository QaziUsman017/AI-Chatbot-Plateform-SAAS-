# AI Chatbot Platform

This project is a modular AI chatbot platform scaffold for incremental development.

## Project structure

- `backend/` contains the FastAPI application, domain models, schemas, services, database layer, and tests.
- `frontend/` contains static web app files for the user-facing chat experience.
- `dashboard/` contains admin dashboard screens.
- `knowledge_base/` stores uploaded and processed knowledge content.
- `scripts/` contains operational scripts for ingestion and maintenance tasks.

## Planned scope

The application will evolve across the 18-step / 22-day roadmap, with the initial implementation focused on structure and modular architecture.

## Notes

- Do not implement business logic yet.
- Keep service boundaries clear for AI, RAG, document processing, crawlers, analytics, and client management.
- Real implementation should be added incrementally in each planned module.

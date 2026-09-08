"""Routes for client-specific document uploads."""

from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue,
)

from backend.config import UPLOAD_DIR
from backend.database.mongodb import (
    delete_document,
    get_client,
    save_document,
)
from backend.database.vector_db import (
    COLLECTION_NAME,
    client as qdrant_client,
    create_collection,
)
from backend.services.documents.text_processor import (
    extract_text,
)
from backend.services.rag.rag_service import (
    index_text,
)


router = APIRouter(
    prefix="/upload",
    tags=["upload"],
)


UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


ALLOWED_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".docx",
}


# =========================================================
# HEALTH
# =========================================================

@router.get("/health")
async def upload_health() -> dict[str, str]:
    return {
        "status": "ok",
        "module": "upload",
    }


# =========================================================
# UPLOAD DOCUMENT
# =========================================================

@router.post("")
async def upload_document(
    client_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict[str, str | int]:

    client_id = client_id.strip()

    # ==========================================
    # Validate client
    # ==========================================

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    existing_client = await get_client(
        client_id
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # ==========================================
    # Validate file
    # ==========================================

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Allowed: TXT, PDF, DOCX."
            ),
        )

    # ==========================================
    # Safe filename
    # ==========================================

    safe_filename = Path(
        file.filename
    ).name

    # ==========================================
    # Client-specific folder
    # ==========================================

    client_upload_dir = (
        UPLOAD_DIR / client_id
    )

    client_upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        client_upload_dir / safe_filename
    )

    # ==========================================
    # Delete old Qdrant chunks
    # ==========================================

    try:

        create_collection()

        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="client_id",
                        match=MatchValue(
                            value=client_id,
                        ),
                    ),
                    FieldCondition(
                        key="source",
                        match=MatchValue(
                            value=safe_filename,
                        ),
                    ),
                ]
            ),
        )

    except Exception as error:

        print(
            "Warning: Could not remove old Qdrant chunks:",
            error,
        )

    # ==========================================
    # Save file
    # ==========================================

    try:

        contents = await file.read()

        destination.write_bytes(
            contents
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not save file: {error}",
        ) from error

    # ==========================================
    # Extract text
    # ==========================================

    try:

        text = extract_text(
            destination
        )

        if not text.strip():

            # Remove invalid/empty uploaded file.
            try:
                if destination.exists():
                    destination.unlink()
            except Exception as cleanup_error:
                print(
                    "Warning: Could not remove empty file:",
                    cleanup_error,
                )

            raise HTTPException(
                status_code=400,
                detail=(
                    "The uploaded file contains "
                    "no readable text."
                ),
            )

        # ==========================================
        # Index into client-specific RAG
        # ==========================================

        chunks_indexed = index_text(
            text,
            source=safe_filename,
            client_id=client_id,
        )

        if chunks_indexed <= 0:

            # Remove file because nothing useful was
            # indexed into the knowledge base.

            try:
                if destination.exists():
                    destination.unlink()
            except Exception as cleanup_error:
                print(
                    "Warning: Could not remove "
                    "unindexed file:",
                    cleanup_error,
                )

            raise HTTPException(
                status_code=400,
                detail=(
                    "The document could not be indexed "
                    "because no readable chunks were created."
                ),
            )

    except HTTPException:
        raise

    except Exception as error:

        # Best-effort cleanup of the physical file
        # when document processing fails.

        try:
            if destination.exists():
                destination.unlink()
        except Exception as cleanup_error:
            print(
                "Warning: Could not clean up "
                "failed upload:",
                cleanup_error,
            )

        raise HTTPException(
            status_code=500,
            detail=f"Could not process file: {error}",
        ) from error

    # ==========================================
    # Save document metadata to MongoDB
    # ==========================================

    try:

        await save_document(
            client_id=client_id,
            filename=safe_filename,
            filetype=(
                file.content_type
                or extension.lstrip(".")
            ),
            path=str(destination),
            status="processed",
        )

    except Exception as error:

        # -------------------------------------------------
        # MongoDB metadata save failed.
        #
        # Roll back the physical file and Qdrant chunks
        # so we don't leave an incomplete document.
        # -------------------------------------------------

        try:

            if destination.exists():
                destination.unlink()

        except Exception as cleanup_error:

            print(
                "Warning: Could not remove file "
                "after MongoDB failure:",
                cleanup_error,
            )

        try:

            create_collection()

            qdrant_client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="client_id",
                            match=MatchValue(
                                value=client_id,
                            ),
                        ),
                        FieldCondition(
                            key="source",
                            match=MatchValue(
                                value=safe_filename,
                            ),
                        ),
                    ]
                ),
            )

        except Exception as cleanup_error:

            print(
                "Warning: Could not roll back "
                "Qdrant chunks:",
                cleanup_error,
            )

        raise HTTPException(
            status_code=500,
            detail=(
                "Document was indexed, but its "
                f"database metadata could not be saved: {error}"
            ),
        ) from error

    # ==========================================
    # Response
    # ==========================================

    return {
        "message": (
            "File uploaded and processed successfully."
        ),
        "filename": safe_filename,
        "client_id": client_id,
        "chunks_indexed": chunks_indexed,
    }


# =========================================================
# GET CLIENT DOCUMENTS
# =========================================================

@router.get("/{client_id}")
async def get_client_documents(
    client_id: str,
) -> list[dict[str, str | int]]:

    client_id = client_id.strip()

    # ==========================================
    # Validate client
    # ==========================================

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    existing_client = await get_client(
        client_id
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # ==========================================
    # Client directory
    # ==========================================

    client_upload_dir = (
        UPLOAD_DIR / client_id
    )

    if not client_upload_dir.exists():
        return []

    documents = []

    for file_path in client_upload_dir.iterdir():

        if not file_path.is_file():
            continue

        extension = file_path.suffix.lower()

        # Ignore unsupported files that may have been
        # placed manually inside the upload directory.

        if extension not in ALLOWED_EXTENSIONS:
            continue

        # ================================================
        # BACKFILL / SYNC DOCUMENT METADATA
        # ================================================
        #
        # Older documents may already exist physically
        # and inside Qdrant but were uploaded before
        # MongoDB document metadata was implemented.
        #
        # Register them now.
        #
        # save_document() uses upsert, so repeated
        # Knowledge Base page loads will NOT create
        # duplicate records.
        # ================================================

        try:

            await save_document(
                client_id=client_id,
                filename=file_path.name,
                filetype=extension.lstrip("."),
                path=str(file_path),
                status="processed",
            )

        except Exception as error:

            print(
                "Warning: Could not sync document "
                "metadata to MongoDB:",
                file_path.name,
                error,
            )

        documents.append(
            {
                "filename": file_path.name,
                "status": "processed",
            }
        )

    documents.sort(
        key=lambda document: document["filename"]
    )

    return documents


# =========================================================
# DELETE DOCUMENT
# =========================================================

@router.delete("/{client_id}/{filename}")
async def delete_client_document(
    client_id: str,
    filename: str,
) -> dict[str, str]:

    client_id = client_id.strip()

    # ==========================================
    # Validate client
    # ==========================================

    if not client_id:
        raise HTTPException(
            status_code=400,
            detail="client_id cannot be empty.",
        )

    existing_client = await get_client(
        client_id
    )

    if not existing_client:
        raise HTTPException(
            status_code=404,
            detail="Client not found.",
        )

    # ==========================================
    # Safe filename
    # ==========================================

    safe_filename = Path(
        filename
    ).name

    if safe_filename != filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    # ==========================================
    # File path
    # ==========================================

    file_path = (
        UPLOAD_DIR
        / client_id
        / safe_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    # ==========================================
    # Delete file
    # ==========================================

    try:

        file_path.unlink()

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not delete document: {error}"
            ),
        ) from error

    # ==========================================
    # Delete Qdrant chunks
    # ==========================================

    try:

        create_collection()

        qdrant_client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="client_id",
                        match=MatchValue(
                            value=client_id,
                        ),
                    ),
                    FieldCondition(
                        key="source",
                        match=MatchValue(
                            value=safe_filename,
                        ),
                    ),
                ]
            ),
        )

    except Exception as error:

        print(
            "Warning: Could not delete Qdrant chunks:",
            error,
        )

    # ==========================================
    # Delete MongoDB document metadata
    # ==========================================

    try:

        await delete_document(
            client_id=client_id,
            filename=safe_filename,
        )

    except Exception as error:

        # The physical file has already been deleted.
        # Report the metadata problem clearly rather
        # than silently hiding it.

        raise HTTPException(
            status_code=500,
            detail=(
                "Document file and vector data were deleted, "
                "but MongoDB metadata could not be deleted: "
                f"{error}"
            ),
        ) from error

    # ==========================================
    # Response
    # ==========================================

    return {
        "message": "Document deleted successfully.",
        "filename": safe_filename,
        "client_id": client_id,
    }
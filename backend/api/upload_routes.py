"""
Routes for client-specific document uploads.
"""

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
    get_client_documents,
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

    # =====================================================
    # VALIDATE CLIENT
    # =====================================================

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

    # =====================================================
    # VALIDATE FILE
    # =====================================================

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

    # =====================================================
    # SAFE FILENAME
    # =====================================================

    safe_filename = Path(
        file.filename
    ).name

    # =====================================================
    # CLIENT-SPECIFIC TEMPORARY DIRECTORY
    # =====================================================

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

    # =====================================================
    # DELETE OLD QDRANT CHUNKS
    # =====================================================

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

    # =====================================================
    # SAVE UPLOADED FILE TEMPORARILY
    # =====================================================

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

    # =====================================================
    # EXTRACT + PROCESS + INDEX
    # =====================================================

    try:

        text = extract_text(
            destination
        )

        if not text.strip():

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

        # =================================================
        # INDEX INTO CLIENT-SPECIFIC RAG
        # =================================================

        chunks_indexed = index_text(
            text,
            source=safe_filename,
            client_id=client_id,
        )

        if chunks_indexed <= 0:

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

    # =====================================================
    # SAVE DOCUMENT METADATA TO MONGODB
    # =====================================================

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

        # =================================================
        # ROLLBACK PHYSICAL FILE
        # =================================================

        try:

            if destination.exists():
                destination.unlink()

        except Exception as cleanup_error:

            print(
                "Warning: Could not remove file "
                "after MongoDB failure:",
                cleanup_error,
            )

        # =================================================
        # ROLLBACK QDRANT
        # =================================================

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
                "database metadata could not be saved: "
                f"{error}"
            ),
        ) from error

    # =====================================================
    # RESPONSE
    # =====================================================

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
#
# IMPORTANT:
# MongoDB is now the SOURCE OF TRUTH.
#
# Do NOT read the local filesystem here.
#
# Vercel/serverless filesystems are not persistent.
# =========================================================

@router.get("/{client_id}")
async def get_client_documents_route(
    client_id: str,
) -> list[dict]:

    client_id = client_id.strip()

    # =====================================================
    # VALIDATE CLIENT
    # =====================================================

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

    # =====================================================
    # LOAD DOCUMENTS FROM MONGODB
    # =====================================================

    try:

        documents = await get_client_documents(
            client_id
        )

    except Exception as error:

        print(
            "Knowledge Base document lookup failed:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not load knowledge-base documents."
            ),
        ) from error

    # =====================================================
    # NORMALIZE RESPONSE
    # =====================================================

    result = []

    for document in documents:

        filename = (
            document.get("filename")
            or document.get("file_name")
            or document.get("name")
            or "Document"
        )

        result.append(
            {
                "filename": str(filename),
                "status": (
                    document.get("status")
                    or "processed"
                ),
                "filetype": (
                    document.get("filetype")
                    or ""
                ),
                "created_at": document.get(
                    "created_at"
                ),
                "updated_at": document.get(
                    "updated_at"
                ),
            }
        )

    return result


# =========================================================
# DELETE DOCUMENT
# =========================================================

@router.delete("/{client_id}/{filename}")
async def delete_client_document(
    client_id: str,
    filename: str,
) -> dict[str, str]:

    client_id = client_id.strip()

    # =====================================================
    # VALIDATE CLIENT
    # =====================================================

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

    # =====================================================
    # SAFE FILENAME
    # =====================================================

    safe_filename = Path(
        filename
    ).name

    if safe_filename != filename:

        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    # =====================================================
    # DELETE PHYSICAL FILE - BEST EFFORT ONLY
    # =====================================================
    #
    # The physical file may already be gone on Vercel.
    # Therefore its absence must NOT cause deletion to fail.
    # =====================================================

    file_path = (
        UPLOAD_DIR
        / client_id
        / safe_filename
    )

    if file_path.exists():

        try:

            file_path.unlink()

        except Exception as error:

            print(
                "Warning: Could not delete physical file:",
                error,
            )

    # =====================================================
    # DELETE QDRANT CHUNKS
    # =====================================================

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

    # =====================================================
    # DELETE MONGODB DOCUMENT METADATA
    # =====================================================

    try:

        deleted = await delete_document(
            client_id=client_id,
            filename=safe_filename,
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Document vector data was processed, "
                "but MongoDB metadata could not be deleted: "
                f"{error}"
            ),
        ) from error

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Document metadata not found.",
        )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {
        "message": "Document deleted successfully.",
        "filename": safe_filename,
        "client_id": client_id,
    }
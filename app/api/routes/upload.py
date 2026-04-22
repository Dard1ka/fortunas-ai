from __future__ import annotations

import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas import UploadPreviewResponse, UploadResponse
from app.services.excel_upload import (
    ALLOWED_EXTENSIONS,
    ExcelValidationError,
    upload_excel,
    validate_excel,
)

log = logging.getLogger("fortunas.upload")
router = APIRouter(tags=["upload"])


def _check_ext(filename: str) -> None:
    lower = filename.lower()
    if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Format tidak didukung. Gunakan: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


@router.post("/upload/preview", response_model=UploadPreviewResponse)
async def preview_upload(file: UploadFile = File(...)) -> UploadPreviewResponse:
    _check_ext(file.filename or "")
    content = await file.read()
    try:
        result = validate_excel(content, file.filename or "upload.xlsx")
    except ExcelValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    result.pop("_rows", None)
    status = "success" if result["invalid_rows"] == 0 else "partial_success"
    return UploadPreviewResponse(status=status, **result)


@router.post("/upload/excel", response_model=UploadResponse)
async def upload_excel_endpoint(file: UploadFile = File(...)) -> UploadResponse:
    _check_ext(file.filename or "")
    content = await file.read()
    try:
        result = upload_excel(content, file.filename or "upload.xlsx")
    except ExcelValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        # Tangkap exception tak terduga supaya frontend tetap dapat JSON
        # (bukan plaintext "Internal Server Error" dari uvicorn).
        log.exception("Upload excel crash: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Upload error: {type(exc).__name__}: {exc}",
        )

    return UploadResponse(**result)

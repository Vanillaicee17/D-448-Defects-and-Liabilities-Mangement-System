from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.services.ingestion.orchestrator import IngestionOrchestrator
from app.core.auth import get_current_user

router = APIRouter(prefix="/ingestion", tags=["Ingestion"])

orchestrator = IngestionOrchestrator()


# =========================================================
# REQUEST SCHEMAS
# =========================================================

class EmailIngestionRequest(BaseModel):
    subject: str
    body: str
    attachments: Optional[List[str]] = []  # base64 encoded PDFs


class FormIngestionRequest(BaseModel):
    data: dict  # structured form data


# =========================================================
# PDF INGESTION
# =========================================================

@router.post("/pdf")
async def ingest_pdf(
    file: UploadFile = File(...),
    user=Depends(get_current_user)
):
    try:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail="Only PDF files are allowed")

        file_bytes = await file.read()

        result = orchestrator.process_pdf(file_bytes)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# EMAIL INGESTION
# =========================================================

@router.post("/email")
def ingest_email(
    payload: EmailIngestionRequest,
    user=Depends(get_current_user)
):
    try:
        result = orchestrator.process_email(
            subject=payload.subject,
            body=payload.body,
            attachments=payload.attachments
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================
# FORM INGESTION
# =========================================================

@router.post("/form")
def ingest_form(
    payload: FormIngestionRequest,
    user=Depends(get_current_user)
):
    try:
        result = orchestrator.process_form(payload.data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

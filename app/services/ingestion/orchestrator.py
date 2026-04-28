import base64
import logging
from typing import Dict, List

from app.services.ingestion.pdf_handler import PDFHandler
from app.services.ingestion.llm_service import LLMService

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """
    Central orchestration layer for all ingestion types:
    - PDF
    - Email
    - Form
    """

    def __init__(self):
        self.pdf_handler = PDFHandler()
        self.llm_service = LLMService()

    # =========================================================
    # PDF INGESTION
    # =========================================================

    def process_pdf(self, file_bytes: bytes) -> Dict:
        """
        Full pipeline:
        PDF → Text Extraction → LLM → Structured Output
        """
        try:
            logger.info("Starting PDF ingestion pipeline")

            # Step 1: Extract text (digital or OCR)
            extraction = self.pdf_handler.process_pdf(file_bytes)

            text = extraction["text"]
            ocr_confidence = extraction["confidence"]

            # Step 2: LLM extraction
            structured = self.llm_service.extract_structured_data(text)

            # Step 3: Combine confidence
            final_confidence = self._combine_confidence(
                ocr_confidence,
                structured.get("confidence_score", 0.0)
            )

            structured["confidence_score"] = final_confidence

            return {
                "status": "success",
                "confidence_score": final_confidence,
                "extracted_fields": structured
            }

        except Exception as e:
            logger.error(f"PDF ingestion failed: {e}")
            return self._failure_response()

    # =========================================================
    # EMAIL INGESTION
    # =========================================================

    def process_email(self, subject: str, body: str, attachments: List[str]) -> Dict:
        """
        Email ingestion:
        - Uses body text directly
        - Processes PDF attachments if present
        """

        try:
            logger.info("Starting email ingestion pipeline")

            combined_text = f"{subject}\n\n{body}"

            attachment_confidences = []

            # Process attachments (if any)
            for idx, encoded_file in enumerate(attachments or []):
                try:
                    logger.info(f"Processing attachment {idx + 1}")

                    file_bytes = base64.b64decode(encoded_file)

                    extraction = self.pdf_handler.process_pdf(file_bytes)

                    combined_text += "\n\n" + extraction["text"]
                    attachment_confidences.append(extraction["confidence"])

                except Exception as e:
                    logger.warning(f"Attachment {idx+1} failed: {e}")

            # LLM extraction
            structured = self.llm_service.extract_structured_data(
                combined_text)

            # Confidence calculation
            avg_attachment_conf = (
                sum(attachment_confidences) / len(attachment_confidences)
                if attachment_confidences else 1.0
            )

            final_confidence = self._combine_confidence(
                avg_attachment_conf,
                structured.get("confidence_score", 0.0)
            )

            structured["confidence_score"] = final_confidence

            return {
                "status": "success",
                "confidence_score": final_confidence,
                "extracted_fields": structured
            }

        except Exception as e:
            logger.error(f"Email ingestion failed: {e}")
            return self._failure_response()

    # =========================================================
    # FORM INGESTION
    # =========================================================

    def process_form(self, form_data: Dict) -> Dict:
        """
        Direct structured ingestion (no OCR, no LLM)
        """

        try:
            logger.info("Processing structured form input")

            # Since form is already structured, just return it
            return {
                "status": "success",
                "confidence_score": 1.0,
                "extracted_fields": form_data
            }

        except Exception as e:
            logger.error(f"Form ingestion failed: {e}")
            return self._failure_response()

    # =========================================================
    # CONFIDENCE COMBINATION
    # =========================================================

    def _combine_confidence(self, ocr_conf: float, llm_conf: float) -> float:
        """
        Final confidence calculation
        """
        final = (0.4 * ocr_conf) + (0.6 * llm_conf)
        return round(final, 3)

    # =========================================================
    # FAILURE RESPONSE
    # =========================================================

    def _failure_response(self) -> Dict:
        return {
            "status": "failed",
            "confidence_score": 0.0,
            "extracted_fields": {}
        }

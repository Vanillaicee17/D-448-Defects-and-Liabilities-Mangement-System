import io
import logging
from typing import Dict

from pypdf import PdfReader
from pdf2image import convert_from_bytes

from app.services.ingestion.ocr_service import OCRService

logger = logging.getLogger(__name__)


class PDFHandler:
    """
    Handles PDF ingestion:
    - Detects digital vs scanned PDFs
    - Extracts text using pypdf (digital)
    - Falls back to OCR (scanned)
    """

    def __init__(self):
        self.ocr_service = OCRService()

    # -----------------------------
    # Public Entry Point
    # -----------------------------

    def process_pdf(self, file_bytes: bytes) -> Dict:
        """
        Main method to process PDF.

        Returns:
        {
            "text": "...",
            "confidence": float
        }
        """

        logger.info("Starting PDF processing...")

        # Step 1: Try digital extraction
        text = self._extract_text_pypdf(file_bytes)

        if self._is_text_meaningful(text):
            logger.info("Digital PDF detected (using pypdf)")
            return {
                "text": text.strip(),
                "confidence": 1.0  # digital = high confidence
            }

        # Step 2: Fallback to OCR
        logger.info("Scanned PDF detected (using OCR)")

        images = self._convert_pdf_to_images(file_bytes)

        ocr_result = self.ocr_service.extract_text_from_images(images)

        return ocr_result

    # -----------------------------
    # Digital PDF Extraction
    # -----------------------------

    def _extract_text_pypdf(self, file_bytes: bytes) -> str:
        """
        Extract text using pypdf
        """
        try:
            reader = PdfReader(io.BytesIO(file_bytes))

            text_parts = []

            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Failed to extract page {page_num}: {e}")

            return "\n".join(text_parts)

        except Exception as e:
            logger.error(f"pypdf extraction failed: {e}")
            return ""

    # -----------------------------
    # Heuristic: Is this text usable?
    # -----------------------------

    def _is_text_meaningful(self, text: str) -> bool:
        """
        Determine if extracted text is meaningful enough to skip OCR
        """
        if not text:
            return False

        # Remove whitespace
        cleaned = text.strip()

        if len(cleaned) < 50:
            return False

        # Check for readable characters ratio
        alpha_ratio = sum(c.isalnum() for c in cleaned) / len(cleaned)

        if alpha_ratio < 0.3:
            return False

        return True

    # -----------------------------
    # Convert PDF → Images
    # -----------------------------

    def _convert_pdf_to_images(self, file_bytes: bytes):
        """
        Convert PDF pages to images using pdf2image
        """
        try:
            images = convert_from_bytes(
                file_bytes,
                dpi=300,  # high DPI improves OCR accuracy
                fmt="png"
            )
            return images

        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            raise

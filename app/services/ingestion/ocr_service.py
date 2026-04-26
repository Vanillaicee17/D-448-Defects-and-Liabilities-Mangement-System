import numpy as np
from typing import List, Dict
from PIL import Image
import easyocr
import pytesseract
import cv2
import logging

logger = logging.getLogger(__name__)


class OCRService:
    """
    OCR Service using EasyOCR (primary) with Tesseract fallback.
    """

    _reader = None  # Singleton instance

    def __init__(self):
        if OCRService._reader is None:
            logger.info("Loading EasyOCR model...")
            OCRService._reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR model loaded.")

        self.reader = OCRService._reader

    # -----------------------------
    # Public Method
    # -----------------------------

    def extract_text_from_images(self, images: List[Image.Image]) -> Dict:
        """
        Takes a list of PIL images and returns:
        {
            "text": "...",
            "confidence": float
        }
        """
        all_text = []
        confidences = []

        for idx, image in enumerate(images):
            logger.info(f"Processing page {idx + 1}")

            text, conf = self._run_easyocr(image)

            # Fallback condition
            if conf < 0.6:
                logger.warning(
                    f"Low confidence ({conf:.2f}) on page {idx+1}, using Tesseract fallback")
                text, conf = self._run_tesseract(image)

            all_text.append(text)
            confidences.append(conf)

        final_text = "\n\n".join(all_text)
        final_confidence = float(np.mean(confidences)) if confidences else 0.0

        return {
            "text": final_text.strip(),
            "confidence": round(final_confidence, 3)
        }

    # -----------------------------
    # EasyOCR
    # -----------------------------

    def _run_easyocr(self, image: Image.Image):
        """
        Layout-aware EasyOCR with line grouping
        """
        image_np = self._pil_to_cv(image)

        results = self.reader.readtext(image_np, detail=1)

        if not results:
            return "", 0.0

        # Step 1: Extract bounding boxes + text
        boxes = []
        confs = []

        for (bbox, text, conf) in results:
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]

            x_min = min(x_coords)
            y_min = min(y_coords)

            boxes.append({
                "x": x_min,
                "y": y_min,
                "text": text,
                "conf": conf
            })
            confs.append(conf)

        # Step 2: Sort by Y (top to bottom)
        boxes.sort(key=lambda b: b["y"])

        # Step 3: Group into lines
        lines = []
        current_line = []
        current_y = None
        y_threshold = 15  # tune this

        for box in boxes:
            if current_y is None:
                current_y = box["y"]

            if abs(box["y"] - current_y) < y_threshold:
                current_line.append(box)
            else:
                lines.append(current_line)
                current_line = [box]
                current_y = box["y"]

        if current_line:
            lines.append(current_line)

        # Step 4: Sort each line by X (left → right)
        structured_lines = []
        for line in lines:
            line.sort(key=lambda b: b["x"])
            line_text = " ".join([b["text"] for b in line])
            structured_lines.append(line_text)

        full_text = "\n".join(structured_lines)
        avg_conf = float(np.mean(confs)) if confs else 0.0

        return full_text, avg_conf

    # -----------------------------
    # Tesseract Fallback
    # -----------------------------

    def _run_tesseract(self, image: Image.Image):
        """
        Run Tesseract OCR with preprocessing.
        Returns (text, confidence approx)
        """
        image_np = self._pil_to_cv(image)

        # Preprocessing for better OCR
        gray = cv2.cvtColor(image_np, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 3)
        thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )

        custom_config = r'--oem 3 --psm 6'

        data = pytesseract.image_to_data(
            thresh,
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )

        texts = []
        confs = []

        n_boxes = len(data['text'])
        for i in range(n_boxes):
            text = data['text'][i].strip()
            conf = int(data['conf'][i])

            if text and conf > 0:
                texts.append(text)
                confs.append(conf / 100.0)

        full_text = " ".join(texts)
        avg_conf = float(np.mean(confs)) if confs else 0.0

        return full_text, avg_conf

    # -----------------------------
    # Utility
    # -----------------------------

    def _pil_to_cv(self, image: Image.Image):
        """
        Convert PIL Image to OpenCV format
        """
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

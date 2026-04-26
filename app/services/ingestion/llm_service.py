import json
import logging
from typing import Dict

import ollama
from pydantic import ValidationError

from app.schemas.ingestion import DefectExtraction

logger = logging.getLogger(__name__)


class LLMService:
    """
    Handles LLM-based structured extraction using Ollama (offline).
    """

    def __init__(self, model: str = "llama3:8b-instruct-q4_K_M"):
        self.model = model

    # -----------------------------
    # Public Method
    # -----------------------------

    def extract_structured_data(self, text: str) -> Dict:
        """
        Takes raw OCR/text and returns validated structured JSON.
        """

        try:
            prompt = self._build_prompt(text)

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system",
                        "content": "You are a strict information extraction system."},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": 0.0
                }
            )

            raw_output = response["message"]["content"]

            logger.info("LLM raw output received")

            json_data = self._safe_json_parse(raw_output)

            validated = DefectExtraction(**json_data)

            return validated.model_dump()

        except ValidationError as ve:
            logger.error(f"Validation failed: {ve}")
            return self._failure_response()

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._failure_response()

    # -----------------------------
    # Prompt Builder
    # -----------------------------

    def _build_prompt(self, text: str) -> str:
        return f"""
Extract structured information from the following defect report.

IMPORTANT RULES:
- Output ONLY valid JSON
- Do NOT include explanations or markdown
- If a field is missing, return null
- Do NOT guess or hallucinate values

Expected JSON format:

{{
  "vessel_name": string or null,
  "delivery_date": string or null,
  "shipyard_yard_number": string or null,
  "guarantee_period_end_date": string or null,

  "guarantee_defect_number": string or null,
  "department": string or null,
  "system_equipment": string or null,
  "subsystem_subassembly": string or null,

  "defect_description": string or null,
  "assistance_required": string or null,
  "spares_required": string or null,

  "hod": {{
    "remarks": string or null,
    "name": string or null,
    "rank": string or null,
    "number": string or null
  }},

  "ship_commanding_officer": {{
    "remarks": string or null,
    "name": string or null,
    "rank": string or null,
    "number": string or null
  }},

  "overseeing_team": {{
    "remarks": string or null,
    "name": string or null,
    "rank": string or null,
    "number": string or null
  }},

  "guarantee_department": {{
    "name": string or null,
    "grade": string or null,
    "employee_number": string or null
  }},

  "confidence_score": float (0.0 to 1.0)
}}

TEXT:
{text}
"""

    # -----------------------------
    # JSON Parsing (robust)
    # -----------------------------

    def _safe_json_parse(self, raw_output: str) -> Dict:
        """
        Extract JSON safely even if LLM wraps it in text
        """

        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            logger.warning("Direct JSON parse failed, attempting recovery")

            # Try to extract JSON substring
            start = raw_output.find("{")
            end = raw_output.rfind("}")

            if start != -1 and end != -1:
                try:
                    return json.loads(raw_output[start:end + 1])
                except Exception:
                    pass

        raise ValueError("Failed to parse JSON from LLM output")

    # -----------------------------
    # Failure Fallback
    # -----------------------------

    def _failure_response(self) -> Dict:
        """
        Return empty structured response on failure
        """
        return DefectExtraction(
            vessel_name=None,
            delivery_date=None,
            shipyard_yard_number=None,
            guarantee_period_end_date=None,
            guarantee_defect_number=None,
            department=None,
            system_equipment=None,
            subsystem_subassembly=None,
            defect_description=None,
            assistance_required=None,
            spares_required=None,
            hod={},
            ship_commanding_officer={},
            overseeing_team={},
            guarantee_department={},
            confidence_score=0.0
        ).model_dump()

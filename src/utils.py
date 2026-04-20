"""
Shared utilities: data models, I/O helpers, and extraction logic.
Centralising extract_json and compute_heuristic_confidence here ensures
both BaselinePipeline and AutoPromptEngine use identical logic —
critical for a fair benchmark comparison.
"""
import json
import re
import os
import pandas as pd
from pydantic import BaseModel
from typing import Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class Review(BaseModel):
    review_id: str
    review_text: str


class ExtractedData(BaseModel):
    review_id: str
    product: str
    sentiment: str
    reason: str
    confidence: float = 0.0
    prompt_used: str = ""
    time_taken_ms: Optional[float] = None  # latency tracking


# ---------------------------------------------------------------------------
# JSON extraction — single source of truth for both pipelines
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    """
    Robustly extract a JSON object from an LLM response.

    Handles:
    - Plain JSON responses
    - JSON wrapped in markdown code fences (```json ... ```)
    - Leading/trailing freeform text before or after the JSON object

    Raises json.JSONDecodeError if no valid JSON is found.
    """
    text = text.strip()

    # 1. Try markdown-fenced JSON first: ```json { ... } ```
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    # 2. Pull out the first { ... } block from free text
    bare = re.search(r"\{.*\}", text, re.DOTALL)
    if bare:
        return json.loads(bare.group(0))

    # 3. Last resort: try the whole string as-is
    return json.loads(text)


# ---------------------------------------------------------------------------
# Shared confidence scorer — used by BOTH pipelines for a fair comparison
# ---------------------------------------------------------------------------

VALID_SENTIMENTS = {"positive", "negative", "neutral", "mixed"}


def compute_heuristic_confidence(response_data: dict) -> float:
    """
    Score extraction quality using heuristics (0.0 – 1.0).

    Scoring breakdown (total = 1.0):
      0.40 — all required fields present
      0.30 — sentiment is one of the four valid values
      0.20 — product name is a plausible length (2–50 chars)
      0.10 — reason is non-trivial (> 10 chars)

    Both BaselinePipeline and AutoPromptEngine call this function,
    ensuring the benchmark comparison is based on identical criteria.
    """
    score = 0.0

    required_fields = {"product", "sentiment", "reason"}
    if required_fields.issubset(response_data.keys()):
        score += 0.40

    sentiment = response_data.get("sentiment", "").lower().strip()
    if sentiment in VALID_SENTIMENTS:
        score += 0.30

    product = response_data.get("product", "")
    if 2 < len(product) < 50:
        score += 0.20

    reason = response_data.get("reason", "")
    if len(reason) > 10:
        score += 0.10

    return round(min(score, 1.0), 4)


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_reviews(csv_path: str) -> pd.DataFrame:
    """Load reviews from CSV, forcing review_id to string to prevent type mismatches."""
    return pd.read_csv(csv_path, dtype={"review_id": str})


def save_results(results: list, output_path: str) -> None:
    """Persist a list of ExtractedData objects to a JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df = pd.DataFrame([r.model_dump() for r in results])
    df.to_json(output_path, orient="records", indent=2)
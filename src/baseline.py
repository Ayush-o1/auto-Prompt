"""
Baseline Pipeline — static single-prompt approach used as the control group.

Design decisions:
- Deliberately simple: one fixed prompt, no variant selection.
- Uses the same extract_json and compute_heuristic_confidence from utils
  as AutoPromptEngine, ensuring the benchmark is a fair comparison.
- Manual retry loop (not Tenacity) kept intentional to show contrast with
  the engine; a future refactor can unify this via an ABC.
"""
import time

import google.generativeai as genai
from loguru import logger

from src.utils import Review, ExtractedData, extract_json, compute_heuristic_confidence


class BaselinePipeline:
    """Single static-prompt extraction pipeline (benchmark control group)."""

    # Double-braced to escape Python format() interpolation
    _STATIC_TEMPLATE = (
        "Extract the product name and sentiment from this review. "
        'Respond ONLY with JSON: {{"product": "...", "sentiment": "...", "reason": "..."}}\n'
        "Review: '{text}'"
    )

    def __init__(self, config: dict) -> None:
        genai.configure(api_key=config["api_key"])
        self.config = config
        self.model = genai.GenerativeModel(
            config.get("generator_model", "models/gemini-2.0-flash-lite")
        )

    def process(self, review: Review) -> ExtractedData:
        """
        Process a single review with the static prompt.

        Retries up to 3 times on transient network errors with
        linear back-off (10 s, 20 s, 30 s).
        """
        prompt = self._STATIC_TEMPLATE.format(text=review.review_text)
        max_retries = 3

        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.1},
                )
                data = extract_json(response.text)  # shared utility — no duplicate
                confidence = compute_heuristic_confidence(data)  # real score, not 0.5

                return ExtractedData(
                    review_id=review.review_id,
                    product=data.get("product", "unknown"),
                    sentiment=data.get("sentiment", "unknown"),
                    reason=data.get("reason", ""),
                    confidence=confidence,
                    prompt_used="static_baseline",
                )

            except Exception as exc:
                err = str(exc).lower()
                is_network_error = any(
                    kw in err for kw in ("unavailable", "connection", "timeout", "tcp")
                )

                if is_network_error and attempt < max_retries - 1:
                    wait = 10 * (attempt + 1)
                    logger.warning(
                        f"Network error for review {review.review_id} "
                        f"(attempt {attempt + 1}/{max_retries}) — retrying in {wait}s: {exc}"
                    )
                    time.sleep(wait)
                    continue

                logger.error(f"Baseline failed for review {review.review_id}: {exc}")
                return ExtractedData(
                    review_id=review.review_id,
                    product="error",
                    sentiment="error",
                    reason=str(exc)[:200],
                    confidence=0.0,
                    prompt_used="static_baseline_failed",
                )
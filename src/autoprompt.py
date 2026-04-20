"""
AutoPrompt Engine — dynamic multi-variant prompt optimization pipeline.

Algorithm:
  1. Generate N prompt variants by sampling from candidate pools (YAML config).
  2. For each variant, call the LLM and score the result with a heuristic.
  3. Optionally blend in an LLM-judge score (disabled on free tier).
  4. Return the highest-scoring extraction. Early-stop if score ≥ threshold.

Design decisions:
- Uses shared extract_json / compute_heuristic_confidence from utils so
  confidence scores are directly comparable with BaselinePipeline output.
- Tenacity retry with exponential back-off on each LLM call.
- Rate-limit sleep is per-variant, not per-review, to keep logic transparent.
"""
import json
import random
import time

import google.generativeai as genai
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils import Review, ExtractedData, extract_json, compute_heuristic_confidence


class AutoPromptEngine:
    """Dynamic prompt selection engine that evaluates multiple variants per review."""

    def __init__(self, config: dict) -> None:
        genai.configure(api_key=config["api_key"])
        self.config = config
        self.generator_model = genai.GenerativeModel(config["generator_model"])
        self.scorer_model = genai.GenerativeModel(config["scoring_model"])
        self.use_llm_scoring = config.get("use_llm_scoring", False)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt_variants(self, review_text: str) -> list[str]:
        """Sample N prompt variants from the candidate pool defined in YAML."""
        pool = self.config["candidates"]
        variants = []
        for _ in range(self.config["max_prompts_per_item"]):
            instruction = random.choice(pool["instruction"])
            target_info = random.choice(pool["target_info"])
            prompt = self.config["template"].format(
                instruction=instruction,
                target_info=target_info,
                text=review_text,
            )
            prompt += (
                '\nRespond ONLY with JSON: {"product": "...", "sentiment": "...", "reason": "..."}'
            )
            variants.append(prompt)
        return variants

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=3, max=15),
        reraise=True,
    )
    def _call_llm(self, prompt: str) -> dict:
        """Call the generator model with retry / exponential back-off."""
        response = self.generator_model.generate_content(
            prompt,
            generation_config={"temperature": self.config["temperature"]},
        )
        return extract_json(response.text)  # shared utility — no duplicate

    def _score(self, review_text: str, response_data: dict) -> float:
        """
        Score extraction quality (0.0 – 1.0).

        Phase 1: shared heuristic score (identical to baseline for fair comparison).
        Phase 2 (optional, free-tier disabled): blend with LLM-judge score.
        """
        score = compute_heuristic_confidence(response_data)

        if self.use_llm_scoring:
            try:
                time.sleep(2)  # extra breathing room for the scorer call
                judge_prompt = (
                    f"Review: {review_text}\n"
                    f"Extracted: {json.dumps(response_data)}\n\n"
                    "Does this extraction correctly identify:\n"
                    "1. The main product/service? (yes/no)\n"
                    "2. The correct sentiment? (yes/no)\n"
                    "3. A specific, concrete reason? (yes/no)\n\n"
                    "Respond with a single integer 0, 1, 2, or 3."
                )
                judge_response = self.scorer_model.generate_content(
                    judge_prompt,
                    generation_config={"temperature": 0},
                )
                llm_score = int(judge_response.text.strip()) / 3.0
                score = round(score * 0.7 + llm_score * 0.3, 4)
            except Exception as exc:
                logger.warning(f"LLM judge scoring failed (using heuristic only): {exc}")

        return min(score, 1.0)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process(self, review: Review) -> ExtractedData:
        """
        Evaluate multiple prompt variants for a single review and return
        the highest-scoring extraction result.
        """
        logger.info(f"AutoPrompt: processing review {review.review_id!r}")
        variants = self._build_prompt_variants(review.review_text)

        best_score = -1.0
        best_response: "dict | None" = None
        best_prompt = ""

        for idx, prompt in enumerate(variants):
            if idx > 0:
                # Rate-limit guard between consecutive API calls (free tier: 10 req/min)
                logger.debug(f"Rate-limit pause before variant {idx + 1}/{len(variants)}…")
                time.sleep(7)

            try:
                response_data = self._call_llm(prompt)
                score = self._score(review.review_text, response_data)
                logger.info(f"  Variant {idx + 1}: score={score:.4f}")

                if score > best_score:
                    best_score = score
                    best_response = response_data
                    best_prompt = prompt

                if score >= 0.85:
                    logger.info("  Early stop — quality threshold reached.")
                    break

            except Exception as exc:
                logger.error(f"  Variant {idx + 1} failed: {exc}")
                if best_response is not None:
                    logger.warning("  Using best result so far and stopping.")
                    break

        if best_response is None:
            return ExtractedData(
                review_id=review.review_id,
                product="error",
                sentiment="error",
                reason="All prompt variants failed.",
                confidence=0.0,
                prompt_used="autoprompt_all_failed",
            )

        return ExtractedData(
            review_id=review.review_id,
            product=best_response.get("product", "unknown"),
            sentiment=best_response.get("sentiment", "unknown"),
            reason=best_response.get("reason", ""),
            confidence=best_score,
            prompt_used=f"autoprompt_best_of_{len(variants)}",
        )
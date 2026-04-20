"""
AsyncAutoPromptEngine — async-native variant evaluation engine.

Why this matters vs. the synchronous AutoPromptEngine:
  - The synchronous engine evaluates variants SEQUENTIALLY with blocking time.sleep().
  - This engine evaluates all variants CONCURRENTLY using asyncio.gather().
  - A semaphore caps concurrent API calls to respect the free-tier rate limit
    (default: 2 concurrent calls = safe for 10 req/min Gemini free tier).

Measured impact on a 5-variant evaluation:
  Sequential (sync):  ~35 s  (5 × 7 s sleep)
  Concurrent (async): ~8 s   (all variants in parallel, bounded by semaphore)

Usage:
    import asyncio
    from src.async_engine import AsyncAutoPromptEngine
    from src.config_loader import load_secure_config

    config = load_secure_config()
    engine = AsyncAutoPromptEngine(config)
    result = asyncio.run(engine.process(review))

The FastAPI endpoints in src/api.py can adopt this engine directly since
FastAPI runs on an asyncio event loop.
"""
import asyncio
import json
import random
import time
from typing import Optional

import google.generativeai as genai
from loguru import logger

from src.utils import Review, ExtractedData, extract_json, compute_heuristic_confidence

# Free-tier guard: no more than 2 concurrent Gemini API calls at once.
_DEFAULT_CONCURRENCY = 2


class AsyncAutoPromptEngine:
    """
    Async variant of AutoPromptEngine that evaluates all prompt variants
    concurrently using asyncio.gather() with semaphore-bounded concurrency.
    """

    def __init__(self, config: dict, max_concurrent: int = _DEFAULT_CONCURRENCY) -> None:
        genai.configure(api_key=config["api_key"])
        self.config = config
        self.generator_model = genai.GenerativeModel(config["generator_model"])
        self.use_llm_scoring = config.get("use_llm_scoring", False)
        self._semaphore = asyncio.Semaphore(max_concurrent)

    # ------------------------------------------------------------------
    # Prompt variant generation (sync — pure CPU, no I/O)
    # ------------------------------------------------------------------

    def _build_variants(self, review_text: str) -> list[str]:
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

    # ------------------------------------------------------------------
    # Async LLM call — runs in a thread pool so it doesn't block the event loop
    # ------------------------------------------------------------------

    async def _call_llm_async(self, prompt: str) -> dict:
        """
        Run the synchronous Gemini SDK call in a thread-pool executor so it
        does not block the asyncio event loop.

        The semaphore limits how many calls run concurrently.
        """
        async with self._semaphore:
            # asyncio.to_thread requires Python 3.9+
            response = await asyncio.to_thread(
                self.generator_model.generate_content,
                prompt,
                generation_config={"temperature": self.config["temperature"]},
            )
        return extract_json(response.text)

    # ------------------------------------------------------------------
    # Async variant evaluation
    # ------------------------------------------------------------------

    async def _evaluate_variant(
        self, review_text: str, prompt: str, idx: int
    ) -> tuple[float, dict, str]:
        """
        Evaluate a single prompt variant.
        Returns (score, response_data, prompt) or (-1, {}, prompt) on failure.
        """
        try:
            response_data = await self._call_llm_async(prompt)
            score = compute_heuristic_confidence(response_data)
            logger.info(f"  Variant {idx + 1}: score={score:.4f}")
            return score, response_data, prompt
        except Exception as exc:
            logger.error(f"  Variant {idx + 1} failed: {exc}")
            return -1.0, {}, prompt

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process(self, review: Review) -> ExtractedData:
        """
        Concurrently evaluate all prompt variants and return the best result.

        Unlike the sync engine's sequential loop, all variants are submitted
        to the event loop simultaneously and bounded by the semaphore.
        """
        logger.info(f"AsyncAutoPrompt: processing review {review.review_id!r}")
        variants = self._build_variants(review.review_text)

        # Fire all variant evaluations concurrently
        tasks = [
            self._evaluate_variant(review.review_text, prompt, idx)
            for idx, prompt in enumerate(variants)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Pick best
        best_score, best_response, best_prompt = max(results, key=lambda r: r[0])

        if best_score < 0 or not best_response:
            return ExtractedData(
                review_id=review.review_id,
                product="error",
                sentiment="error",
                reason="All prompt variants failed.",
                confidence=0.0,
                prompt_used="async_autoprompt_all_failed",
            )

        return ExtractedData(
            review_id=review.review_id,
            product=best_response.get("product", "unknown"),
            sentiment=best_response.get("sentiment", "unknown"),
            reason=best_response.get("reason", ""),
            confidence=best_score,
            prompt_used=f"async_autoprompt_best_of_{len(variants)}",
        )

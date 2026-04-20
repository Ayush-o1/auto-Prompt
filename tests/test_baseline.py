"""
Unit tests for BaselinePipeline.

Key design decision: all Gemini API calls are patched at the
google.generativeai.GenerativeModel level so tests run completely
offline — no real API key required, no network calls, no flakiness.
"""
from unittest.mock import MagicMock, patch

import pytest

from src.baseline import BaselinePipeline
from src.utils import ExtractedData, Review


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_config() -> dict:
    return {
        "api_key": "test-key-not-real",
        "generator_model": "models/gemini-2.0-flash-lite",
        "temperature": 0.1,
    }


@pytest.fixture
def sample_review() -> Review:
    return Review(review_id="42", review_text="This coffee maker is fantastic!")


def _make_pipeline(mock_config: dict) -> tuple[BaselinePipeline, MagicMock]:
    """
    Return a (pipeline, mock_model) pair.
    The pipeline's underlying GenerativeModel is fully mocked.
    """
    with patch("google.generativeai.configure"):
        with patch("google.generativeai.GenerativeModel") as MockModel:
            mock_model_instance = MagicMock()
            MockModel.return_value = mock_model_instance
            pipeline = BaselinePipeline(mock_config)
            return pipeline, mock_model_instance


# ---------------------------------------------------------------------------
# Initialisation tests
# ---------------------------------------------------------------------------

class TestBaselinePipelineInit:
    def test_stores_config(self, mock_config):
        pipeline, _ = _make_pipeline(mock_config)
        assert pipeline.config == mock_config

    def test_model_is_created(self, mock_config):
        """Verify that a GenerativeModel is instantiated during __init__."""
        with patch("google.generativeai.configure"):
            with patch("google.generativeai.GenerativeModel") as MockModel:
                MockModel.return_value = MagicMock()
                BaselinePipeline(mock_config)
                MockModel.assert_called_once_with(mock_config["generator_model"])


# ---------------------------------------------------------------------------
# Happy-path extraction tests
# ---------------------------------------------------------------------------

class TestBaselinePipelineProcess:
    def test_returns_extracted_data_type(self, mock_config, sample_review):
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.return_value.text = (
            '{"product": "coffee maker", "sentiment": "positive", "reason": "fantastic taste"}'
        )
        result = pipeline.process(sample_review)
        assert isinstance(result, ExtractedData)

    def test_correct_review_id_preserved(self, mock_config, sample_review):
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.return_value.text = (
            '{"product": "coffee maker", "sentiment": "positive", "reason": "great"}'
        )
        result = pipeline.process(sample_review)
        assert result.review_id == sample_review.review_id

    def test_product_and_sentiment_extracted(self, mock_config, sample_review):
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.return_value.text = (
            '{"product": "Espresso Machine", "sentiment": "negative", "reason": "broke quickly"}'
        )
        result = pipeline.process(sample_review)
        assert result.product == "Espresso Machine"
        assert result.sentiment == "negative"

    def test_confidence_is_computed_not_hardcoded(self, mock_config, sample_review):
        """
        Confidence must now reflect heuristic scoring, NOT the old hard-coded 0.5.
        A well-formed response with all fields + valid sentiment should score > 0.5.
        """
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.return_value.text = (
            '{"product": "Coffee Maker", "sentiment": "positive", "reason": "brews perfectly"}'
        )
        result = pipeline.process(sample_review)
        assert result.confidence > 0.5, (
            "Confidence must be computed from heuristics, not hard-coded to 0.5. "
            f"Got: {result.confidence}"
        )

    def test_confidence_within_valid_range(self, mock_config, sample_review):
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.return_value.text = (
            '{"product": "Kettle", "sentiment": "neutral", "reason": "does the job"}'
        )
        result = pipeline.process(sample_review)
        assert 0.0 <= result.confidence <= 1.0

    def test_handles_markdown_fenced_json(self, mock_config, sample_review):
        """Verify that JSON wrapped in markdown code fences is parsed correctly."""
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.return_value.text = (
            "```json\n"
            '{"product": "Blender", "sentiment": "mixed", "reason": "good but loud"}\n'
            "```"
        )
        result = pipeline.process(sample_review)
        assert result.product == "Blender"
        assert result.sentiment == "mixed"


# ---------------------------------------------------------------------------
# Error / fallback tests
# ---------------------------------------------------------------------------

class TestBaselinePipelineErrors:
    def test_returns_error_sentinel_on_total_failure(self, mock_config, sample_review):
        """All retry attempts fail → must return an error ExtractedData, not raise."""
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.side_effect = Exception("API unreachable")
        result = pipeline.process(sample_review)
        assert result.product == "error"
        assert result.sentiment == "error"
        assert result.confidence == 0.0

    def test_error_result_preserves_review_id(self, mock_config, sample_review):
        pipeline, mock_model = _make_pipeline(mock_config)
        mock_model.generate_content.side_effect = RuntimeError("Quota exceeded")
        result = pipeline.process(sample_review)
        assert result.review_id == sample_review.review_id

    def test_network_error_triggers_retry(self, mock_config, sample_review):
        """
        A transient 'unavailable' error on the first attempt should retry and
        succeed on the second attempt.
        """
        pipeline, mock_model = _make_pipeline(mock_config)

        good_response = MagicMock()
        good_response.text = (
            '{"product": "Kettle", "sentiment": "positive", "reason": "heats fast"}'
        )
        mock_model.generate_content.side_effect = [
            Exception("Service unavailable"),
            good_response,
        ]

        with patch("time.sleep"):  # skip actual sleep in tests
            result = pipeline.process(sample_review)

        assert result.product == "Kettle"
        assert mock_model.generate_content.call_count == 2

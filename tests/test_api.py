"""
Integration tests for the FastAPI endpoints.

All external dependencies (pipelines, database) are mocked so tests
run fully offline and do not require a real Gemini API key or database.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api import app
from src.utils import ExtractedData


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _good_result(review_id: str = "test-1", pipeline: str = "baseline") -> ExtractedData:
    return ExtractedData(
        review_id=review_id,
        product="Coffee Maker",
        sentiment="positive",
        reason="Makes great espresso",
        confidence=0.90,
        prompt_used=pipeline,
    )


@pytest.fixture
def client_with_mock_pipelines():
    """
    Return a TestClient with both pipelines fully mocked.
    Also patches init_db and get_db so no real SQLite file is created.
    """
    mock_baseline = MagicMock()
    mock_autoprompt = MagicMock()

    mock_baseline.process.return_value = _good_result("t1", "static_baseline")
    mock_autoprompt.process.return_value = _good_result("t1", "autoprompt_best_of_2")
    # Give autoprompt a slightly higher confidence to show the delta
    mock_autoprompt.process.return_value.confidence = 0.95

    with patch("src.api.init_db"):
        with patch("src.api.load_secure_config", return_value={"generator_model": "test-model"}):
            with patch("src.api.BaselinePipeline", return_value=mock_baseline):
                with patch("src.api.AutoPromptEngine", return_value=mock_autoprompt):
                    with patch("src.api.get_db") as mock_get_db:
                        mock_db = MagicMock()
                        mock_get_db.return_value.__enter__ = MagicMock(return_value=mock_db)
                        mock_get_db.return_value.__exit__ = MagicMock(return_value=False)

                        with patch("src.api.save_benchmark_run") as mock_save:
                            mock_run = MagicMock()
                            mock_run.id = 42
                            mock_save.return_value = mock_run

                            with patch("src.api.list_benchmark_runs") as mock_list:
                                mock_list.return_value = []

                                with patch("src.api.get_run_results") as mock_detail:
                                    mock_detail.return_value = []

                                    app.state.testing = True
                                    # Manually seed the _pipelines dict used by routes
                                    import src.api as api_module
                                    api_module._pipelines["baseline"] = mock_baseline
                                    api_module._pipelines["autoprompt"] = mock_autoprompt
                                    api_module._pipelines["model_name"] = "test-model"

                                    client = TestClient(app, raise_server_exceptions=True)
                                    yield client, mock_baseline, mock_autoprompt, mock_save, mock_list, mock_detail


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200

    def test_health_body_structure(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        body = client.get("/api/v1/health").json()
        assert body["status"] == "ok"
        assert "timestamp" in body
        assert "pipelines_loaded" in body
        assert body["version"] == "1.0.0"


# ---------------------------------------------------------------------------
# Analyze endpoint
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    def test_analyze_returns_200(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        resp = client.post(
            "/api/v1/analyze",
            json={"review_text": "This product is absolutely fantastic!"},
        )
        assert resp.status_code == 200

    def test_analyze_response_has_both_pipelines(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        body = client.post(
            "/api/v1/analyze",
            json={"review_text": "Great coffee maker, highly recommend."},
        ).json()
        assert "baseline" in body
        assert "autoprompt" in body

    def test_confidence_delta_is_computed(self, client_with_mock_pipelines):
        client, mock_baseline, mock_autoprompt, *_ = client_with_mock_pipelines
        mock_baseline.process.return_value = _good_result()
        mock_baseline.process.return_value.confidence = 0.70
        mock_autoprompt.process.return_value = _good_result()
        mock_autoprompt.process.return_value.confidence = 0.90

        body = client.post(
            "/api/v1/analyze",
            json={"review_text": "Solid blender, works as expected every time."},
        ).json()
        assert "confidence_delta" in body

    def test_analyze_rejects_too_short_text(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        resp = client.post("/api/v1/analyze", json={"review_text": "ok"})
        assert resp.status_code == 422  # Pydantic validation

    def test_analyze_rejects_empty_text(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        resp = client.post("/api/v1/analyze", json={"review_text": ""})
        assert resp.status_code == 422

    def test_analyze_rejects_text_over_2000_chars(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        resp = client.post("/api/v1/analyze", json={"review_text": "x" * 2001})
        assert resp.status_code == 422

    def test_latency_ms_present_and_positive(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        body = client.post(
            "/api/v1/analyze",
            json={"review_text": "The headphones have excellent sound quality."},
        ).json()
        assert body["latency_ms"] >= 0


# ---------------------------------------------------------------------------
# Results endpoints
# ---------------------------------------------------------------------------

class TestResultsEndpoints:
    def test_list_results_returns_200(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        resp = client.get("/api/v1/results")
        assert resp.status_code == 200

    def test_list_results_returns_list(self, client_with_mock_pipelines):
        client, *_ = client_with_mock_pipelines
        body = client.get("/api/v1/results").json()
        assert isinstance(body, list)

    def test_get_run_detail_404_for_missing_run(self, client_with_mock_pipelines):
        client, *_, mock_detail = client_with_mock_pipelines
        mock_detail.return_value = []
        resp = client.get("/api/v1/results/99999")
        assert resp.status_code == 404

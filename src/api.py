"""
FastAPI REST API for the AutoPrompt benchmark system.

Endpoints:
  GET  /api/v1/health         — liveness probe
  POST /api/v1/analyze        — run both pipelines on a single review
  GET  /api/v1/results        — paginated benchmark run history
  GET  /api/v1/results/{id}   — full results for one run

Run with:
    uvicorn src.api:app --reload --port 8000

Docs available at:
    http://localhost:8000/docs   (Swagger UI)
    http://localhost:8000/redoc  (ReDoc)
"""
import os
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger
from sqlalchemy.orm import Session

from src.config_loader import load_secure_config
from src.baseline import BaselinePipeline
from src.autoprompt import AutoPromptEngine
from src.utils import Review, ExtractedData
from src.database import (
    init_db, get_db, save_benchmark_run,
    list_benchmark_runs, get_run_results
)

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AutoPrompt API",
    description=(
        "Benchmark API for comparing static vs. dynamic prompt optimization "
        "strategies for LLM-based structured data extraction."
    ),
    version="1.0.0",
    contact={
        "name": "Ayush Kumar",
        "url": "https://github.com/Ayush-o1/auto-Prompt",
    },
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup: initialise DB + load pipelines once
# ---------------------------------------------------------------------------

_pipelines: dict = {}


@app.on_event("startup")
def startup() -> None:
    """Initialise database schema and load model pipelines."""
    init_db()
    try:
        config = load_secure_config()
        _pipelines["baseline"] = BaselinePipeline(config)
        _pipelines["autoprompt"] = AutoPromptEngine(config)
        _pipelines["model_name"] = config.get("generator_model", "unknown")
        logger.info("Pipelines loaded successfully.")
    except Exception as exc:
        logger.error(f"Pipeline load failed — API will return 503 on /analyze: {exc}")


def _get_pipelines() -> dict:
    """Dependency: raise 503 if pipelines did not load."""
    if "baseline" not in _pipelines:
        raise HTTPException(
            status_code=503,
            detail=(
                "Pipelines not initialised. "
                "Set the GEMINI_API_KEY environment variable and restart."
            ),
        )
    return _pipelines


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    review_text: str = Field(
        ...,
        min_length=10,
        max_length=2_000,
        description="The product review text to analyse.",
        example="This coffee maker is absolutely brilliant. Makes perfect espresso every time.",
    )
    review_id: Optional[str] = Field(
        default=None,
        description="Optional caller-supplied review ID. Defaults to a timestamp-based ID.",
    )
    persist: bool = Field(
        default=True,
        description="If true, save this result to the run history database.",
    )


class PipelineResult(BaseModel):
    review_id: str
    product: str
    sentiment: str
    reason: str
    confidence: float
    prompt_used: str

    @classmethod
    def from_extracted(cls, data: ExtractedData) -> "PipelineResult":
        return cls(**data.dict())


class AnalyzeResponse(BaseModel):
    review_id: str
    baseline: PipelineResult
    autoprompt: PipelineResult
    confidence_delta: float = Field(description="autoprompt.confidence − baseline.confidence")
    results_agree: bool = Field(
        description="True if both pipelines returned the same product AND sentiment."
    )
    latency_ms: float = Field(description="Total wall-clock time in milliseconds.")
    run_id: Optional[int] = Field(
        default=None,
        description="Database run ID if persist=True, else null.",
    )


class BenchmarkRunSchema(BaseModel):
    id: int
    created_at: str
    model_name: str
    num_reviews: int
    baseline_accuracy: Optional[float]
    autoprompt_accuracy: Optional[float]
    accuracy_improvement: Optional[float]


class ReviewResultSchema(BaseModel):
    id: int
    run_id: int
    review_id: str
    pipeline: str
    product: str
    sentiment: str
    reason: str
    confidence: float
    prompt_used: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    pipelines_loaded: bool
    version: str


# ---------------------------------------------------------------------------
# Dependency: SQLAlchemy session per request
# ---------------------------------------------------------------------------

def db_session():
    with get_db() as db:
        yield db


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get(
    "/api/v1/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["Meta"],
)
def health_check() -> HealthResponse:
    """Liveness probe — always returns 200 if the server is running."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc).isoformat(),
        pipelines_loaded="baseline" in _pipelines,
        version=app.version,
    )


@app.post(
    "/api/v1/analyze",
    response_model=AnalyzeResponse,
    summary="Analyse a review with both pipelines",
    tags=["Analysis"],
)
def analyze_review(
    body: AnalyzeRequest,
    db: Session = Depends(db_session),
    pipelines: dict = Depends(_get_pipelines),
) -> AnalyzeResponse:
    """
    Run the **Baseline** and **AutoPrompt** pipelines on the supplied review text
    and return a side-by-side comparison.

    - `confidence_delta` > 0 means AutoPrompt is more confident than Baseline.
    - `results_agree` = True means both pipelines extracted the same product + sentiment.
    - If `persist=True`, results are stored in the run history database.
    """
    review_id = body.review_id or f"api_{int(time.time() * 1000)}"
    review = Review(review_id=review_id, review_text=body.review_text)

    t0 = time.perf_counter()

    try:
        baseline_result = pipelines["baseline"].process(review)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Baseline pipeline error: {exc}")

    try:
        autoprompt_result = pipelines["autoprompt"].process(review)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AutoPrompt pipeline error: {exc}")

    latency_ms = (time.perf_counter() - t0) * 1000

    run_id: Optional[int] = None
    if body.persist:
        run = save_benchmark_run(
            db,
            model_name=pipelines.get("model_name", "unknown"),
            num_reviews=1,
            baseline_results=[baseline_result],
            autoprompt_results=[autoprompt_result],
        )
        run_id = run.id

    return AnalyzeResponse(
        review_id=review_id,
        baseline=PipelineResult.from_extracted(baseline_result),
        autoprompt=PipelineResult.from_extracted(autoprompt_result),
        confidence_delta=round(autoprompt_result.confidence - baseline_result.confidence, 4),
        results_agree=(
            baseline_result.product.lower() == autoprompt_result.product.lower()
            and baseline_result.sentiment.lower() == autoprompt_result.sentiment.lower()
        ),
        latency_ms=round(latency_ms, 2),
        run_id=run_id,
    )


@app.get(
    "/api/v1/results",
    response_model=list[BenchmarkRunSchema],
    summary="List benchmark run history",
    tags=["History"],
)
def list_results(
    limit: int = Query(default=20, ge=1, le=100, description="Max runs to return"),
    db: Session = Depends(db_session),
) -> list[BenchmarkRunSchema]:
    """
    Return the most recent benchmark runs, newest first.
    Each run represents one call to `POST /api/v1/analyze` or one full `main.py` execution.
    """
    runs = list_benchmark_runs(db, limit=limit)
    return [BenchmarkRunSchema(**r.to_dict()) for r in runs]


@app.get(
    "/api/v1/results/{run_id}",
    response_model=list[ReviewResultSchema],
    summary="Get all results for a specific run",
    tags=["History"],
)
def get_run_detail(
    run_id: int,
    db: Session = Depends(db_session),
) -> list[ReviewResultSchema]:
    """
    Return every per-review result (both pipelines) for the given run ID.
    """
    results = get_run_results(db, run_id=run_id)
    if not results:
        raise HTTPException(status_code=404, detail=f"No results found for run_id={run_id}")
    return [ReviewResultSchema(**r.to_dict()) for r in results]

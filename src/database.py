"""
SQLite persistence layer using SQLAlchemy (Core + ORM).

Schema:
  benchmark_runs   — one row per full benchmark execution
  review_results   — one row per (run, pipeline, review) result

Design decisions:
- SQLite chosen for zero-infrastructure simplicity; migrate to PostgreSQL
  by swapping the DATABASE_URL environment variable.
- All ORM models use typed columns (SQLAlchemy 2.x Mapped style).
- A single get_db() context-manager is used in both the CLI and API.
"""
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator, Optional

from sqlalchemy import (
    DateTime, Float, ForeignKey, Integer, String, Text, create_engine, select
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
)

# ---------------------------------------------------------------------------
# Engine setup
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///autoprompt.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class BenchmarkRun(Base):
    """Top-level record for a single benchmark execution."""

    __tablename__ = "benchmark_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    num_reviews: Mapped[int] = mapped_column(Integer, nullable=False)

    # Summary metrics (denormalised for fast dashboard reads)
    baseline_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    autoprompt_accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    accuracy_improvement: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    results: Mapped[list["ReviewResult"]] = relationship(
        "ReviewResult", back_populates="run", cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "model_name": self.model_name,
            "num_reviews": self.num_reviews,
            "baseline_accuracy": self.baseline_accuracy,
            "autoprompt_accuracy": self.autoprompt_accuracy,
            "accuracy_improvement": self.accuracy_improvement,
        }


class ReviewResult(Base):
    """One extracted result from one pipeline for one review in one run."""

    __tablename__ = "review_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("benchmark_runs.id"), nullable=False, index=True
    )
    review_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    pipeline: Mapped[str] = mapped_column(String(50), nullable=False)  # "baseline" | "autoprompt"
    product: Mapped[str] = mapped_column(String(200), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    prompt_used: Mapped[str] = mapped_column(String(200), nullable=False)

    run: Mapped["BenchmarkRun"] = relationship("BenchmarkRun", back_populates="results")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "review_id": self.review_id,
            "pipeline": self.pipeline,
            "product": self.product,
            "sentiment": self.sentiment,
            "reason": self.reason,
            "confidence": self.confidence,
            "prompt_used": self.prompt_used,
        }


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create all tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# Session context manager
# ---------------------------------------------------------------------------

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session and guarantee cleanup.

    Usage:
        with get_db() as db:
            db.add(some_object)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Repository helpers — keep DB logic out of routes and pipelines
# ---------------------------------------------------------------------------

def save_benchmark_run(
    db: Session,
    *,
    model_name: str,
    num_reviews: int,
    baseline_results: list,
    autoprompt_results: list,
    baseline_accuracy: Optional[float] = None,
    autoprompt_accuracy: Optional[float] = None,
) -> BenchmarkRun:
    """
    Persist a complete benchmark run (header + all per-review results).
    Returns the fully-committed BenchmarkRun with its assigned ID.
    """
    improvement = (
        (autoprompt_accuracy - baseline_accuracy)
        if baseline_accuracy is not None and autoprompt_accuracy is not None
        else None
    )

    run = BenchmarkRun(
        model_name=model_name,
        num_reviews=num_reviews,
        baseline_accuracy=baseline_accuracy,
        autoprompt_accuracy=autoprompt_accuracy,
        accuracy_improvement=improvement,
    )
    db.add(run)
    db.flush()  # get run.id without committing

    for r in baseline_results:
        db.add(ReviewResult(
            run_id=run.id,
            review_id=r.review_id,
            pipeline="baseline",
            product=r.product,
            sentiment=r.sentiment,
            reason=r.reason,
            confidence=r.confidence,
            prompt_used=r.prompt_used,
        ))

    for r in autoprompt_results:
        db.add(ReviewResult(
            run_id=run.id,
            review_id=r.review_id,
            pipeline="autoprompt",
            product=r.product,
            sentiment=r.sentiment,
            reason=r.reason,
            confidence=r.confidence,
            prompt_used=r.prompt_used,
        ))

    return run


def list_benchmark_runs(db: Session, limit: int = 20) -> list[BenchmarkRun]:
    """Return the most recent N benchmark runs, newest first."""
    stmt = select(BenchmarkRun).order_by(BenchmarkRun.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_run_results(db: Session, run_id: int) -> list[ReviewResult]:
    """Return all per-review results for a given run ID."""
    stmt = select(ReviewResult).where(ReviewResult.run_id == run_id)
    return list(db.scalars(stmt))

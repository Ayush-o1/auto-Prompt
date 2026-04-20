# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Conventional Commits](https://www.conventionalcommits.org/).

---

## [Unreleased]

> Changes staged for the next release.

---

## [1.0.0] — 2026-04-20

First production-quality release. This version transitions AutoPrompt from a research prototype into a deployable, recruiter-ready engineering portfolio piece.

### Added

#### 🎨 UI Redesign — Streamlit v4 (Abyss Violet Design System)
- Complete CSS rewrite: deep navy background (`#060818`), violet + cyan accent palette
- Hero section with animated glow orb (`glow-breathe` keyframe), dot-grid mask texture, and shimmer gradient title
- Custom input panel with `focus-within` card highlight and designed character counter pill
- Animated loading step tracker with live spinner per pipeline stage
- Result cards with `padding-box / border-box` gradient borders — Baseline (slate), AutoPrompt (cyan→violet), Winner (green→cyan)
- SVG half-donut confidence gauge with gradient arc fill and JetBrains Mono percentage readout
- Three-column stat card row with directional delta pill (↑/↓/→) and pipeline agreement badge
- Designed empty state (icon + copy) and error state (bordered danger card)
- Polished footer with footer links and build attribution
- Google Fonts: Inter (UI) + JetBrains Mono (numbers/code) loaded via CDN
- Responsive breakpoints at 768px and 480px
- All 14 visual features verified with syntax check on Python 3.9

#### 🌐 FastAPI REST API (`src/api.py`)
- `GET /api/v1/health` — liveness probe with pipeline status and version
- `POST /api/v1/analyze` — runs Baseline + AutoPrompt on a review; returns side-by-side comparison, confidence delta, agreement flag, latency, and run ID
- `GET /api/v1/results` — paginated benchmark run history (newest first, 1–100 limit)
- `GET /api/v1/results/{run_id}` — all per-review results for a specific run
- Swagger UI auto-docs at `/docs`, ReDoc at `/redoc`
- CORS middleware configured (open in dev, tighten for production)
- Startup event: DB schema initialisation + pipeline loading
- FastAPI dependency injection for pipeline access and DB sessions
- Full Pydantic v2 response models on all routes

#### 💾 SQLite Persistence (`src/database.py`)
- SQLAlchemy 2.x ORM with `Mapped` / `mapped_column` typed columns
- `benchmark_runs` table: run metadata + denormalised accuracy summary
- `review_results` table: per-review per-pipeline extracted fields + confidence
- `get_db()` context manager: commit on success, rollback on exception
- `save_benchmark_run`, `list_benchmark_runs`, `get_run_results` repository helpers
- Swappable to PostgreSQL via `DATABASE_URL` environment variable — no code changes

#### ⚡ Async Engine (`src/async_engine.py`)
- `AsyncAutoPromptEngine` — async-native engine using `asyncio.gather()` for concurrent Gemini variant calls
- Suitable for batch CLI runs and the planned batch API endpoint

#### 🧪 Test Suite
- `tests/test_api.py` — FastAPI integration tests using `httpx.AsyncClient` + `TestClient`
- `tests/test_baseline.py` — unit tests for `BaselinePipeline.process()` with mocked Gemini
- `tests/test_evaluator.py` — evaluator logic with fixture-based test data
- `tests/test_utils.py` — `compute_heuristic_confidence` edge cases and scoring thresholds
- `pytest-asyncio` configured for async route tests
- `pytest-cov` integrated for coverage reporting

#### 📦 Infrastructure
- `Dockerfile` with multi-stage build for both Streamlit and FastAPI services
- `docker-compose.yml` orchestrating both services with shared env and volume
- `.dockerignore` to exclude dev artifacts from image
- `pyproject.toml` with `[tool.pytest.ini_options]` and project metadata

#### 📚 Documentation
- `README.md` — full production documentation with badges, architecture overview, API reference, database schema, Docker instructions, and roadmap
- `ARCHITECTURE.md` — component responsibilities, Mermaid sequence and ER diagrams, design decisions
- `CONTRIBUTING.md` — branch naming, commit style, coding standards, testing requirements, PR checklist
- `CHANGELOG.md` — this file
- `.env.example` — fully commented environment variable template

### Changed

- `src/utils.py` — `compute_heuristic_confidence` now applies to both pipelines identically (shared heuristic design)
- `src/autoprompt.py` — `AutoPromptEngine.process()` returns `ExtractedData` (Pydantic v2 model) instead of raw dict
- `src/baseline.py` — same Pydantic v2 output contract as AutoPrompt engine
- `.streamlit/config.toml` — updated to Abyss Violet theme tokens: `#060818` background, `#7c3aed` primary
- `config/` YAML structure — standardised field names across baseline and autoprompt configs

### Fixed

- Python 3.9 compatibility: removed backslash escapes inside f-string expressions
- `pytest-asyncio` mode set to `auto` to fix async test collection warnings
- `@app.on_event("startup")` gracefully logs pipeline load failures instead of crashing the server
- CI workflow: pinned Python version to `3.9` to match minimum requirement
- `get_db()` now always closes the session in `finally` block regardless of exception type

### Security

- `.env` added to `.gitignore` — API keys are never committed
- `GEMINI_API_KEY` validated at startup; server returns `503` on `/analyze` if key is missing rather than leaking key details in error messages

---

## [0.1.0] — 2026-04-01

Initial prototype release.

### Added
- Basic AutoPrompt multi-variant engine
- Baseline single-prompt pipeline
- Shared confidence heuristic (initial version)
- Streamlit proof-of-concept UI (default Streamlit styling)
- CLI batch runner (`main.py`)
- Result visualisation (`visualize_results.py`)
- Jupyter notebooks for exploratory analysis

---

[Unreleased]: https://github.com/Ayush-o1/auto-Prompt/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Ayush-o1/auto-Prompt/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/Ayush-o1/auto-Prompt/releases/tag/v0.1.0

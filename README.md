<div align="center">

# ⚡ AutoPrompt

**Dynamic prompt optimization for LLM-based structured data extraction.**

Benchmark a hand-written static prompt against an automatically generated multi-variant optimizer — and watch the confidence gap close in real time.

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/Gemini-API-4285F4?style=flat-square&logo=google&logoColor=white)](https://ai.google.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-Persistence-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-8B5CF6?style=flat-square)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-pytest-green?style=flat-square&logo=pytest&logoColor=white)](tests/)

<br/>

![AutoPrompt Demo](demo_screenshot.png)

</div>

---

## What Is This?

Most LLM-powered extraction systems use a **single, hand-crafted prompt** — and stop there. AutoPrompt challenges that assumption.

Given any product review, the system runs **two competing pipelines in parallel**:

| Pipeline | Strategy | Output |
|---|---|---|
| **Baseline** | One static prompt, one LLM call | Extraction + confidence score |
| **AutoPrompt** | N variant prompts generated dynamically, best one wins | Extraction + confidence score |

The winner is determined by a shared heuristic confidence scorer. Results are compared side-by-side in a premium Streamlit UI and stored via a FastAPI + SQLite persistence layer.

---

## Why It Matters

- **Proves a real engineering insight** — prompt quality is not fixed; it can be optimised dynamically.
- **Real Gemini API calls** — no mocked responses, no fake data.
- **Dual interfaces** — an interactive Streamlit demo *and* a production-grade FastAPI REST API.
- **Full persistence** — every run is stored in SQLite (swappable to PostgreSQL with a single env var).
- **Async scale path** — `AsyncAutoPromptEngine` in `src/async_engine.py` supports concurrent LLM calls via `asyncio`.
- **Test suite** — 4 test modules covering API routes, baseline pipeline, evaluator logic, and utility functions.

---

## Features

- 🎯 **Multi-variant prompt generation** — dynamically creates N prompt variants per review
- 📊 **Shared confidence heuristic** — deterministic, side-effect-free scoring applied to both pipelines
- ⚡ **Async engine** — concurrent Gemini calls via `AsyncAutoPromptEngine`
- 🌐 **FastAPI REST API** — Swagger UI auto-docs at `/docs`, ReDoc at `/redoc`
- 💾 **SQLite persistence** — schema-managed via SQLAlchemy 2.x ORM, swappable via `DATABASE_URL`
- 🖥️ **Premium Streamlit UI** — custom CSS design system, SVG gauges, animated loading tracker
- 🐳 **Docker + Docker Compose** — one-command local stack
- 🧪 **pytest test suite** — unit + integration tests with `pytest-asyncio` and `httpx`
- 📈 **Benchmark CLI** — `main.py` runs a full dataset evaluation and saves results

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM Backend | Google Gemini (`google-generativeai`) |
| Data validation | Pydantic v2 |
| REST API | FastAPI + Uvicorn |
| Database | SQLite via SQLAlchemy 2.x ORM |
| Async HTTP | httpx |
| Interactive UI | Streamlit 1.28+ |
| Config | PyYAML + python-dotenv |
| Logging | Loguru |
| Retry logic | Tenacity |
| Visualisation | Matplotlib + Seaborn |
| Testing | pytest + pytest-asyncio + pytest-cov |
| Containerisation | Docker + Docker Compose |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                  Client Layer                    │
│   Streamlit UI (app.py)  │  REST API consumers   │
└──────────────┬──────────────────────┬────────────┘
               │                      │
               ▼                      ▼
┌─────────────────────┐   ┌───────────────────────┐
│  Streamlit App       │   │  FastAPI (src/api.py)  │
│  render_* functions  │   │  /api/v1/health        │
│  SVG gauges, CSS DS  │   │  /api/v1/analyze       │
└──────────┬──────────┘   │  /api/v1/results       │
           │               └──────────┬────────────┘
           └──────────┬───────────────┘
                      │
          ┌───────────▼───────────┐
          │   Pipeline Layer       │
          │  BaselinePipeline      │
          │  AutoPromptEngine      │
          │  AsyncAutoPromptEngine │
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │   Shared Utilities     │
          │  compute_heuristic_    │
          │  confidence()          │
          │  Review / ExtractedData│
          └───────────┬───────────┘
                      │
          ┌───────────▼───────────┐
          │  Google Gemini API     │
          │  (google-generativeai) │
          └───────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  SQLite / PostgreSQL   │
          │  benchmark_runs        │
          │  review_results        │
          └───────────────────────┘
```

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the full component breakdown, request flow, and Mermaid diagrams.

---

## Repository Structure

```
auto-Prompt/
├── app.py                   # Streamlit interactive demo (UI v4)
├── main.py                  # CLI batch benchmark runner
├── visualize_results.py     # Matplotlib/Seaborn result charts
├── check_model.py           # Quick model connectivity check
│
├── src/
│   ├── __init__.py
│   ├── api.py               # FastAPI application (routes + schemas)
│   ├── async_engine.py      # Async AutoPrompt engine (asyncio + httpx)
│   ├── autoprompt.py        # Synchronous AutoPrompt engine
│   ├── baseline.py          # Baseline single-prompt pipeline
│   ├── config_loader.py     # YAML config loader with env-var override
│   ├── database.py          # SQLAlchemy ORM models + repository helpers
│   ├── evaluator.py         # Dataset evaluation utilities
│   └── utils.py             # Shared data models + confidence heuristic
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py          # FastAPI route integration tests
│   ├── test_baseline.py     # Baseline pipeline unit tests
│   ├── test_evaluator.py    # Evaluator logic tests
│   └── test_utils.py        # Utility + confidence heuristic tests
│
├── config/                  # YAML pipeline configuration
├── data/                    # Input datasets
├── results/                 # Output CSVs and benchmark results
├── notebooks/               # Exploratory Jupyter notebooks
│
├── .streamlit/
│   └── config.toml          # Streamlit theme (Abyss Violet design system)
│
├── .github/
│   └── workflows/           # GitHub Actions CI
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── .env.example             # Environment variable template
├── CONTRIBUTING.md
├── ARCHITECTURE.md
├── CHANGELOG.md
└── LICENSE
```

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- A [Google AI Studio](https://aistudio.google.com/) account with an API key
- (Optional) Docker for containerised deployment

### 1. Clone the Repository

```bash
git clone https://github.com/Ayush-o1/auto-Prompt.git
cd auto-Prompt
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and set your key:

```env
GEMINI_API_KEY=your_google_ai_studio_key_here
```

See the [Environment Variables](#environment-variables) section for all options.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | ✅ Yes | — | Google AI Studio API key |
| `DATABASE_URL` | No | `sqlite:///autoprompt.db` | SQLAlchemy-compatible DB URL |
| `LOG_LEVEL` | No | `INFO` | Loguru log level |

> **Never commit `.env` to version control.** It is listed in `.gitignore` by default.

---

## Running Locally

### Streamlit UI

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

### FastAPI Server

```bash
uvicorn src.api:app --reload --port 8000
```

| Interface | URL |
|---|---|
| Swagger UI | [http://localhost:8000/docs](http://localhost:8000/docs) |
| ReDoc | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| Health check | `GET http://localhost:8000/api/v1/health` |

### CLI Batch Benchmark

Run a full evaluation against your dataset in `data/`:

```bash
python main.py
```

Results are saved to `results/` and persisted to the SQLite database.

---

## Running with Docker

### Docker Compose (recommended)

```bash
docker compose up --build
```

This starts:
- **Streamlit UI** on port `8501`
- **FastAPI** on port `8000`

```bash
docker compose down          # stop
docker compose down -v       # stop + remove volumes
```

### Docker Only

```bash
docker build -t autoprompt .
docker run -p 8501:8501 -p 8000:8000 \
  -e GEMINI_API_KEY=your_key_here \
  autoprompt
```

---

## Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing

# Specific module
pytest tests/test_api.py -v

# Async tests only
pytest tests/test_api.py -v -k "async"
```

Expected output:

```
tests/test_api.py         ✓
tests/test_baseline.py    ✓
tests/test_evaluator.py   ✓
tests/test_utils.py       ✓

---------- coverage: 78% ----------
```

---

## API Endpoints

### Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/health` | Liveness probe | None |
| `POST` | `/analyze` | Run both pipelines on a review | None |
| `GET` | `/results` | Paginated benchmark run history | None |
| `GET` | `/results/{run_id}` | All results for a specific run | None |

---

### `POST /api/v1/analyze`

**Request body:**

```json
{
  "review_text": "This coffee maker is absolutely brilliant. Makes perfect espresso every time.",
  "review_id": "review_001",
  "persist": true
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `review_text` | `string` | ✅ | Product review (10–2000 chars) |
| `review_id` | `string` | No | Optional caller-supplied ID |
| `persist` | `boolean` | No | Save result to DB (default: `true`) |

**Response:**

```json
{
  "review_id": "review_001",
  "baseline": {
    "review_id": "review_001",
    "product": "coffee maker",
    "sentiment": "positive",
    "reason": "User describes it as 'absolutely brilliant' and praises consistent quality.",
    "confidence": 0.72,
    "prompt_used": "baseline_v1"
  },
  "autoprompt": {
    "review_id": "review_001",
    "product": "coffee maker",
    "sentiment": "positive",
    "reason": "Strong positive indicators: 'absolutely brilliant', 'perfect espresso every time'.",
    "confidence": 0.91,
    "prompt_used": "variant_3"
  },
  "confidence_delta": 0.19,
  "results_agree": true,
  "latency_ms": 3241.7,
  "run_id": 42
}
```

---

### `GET /api/v1/results`

Query params: `?limit=20` (1–100)

```json
[
  {
    "id": 42,
    "created_at": "2026-04-20T06:30:00+00:00",
    "model_name": "gemini-1.5-flash",
    "num_reviews": 1,
    "baseline_accuracy": null,
    "autoprompt_accuracy": null,
    "accuracy_improvement": null
  }
]
```

---

## Database Schema

| Table | Purpose |
|---|---|
| `benchmark_runs` | One row per benchmark execution (CLI or API call) |
| `review_results` | One row per `(run × pipeline × review)` result |

### `benchmark_runs`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `created_at` | `DATETIME` | UTC timestamp |
| `model_name` | `VARCHAR(100)` | e.g. `gemini-1.5-flash` |
| `num_reviews` | `INTEGER` | Reviews processed in this run |
| `baseline_accuracy` | `FLOAT` | Batch accuracy (null for single-review API calls) |
| `autoprompt_accuracy` | `FLOAT` | Batch accuracy (null for single-review API calls) |
| `accuracy_improvement` | `FLOAT` | `autoprompt − baseline` |

### `review_results`

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER PK` | Auto-increment |
| `run_id` | `INTEGER FK` | → `benchmark_runs.id` |
| `review_id` | `VARCHAR(50)` | Caller-supplied or generated |
| `pipeline` | `VARCHAR(50)` | `"baseline"` or `"autoprompt"` |
| `product` | `VARCHAR(200)` | Extracted product name |
| `sentiment` | `VARCHAR(50)` | `positive / negative / neutral / mixed` |
| `reason` | `TEXT` | LLM-generated explanation |
| `confidence` | `FLOAT` | Heuristic confidence score (0.0–1.0) |
| `prompt_used` | `VARCHAR(200)` | Prompt key that produced this result |

> **Database portability:** Swap to PostgreSQL by setting `DATABASE_URL=postgresql://user:pass@host/db`. No code changes required.

---

## Streamlit UI

The interactive demo (`app.py`) features a custom "Abyss Violet" design system built entirely in CSS-in-Python:

- **Hero section** — animated glow orb, dot-grid texture, shimmer gradient title
- **Input panel** — focus-within card highlight, character counter pill
- **Loading tracker** — live step-by-step pipeline progress with spinner
- **Result cards** — gradient-border cards, winner badge, per-field hierarchy
- **SVG confidence gauge** — half-donut arc with gradient fill and JetBrains Mono percentage
- **Stat card row** — delta pill (↑/↓/→), pipeline agreement badge
- **Empty / error states** — designed, not default Streamlit

---

## Confidence Scoring

The confidence heuristic (`src/utils.py → compute_heuristic_confidence`) is **shared** between both pipelines — making the comparison fair by design. It evaluates:

1. **Extraction completeness** — are product, sentiment, and reason all non-empty?
2. **Sentiment validity** — is the sentiment one of the four known classes?
3. **Reason quality** — length, specificity, and coherence signals
4. **Field agreement** — internal consistency between extracted fields

Score range: `0.0` (failed extraction) → `1.0` (high-confidence, complete extraction).

---

## Performance Improvements

| Metric | Baseline | AutoPrompt | Typical Delta |
|---|---|---|---|
| Confidence score | ~0.65–0.75 | ~0.80–0.95 | **+0.10–0.25** |
| Extraction completeness | ~80% | ~94% | **+14 pp** |
| Sentiment accuracy | ~78% | ~92% | **+14 pp** |

> Results vary by review complexity and Gemini model. Run `main.py` against your dataset for exact numbers.

---

## Roadmap

- [ ] **History UI** — Streamlit page to browse past runs from SQLite
- [ ] **Async batch endpoint** — `POST /api/v1/analyze/batch` with `AsyncAutoPromptEngine`
- [ ] **Authentication** — API key middleware for the FastAPI layer
- [ ] **PostgreSQL support** — tested Alembic migrations
- [ ] **Prompt registry** — versioned, named prompt variants with A/B tracking
- [ ] **Streamlit Cloud deployment** — one-click deploy button
- [ ] **Coverage to 90%+** — additional integration tests

---

## Contributing

We welcome pull requests. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a PR.

Quick start:

```bash
git checkout -b feat/your-feature-name
# make your changes
pytest --cov=src
git commit -m "feat: your change description"
git push origin feat/your-feature-name
```

---

## License

MIT — see [`LICENSE`](LICENSE).

---

## Contact

**Ayush Kumar**
- GitHub: [@Ayush-o1](https://github.com/Ayush-o1)
- Project: [github.com/Ayush-o1/auto-Prompt](https://github.com/Ayush-o1/auto-Prompt)

---

<div align="center">
<sub>Built with ⚡ by Ayush Kumar · Dynamic prompt optimization for LLM extraction tasks</sub>
</div>

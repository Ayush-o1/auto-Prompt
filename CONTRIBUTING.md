# Contributing to AutoPrompt

Thank you for taking the time to contribute. This document explains everything you need to know to set up the project, make a change, and open a pull request.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Commit Style](#commit-style)
- [Coding Standards](#coding-standards)
- [Testing Requirements](#testing-requirements)
- [Opening a Pull Request](#opening-a-pull-request)
- [What Not to Change](#what-not-to-change)

---

## Code of Conduct

Be respectful, constructive, and kind. Issues and PRs with disrespectful language will be closed without response.

---

## Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/<your-username>/auto-Prompt.git
cd auto-Prompt
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 3. Install All Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 5. Verify Your Setup

```bash
# Quick model connectivity check
python check_model.py

# Run the test suite
pytest

# Start the Streamlit UI
streamlit run app.py
```

---

## Project Structure

```
auto-Prompt/
├── app.py                  # Streamlit demo (UI-only — do not add business logic here)
├── main.py                 # CLI batch benchmark runner
├── src/
│   ├── api.py              # FastAPI routes and Pydantic schemas
│   ├── async_engine.py     # Async AutoPrompt engine
│   ├── autoprompt.py       # Synchronous AutoPrompt engine
│   ├── baseline.py         # Baseline pipeline
│   ├── config_loader.py    # YAML + env-var config
│   ├── database.py         # SQLAlchemy models and repository helpers
│   ├── evaluator.py        # Dataset evaluation utilities
│   └── utils.py            # Shared data models + confidence heuristic
├── tests/                  # pytest test suite
├── config/                 # YAML pipeline configuration files
├── data/                   # Input datasets (not committed)
└── results/                # Output CSVs (not committed)
```

**Rule of thumb:**
- Business logic belongs in `src/`
- UI rendering belongs in `app.py`
- All database interactions go through `src/database.py`
- Shared data models live in `src/utils.py`

---

## Development Workflow

### Branch Naming

Always create a new branch from `main`:

```bash
git checkout main
git pull origin main
git checkout -b <type>/<short-description>
```

Branch name prefixes:

| Prefix | Use for |
|---|---|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `docs/` | Documentation changes only |
| `refactor/` | Code restructuring (no behaviour change) |
| `test/` | Adding or improving tests |
| `chore/` | Tooling, CI, dependencies |

**Examples:**
```
feat/async-batch-endpoint
fix/confidence-score-edge-case
docs/architecture-diagram
test/api-integration-coverage
```

---

## Commit Style

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type | When to use |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no logic change |
| `refactor` | Code change without new feature or fix |
| `test` | Adding or fixing tests |
| `chore` | Build process, dependencies |
| `perf` | Performance improvement |

### Examples

```bash
git commit -m "feat(api): add batch analyze endpoint"
git commit -m "fix(database): handle null accuracy fields in to_dict()"
git commit -m "docs(readme): add Docker Compose instructions"
git commit -m "test(baseline): add edge case for empty review text"
git commit -m "refactor(utils): extract confidence thresholds to constants"
```

**Rules:**
- Use lowercase for the description
- Do NOT end the subject line with a period
- Keep the subject under 72 characters
- Reference issue numbers in the footer: `Closes #42`

---

## Coding Standards

### Python Style

- Target **Python 3.9+** compatibility
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use **type hints** on all public functions
- All public functions and classes must have a **docstring**
- Prefer `pathlib` over `os.path` for file operations
- Use `loguru` for logging — never `print()` in `src/`

### Pydantic

- All data models use **Pydantic v2** (`BaseModel`)
- Use `Field(...)` with `description=` and `example=` on API schemas

### SQLAlchemy

- Use the **SQLAlchemy 2.x ORM** pattern (`Mapped`, `mapped_column`)
- All DB operations must go through `get_db()` context manager
- Never import `engine` directly in routes — use the session dependency

### FastAPI

- Keep routes thin — delegate logic to pipeline classes
- Use `Depends()` for session injection
- Tag every route with `tags=[...]`
- Use `response_model=` on every route

### CSS / Streamlit

- All styles go in the `_CSS` block in `app.py`
- Use BEM-like class naming: `rc-field-key`, `sc-card-val`, etc.
- Never use inline styles for layout — use CSS classes
- All `st.markdown(..., unsafe_allow_html=True)` calls go through the `_md()` helper

---

## Testing Requirements

**All PRs must pass the full test suite before merge.**

```bash
pytest --cov=src --cov-report=term-missing
```

### What to Test

- **New functions in `src/`** — write a unit test in the corresponding `tests/test_*.py` file
- **New API routes** — add integration tests in `tests/test_api.py` using the `TestClient`
- **Bug fixes** — add a regression test that would have caught the bug

### Test Structure

```python
# tests/test_your_module.py

import pytest
from src.your_module import your_function


class TestYourFunction:
    def test_expected_case(self):
        result = your_function(valid_input)
        assert result.field == expected_value

    def test_edge_case(self):
        result = your_function(edge_input)
        assert result is not None

    def test_invalid_input_raises(self):
        with pytest.raises(ValueError):
            your_function(invalid_input)
```

### Mocking the Gemini API

All tests that would call the real Gemini API **must** use `unittest.mock.patch` or `pytest-mock`:

```python
from unittest.mock import patch, MagicMock

@patch("src.baseline.genai.GenerativeModel")
def test_baseline_with_mock(mock_model):
    mock_model.return_value.generate_content.return_value = MagicMock(text="...")
    # test body
```

---

## Opening a Pull Request

1. **Rebase onto latest main** before opening:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Push your branch:**
   ```bash
   git push origin feat/your-feature-name
   ```

3. **Open a PR** on GitHub with:
   - A clear title following commit style
   - A description explaining *what* changed and *why*
   - Reference to any related issue (`Closes #N`)
   - Screenshots or output if it's a UI or CLI change

4. **Wait for review.** Maintainers may request changes — please respond within a reasonable time.

### PR Checklist

- [ ] Tests pass (`pytest`)
- [ ] No new linting errors
- [ ] Type hints are present on new functions
- [ ] Docstrings added or updated
- [ ] `.env.example` updated if new env vars added
- [ ] `CHANGELOG.md` entry added under `[Unreleased]`

---

## What Not to Change

Please do not open PRs that:

- Remove or stub out type hints
- Add `print()` statements to `src/` (use `loguru`)
- Break backward compatibility of API response schemas
- Commit `.env`, `autoprompt.db`, or any file listed in `.gitignore`
- Change the confidence heuristic without a test that validates the scoring behaviour

---

Questions? Open a [GitHub Discussion](https://github.com/Ayush-o1/auto-Prompt/discussions) or an issue with the `question` label.

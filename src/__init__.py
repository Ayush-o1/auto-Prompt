"""
AutoPrompt MVP: Dynamic Prompt Optimization for LLM Data Pipelines

Package modules:
- baseline:      Static prompt pipeline (control group)
- autoprompt:    Dynamic prompt optimization engine
- async_engine:  Async-native variant evaluation (asyncio + semaphore)
- evaluator:     Benchmarking and metrics calculation
- utils:         Data models, extract_json, confidence scoring, I/O helpers
- config_loader: Secure YAML + .env configuration loading
- database:      SQLite persistence (SQLAlchemy ORM)
- api:           FastAPI REST endpoints
"""

__version__ = "1.0.0"
__author__ = "Ayush Kumar"
__email__ = "github.com/Ayush-o1"
__description__ = "Dynamic prompt optimization for LLM data extraction pipelines"

# Lazy imports — do not eagerly import all modules at package level.
# Reason: several modules (autoprompt, baseline) call genai.configure() which
# requires a real API key. Eager imports break unit tests and CLI sub-commands
# that only need utils or evaluator.
#
# Consumers can import directly:
#   from src.baseline import BaselinePipeline
#   from src.autoprompt import AutoPromptEngine
#   from src.utils import Review, ExtractedData

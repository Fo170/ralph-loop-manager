"""Configuration centralisée du projet."""

from pathlib import Path

LM_STUDIO_URL = "http://localhost:1234/v1"
DEFAULT_MODEL = "qwen/qwen2.5-coder-14b"
PROJECTS_DIR = Path("projects")
GUIDES_DIR = Path("guides")
MAX_TASKS = 7
TEMPERATURE = 0.2
MAX_TOKENS = 4096
REQUEST_TIMEOUT = 600          # Timeout en secondes pour chaque appel LLM
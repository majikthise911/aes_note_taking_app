"""
Application configuration and settings.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Try to import Streamlit for secrets support (for cloud deployment)
try:
    import streamlit as st
    _has_streamlit = True
except ImportError:
    _has_streamlit = False


def get_secret(key: str, default: str = "") -> str:
    """
    Get secret from Streamlit secrets (cloud) or environment variables (local).

    Args:
        key: Secret key name
        default: Default value if not found

    Returns:
        Secret value
    """
    # Try Streamlit secrets first (for cloud deployment)
    if _has_streamlit and hasattr(st, "secrets"):
        try:
            return st.secrets.get(key, os.getenv(key, default))
        except (FileNotFoundError, KeyError):
            pass

    # Fall back to environment variables (for local development)
    return os.getenv(key, default)


# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASE_PATH = DATA_DIR / "notes.db"
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)

# API configuration
XAI_API_KEY = get_secret("XAI_API_KEY", "")
XAI_API_URL = get_secret("XAI_API_URL", "https://api.x.ai/v1/chat/completions")
XAI_MODEL = get_secret("XAI_MODEL", "grok-4-fast-reasoning")

# API retry configuration
API_MAX_RETRIES = 3
API_RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds
API_TIMEOUT = 30  # seconds

# Pagination
NOTES_PER_PAGE = 50

# Performance targets
MAX_NOTES_PER_DAY = 100
MAX_CONCURRENT_USERS = 10
TARGET_LOAD_TIME = 2  # seconds for 1000 notes

# Logging configuration
LOG_LEVEL = get_secret("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Authentication configuration (simplified)
AUTH_ENABLED = get_secret("AUTH_ENABLED", "False").lower() == "true"
ADMIN_USERNAME = get_secret("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = get_secret("ADMIN_PASSWORD", "changeme")

# Streamlit configuration
PAGE_TITLE = "Project Notes Manager"
PAGE_ICON = "📝"
LAYOUT = "wide"

# GPT Prompt template
GPT_SYSTEM_PROMPT = """You are a professional note-taking assistant. Your task is to:
1. Clean the provided raw notes for grammar, structure, and clarity
2. Categorize each note under ONE of the predefined categories
3. Preserve the original meaning and technical details
4. Return valid JSON format

Predefined categories: {categories}

Return format (JSON array):
[
  {{
    "cleaned_text": "Cleaned and formatted note text",
    "category": "Category Name",
    "date": "YYYY-MM-DD",
    "timestamp": "HH:MM:SS"
  }}
]
"""

def get_gpt_prompt(raw_notes: str, categories: list) -> str:
    """
    Generate the complete GPT prompt with categories and raw notes.

    Args:
        raw_notes: Raw note text from user
        categories: List of valid categories

    Returns:
        Complete prompt string
    """
    categories_str = ", ".join(categories)
    system_prompt = GPT_SYSTEM_PROMPT.format(categories=categories_str)
    return f"{system_prompt}\n\nRaw Notes:\n{raw_notes}"

"""Configuration and constants."""

import logging
import os
import pathlib
import sys
from dataclasses import dataclass
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("jobapp")

# API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-3-pro-preview"

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = (
    "gpt-5.1"  # Used for humanization (different model = different fingerprint)
)


def validate_config() -> None:
    """Validate required configuration at startup.

    Raises:
        SystemExit: If required environment variables are missing.
    """
    missing = []
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not PERSONAL_INFO.get("name"):
        missing.append("USER_NAME")
    if not PERSONAL_INFO.get("email"):
        missing.append("USER_EMAIL")

    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("See .env.example for required configuration.")
        sys.exit(1)


# Personal Information (from environment variables)
PERSONAL_INFO = {
    "name": os.environ.get("USER_NAME", ""),
    "title": os.environ.get("USER_TITLE", ""),
    "location": os.environ.get("USER_LOCATION", ""),
    "email": os.environ.get("USER_EMAIL", ""),
    "phone": os.environ.get("USER_PHONE", ""),
    "linkedin": os.environ.get("USER_LINKEDIN", ""),
}

# Filename slug derived from personal info (e.g., "john_doe")
FILENAME_SLUG = os.environ.get(
    "FILENAME_SLUG",
    PERSONAL_INFO["name"].lower().replace(" ", "_")
    if PERSONAL_INFO["name"]
    else "user",
)

# Paths
APP_DIR = pathlib.Path(__file__).parent
PROMPTS_DIR = APP_DIR / "prompts"
TEMPLATES_DIR = APP_DIR / "templates"
OUTPUT_DIR = APP_DIR.parent / "output"

# Constants (magic numbers)
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MIN_PROMPT_LENGTH = 50
HTTP_TIMEOUT_SECONDS = 30


@dataclass
class JobInfo:
    """Structured job information."""

    title: str
    company: str
    description: str
    url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for backward compatibility."""
        return {
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "url": self.url,
        }

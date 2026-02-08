from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3-flash-preview")
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")
POPPLER_PATH = os.getenv("POPPLER_PATH", "")

"""Vercel Serverless Function entry point for CASHNET FastAPI backend."""

import os
import sys
from pathlib import Path

# Add project root directory to sys.path so that src.backend and models are importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set default directories if not set
os.environ.setdefault("DEFAULT_DATA_DIR", str(PROJECT_ROOT / "data_v2"))
os.environ.setdefault("MODELS_DIR", str(PROJECT_ROOT / "models"))

from src.backend.main import app

# Export app instance for Vercel Python ASGI handler
__all__ = ["app"]

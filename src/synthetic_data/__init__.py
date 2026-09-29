"""CASHNET Synthetic Financial Data Generation & Ground Truth Engine.

Smart India Hackathon - SIH26184 | AI-Powered Cybercrime Cash-Out Prediction & Intervention Platform
"""

from .config import GenerationConfig
from .database_loader import load_into_database
from .export import export_all_datasets
from .validation import run_all_validations

__version__ = "1.0.0"
__all__ = [
    "GenerationConfig",
    "export_all_datasets",
    "run_all_validations",
    "load_into_database",
]

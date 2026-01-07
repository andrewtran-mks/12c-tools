import os
from pathlib import Path


class Config:
    """Base defaults. Override in instance/config.py."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(PROJECT_ROOT / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 32 * 1024 * 1024))

    # Paths moved from config.ini → instance/config.py
    RMA_FOLDER_TEMPLATE = os.getenv("RMA_FOLDER_TEMPLATE", "")
    FAILURE_ANALYSIS_FOLDER = os.getenv("FAILURE_ANALYSIS_FOLDER", "")
    ORIGINAL_TEST_FOLDER = os.getenv("ORIGINAL_TEST_FOLDER", "")

    # DB path
    DB_PATH = os.getenv("DB_PATH")
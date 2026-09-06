"""Pytest fixtures and isolated test environment."""

import tempfile
from pathlib import Path
import pytest
from app.config import settings
from app.database import init_db


@pytest.fixture(scope="session", autouse=True)
def isolated_test_environment():
    """Ensure tests run in a completely isolated temporary directory."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp_dir:
        temp_path = Path(temp_dir)
        settings.DATA_DIR = temp_path
        # Initialize schema at settings.DB_PATH
        init_db(settings.DB_PATH)
        yield

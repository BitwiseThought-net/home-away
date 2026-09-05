"""
Shared fixtures for the test suite.

`service.py` resolves `.env`/`.env.example` relative to the process's
current working directory (`ENV_PATH`/`EXAMPLE_PATH` are module-level
relative paths), so isolating cwd per-test keeps tests from reading or
writing real repo files. It also calls `logging.warning`/`.error`/`.info`
directly against the root logger (configured once at import time via
`logging.basicConfig`), which `caplog` captures without any extra setup.
"""
import os
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import service  # noqa: E402


@pytest.fixture
def isolated_cwd(tmp_path, monkeypatch):
    """Runs a test inside an empty temp directory and chdir's into it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def env_vars(monkeypatch):
    """
    Factory for setting a batch of env vars for the duration of a test,
    via monkeypatch so they're automatically cleaned up afterwards.
    """
    def _set(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)
    return _set

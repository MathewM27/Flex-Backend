"""Process entry point. `uvicorn src.main:app` boots this."""

from __future__ import annotations

from src.api.app import create_app

app = create_app()

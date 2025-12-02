#!/usr/bin/env python3
"""Run the JobApp web server."""

import os

import uvicorn

from app.config import validate_config

if __name__ == "__main__":
    validate_config()

    # Configuration from environment with sensible defaults
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    reload = os.environ.get("DEV_MODE", "").lower() in ("1", "true", "yes")

    uvicorn.run(
        "web.api:app",
        host=host,
        port=port,
        reload=reload,
    )

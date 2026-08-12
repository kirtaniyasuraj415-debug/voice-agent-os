"""Vercel serverless entry point for the Voice Agent OS.

Imports the FastAPI app from the project root. Vercel bundles the whole
repo, so the root is added to sys.path to keep absolute imports working.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.server import app  # noqa: E402

# Vercel Python runtime expects an ASGI callable named `app`.
__all__ = ["app"]

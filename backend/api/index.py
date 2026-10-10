"""
Vercel Python runtime entry point. Vercel serves the `app` ASGI variable
found in files under /api; this just re-exports the real FastAPI app.
"""
from app.main import app  # noqa: F401

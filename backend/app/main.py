"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes import auth as auth_routes
from app.api.routes import doctors as doctor_routes
from app.api.routes import posts as post_routes
from app.api.routes import social as social_routes
from app.api.routes import safety as safety_routes

settings = get_settings()

# Refuse to boot in production with unsafe defaults. No-op outside production.
settings.validate_production_safety()

app = FastAPI(title=settings.PROJECT_NAME)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(doctor_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(post_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(social_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(safety_routes.sos_router, prefix=settings.API_V1_PREFIX)
app.include_router(safety_routes.complaints_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {"service": settings.PROJECT_NAME, "status": "ok", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}

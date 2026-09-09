from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .services import config

app = FastAPI(
    title="SlopeGuard API",
    description="AI-based landslide risk prediction and early warning API for Northeast India (prototype).",
    version="1.0.0-prototype",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "SlopeGuard API",
        "status": "running",
        "demo_mode": config.DEMO_MODE,
        "docs": "/docs",
    }
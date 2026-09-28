from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.intelligence import router as intelligence_router
from api.security import (
    APIProtectionMiddleware,
    CORS_ORIGINS,
)


app = FastAPI(
    title="WeatherGPT Intelligence API",
    description=(
        "Member 3 Intelligence and Decision Engine for WeatherGPT. "
        "Provides current weather intelligence, forecast risk analysis, "
        "historical climate analysis, hazards, alerts, and advisories."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(CORS_ORIGINS),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(APIProtectionMiddleware)


app.include_router(
    intelligence_router,
    prefix="/api/v1",
)


@app.get(
    "/health",
    tags=["Health"],
    summary="Check API health",
    description="Returns the health status and version of the Member 3 API.",
)
def health_check():
    return {
        "status": "healthy",
        "service": "weathergpt-intelligence",
        "version": "1.0.0",
    }
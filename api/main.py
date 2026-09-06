from fastapi import FastAPI

from api.routes.intelligence import router as intelligence_router


app = FastAPI(
    title="WeatherGPT Intelligence API",
    description="Member 3 Intelligence and Decision Engine API",
    version="1.0.0",
)


app.include_router(
    intelligence_router,
    prefix="/api/v1",
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "weathergpt-intelligence",
        "version": "1.0.0",
    }
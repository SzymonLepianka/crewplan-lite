from fastapi import FastAPI

from app.modules.planning.router import router as planning_router


app = FastAPI(
    title="CrewPlan Lite API",
    version="0.1.0",
)

app.include_router(planning_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "crewplan-lite-api",
    }

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_frontend_origins
from app.modules.planning.router import router as planning_router


app = FastAPI(
    title="CrewPlan Lite API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_frontend_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(planning_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "crewplan-lite-api",
    }

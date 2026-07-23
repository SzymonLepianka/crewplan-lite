from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.modules.planning import schemas, service


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[schemas.ProjectSummary])
def list_projects(session: Session = Depends(get_session)) -> list[schemas.ProjectSummary]:
    return service.list_projects(session)


@router.get("/{project_id}", response_model=schemas.ProjectSummary)
def get_project(project_id: int, session: Session = Depends(get_session)) -> schemas.ProjectSummary:
    return service.get_project(session, project_id)


@router.get("/{project_id}/planning-data", response_model=schemas.PlanningDataRead)
def get_planning_data(project_id: int, session: Session = Depends(get_session)) -> schemas.PlanningDataRead:
    return service.get_planning_data(session, project_id)

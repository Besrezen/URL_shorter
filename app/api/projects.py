from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectOut

router = APIRouter(prefix='/projects', tags=['projects'])


@router.post('', response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = Project(name=payload.name, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get('', response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Project).filter(Project.owner_id == user.id).all()

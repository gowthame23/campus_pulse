from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_department_service
from api.security import get_current_user, require_roles
from models.administrator import Administrator

router = APIRouter(prefix="/issues", tags=["issues"])


class IssueCreateRequest(BaseModel):
    department_id: str
    issue_name: str
    description: Optional[str] = ""


class IssueUpdateRequest(BaseModel):
    issue_name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None


@router.get("")
def list_issues(
    department_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    dept_service=Depends(get_department_service),
):
    return dept_service.list_department_issues(department_id=department_id)


@router.post("", status_code=201)
def create_issue(
    payload: IssueCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    dept_service=Depends(get_department_service),
):
    iid = dept_service.create_department_issue(
        department_id=payload.department_id,
        issue_name=payload.issue_name,
        description=payload.description,
    )
    return {"status": "success", "issue_id": iid}


@router.put("/{issue_id}")
def update_issue(
    issue_id: str,
    payload: IssueUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    dept_service=Depends(get_department_service),
):
    try:
        dept_service.update_department_issue(
            issue_id=issue_id,
            issue_name=payload.issue_name,
            description=payload.description,
            active=payload.active,
        )
        return {"status": "success", "message": "Issue updated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

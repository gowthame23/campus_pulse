from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_program_service
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(prefix="/programs", tags=["programs"])


class ProgramCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    duration_years: int = Field(ge=1, le=8, default=4)
    description: Optional[str] = ""


@router.get("")
def list_programs(
    current_user=Depends(get_current_user),
    program_service=Depends(get_program_service),
):
    return program_service.list_programs()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_program(
    payload: ProgramCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    program_service=Depends(get_program_service),
):
    try:
        return program_service.create_program(
            name=payload.name,
            duration_years=payload.duration_years,
            description=payload.description or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{program_id}", status_code=status.HTTP_200_OK)
def delete_program(
    program_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    program_service=Depends(get_program_service),
):
    program_service.delete_program(program_id)
    return {"message": "Program deleted successfully."}

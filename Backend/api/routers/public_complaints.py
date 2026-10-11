from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from api.security import block_super_admin, get_current_user
from api.dependencies import get_public_complaint_service
from services.public_complaint_service import PublicComplaintService
from api.schemas import ComplaintAffectedRequest

router = APIRouter(
    prefix="/public-complaints",
    tags=["public-complaints"],
    dependencies=[Depends(block_super_admin)],
)


@router.get("/locations")
def get_public_locations(
    current_user=Depends(get_current_user),
    service: PublicComplaintService = Depends(get_public_complaint_service),
):
    return service.list_public_locations()


@router.get("/{location_id}/departments")
def get_public_departments(
    location_id: str,
    current_user=Depends(get_current_user),
    service: PublicComplaintService = Depends(get_public_complaint_service),
):
    return service.list_public_departments(location_id)


@router.get("/{location_id}/{department_id}/issues")
def get_public_issues(
    location_id: str,
    department_id: str,
    current_user=Depends(get_current_user),
    service: PublicComplaintService = Depends(get_public_complaint_service),
):
    return service.list_public_issues(location_id, department_id)


@router.get("")
def list_public_complaints(
    location_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    issue_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    service: PublicComplaintService = Depends(get_public_complaint_service),
):
    # Rule 6: 0 matching complaints returns 200 OK with []
    return service.list_public_complaints(
        location_id=location_id,
        department_id=department_id,
        issue_id=issue_id,
        status=status_filter,
        search=search,
    )


@router.get("/{complaint_id}")
def get_public_complaint_details(
    complaint_id: str,
    current_user=Depends(get_current_user),
    service: PublicComplaintService = Depends(get_public_complaint_service),
):
    try:
        return service.get_public_complaint(complaint_id, current_user.user_id)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(v_err))


@router.post("/{complaint_id}/join")
def join_public_complaint(
    complaint_id: str,
    payload: Optional[ComplaintAffectedRequest] = None,
    current_user=Depends(get_current_user),
    service: PublicComplaintService = Depends(get_public_complaint_service),
):
    try:
        room_note = payload.room_note if payload else None
        return service.join_public_complaint(complaint_id, current_user.user_id, room_note=room_note)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        detail = str(v_err)
        if "already joined" in detail.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

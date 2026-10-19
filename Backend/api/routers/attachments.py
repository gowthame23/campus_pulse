import os
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from api.dependencies import get_attachment_service, get_complaint_service
from api.schemas import AttachmentResponse
from api.security import get_current_user
from models.complaint import Complaint

router = APIRouter(tags=["attachments"])
def _ensure_attachment_access(complaint, current_user, complaint_service):
    role = (current_user.role or "").lower()
    if role in ("administrator", "app_manager"):
        return
    if role == "student":
        user_ids = {str(current_user.user_id).lower()}
        if getattr(current_user, "email", None):
            user_ids.add(str(current_user.email).lower())
        if str(complaint.created_by).lower() in user_ids:
            return
        # Allow access to Community or Public complaints
        vis = (getattr(complaint, "visibility_type", "") or "").lower()
        if vis in ("public", "community"):
            return
    elif role in ("coordinator", "employee"):
        if complaint.assigned_to == current_user.user_id:
            return
        coord_assignments = complaint_service.auth_service.list_coordinator_assignments(coordinator_id=current_user.user_id) or []
        for asgn in coord_assignments:
            a_loc = asgn.get("location_id")
            a_dept = asgn.get("department_id")
            loc_match = a_loc in ("ALL", None, complaint.location_id)
            dept_match = a_dept in ("ALL", None, complaint.department_id)
            if loc_match and dept_match:
                return
    elif role == "location_in_charge":
        locs = complaint_service.auth_service.list_locations()
        assigned_locs = {l.location_id for l in locs if l.in_charge_id == current_user.user_id}
        if complaint.location_id in assigned_locs or complaint.created_by == current_user.user_id or complaint.assigned_to == current_user.user_id:
            return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this complaint's attachments.")


@router.get(
    "/complaints/{complaint_id}/attachments", response_model=List[AttachmentResponse]
)
def get_attachments(
    complaint_id: str,
    current_user=Depends(get_current_user),
    attachment_service=Depends(get_attachment_service),
    complaint_service=Depends(get_complaint_service),
):
    if (current_user.role or "").lower() == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    _ensure_attachment_access(complaint, current_user, complaint_service)
    return attachment_service.list_attachments(complaint_id)


@router.post(
    "/complaints/{complaint_id}/attachments", response_model=List[AttachmentResponse]
)
def upload_attachments(
    complaint_id: str,
    files: List[UploadFile] = File(...),
    category: str = Form("Additional"),
    source: str = Form("gallery"),
    kind: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
    attachment_service=Depends(get_attachment_service),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    u_role = (current_user.role or "").lower()

    # Status & Permission Rules
    if complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint is closed. No uploads allowed.",
        )

    if u_role == "student":
        if complaint.created_by != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied. You did not submit this complaint.",
            )

        if category != "Additional":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Students can only upload under the 'Additional' category.",
            )

    elif u_role in ("coordinator", "employee"):
        if complaint.assigned_to != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff can only upload to complaints assigned to them.",
            )

        if category not in ("Before Repair", "After Repair"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Staff must upload under 'Before Repair' or 'After Repair' categories.",
            )

        if complaint.status == Complaint.RESOLVED:
            if category != "After Repair":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Staff can only upload 'After Repair' images for resolved complaints.",
                )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your role is not authorized to upload images.",
        )

    if len(files) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum of 5 images is allowed per upload request.",
        )

    existing = attachment_service.list_attachments(complaint_id)
    if len(existing) + len(files) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum complaint limit of 20 images reached.",
        )

    uploaded_metadata = []
    job_start = getattr(complaint, "started_at", None) or getattr(complaint, "assigned_at", None)

    for file in files:
        file_bytes = file.file.read()
        try:
            meta = attachment_service.create_attachment(
                complaint_id=complaint_id,
                uploaded_by=current_user.user_id,
                uploader_role=u_role,
                category=category,
                filename=file.filename,
                file_bytes=file_bytes,
                source=source,
                kind=kind,
                job_started_at=job_start,
            )
            uploaded_metadata.append(meta)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)
            )

    count = len(files)
    if u_role == "student":
        timeline_msg = f"Student uploaded {count} image(s) to category '{category}'."
    elif u_role == "coordinator":
        timeline_msg = f"Coordinator uploaded {category} image(s)."
    else:
        timeline_msg = (
            f"{current_user.name} uploaded {count} image(s) to category '{category}'."
        )

    complaint.add_history(timeline_msg)
    complaint_service.save_complaint(complaint)

    return uploaded_metadata


@router.delete(
    "/complaints/{complaint_id}/attachments/{attachment_id}",
    status_code=status.HTTP_200_OK,
)
def delete_attachment(
    complaint_id: str,
    attachment_id: str,
    current_user=Depends(get_current_user),
    attachment_service=Depends(get_attachment_service),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    attachment = attachment_service.get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found."
        )
    if attachment["complaint_id"] != complaint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attachment does not belong to this complaint.",
        )

    try:
        attachment_service.delete_attachment(
            attachment_id=attachment_id,
            user=current_user,
            complaint_status=complaint.status,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_err))

    complaint.add_history(f"Student deleted image {attachment['original_filename']}.")
    complaint_service.save_complaint(complaint)

    return {"message": "Attachment deleted successfully."}


@router.get("/complaints/{complaint_id}/attachments/{attachment_id}/download")
def download_attachment(
    complaint_id: str,
    attachment_id: str,
    current_user=Depends(get_current_user),
    attachment_service=Depends(get_attachment_service),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    attachment = attachment_service.get_attachment(attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found."
        )
    if attachment["complaint_id"] != complaint_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attachment does not belong to this complaint.",
        )

    _ensure_attachment_access(complaint, current_user, complaint_service)

    file_path = attachment.get("file_path") or ""
    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attachment file not found."
        )

    from pathlib import Path
    base_storage_dir = getattr(attachment_service, "storage_dir", Path("storage/attachments").resolve())
    clean_filename = file_path.replace("/static/attachments/", "").replace("storage\\attachments\\", "").replace("storage/attachments/", "")
    target_path = (base_storage_dir / clean_filename).resolve()
    try:
        target_path.relative_to(base_storage_dir)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Invalid file path traversal attempted.",
        )

    if not target_path.exists():
        alt_path = (Path("storage/attachments") / clean_filename).resolve()
        if alt_path.exists():
            target_path = alt_path
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk."
            )

    return FileResponse(
        path=str(target_path),
        filename=attachment["original_filename"],
        media_type="application/octet-stream",
    )

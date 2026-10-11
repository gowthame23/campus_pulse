from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api.dependencies import get_lost_found_service
from api.security import block_super_admin, get_current_user

router = APIRouter(
    prefix="/lost-found", tags=["lost-found"], dependencies=[Depends(block_super_admin)]
)


# ==========================================
# SCHEMAS
# ==========================================
class ItemUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    serial_number: Optional[str] = None
    estimated_value: Optional[float] = None
    exact_location: Optional[str] = None
    current_storage_location: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


class ImageUploadRequest(BaseModel):
    image_url: str
    image_type: Optional[str] = "Overview"


class ClaimReviewRequest(BaseModel):
    decision_notes: Optional[str] = ""


# ==========================================
# 1. ITEM MANAGEMENT API
# ==========================================
class ReportItemPayload(BaseModel):
    type: Optional[str] = None
    report_type: Optional[str] = None
    title: Optional[str] = None
    description: str
    location_id: Optional[str] = None
    building_id: Optional[str] = None
    exact_location: Optional[str] = ""
    current_storage_location: Optional[str] = ""
    lost_date: Optional[str] = None
    date_lost_found: Optional[str] = None
    photos: Optional[list[str]] = None
    photo_url: Optional[str] = None
    image_url: Optional[str] = None
    category: Optional[str] = "Other"
    brand: Optional[str] = ""
    color: Optional[str] = ""
    serial_number: Optional[str] = ""


@router.post("/report", status_code=status.HTTP_201_CREATED)
@router.post("/items", status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ReportItemPayload,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        rpt_type = payload.type or payload.report_type or "Lost"
        loc_id = payload.location_id or payload.building_id
        dt_val = payload.lost_date or payload.date_lost_found
        photos_list = list(payload.photos) if payload.photos else []
        if payload.photo_url and payload.photo_url.strip():
            photos_list.append(payload.photo_url.strip())
        if payload.image_url and payload.image_url.strip():
            photos_list.append(payload.image_url.strip())

        title_val = payload.title
        if not title_val or not title_val.strip():
            clean_d = (payload.description or "").strip()
            title_val = (clean_d[:47] + "...") if len(clean_d) > 50 else clean_d or f"{rpt_type} Item"

        return lf_service.create_item(
            report_type=rpt_type,
            reported_by=current_user.user_id,
            title=title_val,
            description=payload.description,
            category=payload.category or "Other",
            brand=payload.brand or "",
            color=payload.color or "",
            serial_number=payload.serial_number or "",
            date_lost_found=dt_val,
            location_id=loc_id,
            building_id=loc_id,
            exact_location=payload.exact_location or "",
            current_storage_location=payload.current_storage_location or "",
            photos=photos_list,
            user_role=current_user.role,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/items")
def list_items(
    report_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    building_id: Optional[str] = Query(None),
    visibility: Optional[str] = Query(None),
    my_reports: Optional[bool] = Query(False),
    q: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    reported_by = current_user.user_id if my_reports else None
    return lf_service.list_items(
        report_type=report_type,
        category=category,
        status=status_filter,
        building_id=building_id,
        visibility=visibility,
        reported_by=reported_by,
        q=q,
        user=current_user,
    )


def _visible_item_or_404(lf_service, item_id, current_user):
    item = lf_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    role_lower = (current_user.role or "").lower()
    if role_lower == "student":
        if item.get("visibility") != "Public" and item.get("reported_by") != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    elif not lf_service.staff_scope_allows(item, current_user.role, current_user.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")
    return item


@router.get("/items/{item_id}")
def get_item(
    item_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    return _visible_item_or_404(lf_service, item_id, current_user)


@router.get("/items/{item_id}/photo-file/{filename}")
def get_item_photo_file(
    item_id: str,
    filename: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    """Authenticated, authorization-checked photo retrieval. Replaces the
    previous public static mount: a photo belonging to a Private item is now
    only ever served to the owner or in-scope staff, exactly like the item's
    own metadata (_visible_item_or_404) — the filename's randomness is never
    treated as the authorization boundary."""
    item = _visible_item_or_404(lf_service, item_id, current_user)

    photos = (item.get("unique_identifiers") or {}).get("photos") or []
    valid_names = {
        p.rsplit("/", 1)[-1]
        for p in photos
        if isinstance(p, str) and p.startswith("/static/lost_found_photos/")
    }
    if filename not in valid_names:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found.")

    base_dir = getattr(lf_service, "storage_dir", Path("storage/lost_found_photos").resolve())
    target_path = (base_dir / filename).resolve()
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid file path.")

    if not target_path.exists():
        alt_path = (Path("storage/lost_found_photos") / filename).resolve()
        if alt_path.exists():
            target_path = alt_path
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found on disk.")

    return FileResponse(path=str(target_path))


@router.put("/items/{item_id}")
def update_item(
    item_id: str,
    payload: ItemUpdateRequest,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        return lf_service.update_item(
            item_id,
            payload.dict(exclude_unset=True),
            performer_id=current_user.user_id,
            user_role=current_user.role,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.delete("/items/{item_id}")
def delete_item(
    item_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        return lf_service.delete_item(
            item_id,
            performer_id=current_user.user_id,
            user_role=current_user.role,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


class ModerateItemRequest(BaseModel):
    reason: str
    action: Optional[str] = "hide"


@router.post("/items/{item_id}/moderate")
@router.put("/items/{item_id}/moderate")
def moderate_item(
    item_id: str,
    payload: ModerateItemRequest,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        return lf_service.moderate_item(
            item_id,
            performer_id=current_user.user_id,
            user_role=current_user.role,
            reason=payload.reason,
            action=payload.action or "hide",
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# ==========================================
# 2. IMAGE MANAGEMENT API
# ==========================================
@router.post("/items/{item_id}/images", status_code=status.HTTP_201_CREATED)
def upload_item_image(
    item_id: str,
    payload: ImageUploadRequest,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        return lf_service.upload_image(
            item_id=item_id,
            uploaded_by=current_user.user_id,
            image_url=payload.image_url,
            image_type=payload.image_type or "Overview",
            user_role=current_user.role,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/items/{item_id}/images")
def list_item_images(
    item_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    _visible_item_or_404(lf_service, item_id, current_user)
    return lf_service.list_images(item_id)


@router.delete("/images/{image_id}")
def delete_item_image(
    image_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        success = lf_service.delete_image(
            image_id,
            performer_id=current_user.user_id,
            user_role=current_user.role,
        )
        if not success:
            raise HTTPException(status_code=404, detail="Image record not found.")
        return {"message": "Image deleted."}
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))


# ==========================================
# 3. CLAIM MANAGEMENT & VERIFICATION API
# ==========================================
class FlexibleClaimRequest(BaseModel):
    claim_reason: Optional[str] = "Item belongs to me"
    proof_description: Optional[str] = ""
    reason: Optional[str] = None
    description: Optional[str] = None


@router.post("/{item_id}/claim", status_code=status.HTTP_201_CREATED)
@router.post("/items/{item_id}/claim", status_code=status.HTTP_201_CREATED)
def submit_claim(
    item_id: str,
    payload: Optional[FlexibleClaimRequest] = None,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        reason = (payload.reason if payload and payload.reason else (payload.claim_reason if payload else "Item belongs to me"))
        proof = (payload.description if payload and payload.description else (payload.proof_description if payload else ""))
        return lf_service.submit_claim(
            item_id=item_id,
            claimed_by=current_user.user_id,
            claim_reason=reason,
            proof_description=proof,
        )
    except ValueError as err:
        detail = str(err)
        if "already" in detail.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/claims")
def list_claims(
    item_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    my_claims: bool = Query(False),
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    uid = (
        current_user.user_id if (my_claims or current_user.role == "student") else None
    )
    return lf_service.list_claims(item_id=item_id, claimed_by=uid, status=status_filter)


@router.get("/claims/{claim_id}")
def get_claim(
    claim_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    claim = lf_service.get_claim(claim_id)
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found."
        )

    # Privacy Check: Students can only view their own claim or claims on items they reported
    role_lower = (current_user.role or "").lower()
    if role_lower == "student":
        item = lf_service.get_item(claim["item_id"])
        if claim.get("claimed_by") != current_user.user_id and (not item or item.get("reported_by") != current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this claim.",
            )
    return claim


@router.post("/claims/{claim_id}/approve")
@router.put("/claims/{claim_id}/approve")
def approve_claim(
    claim_id: str,
    payload: Optional[ClaimReviewRequest] = None,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    notes = (
        payload.decision_notes if payload else "Approved after verification."
    )
    try:
        return lf_service.approve_claim(
            claim_id,
            reviewer_id=current_user.user_id,
            decision_notes=notes,
            user_role=current_user.role,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/claims/{claim_id}/reject")
@router.put("/claims/{claim_id}/reject")
def reject_claim(
    claim_id: str,
    payload: Optional[ClaimReviewRequest] = None,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    notes = payload.decision_notes if payload and payload.decision_notes else "Ownership proof insufficient"
    try:
        return lf_service.reject_claim(
            claim_id,
            reviewer_id=current_user.user_id,
            decision_notes=notes,
            user_role=current_user.role,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# ==========================================
# 4. MATCHING & RETURN WORKFLOW API
# ==========================================
@router.get("/matches/{item_id}")
@router.get("/{item_id}/matches")
@router.get("/items/{item_id}/matches")
@router.post("/items/{item_id}/run-match")
def run_item_matching(
    item_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    # Rule 10: 0 matches returns [] (NEVER 404 or 500)
    return lf_service.run_matching_engine(item_id)


@router.post("/{item_id}/return")
@router.put("/items/{item_id}/return")
def mark_item_returned(
    item_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        return lf_service.mark_returned(
            item_id, performer_id=current_user.user_id, user_role=current_user.role
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{item_id}/close")
def close_item(
    item_id: str,
    current_user=Depends(get_current_user),
    lf_service=Depends(get_lost_found_service),
):
    try:
        return lf_service.mark_returned(
            item_id, performer_id=current_user.user_id, user_role=current_user.role
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

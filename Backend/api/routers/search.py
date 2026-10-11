from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from api.dependencies import get_global_search_service
from api.security import block_super_admin, get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(
    prefix="/search", tags=["search"], dependencies=[Depends(block_super_admin)]
)


# ==========================================
# SCHEMAS
# ==========================================
class SaveSearchRequest(BaseModel):
    search_name: str
    query: str
    filters: Optional[Dict[str, Any]] = None


# ==========================================
# 1. GLOBAL SEARCH & SUGGESTIONS API
# ==========================================
@router.get("")
def global_search(
    q: str = Query(..., min_length=1),
    entity_type: Optional[str] = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
    search_service=Depends(get_global_search_service),
):
    return search_service.search(
        query=q,
        entity_type=entity_type,
        user_role=current_user.role,
        user_id=current_user.user_id,
        user_department_id=current_user.department_id,
        user_location_id=current_user.location_id,
        limit=limit,
    )


@router.get("/suggestions")
def get_suggestions(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20),
    current_user=Depends(get_current_user),
    search_service=Depends(get_global_search_service),
):
    return search_service.get_suggestions(
        query=q,
        user_role=current_user.role,
        user_id=current_user.user_id,
        user_department_id=current_user.department_id,
        user_location_id=current_user.location_id,
        limit=limit,
    )


@router.post("/reindex", status_code=status.HTTP_200_OK)
def reindex_search_engine(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    search_service=Depends(get_global_search_service),
):
    return search_service.reindex_all(performer_id=current_user.user_id)


# ==========================================
# 2. SEARCH HISTORY API
# ==========================================
@router.get("/history")
def get_search_history(
    current_user=Depends(get_current_user),
    search_service=Depends(get_global_search_service),
):
    return search_service.get_history(user_id=current_user.user_id)


@router.delete("/history")
def clear_search_history(
    current_user=Depends(get_current_user),
    search_service=Depends(get_global_search_service),
):
    return search_service.clear_history(user_id=current_user.user_id)


# ==========================================
# 3. SAVED SEARCHES API
# ==========================================
@router.get("/saved")
def get_saved_searches(
    current_user=Depends(get_current_user),
    search_service=Depends(get_global_search_service),
):
    return search_service.get_saved_searches(user_id=current_user.user_id)


@router.post("/saved", status_code=status.HTTP_201_CREATED)
def save_search(
    payload: SaveSearchRequest,
    current_user=Depends(get_current_user),
    search_service=Depends(get_global_search_service),
):
    return search_service.save_search(
        user_id=current_user.user_id,
        search_name=payload.search_name,
        query=payload.query,
        filters=payload.filters,
    )


@router.delete("/saved/{saved_search_id}")
def delete_saved_search(
    saved_search_id: str,
    current_user=Depends(get_current_user),
    search_service=Depends(get_global_search_service),
):
    return search_service.delete_saved_search(
        saved_search_id=saved_search_id, user_id=current_user.user_id
    )

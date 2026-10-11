from typing import Optional
from fastapi import APIRouter, Depends, Query
from api.security import get_current_user
from services.master_service import MasterReferenceService

router = APIRouter(prefix="/master-references", tags=["master-references"])

def get_master_service():
    return MasterReferenceService()

@router.get("")
def list_master_references(
    category: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    master_service=Depends(get_master_service),
):
    return master_service.list_references(category=category)

@router.get("/{category}")
def get_master_references_by_category(
    category: str,
    current_user=Depends(get_current_user),
    master_service=Depends(get_master_service),
):
    return master_service.list_references(category=category)

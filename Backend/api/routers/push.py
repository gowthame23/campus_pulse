from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.security import get_current_user
from services.push_service import (
    get_vapid_public_key,
    remove_subscription,
    save_subscription,
)
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/push", tags=["Push Notifications"])


class PushKeys(BaseModel):
    p256dh: Optional[str] = None
    auth: Optional[str] = None


class PushSubscribeRequest(BaseModel):
    endpoint: str
    keys: Optional[PushKeys] = None
    p256dh: Optional[str] = None
    auth: Optional[str] = None


class PushUnsubscribeRequest(BaseModel):
    endpoint: str


@router.get("/vapid-public-key")
def get_public_key():
    """Retrieve the application VAPID public key for web push subscription."""
    key = get_vapid_public_key()
    return {"public_key": key}


@router.post("/subscribe")
def subscribe_push(
    payload: PushSubscribeRequest,
    current_user=Depends(get_current_user),
):
    """Register or update a browser Web Push subscription for the authenticated user."""
    endpoint = payload.endpoint
    p256dh = payload.p256dh or (payload.keys.p256dh if payload.keys else None)
    auth = payload.auth or (payload.keys.auth if payload.keys else None)

    if not endpoint or not p256dh or not auth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endpoint, p256dh, and auth keys are required for push subscription.",
        )

    try:
        save_subscription(current_user.user_id, endpoint, p256dh, auth)
        return {"status": "subscribed", "user_id": current_user.user_id}
    except Exception as err:
        logger.error(f"Push subscription failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register push subscription.",
        )


@router.post("/unsubscribe")
def unsubscribe_push(
    payload: PushUnsubscribeRequest,
    current_user=Depends(get_current_user),
):
    """Remove a browser Web Push subscription."""
    if not payload.endpoint:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="endpoint is required to unsubscribe.",
        )

    try:
        remove_subscription(payload.endpoint)
        return {"status": "unsubscribed"}
    except Exception as err:
        logger.error(f"Push unsubscribe failed: {err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unsubscribe from push.",
        )

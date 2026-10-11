from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from api.dependencies import get_notification_service
from api.schemas import (
    NotificationCreateRequest,
    NotificationPreferencesRequest,
    NotificationPreferencesResponse,
    NotificationResponse,
)
from api.security import get_current_user, get_ws_user, require_roles
from utils.websocket_manager import manager

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post(
    "", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED
)
def create_notification(
    payload: NotificationCreateRequest,
    current_user=Depends(require_roles("administrator", "app_manager")),
    notification_service=Depends(get_notification_service),
):
    notif = notification_service.publish(
        receiver_id=payload.receiver_id,
        title=payload.title,
        message=payload.message,
        module=payload.module or "Complaint",
        notification_type=payload.notification_type or "info",
        reference_type=payload.reference_type or "Complaint",
        reference_id=payload.reference_id,
        priority=payload.priority or "Medium",
        sender_id=current_user.user_id,
        expires_at=payload.expires_at,
    )
    if not notif:
        raise HTTPException(
            status_code=400, detail="Notification delivery disabled for this recipient."
        )
    return notif


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    module: Optional[str] = None,
    priority: Optional[str] = None,
    read_status: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    return notification_service.list_for_user(
        user_id=current_user.user_id,
        user_role=current_user.role,
        module=module,
        priority=priority,
        read_status=read_status,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/paginated")
def list_notifications_paginated(
    module: Optional[str] = None,
    priority: Optional[str] = None,
    read_status: Optional[bool] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    from utils.pagination import paginate

    notifs = notification_service.list_for_user(
        user_id=current_user.user_id,
        user_role=current_user.role,
        module=module,
        priority=priority,
        read_status=read_status,
        date_from=date_from,
        date_to=date_to,
    )
    return paginate(notifs, page=page, limit=limit)


@router.get("/unread-count")
@router.get("/count")
def get_unread_count(
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    count = notification_service.count_unread(current_user.user_id, current_user.role)
    return {"unread_count": count}


@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    return notification_service.get_preferences(current_user.user_id)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    payload: NotificationPreferencesRequest,
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    return notification_service.update_preferences(
        user_id=current_user.user_id,
        in_app_enabled=(
            payload.in_app_enabled if payload.in_app_enabled is not None else True
        ),
        email_enabled=(
            payload.email_enabled if payload.email_enabled is not None else False
        ),
        push_enabled=(
            payload.push_enabled if payload.push_enabled is not None else False
        ),
    )


@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification_details(
    notification_id: str,
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    notif = notification_service.get_notification(
        notification_id,
        user_id=current_user.user_id,
        user_role=current_user.role,
        mark_as_read=True,
    )
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return notif


@router.post("/mark-all-read")
@router.put("/read-all")
def mark_all_notifications_read(
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    count = notification_service.mark_all_read(current_user.role, current_user.user_id)
    return {"message": f"Marked {count} notifications as read.", "count": count}


@router.patch("/{notification_id}/read")
@router.post("/{notification_id}/read")
@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    success = notification_service.mark_read(
        notification_id, user_id=current_user.user_id, user_role=current_user.role
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"message": "Notification marked as read."}


@router.delete("/{notification_id}")
def delete_single_notification(
    notification_id: str,
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    success = notification_service.delete_notification(
        notification_id, user_id=current_user.user_id, user_role=current_user.role
    )
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"message": "Notification soft deleted."}


@router.delete("")
def clear_notifications(
    current_user=Depends(get_current_user),
    notification_service=Depends(get_notification_service),
):
    count = notification_service.clear_notifications(
        user_id=current_user.user_id, user_role=current_user.role
    )
    return {"message": "Notifications cleared.", "count": count}


@router.websocket("/ws/{target_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    target_id: str,
    notification_service=Depends(get_notification_service),
):
    """WebSocket endpoint for real-time notification updates per user or role.
    This endpoint requires a query parameter token for authentication: /ws/{target_id}?token=ACCESS_TOKEN
    """
    user = get_ws_user(websocket.query_params.get("token"))
    if not user:
        await websocket.close(code=1008)
        return

    # Ensure token user matches target_id or has role-based target access
    if user.user_id.lower() != target_id.lower() and user.role.lower() != target_id.lower():
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, target_id)

    # Deliver pending notifications that arrived while user was offline
    try:
        pending = notification_service.deliver_pending_websocket(target_id)
        for p in pending:
            await websocket.send_json(
                {"event": "offline_notification_delivered", "data": p}
            )
    except Exception as err:
        print(f"[WS Offline Deliver Error] {err}")

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, target_id)

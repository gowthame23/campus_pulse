from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from api.dependencies import (
    get_auth_service,
    get_chat_service,
    get_notification_service,
)
from api.security import get_current_user, get_ws_user
from utils.websocket_manager import manager

router = APIRouter(prefix="/chat", tags=["chat"])

SUPPORTED_CHAT_ROLES = {
    "administrator",
    "app_manager",
    "location_in_charge",
    "coordinator",
}


@router.get("/users")
@router.get("/contacts")
def list_chat_users(
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    """Returns directory of active staff members eligible for 1:1 personal chat.
    Students are strictly rejected."""
    u_role = (current_user.role or "").lower()
    if u_role not in SUPPORTED_CHAT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students are not permitted to access personal chat.",
        )

    all_users = auth_service.list_users()
    all_locations = auth_service.list_locations()
    all_departments = auth_service.list_departments()

    loc_map = {l.location_id: l.name for l in all_locations}
    dept_map = {d.department_id: d.name for d in all_departments}

    contacts = []
    for u in all_users:
        r = (u.role or "").lower()
        if r in SUPPORTED_CHAT_ROLES and u.user_id != current_user.user_id and getattr(u, "active", True):
            loc_id = getattr(u, "location_id", None)
            dept_id = getattr(u, "department_id", None)
            contacts.append(
                {
                    "user_id": u.user_id,
                    "name": u.name,
                    "email": u.email,
                    "role": u.role,
                    "location_id": loc_id,
                    "location_name": loc_map.get(loc_id, loc_id or ""),
                    "department_id": dept_id,
                    "department_name": dept_map.get(dept_id, dept_id or ""),
                    "is_online": manager.is_online(u.user_id),
                }
            )

    return contacts


@router.post("/start")
@router.post("/personal/start")
def start_chat(
    payload: dict,
    current_user=Depends(get_current_user),
    chat_service=Depends(get_chat_service),
    auth_service=Depends(get_auth_service),
):
    """Starts or retrieves a conversation.
    Supports either Lost & Found items (with item_id) or Personal 1:1 chat (with recipient_id / user_id)."""
    item_id = payload.get("item_id")
    recipient_id = (
        payload.get("recipient_id")
        or payload.get("user_id")
        or payload.get("other_user_id")
    )

    if item_id:
        # Lost & Found case chat
        linked = chat_service.get_conversation_for_item(item_id)
        if linked:
            if current_user.user_id not in chat_service.get_participants(
                linked["conversation_id"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not a participant in this conversation",
                )
            return {
                "conversation_id": linked["conversation_id"],
                "item_id": linked.get("item_id"),
                "read_only": bool(linked.get("read_only")),
            }
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conversation for this item not available. Contact must be accepted first.",
        )

    if recipient_id:
        # Personal 1:1 chat
        u_role = (current_user.role or "").lower()
        if u_role not in SUPPORTED_CHAT_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not permitted to use personal chat.",
            )

        if recipient_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot start a conversation with yourself.",
            )

        recipient = auth_service.get_user(recipient_id)
        if not recipient or not getattr(recipient, "active", True):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient user not found or inactive.",
            )

        rec_role = (recipient.role or "").lower()
        if rec_role not in SUPPORTED_CHAT_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Target user is not eligible for personal chat.",
            )

        conv_id = chat_service.start_personal_conversation(
            current_user.user_id, recipient_id
        )
        return {
            "conversation_id": conv_id,
            "other_user_id": recipient_id,
            "other_user": {
                "user_id": recipient.user_id,
                "name": recipient.name,
                "role": recipient.role,
                "email": recipient.email,
            },
            "read_only": False,
            "item_id": None,
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either item_id (for Lost & Found) or recipient_id (for personal chat) is required.",
    )


@router.post("/message")
def post_message(
    payload: dict,
    current_user=Depends(get_current_user),
    chat_service=Depends(get_chat_service),
    auth_service=Depends(get_auth_service),
    notification_service=Depends(get_notification_service),
):
    conv = payload.get("conversation_id")
    content = payload.get("content")
    if not conv or not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="conversation_id and content required",
        )
    if not isinstance(content, str) or len(content) > 2000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="content must be text of at most 2000 characters",
        )

    # ensure sender is a participant
    if not chat_service.is_participant(conv, current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    # Check whether personal conversation or item conversation
    link = chat_service.get_link_for_conversation(conv)
    is_personal = not (link and link.get("item_id"))

    if is_personal:
        u_role = (current_user.role or "").lower()
        if u_role not in SUPPORTED_CHAT_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not permitted to use personal chat.",
            )

        # Verify other participant
        parts = conv.split(":")
        other_id = (
            parts[2]
            if len(parts) == 3 and parts[1] == current_user.user_id
            else (parts[1] if len(parts) == 3 else None)
        )
        if other_id:
            other_user = auth_service.get_user(other_id)
            if (
                not other_user
                or not getattr(other_user, "active", True)
                or (other_user.role or "").lower() not in SUPPORTED_CHAT_ROLES
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Recipient is not an active authorized staff member.",
                )

    # Do not allow sending if conversation is read-only (e.g., closed Lost & Found case)
    if chat_service.is_read_only(conv):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Conversation is read-only"
        )

    msg = chat_service.save_message(conv, current_user.user_id, content)

    # Notify the other party via notification service & WebSocket
    parts = conv.split(":")
    if len(parts) == 3:
        a, b = parts[1], parts[2]
        target = b if current_user.user_id == a else a
        sender_name = current_user.name or "Staff Member"
        notification_service.publish(
            receiver_id=target,
            title=f"New Message from {sender_name}",
            message=content[:120],
            module="Chat",
            reference_type="Chat",
            reference_id=conv,
            sender_id=current_user.user_id,
        )
        # push websocket directly
        manager.push_sync(target, {"event": "chat_message", "data": msg})

    return msg


@router.get("/conversations")
def list_conversations(
    current_user=Depends(get_current_user),
    chat_service=Depends(get_chat_service),
    auth_service=Depends(get_auth_service),
):
    """Returns conversation list for current user.
    Students only receive conversations linked to Lost & Found items.
    Staff members receive both personal and item conversations."""
    u_role = (current_user.role or "").lower()
    all_convs = chat_service.list_conversations(current_user.user_id)
    filtered = []

    for c in all_convs:
        item_id = c.get("item_id")
        parts = c["conversation_id"].split(":")
        other_id = None
        if len(parts) == 3:
            other_id = parts[2] if current_user.user_id == parts[1] else parts[1]
        elif c.get("participant_a") and c.get("participant_b"):
            other_id = (
                c["participant_b"]
                if current_user.user_id == c["participant_a"]
                else c["participant_a"]
            )

        if item_id:
            # Lost & Found conversation
            other_user = auth_service.get_user(other_id) if other_id else None
            filtered.append(
                {
                    "conversation_id": c["conversation_id"],
                    "other_user_id": other_id,
                    "other_user_name": other_user.name if other_user else (other_id or "Item Contact"),
                    "other_user_role": other_user.role if other_user else None,
                    "last_message": c["last_message"],
                    "last_sender": c["last_sender"],
                    "last_at": c["last_at"],
                    "item_id": item_id,
                    "read_only": bool(c.get("read_only")),
                    "unread_count": c.get("unread_count", 0),
                    "type": "lost_found",
                }
            )
        else:
            # Personal conversation — reject students
            if u_role not in SUPPORTED_CHAT_ROLES:
                continue

            other_user = auth_service.get_user(other_id) if other_id else None
            filtered.append(
                {
                    "conversation_id": c["conversation_id"],
                    "other_user_id": other_id,
                    "other_user_name": other_user.name if other_user else (other_id or "Staff User"),
                    "other_user_role": other_user.role if other_user else None,
                    "other_user_email": other_user.email if other_user else None,
                    "last_message": c["last_message"],
                    "last_sender": c["last_sender"],
                    "last_at": c["last_at"],
                    "item_id": None,
                    "read_only": False,
                    "unread_count": c.get("unread_count", 0),
                    "type": "personal",
                }
            )

    return filtered


@router.get("/unread-count")
def get_unread_count(
    current_user=Depends(get_current_user),
    chat_service=Depends(get_chat_service),
):
    """Returns total unread message count for supported staff members."""
    u_role = (current_user.role or "").lower()
    if u_role not in SUPPORTED_CHAT_ROLES:
        return {"unread_count": 0}
    cnt = chat_service.get_total_unread_count(current_user.user_id)
    return {"unread_count": cnt}


@router.get("/{conversation_id}")
def list_conv(
    conversation_id: str,
    current_user=Depends(get_current_user),
    chat_service=Depends(get_chat_service),
):
    if not chat_service.is_participant(conversation_id, current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation",
        )

    link = chat_service.get_link_for_conversation(conversation_id)
    is_personal = not (link and link.get("item_id"))
    if is_personal:
        u_role = (current_user.role or "").lower()
        if u_role not in SUPPORTED_CHAT_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not permitted to access personal chat.",
            )

    # Mark incoming unread messages as read
    chat_service.mark_as_read(conversation_id, current_user.user_id)
    msgs = chat_service.list_messages(conversation_id)
    return msgs


@router.websocket("/ws/chat/{conversation_id}/{user_id}")
async def chat_ws(websocket: WebSocket, conversation_id: str, user_id: str):
    # Support single-use ticket (?ticket=WST-...) or fallback token (?token=...)
    ticket = websocket.query_params.get("ticket")
    token = websocket.query_params.get("token")
    user = get_ws_user(token=token, ticket=ticket)
    # ensure the user matches the requested user_id and is participant
    if not user or user.user_id != user_id:
        await websocket.close(code=4001 if ticket else 1008)
        return

    # ensure user is participant of the conversation
    chat_service = get_chat_service()
    if not chat_service.is_participant(conversation_id, user_id):
        await websocket.close(code=1008)
        return

    # If it is personal chat, ensure user role is supported (students not allowed)
    link = chat_service.get_link_for_conversation(conversation_id)
    if not (link and link.get("item_id")):
        u_role = (user.role or "").lower()
        if u_role not in SUPPORTED_CHAT_ROLES:
            await websocket.close(code=1008)
            return

    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Campus Pulse - API Documentation

Base URL: `http://localhost:8000`

---

## 🔑 Authentication Endpoints (`/auth`)

### `POST /auth/login`
- **Description:** Authenticate user credentials and return Bearer token.
- **Request Body:**
  ```json
  {
    "email": "user@campus.com",
    "password": "Password@123"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "access_token": "<token_string>",
    "token_type": "bearer",
    "user": {
      "user_id": "USR-123456",
      "name": "John Doe",
      "email": "user@campus.com",
      "role": "student",
      "first_login": false,
      "active": true
    }
  }
  ```

### `POST /auth/change-password`
- **Description:** Password change for authenticated users.
- **Headers:** `Authorization: Bearer <token>`
- **Request Body:** `{"old_password": "OldPassword@123", "new_password": "NewPassword@123"}`

### `POST /auth/password-reset/request`
- **Description:** Request an OTP for password reset.
- **Request Body:** `{"email": "user@campus.edu"}`
- **Response (200 OK):** `{"reset_id": "<reset_id>", "message": "OTP sent to registered email."}`

### `POST /auth/password-reset/verify`
- **Description:** Verify OTP code received via email.
- **Request Body:** `{"reset_id": "<reset_id>", "otp": "123456"}`
- **Response (200 OK):** `{"reset_token": "<reset_token>", "message": "OTP verified successfully."}`

### `POST /auth/password-reset/complete`
- **Description:** Complete password reset using verified `reset_token`.
- **Request Body:** `{"reset_token": "<reset_token>", "new_password": "NewPassword@123"}`
- **Response (200 OK):** `{"message": "Password reset successful.", "user_id": "<user_id>"}`

### `POST /auth/reset-password` (Deprecated)
- **Response (410 GONE):** Use `/auth/password-reset/request`, `/verify`, and `/complete`.

---

## 👥 User Management (`/users`)

### `GET /users`
- **Roles Required:** `administrator`, `app_manager`
- **Query Params:** `role` (optional)
- **Response:** List of user profiles.

### `POST /users`
- **Roles Required:** `administrator`, `app_manager`
- **Description:** Create new user account enforcing creation role hierarchy.

### `PATCH /users/{user_id}`
- **Description:** Update user status (`active`), name, email, department, or location mapping.

### `DELETE /users/{user_id}`
- **Description:** Delete user account if no active complaint dependencies exist.

### `POST /users/transfer-coordinator`
- **Description:** Transfer active complaints from an old coordinator to a new coordinator before account deactivation.

---

## 📋 Complaint Endpoints (`/complaints`)

### `GET /complaints`
- **Query Params:** `status_filter`, `department_id`, `location_id`, `include_archived`
- **Description:** Returns complaints visible to current role, enriched with dynamic `due_date` and `sla_status` (`🟢 On Time`, `🟡 Due Today`, `🔴 Overdue`).

### `POST /complaints`
- **Roles Required:** `student`, `location_in_charge`
- **Request Body:**
  ```json
  {
    "location_id": "LOC_1",
    "department_id": "DEPT_1",
    "complaint_type": "Fan",
    "description": "Fan speed regulator broken.",
    "attachment_url": "https://example.com/photo.jpg"
  }
  ```
- **Response (201 Created):** Newly created complaint object.

### `POST /complaints/{complaint_id}/assign`
- **Roles Required:** `coordinator`, `app_manager`, `administrator`
- **Request Body:** `{"coordinator_id": "USR_COORD_1"}`

### `POST /complaints/{complaint_id}/resolve`
- **Request Body:** `{"notes": "Replaced regulator knob."}`

### `POST /complaints/{complaint_id}/reopen`
- **Request Body:** `{"reason": "Fan is still making noise."}`

---

## 🔔 Notifications (`/notifications`)

- `GET /notifications`: List notifications for current user.
- `POST /notifications/read-all`: Mark all notifications for current user as read.
- `PUT /notifications/{id}/read`: Mark single notification as read.
- `DELETE /notifications/{id}`: Delete single notification.
- `DELETE /notifications`: Clear all notifications.

---

## ⚙️ Settings & Data Maintenance (`/settings`)

- `GET /settings/duplicates`: Scan for duplicate department/location records.
- `POST /settings/resolve-duplicate`: Safely consolidate duplicates by migrating complaints/users before deleting stale records.
- `GET /settings/backup`: Export full JSON database snapshot.
- `POST /settings/restore`: Restore database from JSON backup snapshot.

---

## 💬 Chat (`/chat`)

Notes: Conversations are domain-bound to Lost & Found items. Clients cannot create arbitrary user-to-user chats — conversations for an item are created by the server when an ownership claim is approved.

### `POST /chat/start`
- **Description:** Request the conversation for a given `item_id`. The endpoint will return the existing conversation linked to the item if one exists; it will NOT create a new conversation from the client.
- **Request Body:** `{"item_id": "LF_F01"}`
- **Response (200):** `{"conversation_id": "chat:USER_A:USER_B", "item_id": "LF_F01", "read_only": false}`

### `POST /chat/message`
- **Description:** Send a message in a conversation. Requires `conversation_id` and `content`. The sender must be a participant and the conversation must not be read-only.
- **Request Body:** `{"conversation_id": "chat:USER_A:USER_B", "content": "Hello"}`
- **Response (200):** The saved message object `{message_id, conversation_id, sender_id, content, created_at, is_read}`

### `GET /chat/{conversation_id}`
- **Description:** List messages for a conversation. Caller must be a participant.

### `GET /chat/conversations`
- **Description:** List conversations for current user. Only returns conversations linked to Lost & Found items. Each item includes `item_id` and `read_only` flags so clients can render appropriate UI (disable input when `read_only` is true).

### WebSocket: `/ws/chat/{conversation_id}/{user_id}`
- **Auth:** Short-term token via query string `?token=<access_token>` is supported for WebSocket authentication. The token must match a server session for the connecting user and the user must be a participant in the conversation.
- **Events:** `chat_message` (payload = message object), `chat_created` (sent on conversation creation during claim approval).

Audit: Conversation creation, message sends, and read-only transitions are logged in the `audit_logs` table under module `Chat`.

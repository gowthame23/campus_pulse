import base64
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from utils.helper import generate_id, now_string

_PHOTO_MAX_BYTES = 5 * 1024 * 1024  # 5 MB, matches the frontend's existing limit
_PHOTO_SIGNATURES = {
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG",),
    "gif": (b"GIF87a", b"GIF89a"),
    "webp": (b"RIFF",),
}


class LostFoundService:
    REPORT_TYPES = ("Lost", "Found")
    CATEGORIES = (
        "Electronics",
        "Documents",
        "Wallet",
        "Keys",
        "Jewelry",
        "Clothing",
        "Books",
        "Bags",
        "Sports Equipment",
        "Other",
    )
    ITEM_STATUSES = (
        "Reported",
        "Under Review",
        "Matched",
        "Claim Submitted",
        "Verification Pending",
        "Ready for Return",
        "Returned",
        "Closed",
        "Rejected",
        "Archived",
    )
    VISIBILITIES = ("Public", "Private")
    IMAGE_TYPES = (
        "Overview",
        "Serial Number",
        "Proof of Ownership",
        "Additional Evidence",
    )

    def __init__(
        self,
        notification_service=None,
        audit_service=None,
        db_path="storage/campus_pulse.db",
        auth_service=None,
    ):
        self.db_path = Path(db_path)
        self.storage_dir = (self.db_path.parent / "lost_found_photos").resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.notification_service = notification_service
        self.audit_service = audit_service
        self.auth_service = auth_service

    def staff_scope_allows(self, item, role, user_id):
        """Whether a non-student staff member's role+location assignment covers
        this item. Administrator is institution-wide. If the item has no
        location recorded, or auth_service wasn't wired in, scope can't be
        narrowed, so access is allowed (preserves existing behavior for the
        many items that don't set a location)."""
        role = (role or "").lower()
        if role == "administrator":
            return True
        item_loc = item.get("location_id") or item.get("building_id")
        if not item_loc or not self.auth_service:
            return True
        if role == "app_manager":
            return self.auth_service.is_app_manager_assigned(user_id, item_loc)
        if role == "location_in_charge":
            return self.auth_service.is_warden_assigned(user_id, item_loc)
        if role == "coordinator":
            assignments = self.auth_service.list_coordinator_assignments(coordinator_id=user_id) or []
            return any(a.get("location_id") in ("ALL", None, item_loc) for a in assignments)
        return True
        self._ensure_seeds()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_seeds(self):
        pass

    def _persist_photo(self, raw):
        """Accepts either a plain URL (passed through unchanged) or an inline
        `data:image/...;base64,...` URI from the file picker. Base64 payloads
        are decoded, validated, and written to disk under
        storage/lost_found_photos/ so the DB stores a small served path
        instead of the full image bytes as text."""
        if not raw or not isinstance(raw, str) or not raw.startswith("data:"):
            return raw

        try:
            header, encoded = raw.split(",", 1)
        except ValueError:
            return raw

        if ";base64" not in header:
            return raw

        mime = header[5:].split(";", 1)[0].lower()  # e.g. "image/jpeg"
        ext = mime.split("/", 1)[1] if "/" in mime else ""
        ext = {"jpg": "jpeg"}.get(ext, ext)
        if ext not in _PHOTO_SIGNATURES:
            raise ValueError(f"Unsupported photo format '{ext}'. Allowed: JPG, PNG, GIF, WEBP.")

        try:
            file_bytes = base64.b64decode(encoded, validate=True)
        except Exception:
            raise ValueError("Photo data is not valid base64 content.")

        if len(file_bytes) > _PHOTO_MAX_BYTES:
            raise ValueError("Photo exceeds the maximum allowed size of 5 MB.")

        if not any(file_bytes.startswith(sig) for sig in _PHOTO_SIGNATURES[ext]):
            raise ValueError(f"Photo content does not match a valid {ext.upper()} file.")

        storage_dir = self.storage_dir
        stored_filename = f"{generate_id('LFP')}.{'jpg' if ext == 'jpeg' else ext}"
        with open(storage_dir / stored_filename, "wb") as f:
            f.write(file_bytes)

        return f"/static/lost_found_photos/{stored_filename}"

    # ==========================================
    # 1. ITEM MANAGEMENT
    # ==========================================
    def list_items(
        self,
        report_type=None,
        category=None,
        status=None,
        building_id=None,
        visibility=None,
        q=None,
        user=None,
        include_deleted=False,
        reported_by=None,
    ):
        query = """
            SELECT l.*, u.name as reported_by_name
            FROM lost_found_items l
            LEFT JOIN users u ON l.reported_by = u.user_id
            WHERE 1=1
        """
        params = []

        if not include_deleted:
            query += " AND (l.is_deleted = 0 OR l.is_deleted IS NULL)"

        if reported_by:
            query += " AND l.reported_by = ?"
            params.append(reported_by)

        # Role Scoping
        if user:
            role = (user.role or "").lower()
            if role == "student":
                query += " AND (l.visibility = 'Public' OR l.reported_by = ?)"
                params.append(user.user_id)

        if report_type:
            query += " AND LOWER(l.report_type) = LOWER(?)"
            params.append(report_type)
        if category:
            query += " AND LOWER(l.category) = LOWER(?)"
            params.append(category)
        if status:
            s_lower = status.lower()
            if s_lower == "active":
                query += " AND l.status NOT IN ('Returned', 'Resolved', 'Closed', 'Archived')"
            elif s_lower in ("resolved", "returned"):
                query += " AND l.status IN ('Returned', 'Resolved', 'Closed')"
            else:
                query += " AND l.status = ?"
                params.append(status)
        if building_id:
            query += " AND l.building_id = ?"
            params.append(building_id)
        if visibility:
            query += " AND l.visibility = ?"
            params.append(visibility)

        if q:
            term = f"%{q.strip()}%"
            query += " AND (l.title LIKE ? OR l.description LIKE ? OR l.brand LIKE ? OR l.color LIKE ? OR l.serial_number LIKE ?)"
            params.extend([term, term, term, term, term])

        query += " ORDER BY l.created_at DESC"

        with self._connect() as conn:
            return [
                self._row_to_dict(r) for r in conn.execute(query, params).fetchall()
            ]

    def get_item(self, item_id):
        query = """
            SELECT l.*, u.name as reported_by_name
            FROM lost_found_items l
            LEFT JOIN users u ON l.reported_by = u.user_id
            WHERE l.item_id = ? AND (l.is_deleted = 0 OR l.is_deleted IS NULL)
        """
        with self._connect() as conn:
            row = conn.execute(query, (item_id,)).fetchone()
            return self._row_to_dict(row) if row else None

    def create_item(
        self,
        report_type,
        reported_by,
        title,
        description,
        category="Other",
        brand="",
        color="",
        serial_number="",
        unique_identifiers=None,
        estimated_value=0.0,
        date_lost_found="",
        time_lost_found="",
        campus_id=None,
        building_id=None,
        block_id=None,
        floor_id=None,
        room_id=None,
        exact_location="",
        current_storage_location="",
        visibility="Public",
        user_role="Student",
        photos=None,
        location_id=None,
        lost_date=None,
    ):
        # 1. Student Role Guard
        if (user_role or "").lower() != "student":
            raise PermissionError("Only students can report lost or found items.")

        # 2. Normalize Report Type (LOST -> Lost, FOUND -> Found)
        rt_upper = (report_type or "").upper()
        if rt_upper == "LOST":
            report_type = "Lost"
        elif rt_upper == "FOUND":
            report_type = "Found"

        if report_type not in self.REPORT_TYPES:
            raise ValueError(
                f"Invalid Report Type. Allowed: LOST or FOUND."
            )

        # 3. Title & Description Validation
        if not title or len(title.strip()) > 150:
            raise ValueError("Title is required and must be under 150 characters.")
        if not description or not description.strip():
            raise ValueError("Description is required.")

        # 4. Location Active Check
        loc_check_id = location_id or building_id
        if loc_check_id:
            with self._connect() as conn:
                row = conn.execute("SELECT active FROM locations WHERE location_id = ? OR LOWER(name) = ?", (loc_check_id, loc_check_id.lower())).fetchone()
                if row and dict(row).get("active") == 0:
                    raise ValueError("Selected location is inactive.")

        # 5. Future Date Check
        today_str = datetime.now().strftime("%Y-%m-%d")
        date_str = lost_date or date_lost_found or today_str
        if date_str > today_str:
            raise ValueError("Lost/found date cannot be in the future.")

        # 6. Photos Validation (max 3 photos)
        photos = photos or []
        if len(photos) > 3:
            raise ValueError("Maximum 3 photos allowed.")
        photos = [self._persist_photo(p) for p in photos]

        iid = generate_id("LFI")
        now = now_string()
        uniq_dict = unique_identifiers or {}
        if photos:
            uniq_dict["photos"] = photos
        uniq_json = json.dumps(uniq_dict)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO lost_found_items
                (item_id, report_type, reported_by, title, description, category, brand, color, serial_number, unique_identifiers, estimated_value, date_lost_found, time_lost_found, campus_id, building_id, block_id, floor_id, room_id, exact_location, current_storage_location, status, visibility, created_at, updated_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, 0)
                """,
                (
                    iid,
                    report_type,
                    reported_by,
                    title.strip(),
                    description.strip(),
                    category,
                    brand,
                    color,
                    serial_number,
                    uniq_json,
                    float(estimated_value),
                    date_str,
                    time_lost_found,
                    campus_id,
                    loc_check_id,
                    block_id,
                    floor_id,
                    room_id,
                    exact_location,
                    current_storage_location,
                    visibility,
                    now,
                    now,
                ),
            )

        item = self.get_item(iid)

        if self.audit_service:
            self.audit_service.log_event(
                module="Lost & Found",
                entity_type="Item",
                entity_id=iid,
                action="CREATE",
                performed_by=reported_by,
                description=f"User {reported_by} reported {report_type} item {title}",
            )

        # Notify via NotificationService
        if self.notification_service:
            self.notification_service.publish(
                receiver_id=reported_by,
                title=f"{report_type} Item Report Created",
                message=f"Your {report_type} item report '{title}' (#{iid}) has been submitted.",
                module="Lost & Found",
                notification_type="lost_found_created",
                reference_type="LostItem" if report_type == "Lost" else "FoundItem",
                reference_id=iid,
                priority="Medium",
            )

        # Log Audit
        if self.audit_service:
            self.audit_service.log_event(
                module="Lost & Found",
                entity_type="Item",
                entity_id=iid,
                action="CREATE",
                performed_by=reported_by,
                performed_role=user_role,
                new_value=item,
                description=f"Created {report_type} item report '{title}'",
            )

        # Trigger automatic matching check asynchronously
        self.run_matching_engine(iid)

        return item

    def update_item(self, item_id, updates, performer_id="system", user_role="Student"):
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found.")

        role_lower = (user_role or "").lower()
        if performer_id != "system" and performer_id != item["reported_by"] and role_lower not in ("administrator", "app_manager", "super_admin", "admin"):
            raise PermissionError("You are not authorized to update this item.")

        allowed = (
            "title",
            "description",
            "category",
            "brand",
            "color",
            "serial_number",
            "estimated_value",
            "exact_location",
            "current_storage_location",
            "status",
            "visibility",
        )
        set_clauses = []
        params = []
        for k in allowed:
            if k in updates:
                set_clauses.append(f"{k} = ?")
                params.append(updates[k])

        if set_clauses:
            now = now_string()
            set_clauses.append("updated_at = ?")
            params.append(now)
            params.append(item_id)
            with self._connect() as conn:
                conn.execute(
                    f"UPDATE lost_found_items SET {', '.join(set_clauses)} WHERE item_id = ?",
                    params,
                )

        updated = self.get_item(item_id)
        if self.audit_service:
            self.audit_service.log_event(
                module="Lost & Found",
                entity_type="Item",
                entity_id=item_id,
                action="UPDATE",
                performed_by=performer_id,
                old_value=item,
                new_value=updated,
                description=f"Updated item {item['title']}",
            )

        # If the item is closed, mark linked conversation read-only
        try:
            if updated and updated.get("status") == "Closed":
                from services.chat_service import ChatService

                chat_service = ChatService()
                linked = chat_service.get_conversation_for_item(item_id)
                if linked:
                    chat_service.set_read_only(linked["conversation_id"], True)
        except Exception:
            pass

        return updated

    def delete_item(self, item_id, performer_id="system", user_role="Student"):
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found.")

        role_lower = (user_role or "").lower()
        if (
            performer_id != "system"
            and performer_id != item["reported_by"]
            and role_lower not in ("administrator", "app_manager", "super_admin", "admin")
        ):
            raise PermissionError("You can only delete your own reports.")

        if role_lower == "student" and item.get("status") in ("Returned", "Resolved", "Closed"):
            raise ValueError("Returned or resolved reports cannot be deleted.")

        now = now_string()
        with self._connect() as conn:
            # 1. Soft delete the main report item
            conn.execute(
                "UPDATE lost_found_items SET is_deleted = 1, deleted_at = ?, deleted_by = ?, status = 'Closed' WHERE item_id = ?",
                (now, performer_id, item_id),
            )

            # 2. Cancel / delete all associated ownership claims
            conn.execute(
                "UPDATE ownership_claims SET status = 'Cancelled' WHERE item_id = ?",
                (item_id,),
            )

            # 3. Soft-delete all related notifications for this item and its claims
            conn.execute(
                """
                UPDATE notifications 
                SET is_deleted = 1, deleted_at = ?, deleted_by = ?
                WHERE (
                    reference_id = ?
                    OR reference_id IN (SELECT claim_id FROM ownership_claims WHERE item_id = ?)
                    OR (module = 'Lost & Found' AND (message LIKE '%' || ? || '%' OR title LIKE '%' || ? || '%'))
                )
                AND (is_deleted = 0 OR is_deleted IS NULL)
                """,
                (now, performer_id, item_id, item_id, item_id, item_id),
            )

            # 4. Remove associated images
            conn.execute(
                "DELETE FROM lost_found_images WHERE item_id = ?",
                (item_id,),
            )

            # 5. Mark linked chat conversations read-only and soft-delete chat notifications
            conn.execute(
                "UPDATE chat_conversations SET read_only = 1 WHERE item_id = ?",
                (item_id,),
            )
            conn.execute(
                """
                UPDATE notifications 
                SET is_deleted = 1, deleted_at = ?, deleted_by = ?
                WHERE module = 'Chat' AND (reference_id = ? OR message LIKE '%' || ? || '%')
                AND (is_deleted = 0 OR is_deleted IS NULL)
                """,
                (now, performer_id, item_id, item_id),
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Lost & Found",
                entity_type="Item",
                entity_id=item_id,
                action="SOFT_DELETE",
                performed_by=performer_id,
                description=f"Soft deleted item {item['title']} and cleaned up all dependent operational data",
            )

        return {"message": "Item report and all associated operational records soft deleted successfully."}

    # ==========================================
    # 2. IMAGE MANAGEMENT
    # ==========================================
    def upload_image(self, item_id, uploaded_by, image_url, image_type="Overview", user_role="Student"):
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found.")

        role_lower = (user_role or "").lower()
        if uploaded_by != "system" and uploaded_by != item["reported_by"] and role_lower not in ("administrator", "app_manager", "super_admin", "admin"):
            raise PermissionError("You are not authorized to add images to this item.")

        if image_type not in self.IMAGE_TYPES:
            raise ValueError(
                f"Invalid Image Type. Allowed: {', '.join(self.IMAGE_TYPES)}"
            )

        image_url = self._persist_photo(image_url)

        img_id = generate_id("IMG")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO lost_found_images (image_id, item_id, uploaded_by, image_type, image_url, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (img_id, item_id, uploaded_by, image_type, image_url, now),
            )
        return {
            "image_id": img_id,
            "item_id": item_id,
            "image_type": image_type,
            "image_url": image_url,
            "uploaded_at": now,
        }

    def list_images(self, item_id):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM lost_found_images WHERE item_id = ? ORDER BY uploaded_at ASC",
                (item_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def delete_image(self, image_id, performer_id="system", user_role="Student"):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM lost_found_images WHERE image_id = ?", (image_id,)
            ).fetchone()
            if not row:
                return False
            img_dict = dict(row)
            item = self.get_item(img_dict["item_id"])
            if item:
                role_lower = (user_role or "").lower()
                if (
                    performer_id != "system"
                    and performer_id != item["reported_by"]
                    and performer_id != img_dict.get("uploaded_by")
                    and role_lower not in ("administrator", "app_manager", "super_admin", "admin")
                ):
                    raise PermissionError("You are not authorized to delete this image.")
            cursor = conn.execute(
                "DELETE FROM lost_found_images WHERE image_id = ?", (image_id,)
            )
            return cursor.rowcount > 0

    # ==========================================
    # 3. INTELLIGENT MATCHING ENGINE (DISABLED - SIMPLIFIED SYSTEM)
    # ==========================================
    def run_matching_engine(self, target_item_id):
        # AI matching is disabled in simplified mode. Owner and finder connect directly.
        return []

    # ==========================================
    # 4. OWNERSHIP CLAIMS & RETURN WORKFLOW
    # ==========================================
    def submit_claim(self, item_id, claimed_by, claim_reason="", proof_description=""):
        raise ValueError("Ownership claims workflow is disabled. Owner and finder handle return directly.")
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found.")

        if item.get("status") in ("Returned", "Closed", "CLAIM_APPROVED"):
            raise ValueError("Item has already been claimed or closed.")

        # Check existing claims by this student for this item
        existing = self.list_claims(item_id=item_id, claimed_by=claimed_by)
        if existing:
            raise ValueError("You have already submitted a claim for this item.")

        cid = generate_id("CLM")
        now = now_string()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ownership_claims
                (claim_id, item_id, claimed_by, claim_reason, proof_description, status, created_at)
                VALUES (?, ?, ?, ?, ?, 'Pending', ?)
                """,
                (cid, item_id, claimed_by, claim_reason, proof_description, now),
            )

            # Update item status to Claim Submitted
            conn.execute(
                "UPDATE lost_found_items SET status = 'Claim Submitted', updated_at = ? WHERE item_id = ?",
                (now, item_id),
            )

        claim = self.get_claim(cid)

        if self.notification_service:
            self.notification_service.publish(
                receiver_id=claimed_by,
                title="Ownership Claim Submitted",
                message=f"Your claim for found item '{item['title']}' has been submitted for verification.",
                module="Lost & Found",
                notification_type="claim_submitted",
                reference_type="Claim",
                reference_id=cid,
                priority="Medium",
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Lost & Found",
                entity_type="Claim",
                entity_id=cid,
                action="CREATE",
                performed_by=claimed_by,
                description=f"User {claimed_by} submitted claim for found item {item_id}",
            )

        return claim

    def get_claim(self, claim_id):
        query = """
            SELECT c.*, i.is_deleted as item_is_deleted
            FROM ownership_claims c
            JOIN lost_found_items i ON c.item_id = i.item_id
            WHERE c.claim_id = ?
        """
        with self._connect() as conn:
            row = conn.execute(query, (claim_id,)).fetchone()
            if not row:
                return None
            d = dict(row)
            if d.get("item_is_deleted") == 1 or d.get("status") == "Cancelled":
                return None
            d.pop("item_is_deleted", None)
            return d

    def list_claims(self, item_id=None, claimed_by=None, status=None, include_cancelled=False):
        query = """
            SELECT c.*, i.title as item_title, i.category
            FROM ownership_claims c
            JOIN lost_found_items i ON c.item_id = i.item_id
            WHERE (i.is_deleted = 0 OR i.is_deleted IS NULL)
        """
        params = []
        if not include_cancelled:
            query += " AND c.status != 'Cancelled'"
        if item_id:
            query += " AND c.item_id = ?"
            params.append(item_id)
        if claimed_by:
            query += " AND c.claimed_by = ?"
            params.append(claimed_by)
        if status:
            query += " AND LOWER(c.status) = LOWER(?)"
            params.append(status)

        query += " ORDER BY c.created_at DESC"
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def approve_claim(self, claim_id, reviewer_id, decision_notes="", user_role="Student"):
        claim = self.get_claim(claim_id)
        if not claim:
            raise ValueError("Claim not found.")

        item = self.get_item(claim["item_id"])
        if not item:
            raise ValueError("Item not found.")

        role_lower = (user_role or "").lower()
        if (
            reviewer_id != "system"
            and reviewer_id != item["reported_by"]
            and role_lower not in ("administrator", "app_manager", "location_in_charge", "coordinator", "super_admin", "admin")
        ):
            raise PermissionError("You are not authorized to review claims for this item.")
        if (
            reviewer_id != "system"
            and reviewer_id != item["reported_by"]
            and not self.staff_scope_allows(item, role_lower, reviewer_id)
        ):
            raise PermissionError("This claim belongs to an item outside your assigned location.")

        now = now_string()
        with self._connect() as conn:
            # 1. Approve target claim
            conn.execute(
                "UPDATE ownership_claims SET status = 'Approved', reviewed_by = ?, reviewed_at = ?, decision_notes = ? WHERE claim_id = ?",
                (reviewer_id, now, decision_notes, claim_id),
            )

            # 2. Reject all other pending claims for this item
            conn.execute(
                "UPDATE ownership_claims SET status = 'Rejected', reviewed_by = ?, reviewed_at = ?, decision_notes = 'Auto-rejected: Another ownership claim was approved' WHERE item_id = ? AND claim_id != ? AND status = 'Pending'",
                (reviewer_id, now, claim["item_id"], claim_id),
            )

            # 3. Update item status to Ready for Return
            conn.execute(
                "UPDATE lost_found_items SET status = 'Ready for Return', updated_at = ? WHERE item_id = ?",
                (now, claim["item_id"]),
            )

        updated = self.get_claim(claim_id)

        if self.notification_service:
            self.notification_service.publish(
                receiver_id=claim["claimed_by"],
                title="Ownership Claim Approved!",
                message=f"Your claim for item {claim['item_id']} was APPROVED! Please collect item from storage location.",
                module="Lost & Found",
                notification_type="claim_approved",
                reference_type="Claim",
                reference_id=claim_id,
                priority="High",
            )

        # Create chat conversation for this item between finder (reported_by) and claimant so they can coordinate collection.
        try:
            from services.chat_service import ChatService

            chat_service = ChatService()
            item = self.get_item(claim["item_id"])
            if item:
                finder = item.get("reported_by")
                claimant = claim.get("claimed_by")
                if finder and claimant:
                    conv = chat_service.start_conversation(finder, claimant)
                    chat_service.create_conversation_link(
                        conv, claim["item_id"], participant_a=finder, participant_b=claimant
                    )
                    # Notify both parties about created conversation
                    if self.notification_service:
                        self.notification_service.publish(
                            receiver_id=finder,
                            title="Conversation Created",
                            message=f"A conversation has been created for item {item['title']}",
                            module="Chat",
                            notification_type="chat_created",
                            reference_type="LostItem",
                            reference_id=claim["item_id"],
                            priority="Low",
                        )
                        self.notification_service.publish(
                            receiver_id=claimant,
                            title="Conversation Created",
                            message=f"A conversation has been created for item {item['title']}",
                            module="Chat",
                            notification_type="chat_created",
                            reference_type="LostItem",
                            reference_id=claim["item_id"],
                            priority="Low",
                        )
                    # push websocket direct sync if manager is available
                    try:
                        from utils.websocket_manager import manager

                        manager.push_sync(
                            finder,
                            {
                                "event": "chat_created",
                                "data": {
                                    "conversation_id": conv,
                                    "item_id": claim["item_id"],
                                },
                            },
                        )
                        manager.push_sync(
                            claimant,
                            {
                                "event": "chat_created",
                                "data": {
                                    "conversation_id": conv,
                                    "item_id": claim["item_id"],
                                },
                            },
                        )
                    except Exception:
                        pass
        except Exception:
            # non-fatal: conversation creation shouldn't block claim approval
            pass

        if self.audit_service:
            self.audit_service.log_event(
                module="Lost & Found",
                entity_type="Claim",
                entity_id=claim_id,
                action="APPROVE",
                performed_by=reviewer_id,
                description=f"Approved ownership claim {claim_id}",
            )

        return updated

    def reject_claim(self, claim_id, reviewer_id, decision_notes="", user_role="Student"):
        claim = self.get_claim(claim_id)
        if not claim:
            raise ValueError("Claim not found.")

        item = self.get_item(claim["item_id"])
        if not item:
            raise ValueError("Item not found.")

        role_lower = (user_role or "").lower()
        if (
            reviewer_id != "system"
            and reviewer_id != item["reported_by"]
            and role_lower not in ("administrator", "app_manager", "location_in_charge", "coordinator", "super_admin", "admin")
        ):
            raise PermissionError("You are not authorized to review claims for this item.")
        if (
            reviewer_id != "system"
            and reviewer_id != item["reported_by"]
            and not self.staff_scope_allows(item, role_lower, reviewer_id)
        ):
            raise PermissionError("This claim belongs to an item outside your assigned location.")

        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "UPDATE ownership_claims SET status = 'Rejected', reviewed_by = ?, reviewed_at = ?, decision_notes = ? WHERE claim_id = ?",
                (reviewer_id, now, decision_notes, claim_id),
            )

        updated = self.get_claim(claim_id)
        if self.notification_service:
            self.notification_service.publish(
                receiver_id=claim["claimed_by"],
                title="Ownership Claim Rejected",
                message=f"Your claim for item {claim['item_id']} was Rejected. Notes: {decision_notes}",
                module="Lost & Found",
                notification_type="claim_rejected",
                reference_type="Claim",
                reference_id=claim_id,
                priority="High",
            )

        return updated

    def mark_returned(self, item_id, performer_id="system", user_role="Student"):
        item = self.get_item(item_id)
        if not item:
            raise ValueError("Item not found.")

        role_lower = (user_role or "").lower()
        if (
            performer_id != "system"
            and performer_id != item["reported_by"]
            and role_lower not in ("administrator", "app_manager", "location_in_charge", "coordinator", "super_admin", "admin")
        ):
            raise PermissionError("You are not authorized to mark this item as returned.")
        if (
            performer_id != "system"
            and performer_id != item["reported_by"]
            and not self.staff_scope_allows(item, role_lower, performer_id)
        ):
            raise PermissionError("This item is outside your assigned location.")

        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "UPDATE lost_found_items SET status = 'Returned', updated_at = ? WHERE item_id = ?",
                (now, item_id),
            )

        # Mark linked chat conversation read-only
        try:
            from services.chat_service import ChatService
            chat_service = ChatService()
            linked = chat_service.get_conversation_for_item(item_id)
            if linked:
                chat_service.set_read_only(linked["conversation_id"], True)
        except Exception:
            pass

        if self.audit_service:
            self.audit_service.log_event(
                module="Lost & Found",
                entity_type="Item",
                entity_id=item_id,
                action="STATUS_CHANGE",
                performed_by=performer_id,
                description=f"Item {item_id} verified and returned to owner",
            )

        return self.get_item(item_id)

    def _row_to_dict(self, row):
        if not row:
            return None
        d = dict(row)
        if d.get("unique_identifiers"):
            try:
                d["unique_identifiers"] = json.loads(d["unique_identifiers"])
            except Exception:
                pass
        return d

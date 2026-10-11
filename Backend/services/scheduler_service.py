import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timedelta

from utils.logger import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """Background scheduler that runs periodic tasks in a daemon thread,
    using an atomic SQLite lease lock to ensure only one worker runs tasks."""

    def __init__(self, interval_seconds: int = 300, db_path: str = "storage/campus_pulse.db"):
        self.interval = interval_seconds
        self.db_path = db_path
        self._thread = None
        self._running = False
        self._tasks = []
        self._worker_id = f"{os.getpid()}_{uuid.uuid4().hex[:6]}"

    def register_task(self, name: str, func, *args, **kwargs):
        """Register a periodic task."""
        self._tasks.append({"name": name, "func": func, "args": args, "kwargs": kwargs})
        logger.info(f"Registered scheduler task: {name}")

    def _acquire_lease(self) -> bool:
        """Attempt to acquire or renew the master scheduler lease."""
        try:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expires_str = (datetime.now() + timedelta(seconds=self.interval * 2)).strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect(self.db_path)
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO scheduler_lock (lock_name, locked_by, locked_at, expires_at)
                    VALUES ('master_scheduler', ?, ?, ?)
                    ON CONFLICT(lock_name) DO UPDATE SET
                        locked_by = excluded.locked_by,
                        locked_at = excluded.locked_at,
                        expires_at = excluded.expires_at
                    WHERE scheduler_lock.expires_at < excluded.locked_at
                       OR scheduler_lock.locked_by = excluded.locked_by
                    """,
                    (self._worker_id, now_str, expires_str),
                )
                acquired = cursor.rowcount > 0
            conn.close()
            return acquired
        except Exception as err:
            logger.warning(f"Scheduler lease acquisition check failed: {err}")
            return False

    def _run_tasks(self):
        while self._running:
            if self._acquire_lease():
                for task in self._tasks:
                    try:
                        logger.info(f"Scheduler ({self._worker_id}): running task '{task['name']}'")
                        task["func"](*task["args"], **task["kwargs"])
                    except Exception as e:
                        logger.error(f"Scheduler: task '{task['name']}' failed: {e}")
            else:
                logger.debug(f"Scheduler ({self._worker_id}): lease held by another worker; skipping cycle.")

            # Sleep in small increments so we can stop quickly on exit
            for _ in range(self.interval):
                if not self._running:
                    break
                time.sleep(1)

    def start(self):
        if os.environ.get("RUN_SCHEDULER", "true").lower() in ("false", "0", "no"):
            logger.info("Scheduler disabled via RUN_SCHEDULER env var.")
            return

        if self._running:
            logger.warning("Scheduler is already running.")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_tasks, daemon=True, name=f"CampusPulse-Scheduler-{self._worker_id}"
        )
        self._thread.start()
        logger.info(
            f"Background scheduler started (worker={self._worker_id}). Running every {self.interval}s with {len(self._tasks)} task(s)."
        )

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info(f"Background scheduler stopped (worker={self._worker_id}).")


def create_scheduler(complaint_service, config_service):
    """Factory function to create and configure the scheduler with automatic background tasks."""
    try:
        interval = int(config_service.get_setting("scheduler_interval_seconds", 300))
    except Exception:
        interval = 300

    db_path = getattr(config_service, "db_path", None) or os.environ.get(
        "DATABASE_PATH", "storage/campus_pulse.db"
    )

    scheduler = SchedulerService(interval_seconds=interval, db_path=db_path)

    # Task 1: Auto-close + SLA escalation rules
    def run_automatic_rules():
        try:
            complaint_service.apply_automatic_rules()
        except Exception as e:
            logger.error(f"Auto rules failed: {e}")

    scheduler.register_task("Auto-Close & SLA Escalation", run_automatic_rules)

    # Task 2: Cleanup expired soft-deleted records
    def cleanup_expired():
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            cutoff_date = (datetime.now() - timedelta(days=90)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            cursor = conn.execute(
                "DELETE FROM notifications WHERE is_deleted = 1 AND deleted_at < ?",
                (cutoff_date,),
            )
            if cursor.rowcount > 0:
                logger.info(
                    f"Cleanup: purged {cursor.rowcount} old deleted notifications."
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")

    scheduler.register_task("Cleanup Expired Records", cleanup_expired)

    return scheduler

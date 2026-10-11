import os
import threading
import time

from utils.logger import get_logger

logger = get_logger(__name__)


class SchedulerService:
    """Background scheduler that runs periodic tasks in a daemon thread."""

    def __init__(self, interval_seconds: int = 300):
        self.interval = interval_seconds  # 5 minutes default
        self._thread = None
        self._running = False
        self._tasks = []

    def register_task(self, name: str, func, *args, **kwargs):
        """Register a periodic task."""
        self._tasks.append({"name": name, "func": func, "args": args, "kwargs": kwargs})
        logger.info(f"Registered scheduler task: {name}")

    def _run_tasks(self):
        while self._running:
            for task in self._tasks:
                try:
                    logger.info(f"Scheduler: running task '{task['name']}'")
                    task["func"](*task["args"], **task["kwargs"])
                except Exception as e:
                    logger.error(f"Scheduler: task '{task['name']}' failed: {e}")

            # Sleep in small increments so we can stop quickly on exit
            for _ in range(self.interval):
                if not self._running:
                    break
                time.sleep(1)

    def start(self):
        if self._running:
            logger.warning("Scheduler is already running.")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._run_tasks, daemon=True, name="CampusPulse-Scheduler"
        )
        self._thread.start()
        logger.info(
            f"Background scheduler started. Running every {self.interval}s with {len(self._tasks)} task(s)."
        )

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Background scheduler stopped.")


def create_scheduler(complaint_service, config_service):
    """Factory function to create and configure the scheduler with automatic background tasks."""

    try:
        interval = int(config_service.get_setting("scheduler_interval_seconds", 300))
    except Exception:
        interval = 300

    scheduler = SchedulerService(interval_seconds=interval)

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
            import sqlite3
            from datetime import datetime, timedelta

            db_path = getattr(config_service, "db_path", None) or os.environ.get(
                "DATABASE_PATH", "storage/campus_pulse.db"
            )
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row

            cutoff_date = (datetime.now() - timedelta(days=90)).strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            # Hard-delete notifications soft-deleted over 90 days ago
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

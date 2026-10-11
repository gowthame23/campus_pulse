from datetime import datetime, timedelta

class SLAService:
    DEFAULT_SLA_HOURS = {
        "URGENT": 4,
        "HIGH": 12,
        "MEDIUM": 24,
        "NORMAL": 24,
        "LOW": 72,
    }

    def calculate_due_date(self, priority: str, base_date: datetime = None) -> datetime:
        """Calculates SLA due date based on priority."""
        if base_date is None:
            base_date = datetime.now()
        hours = self.DEFAULT_SLA_HOURS.get((priority or "NORMAL").upper(), 24)
        return base_date + timedelta(hours=hours)

    def is_escalated(self, created_at_str: str, priority: str, current_status: str) -> bool:
        """Checks if complaint has breached SLA resolution window."""
        if current_status in ("Resolved", "Closed", "Cancelled"):
            return False
        try:
            created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
            due_date = self.calculate_due_date(priority, created_at)
            return datetime.now() > due_date
        except Exception:
            return False

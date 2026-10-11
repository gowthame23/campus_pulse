from datetime import datetime, timedelta
from uuid import uuid4

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def generate_id(prefix):
    return f"{prefix}-{uuid4().hex[:8].upper()}"


def now():
    return datetime.now()


def now_string():
    return now().strftime(DATE_FORMAT)


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, DATE_FORMAT)


def add_days_string(days):
    return (now() + timedelta(days=days)).strftime(DATE_FORMAT)


def csv_safe(value):
    """Neutralize spreadsheet formula injection in user-supplied CSV cells."""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value

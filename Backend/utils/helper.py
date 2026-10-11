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
    if isinstance(value, datetime):
        return value
    val_str = str(value).strip()
    try:
        return datetime.strptime(val_str, DATE_FORMAT)
    except (ValueError, TypeError):
        pass
    try:
        return datetime.fromisoformat(val_str)
    except (ValueError, TypeError):
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(val_str, fmt)
        except (ValueError, TypeError):
            pass
    return None



def add_days_string(days):
    return (now() + timedelta(days=days)).strftime(DATE_FORMAT)


def csv_safe(value):
    """Neutralize spreadsheet formula injection in user-supplied CSV cells."""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value

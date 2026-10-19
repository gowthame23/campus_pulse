from fastapi import HTTPException, status

from services.auth_service import AuthService
from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationService:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def validate_unique_department_name(self, name: str, exclude_id: str = None, location_id: str = None):
        """Checks if a department with the given name already exists across campus (case and whitespace insensitive)."""
        normalized_name = " ".join(name.strip().split()).lower()
        for dept in self.auth_service.list_departments():
            dept_normalized = " ".join(dept.name.strip().split()).lower()
            if dept_normalized == normalized_name:
                if exclude_id and dept.department_id == exclude_id:
                    continue
                logger.warning(f"Duplicate department name detected across campus: {name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f'Department "{name.strip()}" already exists. Department names must be unique across campus.',
                )

    def validate_unique_location_name(self, name: str, exclude_id: str = None):
        """Checks if a location with the given name already exists (case-insensitive)."""
        normalized_name = name.strip().lower()
        for loc in self.auth_service.list_locations():
            if loc.name.strip().lower() == normalized_name:
                if exclude_id and loc.location_id == exclude_id:
                    continue
                logger.warning(f"Duplicate location name detected: {name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f'Location "{name.strip()}" already exists. Please choose another name.',
                )

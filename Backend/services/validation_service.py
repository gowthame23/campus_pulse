from fastapi import HTTPException, status

from services.auth_service import AuthService
from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationService:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def validate_unique_department_name(self, name: str, exclude_id: str = None, location_id: str = None):
        """Checks if a department with the given name already exists in the same location (case-insensitive)."""
        normalized_name = name.strip().lower()
        for dept in self.auth_service.list_departments():
            if dept.name.strip().lower() == normalized_name and dept.location_id == location_id:
                if exclude_id and dept.department_id == exclude_id:
                    continue
                logger.warning(f"Duplicate department name detected under location {location_id}: {name}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f'Department "{name.strip()}" already exists under this location. Please choose another name.',
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

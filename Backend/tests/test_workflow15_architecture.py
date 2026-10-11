import pytest
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.domain.duplicate_detection_service import DuplicateDetectionService
from services.domain.sla_service import SLAService
from services.domain.matching_service import MatchingService
from services.domain.file_storage_service import FileStorageService

def test_workflow_15_domain_services():
    # 1. SLA Service
    sla = SLAService()
    due = sla.calculate_due_date("HIGH")
    assert due is not None
    assert sla.is_escalated("2020-01-01 10:00:00", "HIGH", "In Progress") is True
    assert sla.is_escalated("2020-01-01 10:00:00", "HIGH", "Resolved") is False

    # 2. File Storage Service
    storage = FileStorageService(upload_dir="storage/test_attachments")
    val = storage.validate_file("document.pdf", 1024)
    assert val is True
    saved_path = storage.save_file("sample.txt", b"Hello World", subfolder="test")
    assert os.path.exists(saved_path)
    os.remove(saved_path)

    # 3. Duplicate Detection Service
    dupe_service = DuplicateDetectionService()
    dupes = dupe_service.find_potential_duplicates("Water leakage in room", "LOC_1", "DEP_1")
    assert isinstance(dupes, list)

    # 4. Matching Service
    matching = MatchingService()
    matches = matching.find_lost_found_matches("NON_EXISTENT_ID")
    assert matches == []

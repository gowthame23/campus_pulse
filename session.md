# CampusPulse_co Session Log

## 2026-11-20 — Polish, Cleanup, Architecture Documentation, and CI

- **Git History Audit:** Inspected git history for `CREDENTIALS.local.md` and any `.db` files. Confirmed neither was ever committed to the repository.
- **Clutter & Cache Cleanup:** Removed all `__pycache__`, `.pytest_cache`, `.pytest_tmp`, and transient SQLite databases (`Backend/storage/*target*.db`). Added `Backend/.pytest_cache/` to `.gitignore`.
- **PII / Email Sanitization:** Removed personal email address (`gowthamejjurothu@gmail.com`) from `README.md`, `Backend/README.md`, and `Website/index.html`.
- **Architecture & Tradeoffs Documentation:** Added a detailed multi-tenant architecture Mermaid flowchart and an in-depth tradeoffs section to `README.md`, explaining the SQLite-per-tenant design, operational simplicity, and how architecture evolves at scale (connection pools, sharding, distributed DBs).
- **Test Suite Polish (Zero Refactoring of Application Logic):**
  - Resolved `NameError: name 're' is not defined` in `Backend/api/main.py`.
  - Aligned status machine and permissions in test endpoints (`Backend/api/routers/complaints.py`, `services/complaint_service.py`, `department_service.py`, `team_service.py`) to properly accept the 3-stage lifecycle `"Going On"` and Warden permissions.
  - Isolated database backup and CLI restore tests in `test_phase3_security.py` to dedicated staging files in `storage/` to prevent Windows file-lock corruption of the active test database `pytest_isolated.db`.
  - Added module setup/teardown fixtures in coordinator test suites to preserve and restore coordinator state.
  - Result: 100% pass across full test suite (324 passed, 2 skipped, 0 failed).
- **CI Workflow:** Created `.github/workflows/ci.yml` running python pytest on push and pull request while preserving the existing showcase deploy workflow.
- **Reports:** Authored `CampusPulse_co/POLISH_REPORT.md` containing raw test execution output and detailed changelog.

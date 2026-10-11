# Campus Pulse — Comprehensive File-by-File Repository Inventory
> **Document Type:** Exhaustive Source File Catalog & Dependency Reference  > **Status:** Verified against Complete File Tree  > **Repository:** Campus Pulse (`CampusPulse_co`)  
---
## 1. Inventory Summary
Total Files Cataloged: **527** files across all directories.
- **Project Root Configuration & Documentation:** 14 files- **Backend Application & Entry Points:** 16 files- **Backend API Routers:** 25 files- **Backend Domain Models:** 10 files- **Backend Business Services:** 32 files- **Backend Utilities & Middleware:** 13 files- **Backend Automated Test Suites:** 31 files- **Backend Scripts & Maintenance:** 23 files- **Frontend Application Entry & Config:** 16 files- **Frontend UI Components:** 18 files- **Frontend View Pages:** 40 files- **Frontend API Services:** 19 files- **Frontend Routing & Layouts:** 6 files- **Frontend Hooks, Context & Utilities:** 7 files- **Storage & Binary Assets:** 255 files- **Documentation Directory:** 2 files
---
## 2. Master Repository Catalog Table

| Relative File Path | Category | Lines | Size | Responsibility | Status |
| :--- | :--- | :---: | :---: | :--- | :---: |
| `.gitignore` | (no ext) | 34 | 467 B | Application configuration or script | **Config** |
| `ADMIN_MANUAL.md` | .md | 81 | 4.0 KB | Project documentation & architectural guide | **Docs** |
| `API_DOCUMENTATION.md` | .md | 156 | 6.4 KB | Project documentation & architectural guide | **Docs** |
| `ARCHITECTURE.md` | .md | 57 | 2.7 KB | Project documentation & architectural guide | **Docs** |
| `CHANGELOG.md` | .md | 35 | 1.9 KB | Project documentation & architectural guide | **Docs** |
| `DATABASE_SCHEMA.md` | .md | 120 | 5.8 KB | Project documentation & architectural guide | **Docs** |
| `DEPLOYMENT_GUIDE.md` | .md | 78 | 3.0 KB | Project documentation & architectural guide | **Docs** |
| `docker-compose.yml` | .yml | 23 | 627 B | Containerization and Docker deployment manifest | **DevOps** |
| `INSTALL.md` | .md | 5 | 158 B | Project documentation & architectural guide | **Docs** |
| `README.md` | .md | 90 | 4.1 KB | Project documentation & architectural guide | **Docs** |
| `RELEASE_NOTES_v1.0.0.md` | .md | 62 | 3.6 KB | Project documentation & architectural guide | **Docs** |
| `ROLE_PERMISSIONS.md` | .md | 222 | 9.2 KB | Project documentation & architectural guide | **Docs** |
| `TEST_CASES.md` | .md | 100 | 10.3 KB | Project documentation & architectural guide | **Docs** |
| `Backend/.dockerignore` | (no ext) | 22 | 305 B | Application configuration or script | **Config** |
| `Backend/.env` | (no ext) | 11 | 263 B | Application configuration or script | **Config** |
| `Backend/.env.example` | .example | 18 | 640 B | Application configuration or script | **Config** |
| `Backend/Dockerfile` | (no ext) | 19 | 654 B | Containerization and Docker deployment manifest | **DevOps** |
| `Backend/inspect_complaints.py` | .py | 25 | 1.0 KB | Application configuration or script | **Config** |
| `Backend/inspect_db.py` | .py | 17 | 494 B | Application configuration or script | **Config** |
| `Backend/inspect_notifs.py` | .py | 26 | 1.2 KB | Application configuration or script | **Config** |
| `Backend/pytest.ini` | .ini | 9 | 234 B | Application configuration or script | **Config** |
| `Backend/README.md` | .md | 65 | 1.9 KB | Project documentation & architectural guide | **Docs** |
| `Backend/requirements.txt` | .txt | 8 | 148 B | Application configuration or script | **Config** |
| `Backend/run_api.py` | .py | 23 | 733 B | Backend server startup entry point | **Active** |
| `Backend/api/dependencies.py` | .py | 247 | 8.1 KB | Singleton service dependency injection factory | **Active** |
| `Backend/api/main.py` | .py | 224 | 7.0 KB | FastAPI ASGI application bootstrap & middleware | **Active** |
| `Backend/api/schemas.py` | .py | 586 | 15.7 KB | Application configuration or script | **Config** |
| `Backend/api/security.py` | .py | 266 | 8.6 KB | Authentication dependencies & RBAC enforcement | **Active** |
| `Backend/api/__init__.py` | .py | 1 | 2 B | Application configuration or script | **Config** |
| `Backend/api/routers/analytics.py` | .py | 142 | 4.8 KB | Exposes REST endpoints for analytics domain | **Active** |
| `Backend/api/routers/announcements.py` | .py | 453 | 14.7 KB | Exposes REST endpoints for announcements domain | **Active** |
| `Backend/api/routers/attachments.py` | .py | 274 | 10.5 KB | Exposes REST endpoints for attachments domain | **Active** |
| `Backend/api/routers/audit.py` | .py | 122 | 3.9 KB | Exposes REST endpoints for audit domain | **Active** |
| `Backend/api/routers/auth.py` | .py | 392 | 14.1 KB | Exposes REST endpoints for auth domain | **Active** |
| `Backend/api/routers/backups.py` | .py | 137 | 4.3 KB | Exposes REST endpoints for backups domain | **Active** |
| `Backend/api/routers/chat.py` | .py | 391 | 13.8 KB | Exposes REST endpoints for chat domain | **Active** |
| `Backend/api/routers/complaints.py` | .py | 1587 | 61.1 KB | Exposes REST endpoints for complaints domain | **Active** |
| `Backend/api/routers/dashboard.py` | .py | 73 | 2.2 KB | Exposes REST endpoints for dashboard domain | **Active** |
| `Backend/api/routers/departments.py` | .py | 284 | 11.0 KB | Exposes REST endpoints for departments domain | **Active** |
| `Backend/api/routers/feedback.py` | .py | 243 | 7.6 KB | Exposes REST endpoints for feedback domain | **Active** |
| `Backend/api/routers/issues.py` | .py | 64 | 1.9 KB | Exposes REST endpoints for issues domain | **Active** |
| `Backend/api/routers/locations.py` | .py | 471 | 18.8 KB | Exposes REST endpoints for locations domain | **Active** |
| `Backend/api/routers/lost_found.py` | .py | 453 | 16.3 KB | Exposes REST endpoints for lost_found domain | **Active** |
| `Backend/api/routers/master.py` | .py | 25 | 826 B | Exposes REST endpoints for master domain | **Active** |
| `Backend/api/routers/notifications.py` | .py | 243 | 8.0 KB | Exposes REST endpoints for notifications domain | **Active** |
| `Backend/api/routers/platform.py` | .py | 130 | 4.5 KB | Exposes REST endpoints for platform domain | **Active** |
| `Backend/api/routers/programs.py` | .py | 50 | 1.6 KB | Exposes REST endpoints for programs domain | **Active** |
| `Backend/api/routers/public_complaints.py` | .py | 92 | 3.3 KB | Exposes REST endpoints for public_complaints domain | **Active** |
| `Backend/api/routers/reports.py` | .py | 324 | 10.4 KB | Exposes REST endpoints for reports domain | **Active** |
| `Backend/api/routers/search.py` | .py | 124 | 3.8 KB | Exposes REST endpoints for search domain | **Active** |
| `Backend/api/routers/settings.py` | .py | 430 | 14.9 KB | Exposes REST endpoints for settings domain | **Active** |
| `Backend/api/routers/supervisor.py` | .py | 109 | 3.7 KB | Exposes REST endpoints for supervisor domain | **Active** |
| `Backend/api/routers/users.py` | .py | 797 | 30.5 KB | Exposes REST endpoints for users domain | **Active** |
| `Backend/api/routers/__init__.py` | .py | 1 | 2 B | Exposes REST endpoints for __init__ domain | **Active** |
| `Backend/logs/application.log` | .log | 150350 | 18.5 MB | Application configuration or script | **Config** |
| `Backend/middleware/rate_limiter.py` | .py | 107 | 3.5 KB | Application configuration or script | **Config** |
| `Backend/middleware/__init__.py` | .py | 1 | 22 B | Application configuration or script | **Config** |
| `Backend/models/administrator.py` | .py | 9 | 213 B | Domain model & validation schema for administrator | **Active** |
| `Backend/models/app_manager.py` | .py | 9 | 208 B | Domain model & validation schema for app_manager | **Active** |
| `Backend/models/complaint.py` | .py | 170 | 6.4 KB | Domain model & validation schema for complaint | **Active** |
| `Backend/models/coordinator.py` | .py | 9 | 209 B | Domain model & validation schema for coordinator | **Active** |
| `Backend/models/department.py` | .py | 56 | 1.7 KB | Domain model & validation schema for department | **Active** |
| `Backend/models/location.py` | .py | 105 | 3.0 KB | Domain model & validation schema for location | **Active** |
| `Backend/models/location_in_charge.py` | .py | 9 | 221 B | Domain model & validation schema for location_in_charge | **Active** |
| `Backend/models/student.py` | .py | 9 | 201 B | Domain model & validation schema for student | **Active** |
| `Backend/models/user.py` | .py | 188 | 6.9 KB | Domain model & validation schema for user | **Active** |
| `Backend/models/__init__.py` | .py | 1 | 2 B | Domain model & validation schema for __init__ | **Active** |
| `Backend/scripts/audit_run_summary.json` | .json | 115 | 3.4 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/check_dashboards.py` | .py | 20 | 865 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/check_dept.py` | .py | 16 | 608 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/check_other_tables.py` | .py | 17 | 699 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/check_permanent_entities.py` | .py | 25 | 791 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/check_relations.py` | .py | 22 | 1.0 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/cleanup_interim.py` | .py | 13 | 556 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/cleanup_unwanted_users.py` | .py | 154 | 6.1 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/first_cleanup.py` | .py | 59 | 2.4 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/inspect_all_users.py` | .py | 103 | 3.5 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/inspect_candidate_notifs.py` | .py | 24 | 959 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/inspect_schema.py` | .py | 30 | 895 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/preview_cleanup.py` | .py | 58 | 2.3 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/preview_second_cleanup.py` | .py | 37 | 1.6 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/preview_test_run_artifacts.py` | .py | 28 | 1000 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/print_other_roles.py` | .py | 12 | 607 B | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/run_fresh_tests.py` | .py | 332 | 16.2 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/second_cleanup.py` | .py | 61 | 2.4 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/user_cleanup_summary.json` | .json | 95 | 1.9 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/user_inspection_dump.json` | .json | 1370 | 33.5 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/verify_candidate_test_users.py` | .py | 65 | 2.8 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/verify_final_state.py` | .py | 67 | 2.5 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/scripts/verify_first_cleanup.py` | .py | 39 | 1.2 KB | Database maintenance / seed utility script | **Tooling** |
| `Backend/services/analytics_service.py` | .py | 959 | 42.9 KB | Business logic & SQL persistence for analytics_service | **Active** |
| `Backend/services/announcement_service.py` | .py | 544 | 20.8 KB | Business logic & SQL persistence for announcement_service | **Active** |
| `Backend/services/attachment_service.py` | .py | 159 | 6.2 KB | Business logic & SQL persistence for attachment_service | **Active** |
| `Backend/services/audit_service.py` | .py | 412 | 15.2 KB | Business logic & SQL persistence for audit_service | **Active** |
| `Backend/services/auth_service.py` | .py | 2532 | 116.7 KB | Business logic & SQL persistence for auth_service | **Active** |
| `Backend/services/backup_service.py` | .py | 348 | 12.8 KB | Business logic & SQL persistence for backup_service | **Active** |
| `Backend/services/chat_service.py` | .py | 336 | 13.9 KB | Business logic & SQL persistence for chat_service | **Active** |
| `Backend/services/classification_service.py` | .py | 204 | 7.9 KB | Business logic & SQL persistence for classification_service | **Active** |
| `Backend/services/comment_service.py` | .py | 61 | 2.0 KB | Business logic & SQL persistence for comment_service | **Active** |
| `Backend/services/complaint_service.py` | .py | 809 | 33.7 KB | Business logic & SQL persistence for complaint_service | **Active** |
| `Backend/services/config_service.py` | .py | 695 | 19.9 KB | Business logic & SQL persistence for config_service | **Active** |
| `Backend/services/dashboard_service.py` | .py | 367 | 16.9 KB | Business logic & SQL persistence for dashboard_service | **Active** |
| `Backend/services/department_service.py` | .py | 201 | 8.2 KB | Business logic & SQL persistence for department_service | **Active** |
| `Backend/services/dependency_service.py` | .py | 36 | 1.4 KB | Business logic & SQL persistence for dependency_service | **Active** |
| `Backend/services/feedback_service.py` | .py | 498 | 20.0 KB | Business logic & SQL persistence for feedback_service | **Active** |
| `Backend/services/global_search_service.py` | .py | 397 | 17.3 KB | Business logic & SQL persistence for global_search_service | **Active** |
| `Backend/services/location_service.py` | .py | 121 | 5.2 KB | Business logic & SQL persistence for location_service | **Active** |
| `Backend/services/lost_found_service.py` | .py | 932 | 35.8 KB | Business logic & SQL persistence for lost_found_service | **Active** |
| `Backend/services/master_service.py` | .py | 56 | 2.5 KB | Business logic & SQL persistence for master_service | **Active** |
| `Backend/services/notification_service.py` | .py | 602 | 24.2 KB | Business logic & SQL persistence for notification_service | **Active** |
| `Backend/services/platform_service.py` | .py | 294 | 11.4 KB | Business logic & SQL persistence for platform_service | **Active** |
| `Backend/services/program_service.py` | .py | 88 | 3.6 KB | Business logic & SQL persistence for program_service | **Active** |
| `Backend/services/public_complaint_service.py` | .py | 161 | 7.9 KB | Business logic & SQL persistence for public_complaint_service | **Active** |
| `Backend/services/report_service.py` | .py | 697 | 31.0 KB | Business logic & SQL persistence for report_service | **Active** |
| `Backend/services/scheduler_service.py` | .py | 111 | 3.8 KB | Business logic & SQL persistence for scheduler_service | **Active** |
| `Backend/services/validation_service.py` | .py | 37 | 1.8 KB | Business logic & SQL persistence for validation_service | **Active** |
| `Backend/services/__init__.py` | .py | 1 | 2 B | Business logic & SQL persistence for __init__ | **Active** |
| `Backend/services/domain/duplicate_detection_service.py` | .py | 44 | 1.5 KB | Business logic & SQL persistence for duplicate_detection_service | **Active** |
| `Backend/services/domain/file_storage_service.py` | .py | 35 | 1.6 KB | Business logic & SQL persistence for file_storage_service | **Active** |
| `Backend/services/domain/matching_service.py` | .py | 48 | 1.9 KB | Business logic & SQL persistence for matching_service | **Active** |
| `Backend/services/domain/sla_service.py` | .py | 28 | 1.1 KB | Business logic & SQL persistence for sla_service | **Active** |
| `Backend/services/domain/__init__.py` | .py | 1 | 27 B | Business logic & SQL persistence for __init__ | **Active** |
| `Backend/storage/campus_pulse.db` | .db | 26556 | 8.8 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/campus_pulse_audit_baseline.db` | .db | 24529 | 7.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/campus_pulse_backup_pre_scope_baseline_20260813_195935.db` | .db | 12877 | 4.9 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/campus_pulse_backup_pre_superadmin.db` | .db | 21573 | 6.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/pytest_isolated.db` | .db | 26567 | 8.8 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/sqlite_repository.py` | .py | 3907 | 172.8 KB | Application configuration or script | **Config** |
| `Backend/storage/attachments/complaint_CMP-006390AA_additional_ATT-C0FC614A.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-00730FA3_additional_ATT-26936B3B.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-021B6A6A_additional_ATT-CC5700A8.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-03F79FD3_additional_ATT-DBE91803.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-07045D9B_before_1.jpg` | .jpg | 1 | 17 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-10CB0A82_additional_ATT-A39B9A49.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-19455093_additional_ATT-0C1FE7F1.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-19A2A10C_additional_ATT-BC52D39F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-1AA7A74C_additional_ATT-35003CF7.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-1BBC68B2_additional_ATT-270885BE.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-1E13E720_additional_ATT-88EAF964.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-25ACDCCD_additional_ATT-674B1176.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-294BEC19_additional_ATT-B7AE9282.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-2C5845FA_additional_ATT-B4ED4E5A.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-2EC1B544_additional_ATT-3276D3DC.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-2F266386_additional_ATT-9FD387B8.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-36851857_additional_ATT-6276F87E.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-36F9A657_additional_ATT-3231D140.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-39CDCB33_additional_ATT-75484B6A.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-3F7088A2_additional_ATT-0A05778F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-4073B115_additional_ATT-7964010A.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-41823E8D_additional_ATT-95D5AC9F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-473D677E_additional_ATT-B637BE54.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-489DF10C_additional_ATT-97A4DDC0.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-4CC39C5B_additional_ATT-F7C9B242.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-4F16F65B_additional_ATT-AFC5CC52.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-54F7C882_additional_ATT-54C9CDD2.jpg` | .jpg | 1 | 9 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-5518C7F5_additional_ATT-03E9C55A.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-55D02930_additional_ATT-20BC52B7.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-5BD30334_additional_ATT-9758A56A.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-5C5BFA2E_additional_ATT-758FEF4F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-5F938C38_additional_ATT-8E8D7BAF.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-62708087_additional_ATT-B0A61D31.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-64F2F65A_additional_ATT-174AEC5B.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-65587267_additional_ATT-F7416CFF.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-65B7FA05_additional_ATT-25C0A759.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-69B95907_additional_ATT-56C0F5C2.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-6C69002E_additional_ATT-099B044B.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-6D36A91C_additional_ATT-D799EDFD.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-6ED79E6C_additional_ATT-641D1BF1.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-76BF6665_additional_ATT-FC5B95B5.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-773AD27A_additional_ATT-6E9BE534.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-788EEAAE_additional_ATT-139C528F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-7DED7E3F_additional_ATT-50CFAD43.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-7F15CC1F_additional_ATT-37D6967D.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-7F4AC77D_additional_ATT-7F298A25.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-813B5E74_additional_ATT-8905B58C.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-81E4264C_additional_ATT-A875A6C6.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-8684052F_additional_ATT-DE8AE3A2.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-8AD32CB2_additional_ATT-AF28BF26.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-8DE472E1_additional_ATT-D50E446C.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-8FC51A0A_additional_ATT-4818F432.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-90A8BB1F_additional_ATT-91C045F1.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-94B46FFF_additional_ATT-148C0021.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-9BBADC86_after_repair_ATT-86E228EE.png` | .png | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-9C9893EE_additional_ATT-5014DBA9.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-9CA2A2F7_additional_ATT-D0216B3A.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-A06987D5_additional_ATT-06F7A5DF.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-A33EA1A6_additional_ATT-F85FD00C.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-AA91F796_additional_ATT-6657563B.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-AABE7D2B_additional_ATT-DC1AD001.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-AC2DFE2A_additional_ATT-F8DC2267.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-B1DBF80E_additional_ATT-2034299F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-BB419EFF_additional_ATT-6C7E7A5D.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-BC2429E2_additional_ATT-69363F42.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-BD4BCF33_additional_ATT-B43A021E.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-BDE14F0E_additional_ATT-63D2F1EF.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-BF94B8E9_additional_ATT-877792E2.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-C6A3977D_additional_ATT-8D4AF28F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-C74DB009_additional_ATT-82DC5051.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-C94CBD0D_additional_ATT-4C2A3CE3.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-CB4FF33B_additional_ATT-9BDAE4E2.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-CBBED864_additional_ATT-808B0E82.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-CD683AFF_additional_ATT-1A598990.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-CE604271_additional_ATT-CFE8D75B.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-CF6D09A7_additional_ATT-6EF72ECF.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-D40917DC_additional_ATT-83B7EE40.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-D41FE4B6_additional_ATT-19971D14.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-D9569D81_additional_ATT-951C2A09.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-D97E94DC_additional_ATT-9FC3175D.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-DDFA5EB6_additional_ATT-6C9FF9F0.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-E18D6F9B_additional_ATT-DB86D65F.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-E48EA261_additional_ATT-1328339B.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-E59C69A4_additional_ATT-264F4494.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-E5C32B0D_additional_ATT-B5813948.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-E684CBA9_additional_ATT-2063D4F2.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EADC4A32_additional_ATT-2DCA7743.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EB3BE10E_additional_ATT-86EE7083.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-05729DFE.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-0FE00299.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-2A46B37A.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-30921C0F.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-438773C0.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-4782043A.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-4FA1ABFA.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-5A0C6FCE.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-5F3E68F4.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-63C0B2C3.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-683984B1.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-68D3BC59.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-776D1490.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-8DC460E1.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A2F0C2BD.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A472EE4E.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A7B46AC3.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A82FFAD8.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-B0E47751.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-D0D53CCF.png` | .png | 1 | 4 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-ED71F66F_additional_ATT-CF084E45.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-F346592A_additional_ATT-961CA471.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/complaint_CMP-F590544A_additional_ATT-EA6957E0.jpg` | .jpg | 1 | 9 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/doc_7f7fd1af01df4102.pdf` | .pdf | 1 | 41 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/documents/Campus_Pulse_IT_Security_Policy_v1.pdf` | .pdf | 1 | 74 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/audit_report_20261007_221926_RPT-5414C4E7.csv` | .csv | 501 | 48.1 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_180909_RPT-C4016439.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_181818_RPT-8F8F03B2.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_182135_RPT-1CFBAA54.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_183657_RPT-A65F773A.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_183749_RPT-FD83C98C.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_184108_RPT-A41663FD.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_184241_RPT-B637E21C.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_184506_RPT-0515B29F.csv` | .csv | 74 | 7.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_190540_RPT-5AE20ECB.csv` | .csv | 9 | 898 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_192742_RPT-06F15F80.csv` | .csv | 9 | 898 B | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/attachments/reports/complaint_report_20261011_195154_RPT-AFE89501.csv` | .csv | 13 | 1.3 KB | Binary media attachment / evidence file | **Asset** |
| `Backend/storage/backups/CampusPulse_Full_System_Backup_v1.db` | .db | 2991 | 2.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/campus_pulse_backup_pre_stage5_20260815_162700.db` | .db | 14371 | 4.9 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/campus_pulse_pre_cleanup_backup_20261011_185028.db` | .db | 26749 | 8.8 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/campus_pulse_pre_user_cleanup_backup_20261011_191943.db` | .db | 26516 | 8.8 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_160253.db` | .db | 28350 | 8.2 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_160510.db` | .db | 28351 | 8.2 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_160628.db` | .db | 28408 | 8.2 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_233701.db` | .db | 28643 | 8.3 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_233945.db` | .db | 28643 | 8.3 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_235021.db` | .db | 28628 | 8.3 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_235604.db` | .db | 28641 | 8.3 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_235703.db` | .db | 28627 | 8.3 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260922_235839.db` | .db | 28627 | 8.3 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_000019.db` | .db | 29141 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_010935.db` | .db | 29189 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_010938.db` | .db | 29191 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_184708.db` | .db | 29180 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_184713.db` | .db | 29183 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_190249.db` | .db | 29212 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_190252.db` | .db | 29206 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_195603.db` | .db | 29228 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_195607.db` | .db | 29224 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_200945.db` | .db | 29251 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_200950.db` | .db | 29254 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_201047.db` | .db | 29214 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_202446.db` | .db | 29182 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_203954.db` | .db | 29201 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_204040.db` | .db | 29254 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_204047.db` | .db | 29292 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_204202.db` | .db | 29248 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_204208.db` | .db | 29281 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_210544.db` | .db | 29198 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_210549.db` | .db | 29259 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260923_210620.db` | .db | 29243 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260924_000742.db` | .db | 29274 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260924_000802.db` | .db | 29273 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260924_000808.db` | .db | 29389 | 8.5 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260924_001115.db` | .db | 29288 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260924_001122.db` | .db | 29350 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20260924_001158.db` | .db | 29310 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_134144_BKP-5FA1B2B6.db` | .db | 23320 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_134405_BKP-ADF14292.db` | .db | 23314 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_134641_BKP-ABAD9972.db` | .db | 23213 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_141542_BKP-6BED7FF1.db` | .db | 23327 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_141807_BKP-0700D3BB.db` | .db | 23266 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_145432_BKP-749621BB.db` | .db | 23234 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_145704_BKP-6E584582.db` | .db | 23252 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_145935_BKP-3C22724A.db` | .db | 23204 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_151555_BKP-4600A498.db` | .db | 23221 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_151654_BKP-F05DEC9B.db` | .db | 23131 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_151812_BKP-C093D354.db` | .db | 23255 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_152438_BKP-F659A629.db` | .db | 23214 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_203018_BKP-CDEC9FA5.db` | .db | 23577 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_203909_BKP-707AFF8B.db` | .db | 24242 | 8.1 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_203956_BKP-7B256B7D.db` | .db | 24677 | 8.3 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_204102_BKP-93835A95.db` | .db | 25165 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_204202_BKP-564871AB.db` | .db | 25467 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_204216_BKP-EF134F3A.db` | .db | 25652 | 8.5 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_204431_BKP-163A9244.db` | .db | 26139 | 8.6 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_212022_BKP-1202D0C7.db` | .db | 25940 | 8.6 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_212236_BKP-0B519135.db` | .db | 25977 | 8.6 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_212249_BKP-A95E1B4B.db` | .db | 26238 | 8.6 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_212454_BKP-F9430EBB.db` | .db | 27308 | 8.8 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_221917_BKP-EA8DA638.db` | .db | 25931 | 8.6 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_222057_BKP-06BEC92E.db` | .db | 25962 | 8.6 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261007_222312_BKP-64C117AE.db` | .db | 26717 | 8.7 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261011_172917_BKP-CE9E28EB.db` | .db | 26971 | 8.8 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/full_backup_20261011_173215_BKP-7B328E1A.db` | .db | 27581 | 9.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/pre_announcement_cleanup_20261007_124940.db` | .db | 23128 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/pre_fk_cleanup_20260928_181037.db` | .db | 23166 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/pre_test_complaint_cleanup_20261007_125002.db` | .db | 23128 | 8.0 MB | SQLite persistence database file | **Storage** |
| `Backend/storage/backups/pre_user_cleanup_20260924_232015.db` | .db | 29187 | 8.4 MB | SQLite persistence database file | **Storage** |
| `Backend/tests/conftest.py` | .py | 41 | 1.3 KB | Automated test suite verifying conftest | **Test** |
| `Backend/tests/e2e_workflow_test.py` | .py | 532 | 17.7 KB | Automated test suite verifying e2e_workflow_test | **Test** |
| `Backend/tests/run_all_tests.py` | .py | 55 | 2.3 KB | Automated test suite verifying run_all_tests | **Test** |
| `Backend/tests/smoke_test.py` | .py | 135 | 4.6 KB | Automated test suite verifying smoke_test | **Test** |
| `Backend/tests/test_attachment_security.py` | .py | 68 | 2.6 KB | Automated test suite verifying test_attachment_security | **Test** |
| `Backend/tests/test_audit_logs.py` | .py | 31 | 1.0 KB | Automated test suite verifying test_audit_logs | **Test** |
| `Backend/tests/test_chat.py` | .py | 118 | 3.7 KB | Automated test suite verifying test_chat | **Test** |
| `Backend/tests/test_concurrency.py` | .py | 63 | 2.0 KB | Automated test suite verifying test_concurrency | **Test** |
| `Backend/tests/test_directive_features.py` | .py | 211 | 7.9 KB | Automated test suite verifying test_directive_features | **Test** |
| `Backend/tests/test_password_persistence_regression.py` | .py | 401 | 14.1 KB | Automated test suite verifying test_password_persistence_regression | **Test** |
| `Backend/tests/test_personal_chat.py` | .py | 204 | 7.3 KB | Automated test suite verifying test_personal_chat | **Test** |
| `Backend/tests/test_role_location_assignment.py` | .py | 421 | 15.8 KB | Automated test suite verifying test_role_location_assignment | **Test** |
| `Backend/tests/test_security_audit_suite.py` | .py | 1035 | 46.7 KB | Automated test suite verifying test_security_audit_suite | **Test** |
| `Backend/tests/test_user_lifecycle_location_recyclebin.py` | .py | 260 | 9.2 KB | Automated test suite verifying test_user_lifecycle_location_recyclebin | **Test** |
| `Backend/tests/test_workflow10_reports.py` | .py | 64 | 2.1 KB | Automated test suite verifying test_workflow10_reports | **Test** |
| `Backend/tests/test_workflow11_audit.py` | .py | 57 | 1.9 KB | Automated test suite verifying test_workflow11_audit | **Test** |
| `Backend/tests/test_workflow12_settings.py` | .py | 62 | 2.2 KB | Automated test suite verifying test_workflow12_settings | **Test** |
| `Backend/tests/test_workflow13_database.py` | .py | 42 | 1.3 KB | Automated test suite verifying test_workflow13_database | **Test** |
| `Backend/tests/test_workflow14_api_standards.py` | .py | 38 | 1.1 KB | Automated test suite verifying test_workflow14_api_standards | **Test** |
| `Backend/tests/test_workflow15_architecture.py` | .py | 38 | 1.4 KB | Automated test suite verifying test_workflow15_architecture | **Test** |
| `Backend/tests/test_workflow16_super_admin.py` | .py | 213 | 8.2 KB | Automated test suite verifying test_workflow16_super_admin | **Test** |
| `Backend/tests/test_workflow1_auth.py` | .py | 107 | 4.2 KB | Automated test suite verifying test_workflow1_auth | **Test** |
| `Backend/tests/test_workflow2_user_management.py` | .py | 148 | 5.3 KB | Automated test suite verifying test_workflow2_user_management | **Test** |
| `Backend/tests/test_workflow4_complaint_management.py` | .py | 244 | 9.6 KB | Automated test suite verifying test_workflow4_complaint_management | **Test** |
| `Backend/tests/test_workflow5_public_complaints.py` | .py | 99 | 4.0 KB | Automated test suite verifying test_workflow5_public_complaints | **Test** |
| `Backend/tests/test_workflow6_lost_found.py` | .py | 237 | 9.1 KB | Automated test suite verifying test_workflow6_lost_found | **Test** |
| `Backend/tests/test_workflow7_notifications.py` | .py | 87 | 3.0 KB | Automated test suite verifying test_workflow7_notifications | **Test** |
| `Backend/tests/test_workflow7_workload_resolved.py` | .py | 109 | 4.2 KB | Automated test suite verifying test_workflow7_workload_resolved | **Test** |
| `Backend/tests/test_workflow8_announcements.py` | .py | 180 | 6.8 KB | Automated test suite verifying test_workflow8_announcements | **Test** |
| `Backend/tests/test_workflow8_lost_found_deletion_cascade.py` | .py | 101 | 4.3 KB | Automated test suite verifying test_workflow8_lost_found_deletion_cascade | **Test** |
| `Backend/tests/test_workflow9_dashboard.py` | .py | 108 | 4.3 KB | Automated test suite verifying test_workflow9_dashboard | **Test** |
| `Backend/utils/db.py` | .py | 25 | 739 B | Application configuration or script | **Config** |
| `Backend/utils/email.py` | .py | 147 | 6.0 KB | Application configuration or script | **Config** |
| `Backend/utils/excel_importer.py` | .py | 234 | 9.5 KB | Application configuration or script | **Config** |
| `Backend/utils/helper.py` | .py | 33 | 743 B | Application configuration or script | **Config** |
| `Backend/utils/logger.py` | .py | 34 | 883 B | Application configuration or script | **Config** |
| `Backend/utils/pagination.py` | .py | 21 | 660 B | Application configuration or script | **Config** |
| `Backend/utils/passwords.py` | .py | 65 | 2.1 KB | Application configuration or script | **Config** |
| `Backend/utils/response.py` | .py | 20 | 658 B | Application configuration or script | **Config** |
| `Backend/utils/validation.py` | .py | 31 | 747 B | Application configuration or script | **Config** |
| `Backend/utils/websocket_manager.py` | .py | 94 | 3.8 KB | Application configuration or script | **Config** |
| `Backend/utils/__init__.py` | .py | 1 | 2 B | Application configuration or script | **Config** |
| `docs/TENANT_ISOLATION_ARCHITECTURE.md` | .md | 51 | 3.4 KB | Project documentation & architectural guide | **Docs** |
| `docs/WORKFLOW_DIAGRAMS.md` | .md | 382 | 14.6 KB | Project documentation & architectural guide | **Docs** |
| `Frontend/.dockerignore` | (no ext) | 6 | 53 B | Application configuration or script | **Config** |
| `Frontend/.env.example` | .example | 3 | 113 B | Application configuration or script | **Config** |
| `Frontend/Dockerfile` | (no ext) | 18 | 533 B | Application configuration or script | **Config** |
| `Frontend/eslint.config.js` | .js | 21 | 354 B | Application configuration or script | **Config** |
| `Frontend/index.html` | .html | 12 | 300 B | Application configuration or script | **Config** |
| `Frontend/package-lock.json` | .json | 5329 | 175.8 KB | Application configuration or script | **Config** |
| `Frontend/package.json` | .json | 35 | 866 B | Application configuration or script | **Config** |
| `Frontend/postcss.config.js` | .js | 6 | 98 B | Application configuration or script | **Config** |
| `Frontend/tailwind.config.js` | .js | 35 | 979 B | Application configuration or script | **Config** |
| `Frontend/vite.config.js` | .js | 10 | 202 B | Application configuration or script | **Config** |
| `Frontend/src/App.jsx` | .jsx | 5 | 112 B | Root React application container & provider shell | **Active** |
| `Frontend/src/index.css` | .css | 146 | 3.1 KB | Application configuration or script | **Config** |
| `Frontend/src/main.jsx` | .jsx | 19 | 560 B | React 19 DOM bootstrap & root mounting | **Active** |
| `Frontend/src/api/axios.js` | .js | 61 | 1.9 KB | Application configuration or script | **Config** |
| `Frontend/src/components/Badge.jsx` | .jsx | 26 | 1.3 KB | Reusable UI component (Badge) | **Active** |
| `Frontend/src/components/Button.jsx` | .jsx | 50 | 2.3 KB | Reusable UI component (Button) | **Active** |
| `Frontend/src/components/Card.jsx` | .jsx | 15 | 589 B | Reusable UI component (Card) | **Active** |
| `Frontend/src/components/ChatWindow.jsx` | .jsx | 150 | 4.7 KB | Reusable UI component (ChatWindow) | **Active** |
| `Frontend/src/components/ConfirmDialog.jsx` | .jsx | 26 | 709 B | Reusable UI component (ConfirmDialog) | **Active** |
| `Frontend/src/components/DashboardChart.jsx` | .jsx | 181 | 4.4 KB | Reusable UI component (DashboardChart) | **Active** |
| `Frontend/src/components/EmptyState.jsx` | .jsx | 38 | 1.4 KB | Reusable UI component (EmptyState) | **Active** |
| `Frontend/src/components/Input.jsx` | .jsx | 70 | 2.8 KB | Reusable UI component (Input) | **Active** |
| `Frontend/src/components/Loader.jsx` | .jsx | 25 | 1.2 KB | Reusable UI component (Loader) | **Active** |
| `Frontend/src/components/Modal.jsx` | .jsx | 54 | 2.3 KB | Reusable UI component (Modal) | **Active** |
| `Frontend/src/components/PageHeader.jsx` | .jsx | 19 | 709 B | Reusable UI component (PageHeader) | **Active** |
| `Frontend/src/components/SearchBar.jsx` | .jsx | 15 | 554 B | Reusable UI component (SearchBar) | **Active** |
| `Frontend/src/components/Select.jsx` | .jsx | 30 | 1.3 KB | Reusable UI component (Select) | **Active** |
| `Frontend/src/components/StatCard.jsx` | .jsx | 46 | 1.6 KB | Reusable UI component (StatCard) | **Active** |
| `Frontend/src/components/Table.jsx` | .jsx | 164 | 6.9 KB | Reusable UI component (Table) | **Active** |
| `Frontend/src/components/TableToolbar.jsx` | .jsx | 62 | 2.0 KB | Reusable UI component (TableToolbar) | **Active** |
| `Frontend/src/components/Textarea.jsx` | .jsx | 28 | 1.1 KB | Reusable UI component (Textarea) | **Active** |
| `Frontend/src/components/Toast.jsx` | .jsx | 29 | 1.4 KB | Reusable UI component (Toast) | **Active** |
| `Frontend/src/context/AuthContext.jsx` | .jsx | 219 | 6.3 KB | Application configuration or script | **Config** |
| `Frontend/src/context/ThemeContext.jsx` | .jsx | 94 | 2.7 KB | Application configuration or script | **Config** |
| `Frontend/src/hooks/useAsyncData.js` | .js | 26 | 728 B | Application configuration or script | **Config** |
| `Frontend/src/layouts/Footer.jsx` | .jsx | 47 | 1.6 KB | Application shell layout (Footer) | **Active** |
| `Frontend/src/layouts/MainLayout.jsx` | .jsx | 26 | 973 B | Application shell layout (MainLayout) | **Active** |
| `Frontend/src/layouts/Navbar.jsx` | .jsx | 547 | 22.8 KB | Application shell layout (Navbar) | **Active** |
| `Frontend/src/layouts/Sidebar.jsx` | .jsx | 412 | 14.9 KB | Application shell layout (Sidebar) | **Active** |
| `Frontend/src/pages/AccessDeniedPage.jsx` | .jsx | 31 | 1.2 KB | React view component rendering AccessDeniedPage UI | **Active** |
| `Frontend/src/pages/AnalyticsPage.jsx` | .jsx | 530 | 19.8 KB | React view component rendering AnalyticsPage UI | **Active** |
| `Frontend/src/pages/AnnouncementPage.jsx` | .jsx | 745 | 28.2 KB | React view component rendering AnnouncementPage UI | **Active** |
| `Frontend/src/pages/BackupManagementPage.jsx` | .jsx | 500 | 17.8 KB | React view component rendering BackupManagementPage UI | **Active** |
| `Frontend/src/pages/FeedbackPage.jsx` | .jsx | 522 | 19.2 KB | React view component rendering FeedbackPage UI | **Active** |
| `Frontend/src/pages/GlobalSearchPage.jsx` | .jsx | 443 | 15.9 KB | React view component rendering GlobalSearchPage UI | **Active** |
| `Frontend/src/pages/LostFoundPage.jsx` | .jsx | 680 | 25.6 KB | React view component rendering LostFoundPage UI | **Active** |
| `Frontend/src/pages/NotFoundPage.jsx` | .jsx | 31 | 1.2 KB | React view component rendering NotFoundPage UI | **Active** |
| `Frontend/src/pages/NotificationsPage.jsx` | .jsx | 616 | 25.1 KB | React view component rendering NotificationsPage UI | **Active** |
| `Frontend/src/pages/ProfilePage.jsx` | .jsx | 505 | 20.2 KB | React view component rendering ProfilePage UI | **Active** |
| `Frontend/src/pages/ReportsPage.jsx` | .jsx | 307 | 11.0 KB | React view component rendering ReportsPage UI | **Active** |
| `Frontend/src/pages/admin/AdminDashboard.jsx` | .jsx | 318 | 12.3 KB | React view component rendering AdminDashboard UI | **Active** |
| `Frontend/src/pages/admin/AuditLogPage.jsx` | .jsx | 439 | 15.1 KB | React view component rendering AuditLogPage UI | **Active** |
| `Frontend/src/pages/admin/DataCleanupPage.jsx` | .jsx | 497 | 20.1 KB | React view component rendering DataCleanupPage UI | **Active** |
| `Frontend/src/pages/admin/DepartmentManagementPage.jsx` | .jsx | 709 | 23.9 KB | React view component rendering DepartmentManagementPage UI | **Active** |
| `Frontend/src/pages/admin/IssueManagementPage.jsx` | .jsx | 263 | 9.5 KB | React view component rendering IssueManagementPage UI | **Active** |
| `Frontend/src/pages/admin/LocationManagementPage.jsx` | .jsx | 1499 | 47.3 KB | React view component rendering LocationManagementPage UI | **Active** |
| `Frontend/src/pages/admin/SystemSettingsPage.jsx` | .jsx | 420 | 14.0 KB | React view component rendering SystemSettingsPage UI | **Active** |
| `Frontend/src/pages/admin/TechnicalSupportPage.jsx` | .jsx | 207 | 7.7 KB | React view component rendering TechnicalSupportPage UI | **Active** |
| `Frontend/src/pages/admin/UserManagementPage.jsx` | .jsx | 1764 | 77.8 KB | React view component rendering UserManagementPage UI | **Active** |
| `Frontend/src/pages/auth/ActivateAccountPage.jsx` | .jsx | 211 | 8.3 KB | React view component rendering ActivateAccountPage UI | **Active** |
| `Frontend/src/pages/auth/ChangePasswordPage.jsx` | .jsx | 131 | 4.2 KB | React view component rendering ChangePasswordPage UI | **Active** |
| `Frontend/src/pages/auth/ForgotPasswordPage.jsx` | .jsx | 263 | 9.2 KB | React view component rendering ForgotPasswordPage UI | **Active** |
| `Frontend/src/pages/auth/LoginPage.jsx` | .jsx | 186 | 6.9 KB | React view component rendering LoginPage UI | **Active** |
| `Frontend/src/pages/chat/ChatPage.jsx` | .jsx | 672 | 27.8 KB | React view component rendering ChatPage UI | **Active** |
| `Frontend/src/pages/chat/InboxPage.jsx` | .jsx | 58 | 1.7 KB | React view component rendering InboxPage UI | **Active** |
| `Frontend/src/pages/complaints/ComplaintDetailsPage.jsx` | .jsx | 1649 | 65.8 KB | React view component rendering ComplaintDetailsPage UI | **Active** |
| `Frontend/src/pages/complaints/ComplaintListPage.jsx` | .jsx | 809 | 30.2 KB | React view component rendering ComplaintListPage UI | **Active** |
| `Frontend/src/pages/complaints/PublicComplaintsPage.jsx` | .jsx | 1102 | 45.7 KB | React view component rendering PublicComplaintsPage UI | **Active** |
| `Frontend/src/pages/complaints/ResolvedPage.jsx` | .jsx | 331 | 11.7 KB | React view component rendering ResolvedPage UI | **Active** |
| `Frontend/src/pages/complaints/WorkloadPage.jsx` | .jsx | 501 | 18.3 KB | React view component rendering WorkloadPage UI | **Active** |
| `Frontend/src/pages/coordinator/CoordinatorDashboard.jsx` | .jsx | 328 | 12.3 KB | React view component rendering CoordinatorDashboard UI | **Active** |
| `Frontend/src/pages/location/LocationDashboard.jsx` | .jsx | 321 | 12.6 KB | React view component rendering LocationDashboard UI | **Active** |
| `Frontend/src/pages/manager/ManagerDashboard.jsx` | .jsx | 312 | 12.0 KB | React view component rendering ManagerDashboard UI | **Active** |
| `Frontend/src/pages/student/CreateComplaintPage.jsx` | .jsx | 659 | 25.3 KB | React view component rendering CreateComplaintPage UI | **Active** |
| `Frontend/src/pages/student/StudentDashboard.jsx` | .jsx | 323 | 12.1 KB | React view component rendering StudentDashboard UI | **Active** |
| `Frontend/src/pages/superadmin/InstitutionRegistryPage.jsx` | .jsx | 195 | 7.1 KB | React view component rendering InstitutionRegistryPage UI | **Active** |
| `Frontend/src/pages/superadmin/PlatformHealthPage.jsx` | .jsx | 131 | 5.6 KB | React view component rendering PlatformHealthPage UI | **Active** |
| `Frontend/src/pages/superadmin/PlatformSupportPage.jsx` | .jsx | 209 | 7.9 KB | React view component rendering PlatformSupportPage UI | **Active** |
| `Frontend/src/pages/superadmin/SuperAdminDashboard.jsx` | .jsx | 162 | 7.0 KB | React view component rendering SuperAdminDashboard UI | **Active** |
| `Frontend/src/routes/AppRoutes.jsx` | .jsx | 399 | 13.1 KB | React client routing and RBAC guard | **Active** |
| `Frontend/src/routes/ProtectedRoute.jsx` | .jsx | 22 | 793 B | React client routing and RBAC guard | **Active** |
| `Frontend/src/services/analyticsService.js` | .js | 19 | 877 B | Axios HTTP service wrapper for analyticsService | **Active** |
| `Frontend/src/services/announcementService.js` | .js | 37 | 1.6 KB | Axios HTTP service wrapper for announcementService | **Active** |
| `Frontend/src/services/attachmentService.js` | .js | 25 | 866 B | Axios HTTP service wrapper for attachmentService | **Active** |
| `Frontend/src/services/auditService.js` | .js | 18 | 672 B | Axios HTTP service wrapper for auditService | **Active** |
| `Frontend/src/services/authService.js` | .js | 19 | 882 B | Axios HTTP service wrapper for authService | **Active** |
| `Frontend/src/services/backupService.js` | .js | 15 | 733 B | Axios HTTP service wrapper for backupService | **Active** |
| `Frontend/src/services/chatService.js` | .js | 18 | 719 B | Axios HTTP service wrapper for chatService | **Active** |
| `Frontend/src/services/complaintService.js` | .js | 50 | 2.4 KB | Axios HTTP service wrapper for complaintService | **Active** |
| `Frontend/src/services/departmentService.js` | .js | 23 | 1.1 KB | Axios HTTP service wrapper for departmentService | **Active** |
| `Frontend/src/services/feedbackService.js` | .js | 19 | 839 B | Axios HTTP service wrapper for feedbackService | **Active** |
| `Frontend/src/services/locationService.js` | .js | 32 | 1.4 KB | Axios HTTP service wrapper for locationService | **Active** |
| `Frontend/src/services/lostFoundService.js` | .js | 17 | 679 B | Axios HTTP service wrapper for lostFoundService | **Active** |
| `Frontend/src/services/notificationService.js` | .js | 18 | 827 B | Axios HTTP service wrapper for notificationService | **Active** |
| `Frontend/src/services/programService.js` | .js | 7 | 246 B | Axios HTTP service wrapper for programService | **Active** |
| `Frontend/src/services/reportService.js` | .js | 15 | 713 B | Axios HTTP service wrapper for reportService | **Active** |
| `Frontend/src/services/searchService.js` | .js | 15 | 612 B | Axios HTTP service wrapper for searchService | **Active** |
| `Frontend/src/services/settingsService.js` | .js | 21 | 1006 B | Axios HTTP service wrapper for settingsService | **Active** |
| `Frontend/src/services/supervisorService.js` | .js | 5 | 136 B | Axios HTTP service wrapper for supervisorService | **Active** |
| `Frontend/src/services/userService.js` | .js | 49 | 2.0 KB | Axios HTTP service wrapper for userService | **Active** |
| `Frontend/src/utils/constants.js` | .js | 20 | 569 B | Application configuration or script | **Config** |
| `Frontend/src/utils/dateFormatter.js` | .js | 14 | 417 B | Application configuration or script | **Config** |
| `Frontend/src/utils/search.js` | .js | 9 | 244 B | Application configuration or script | **Config** |
| `Frontend/src/utils/statusColor.js` | .js | 34 | 1.2 KB | Application configuration or script | **Config** |
| `Frontend/src/__tests__/App.test.jsx` | .jsx | 14 | 481 B | Application configuration or script | **Config** |
| `Frontend/src/__tests__/Component.test.jsx` | .jsx | 32 | 1.4 KB | Application configuration or script | **Config** |
| `storage/campus_pulse.db` | .db | 8375 | 3.4 MB | SQLite persistence database file | **Storage** |
| `storage/attachments/complaint_CMP-04B62FCE_additional_ATT-F8EDF4A6.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-06742CB8_additional_ATT-978DF55C.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-0F8D3BBE_additional_ATT-B951DCD7.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-15A4D3B3_additional_ATT-E1F1B4A9.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-4C57D5AB_additional_ATT-14A41803.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-8F3281E8_additional_ATT-09AB4619.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-9BC1835B_additional_ATT-BB391BE4.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-B3ED1D39_additional_ATT-64AE0C06.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-C581A968_additional_ATT-110F5422.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-C94A24D5_additional_ATT-B1DB8751.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-CEB79F4D_additional_ATT-85992FFC.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-EBF77BDE_additional_ATT-8C4329F7.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-F44B9F01_additional_ATT-B5E5D5D5.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-FD13B2FB_additional_ATT-B2B99489.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/complaint_CMP-FE6706BA_additional_ATT-C96651C8.jpg` | .jpg | 1 | 11 B | Binary media attachment / evidence file | **Asset** |
| `storage/attachments/documents/Campus_Pulse_IT_Security_Policy_v1.pdf` | .pdf | 1 | 74 B | Binary media attachment / evidence file | **Asset** |
| `storage/backups/CampusPulse_Full_System_Backup_v1.db` | .db | 3320 | 2.6 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_011219_BKP-3A43A644.db` | .db | 23286 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_011243_BKP-65663AC8.db` | .db | 23557 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_011711_BKP-745CA56C.db` | .db | 23288 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_011735_BKP-276BB031.db` | .db | 23570 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012407_BKP-CB2A1656.db` | .db | 23287 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012432_BKP-61F56B7A.db` | .db | 23396 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012612_BKP-C57541F8.db` | .db | 23287 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012647_BKP-54E1CD2C.db` | .db | 23654 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012707_BKP-29A6EB79.db` | .db | 23629 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012734_BKP-22B7DBE2.db` | .db | 23738 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012901_BKP-A1A3D273.db` | .db | 23292 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_012927_BKP-33B0CA66.db` | .db | 23586 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_015428_BKP-B6898655.db` | .db | 23288 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_015455_BKP-0C3F38F5.db` | .db | 23499 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_145226_BKP-F7015641.db` | .db | 23308 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_145252_BKP-89B2EBD5.db` | .db | 23578 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_145611_BKP-6B0701D9.db` | .db | 23313 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260926_145636_BKP-999C4CC7.db` | .db | 23520 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260927_131108_BKP-4C271C51.db` | .db | 23310 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20260927_131241_BKP-2DE4A3E3.db` | .db | 23586 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261005_194224_BKP-D2372B41.db` | .db | 23209 | 8.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261007_150812_BKP-DA803C59.db` | .db | 3897 | 2.7 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261007_152154_BKP-7DB1D875.db` | .db | 5102 | 2.8 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261007_194337_BKP-B9E26B32.db` | .db | 6122 | 3.0 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261007_202518_BKP-8841AF66.db` | .db | 6725 | 3.1 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261007_205812_BKP-CC5C3F1E.db` | .db | 7590 | 3.2 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261007_223837_BKP-4C471D2D.db` | .db | 8127 | 3.4 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261008_110241_BKP-A25D867B.db` | .db | 25928 | 8.6 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261008_110350_BKP-4842A573.db` | .db | 26717 | 8.7 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261008_134056_BKP-D5E5D081.db` | .db | 25893 | 8.6 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261008_134213_BKP-C42568CC.db` | .db | 26731 | 8.7 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261009_010357_BKP-A0828B0F.db` | .db | 26360 | 8.7 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261011_001742_BKP-F78ABE5A.db` | .db | 26291 | 8.7 MB | SQLite persistence database file | **Storage** |
| `storage/backups/full_backup_20261011_014017_BKP-BF920ADE.db` | .db | 26922 | 8.8 MB | SQLite persistence database file | **Storage** |

---
## 3. Detailed File Catalog by Functional Subgroup

### Project Root Configuration & Documentation (14 files)

#### `.gitignore`
- **Filename:** `.gitignore` ((no ext))
- **Lines / Size:** 34 lines (467 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `ADMIN_MANUAL.md`
- **Filename:** `ADMIN_MANUAL.md` (.md)
- **Lines / Size:** 81 lines (4123 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `API_DOCUMENTATION.md`
- **Filename:** `API_DOCUMENTATION.md` (.md)
- **Lines / Size:** 156 lines (6507 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `ARCHITECTURE.md`
- **Filename:** `ARCHITECTURE.md` (.md)
- **Lines / Size:** 57 lines (2721 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `CHANGELOG.md`
- **Filename:** `CHANGELOG.md` (.md)
- **Lines / Size:** 35 lines (1988 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `DATABASE_SCHEMA.md`
- **Filename:** `DATABASE_SCHEMA.md` (.md)
- **Lines / Size:** 120 lines (5929 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `DEPLOYMENT_GUIDE.md`
- **Filename:** `DEPLOYMENT_GUIDE.md` (.md)
- **Lines / Size:** 78 lines (3123 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `docker-compose.yml`
- **Filename:** `docker-compose.yml` (.yml)
- **Lines / Size:** 23 lines (627 bytes)
- **Primary Responsibility:** Containerization and Docker deployment manifest
- **Operational Status:** `DevOps`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `INSTALL.md`
- **Filename:** `INSTALL.md` (.md)
- **Lines / Size:** 5 lines (158 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `README.md`
- **Filename:** `README.md` (.md)
- **Lines / Size:** 90 lines (4160 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `RELEASE_NOTES_v1.0.0.md`
- **Filename:** `RELEASE_NOTES_v1.0.0.md` (.md)
- **Lines / Size:** 62 lines (3687 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `ROLE_PERMISSIONS.md`
- **Filename:** `ROLE_PERMISSIONS.md` (.md)
- **Lines / Size:** 222 lines (9417 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `TEST_CASES.md`
- **Filename:** `TEST_CASES.md` (.md)
- **Lines / Size:** 100 lines (10556 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

#### `Backend/logs/application.log`
- **Filename:** `application.log` (.log)
- **Lines / Size:** 150350 lines (19365057 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Project Root Configuration & Documentation`.

### Backend Application & Entry Points (16 files)

#### `Backend/.dockerignore`
- **Filename:** `.dockerignore` ((no ext))
- **Lines / Size:** 22 lines (305 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/.env`
- **Filename:** `.env` ((no ext))
- **Lines / Size:** 11 lines (263 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/.env.example`
- **Filename:** `.env.example` (.example)
- **Lines / Size:** 18 lines (640 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/Dockerfile`
- **Filename:** `Dockerfile` ((no ext))
- **Lines / Size:** 19 lines (654 bytes)
- **Primary Responsibility:** Containerization and Docker deployment manifest
- **Operational Status:** `DevOps`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/inspect_complaints.py`
- **Filename:** `inspect_complaints.py` (.py)
- **Lines / Size:** 25 lines (1034 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/inspect_db.py`
- **Filename:** `inspect_db.py` (.py)
- **Lines / Size:** 17 lines (494 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/inspect_notifs.py`
- **Filename:** `inspect_notifs.py` (.py)
- **Lines / Size:** 26 lines (1192 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/pytest.ini`
- **Filename:** `pytest.ini` (.ini)
- **Lines / Size:** 9 lines (234 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/README.md`
- **Filename:** `README.md` (.md)
- **Lines / Size:** 65 lines (1977 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/requirements.txt`
- **Filename:** `requirements.txt` (.txt)
- **Lines / Size:** 8 lines (148 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/run_api.py`
- **Filename:** `run_api.py` (.py)
- **Lines / Size:** 23 lines (733 bytes)
- **Primary Responsibility:** Backend server startup entry point
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/api/dependencies.py`
- **Filename:** `dependencies.py` (.py)
- **Lines / Size:** 247 lines (8289 bytes)
- **Primary Responsibility:** Singleton service dependency injection factory
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/api/main.py`
- **Filename:** `main.py` (.py)
- **Lines / Size:** 224 lines (7217 bytes)
- **Primary Responsibility:** FastAPI ASGI application bootstrap & middleware
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/api/schemas.py`
- **Filename:** `schemas.py` (.py)
- **Lines / Size:** 586 lines (16073 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/api/security.py`
- **Filename:** `security.py` (.py)
- **Lines / Size:** 266 lines (8764 bytes)
- **Primary Responsibility:** Authentication dependencies & RBAC enforcement
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

#### `Backend/api/__init__.py`
- **Filename:** `__init__.py` (.py)
- **Lines / Size:** 1 lines (2 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Application & Entry Points`.

### Backend API Routers (25 files)

#### `Backend/api/routers/analytics.py`
- **Filename:** `analytics.py` (.py)
- **Lines / Size:** 142 lines (4958 bytes)
- **Primary Responsibility:** Exposes REST endpoints for analytics domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/announcements.py`
- **Filename:** `announcements.py` (.py)
- **Lines / Size:** 453 lines (15042 bytes)
- **Primary Responsibility:** Exposes REST endpoints for announcements domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/attachments.py`
- **Filename:** `attachments.py` (.py)
- **Lines / Size:** 274 lines (10707 bytes)
- **Primary Responsibility:** Exposes REST endpoints for attachments domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/audit.py`
- **Filename:** `audit.py` (.py)
- **Lines / Size:** 122 lines (3953 bytes)
- **Primary Responsibility:** Exposes REST endpoints for audit domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/auth.py`
- **Filename:** `auth.py` (.py)
- **Lines / Size:** 392 lines (14476 bytes)
- **Primary Responsibility:** Exposes REST endpoints for auth domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/backups.py`
- **Filename:** `backups.py` (.py)
- **Lines / Size:** 137 lines (4379 bytes)
- **Primary Responsibility:** Exposes REST endpoints for backups domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/chat.py`
- **Filename:** `chat.py` (.py)
- **Lines / Size:** 391 lines (14181 bytes)
- **Primary Responsibility:** Exposes REST endpoints for chat domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/complaints.py`
- **Filename:** `complaints.py` (.py)
- **Lines / Size:** 1587 lines (62565 bytes)
- **Primary Responsibility:** Exposes REST endpoints for complaints domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/dashboard.py`
- **Filename:** `dashboard.py` (.py)
- **Lines / Size:** 73 lines (2254 bytes)
- **Primary Responsibility:** Exposes REST endpoints for dashboard domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/departments.py`
- **Filename:** `departments.py` (.py)
- **Lines / Size:** 284 lines (11213 bytes)
- **Primary Responsibility:** Exposes REST endpoints for departments domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/feedback.py`
- **Filename:** `feedback.py` (.py)
- **Lines / Size:** 243 lines (7761 bytes)
- **Primary Responsibility:** Exposes REST endpoints for feedback domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/issues.py`
- **Filename:** `issues.py` (.py)
- **Lines / Size:** 64 lines (1920 bytes)
- **Primary Responsibility:** Exposes REST endpoints for issues domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/locations.py`
- **Filename:** `locations.py` (.py)
- **Lines / Size:** 471 lines (19294 bytes)
- **Primary Responsibility:** Exposes REST endpoints for locations domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/lost_found.py`
- **Filename:** `lost_found.py` (.py)
- **Lines / Size:** 453 lines (16732 bytes)
- **Primary Responsibility:** Exposes REST endpoints for lost_found domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/master.py`
- **Filename:** `master.py` (.py)
- **Lines / Size:** 25 lines (826 bytes)
- **Primary Responsibility:** Exposes REST endpoints for master domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/notifications.py`
- **Filename:** `notifications.py` (.py)
- **Lines / Size:** 243 lines (8213 bytes)
- **Primary Responsibility:** Exposes REST endpoints for notifications domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/platform.py`
- **Filename:** `platform.py` (.py)
- **Lines / Size:** 130 lines (4636 bytes)
- **Primary Responsibility:** Exposes REST endpoints for platform domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/programs.py`
- **Filename:** `programs.py` (.py)
- **Lines / Size:** 50 lines (1621 bytes)
- **Primary Responsibility:** Exposes REST endpoints for programs domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/public_complaints.py`
- **Filename:** `public_complaints.py` (.py)
- **Lines / Size:** 92 lines (3422 bytes)
- **Primary Responsibility:** Exposes REST endpoints for public_complaints domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/reports.py`
- **Filename:** `reports.py` (.py)
- **Lines / Size:** 324 lines (10613 bytes)
- **Primary Responsibility:** Exposes REST endpoints for reports domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/search.py`
- **Filename:** `search.py` (.py)
- **Lines / Size:** 124 lines (3908 bytes)
- **Primary Responsibility:** Exposes REST endpoints for search domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/settings.py`
- **Filename:** `settings.py` (.py)
- **Lines / Size:** 430 lines (15225 bytes)
- **Primary Responsibility:** Exposes REST endpoints for settings domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/supervisor.py`
- **Filename:** `supervisor.py` (.py)
- **Lines / Size:** 109 lines (3776 bytes)
- **Primary Responsibility:** Exposes REST endpoints for supervisor domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/users.py`
- **Filename:** `users.py` (.py)
- **Lines / Size:** 797 lines (31221 bytes)
- **Primary Responsibility:** Exposes REST endpoints for users domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

#### `Backend/api/routers/__init__.py`
- **Filename:** `__init__.py` (.py)
- **Lines / Size:** 1 lines (2 bytes)
- **Primary Responsibility:** Exposes REST endpoints for __init__ domain
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend API Routers`.

### Backend Domain Models (10 files)

#### `Backend/models/administrator.py`
- **Filename:** `administrator.py` (.py)
- **Lines / Size:** 9 lines (213 bytes)
- **Primary Responsibility:** Domain model & validation schema for administrator
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/app_manager.py`
- **Filename:** `app_manager.py` (.py)
- **Lines / Size:** 9 lines (208 bytes)
- **Primary Responsibility:** Domain model & validation schema for app_manager
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/complaint.py`
- **Filename:** `complaint.py` (.py)
- **Lines / Size:** 170 lines (6549 bytes)
- **Primary Responsibility:** Domain model & validation schema for complaint
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/coordinator.py`
- **Filename:** `coordinator.py` (.py)
- **Lines / Size:** 9 lines (209 bytes)
- **Primary Responsibility:** Domain model & validation schema for coordinator
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/department.py`
- **Filename:** `department.py` (.py)
- **Lines / Size:** 56 lines (1768 bytes)
- **Primary Responsibility:** Domain model & validation schema for department
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/location.py`
- **Filename:** `location.py` (.py)
- **Lines / Size:** 105 lines (3065 bytes)
- **Primary Responsibility:** Domain model & validation schema for location
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/location_in_charge.py`
- **Filename:** `location_in_charge.py` (.py)
- **Lines / Size:** 9 lines (221 bytes)
- **Primary Responsibility:** Domain model & validation schema for location_in_charge
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/student.py`
- **Filename:** `student.py` (.py)
- **Lines / Size:** 9 lines (201 bytes)
- **Primary Responsibility:** Domain model & validation schema for student
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/user.py`
- **Filename:** `user.py` (.py)
- **Lines / Size:** 188 lines (7110 bytes)
- **Primary Responsibility:** Domain model & validation schema for user
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

#### `Backend/models/__init__.py`
- **Filename:** `__init__.py` (.py)
- **Lines / Size:** 1 lines (2 bytes)
- **Primary Responsibility:** Domain model & validation schema for __init__
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Domain Models`.

### Backend Business Services (32 files)

#### `Backend/services/analytics_service.py`
- **Filename:** `analytics_service.py` (.py)
- **Lines / Size:** 959 lines (43979 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for analytics_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/announcement_service.py`
- **Filename:** `announcement_service.py` (.py)
- **Lines / Size:** 544 lines (21296 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for announcement_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/attachment_service.py`
- **Filename:** `attachment_service.py` (.py)
- **Lines / Size:** 159 lines (6374 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for attachment_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/audit_service.py`
- **Filename:** `audit_service.py` (.py)
- **Lines / Size:** 412 lines (15516 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for audit_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/auth_service.py`
- **Filename:** `auth_service.py` (.py)
- **Lines / Size:** 2532 lines (119528 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for auth_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/backup_service.py`
- **Filename:** `backup_service.py` (.py)
- **Lines / Size:** 348 lines (13106 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for backup_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/chat_service.py`
- **Filename:** `chat_service.py` (.py)
- **Lines / Size:** 336 lines (14244 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for chat_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/classification_service.py`
- **Filename:** `classification_service.py` (.py)
- **Lines / Size:** 204 lines (8079 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for classification_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/comment_service.py`
- **Filename:** `comment_service.py` (.py)
- **Lines / Size:** 61 lines (2099 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for comment_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/complaint_service.py`
- **Filename:** `complaint_service.py` (.py)
- **Lines / Size:** 809 lines (34556 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for complaint_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/config_service.py`
- **Filename:** `config_service.py` (.py)
- **Lines / Size:** 695 lines (20363 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for config_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/dashboard_service.py`
- **Filename:** `dashboard_service.py` (.py)
- **Lines / Size:** 367 lines (17304 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for dashboard_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/department_service.py`
- **Filename:** `department_service.py` (.py)
- **Lines / Size:** 201 lines (8417 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for department_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/dependency_service.py`
- **Filename:** `dependency_service.py` (.py)
- **Lines / Size:** 36 lines (1434 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for dependency_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/feedback_service.py`
- **Filename:** `feedback_service.py` (.py)
- **Lines / Size:** 498 lines (20433 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for feedback_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/global_search_service.py`
- **Filename:** `global_search_service.py` (.py)
- **Lines / Size:** 397 lines (17685 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for global_search_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/location_service.py`
- **Filename:** `location_service.py` (.py)
- **Lines / Size:** 121 lines (5277 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for location_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/lost_found_service.py`
- **Filename:** `lost_found_service.py` (.py)
- **Lines / Size:** 932 lines (36688 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for lost_found_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/master_service.py`
- **Filename:** `master_service.py` (.py)
- **Lines / Size:** 56 lines (2526 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for master_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/notification_service.py`
- **Filename:** `notification_service.py` (.py)
- **Lines / Size:** 602 lines (24794 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for notification_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/platform_service.py`
- **Filename:** `platform_service.py` (.py)
- **Lines / Size:** 294 lines (11645 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for platform_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/program_service.py`
- **Filename:** `program_service.py` (.py)
- **Lines / Size:** 88 lines (3647 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for program_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/public_complaint_service.py`
- **Filename:** `public_complaint_service.py` (.py)
- **Lines / Size:** 161 lines (8039 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for public_complaint_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/report_service.py`
- **Filename:** `report_service.py` (.py)
- **Lines / Size:** 697 lines (31725 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for report_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/scheduler_service.py`
- **Filename:** `scheduler_service.py` (.py)
- **Lines / Size:** 111 lines (3850 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for scheduler_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/validation_service.py`
- **Filename:** `validation_service.py` (.py)
- **Lines / Size:** 37 lines (1892 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for validation_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/__init__.py`
- **Filename:** `__init__.py` (.py)
- **Lines / Size:** 1 lines (2 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for __init__
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/domain/duplicate_detection_service.py`
- **Filename:** `duplicate_detection_service.py` (.py)
- **Lines / Size:** 44 lines (1503 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for duplicate_detection_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/domain/file_storage_service.py`
- **Filename:** `file_storage_service.py` (.py)
- **Lines / Size:** 35 lines (1679 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for file_storage_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/domain/matching_service.py`
- **Filename:** `matching_service.py` (.py)
- **Lines / Size:** 48 lines (1924 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for matching_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/domain/sla_service.py`
- **Filename:** `sla_service.py` (.py)
- **Lines / Size:** 28 lines (1082 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for sla_service
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

#### `Backend/services/domain/__init__.py`
- **Filename:** `__init__.py` (.py)
- **Lines / Size:** 1 lines (27 bytes)
- **Primary Responsibility:** Business logic & SQL persistence for __init__
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Backend Business Services`.

### Backend Utilities & Middleware (13 files)

#### `Backend/middleware/rate_limiter.py`
- **Filename:** `rate_limiter.py` (.py)
- **Lines / Size:** 107 lines (3576 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/middleware/__init__.py`
- **Filename:** `__init__.py` (.py)
- **Lines / Size:** 1 lines (22 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/db.py`
- **Filename:** `db.py` (.py)
- **Lines / Size:** 25 lines (739 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/email.py`
- **Filename:** `email.py` (.py)
- **Lines / Size:** 147 lines (6183 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/excel_importer.py`
- **Filename:** `excel_importer.py` (.py)
- **Lines / Size:** 234 lines (9720 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/helper.py`
- **Filename:** `helper.py` (.py)
- **Lines / Size:** 33 lines (743 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/logger.py`
- **Filename:** `logger.py` (.py)
- **Lines / Size:** 34 lines (883 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/pagination.py`
- **Filename:** `pagination.py` (.py)
- **Lines / Size:** 21 lines (660 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/passwords.py`
- **Filename:** `passwords.py` (.py)
- **Lines / Size:** 65 lines (2134 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/response.py`
- **Filename:** `response.py` (.py)
- **Lines / Size:** 20 lines (658 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/validation.py`
- **Filename:** `validation.py` (.py)
- **Lines / Size:** 31 lines (747 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/websocket_manager.py`
- **Filename:** `websocket_manager.py` (.py)
- **Lines / Size:** 94 lines (3868 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

#### `Backend/utils/__init__.py`
- **Filename:** `__init__.py` (.py)
- **Lines / Size:** 1 lines (2 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Backend Utilities & Middleware`.

### Backend Automated Test Suites (31 files)

#### `Backend/tests/conftest.py`
- **Filename:** `conftest.py` (.py)
- **Lines / Size:** 41 lines (1287 bytes)
- **Primary Responsibility:** Automated test suite verifying conftest
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/e2e_workflow_test.py`
- **Filename:** `e2e_workflow_test.py` (.py)
- **Lines / Size:** 532 lines (18127 bytes)
- **Primary Responsibility:** Automated test suite verifying e2e_workflow_test
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/run_all_tests.py`
- **Filename:** `run_all_tests.py` (.py)
- **Lines / Size:** 55 lines (2366 bytes)
- **Primary Responsibility:** Automated test suite verifying run_all_tests
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/smoke_test.py`
- **Filename:** `smoke_test.py` (.py)
- **Lines / Size:** 135 lines (4728 bytes)
- **Primary Responsibility:** Automated test suite verifying smoke_test
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_attachment_security.py`
- **Filename:** `test_attachment_security.py` (.py)
- **Lines / Size:** 68 lines (2665 bytes)
- **Primary Responsibility:** Automated test suite verifying test_attachment_security
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_audit_logs.py`
- **Filename:** `test_audit_logs.py` (.py)
- **Lines / Size:** 31 lines (1056 bytes)
- **Primary Responsibility:** Automated test suite verifying test_audit_logs
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_chat.py`
- **Filename:** `test_chat.py` (.py)
- **Lines / Size:** 118 lines (3800 bytes)
- **Primary Responsibility:** Automated test suite verifying test_chat
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_concurrency.py`
- **Filename:** `test_concurrency.py` (.py)
- **Lines / Size:** 63 lines (2099 bytes)
- **Primary Responsibility:** Automated test suite verifying test_concurrency
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_directive_features.py`
- **Filename:** `test_directive_features.py` (.py)
- **Lines / Size:** 211 lines (8071 bytes)
- **Primary Responsibility:** Automated test suite verifying test_directive_features
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_password_persistence_regression.py`
- **Filename:** `test_password_persistence_regression.py` (.py)
- **Lines / Size:** 401 lines (14480 bytes)
- **Primary Responsibility:** Automated test suite verifying test_password_persistence_regression
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_personal_chat.py`
- **Filename:** `test_personal_chat.py` (.py)
- **Lines / Size:** 204 lines (7519 bytes)
- **Primary Responsibility:** Automated test suite verifying test_personal_chat
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_role_location_assignment.py`
- **Filename:** `test_role_location_assignment.py` (.py)
- **Lines / Size:** 421 lines (16220 bytes)
- **Primary Responsibility:** Automated test suite verifying test_role_location_assignment
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_security_audit_suite.py`
- **Filename:** `test_security_audit_suite.py` (.py)
- **Lines / Size:** 1035 lines (47822 bytes)
- **Primary Responsibility:** Automated test suite verifying test_security_audit_suite
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_user_lifecycle_location_recyclebin.py`
- **Filename:** `test_user_lifecycle_location_recyclebin.py` (.py)
- **Lines / Size:** 260 lines (9461 bytes)
- **Primary Responsibility:** Automated test suite verifying test_user_lifecycle_location_recyclebin
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow10_reports.py`
- **Filename:** `test_workflow10_reports.py` (.py)
- **Lines / Size:** 64 lines (2132 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow10_reports
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow11_audit.py`
- **Filename:** `test_workflow11_audit.py` (.py)
- **Lines / Size:** 57 lines (1989 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow11_audit
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow12_settings.py`
- **Filename:** `test_workflow12_settings.py` (.py)
- **Lines / Size:** 62 lines (2205 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow12_settings
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow13_database.py`
- **Filename:** `test_workflow13_database.py` (.py)
- **Lines / Size:** 42 lines (1316 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow13_database
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow14_api_standards.py`
- **Filename:** `test_workflow14_api_standards.py` (.py)
- **Lines / Size:** 38 lines (1104 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow14_api_standards
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow15_architecture.py`
- **Filename:** `test_workflow15_architecture.py` (.py)
- **Lines / Size:** 38 lines (1468 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow15_architecture
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow16_super_admin.py`
- **Filename:** `test_workflow16_super_admin.py` (.py)
- **Lines / Size:** 213 lines (8383 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow16_super_admin
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow1_auth.py`
- **Filename:** `test_workflow1_auth.py` (.py)
- **Lines / Size:** 107 lines (4318 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow1_auth
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow2_user_management.py`
- **Filename:** `test_workflow2_user_management.py` (.py)
- **Lines / Size:** 148 lines (5443 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow2_user_management
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow4_complaint_management.py`
- **Filename:** `test_workflow4_complaint_management.py` (.py)
- **Lines / Size:** 244 lines (9815 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow4_complaint_management
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow5_public_complaints.py`
- **Filename:** `test_workflow5_public_complaints.py` (.py)
- **Lines / Size:** 99 lines (4125 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow5_public_complaints
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow6_lost_found.py`
- **Filename:** `test_workflow6_lost_found.py` (.py)
- **Lines / Size:** 237 lines (9313 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow6_lost_found
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow7_notifications.py`
- **Filename:** `test_workflow7_notifications.py` (.py)
- **Lines / Size:** 87 lines (3081 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow7_notifications
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow7_workload_resolved.py`
- **Filename:** `test_workflow7_workload_resolved.py` (.py)
- **Lines / Size:** 109 lines (4282 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow7_workload_resolved
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow8_announcements.py`
- **Filename:** `test_workflow8_announcements.py` (.py)
- **Lines / Size:** 180 lines (7007 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow8_announcements
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow8_lost_found_deletion_cascade.py`
- **Filename:** `test_workflow8_lost_found_deletion_cascade.py` (.py)
- **Lines / Size:** 101 lines (4397 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow8_lost_found_deletion_cascade
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

#### `Backend/tests/test_workflow9_dashboard.py`
- **Filename:** `test_workflow9_dashboard.py` (.py)
- **Lines / Size:** 108 lines (4409 bytes)
- **Primary Responsibility:** Automated test suite verifying test_workflow9_dashboard
- **Operational Status:** `Test`
- **Architectural Role:** Core component in `Backend Automated Test Suites`.

### Backend Scripts & Maintenance (23 files)

#### `Backend/scripts/audit_run_summary.json`
- **Filename:** `audit_run_summary.json` (.json)
- **Lines / Size:** 115 lines (3442 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/check_dashboards.py`
- **Filename:** `check_dashboards.py` (.py)
- **Lines / Size:** 20 lines (865 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/check_dept.py`
- **Filename:** `check_dept.py` (.py)
- **Lines / Size:** 16 lines (608 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/check_other_tables.py`
- **Filename:** `check_other_tables.py` (.py)
- **Lines / Size:** 17 lines (699 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/check_permanent_entities.py`
- **Filename:** `check_permanent_entities.py` (.py)
- **Lines / Size:** 25 lines (791 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/check_relations.py`
- **Filename:** `check_relations.py` (.py)
- **Lines / Size:** 22 lines (1052 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/cleanup_interim.py`
- **Filename:** `cleanup_interim.py` (.py)
- **Lines / Size:** 13 lines (556 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/cleanup_unwanted_users.py`
- **Filename:** `cleanup_unwanted_users.py` (.py)
- **Lines / Size:** 154 lines (6255 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/first_cleanup.py`
- **Filename:** `first_cleanup.py` (.py)
- **Lines / Size:** 59 lines (2481 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/inspect_all_users.py`
- **Filename:** `inspect_all_users.py` (.py)
- **Lines / Size:** 103 lines (3592 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/inspect_candidate_notifs.py`
- **Filename:** `inspect_candidate_notifs.py` (.py)
- **Lines / Size:** 24 lines (959 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/inspect_schema.py`
- **Filename:** `inspect_schema.py` (.py)
- **Lines / Size:** 30 lines (895 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/preview_cleanup.py`
- **Filename:** `preview_cleanup.py` (.py)
- **Lines / Size:** 58 lines (2372 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/preview_second_cleanup.py`
- **Filename:** `preview_second_cleanup.py` (.py)
- **Lines / Size:** 37 lines (1612 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/preview_test_run_artifacts.py`
- **Filename:** `preview_test_run_artifacts.py` (.py)
- **Lines / Size:** 28 lines (1000 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/print_other_roles.py`
- **Filename:** `print_other_roles.py` (.py)
- **Lines / Size:** 12 lines (607 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/run_fresh_tests.py`
- **Filename:** `run_fresh_tests.py` (.py)
- **Lines / Size:** 332 lines (16547 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/second_cleanup.py`
- **Filename:** `second_cleanup.py` (.py)
- **Lines / Size:** 61 lines (2466 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/user_cleanup_summary.json`
- **Filename:** `user_cleanup_summary.json` (.json)
- **Lines / Size:** 95 lines (1952 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/user_inspection_dump.json`
- **Filename:** `user_inspection_dump.json` (.json)
- **Lines / Size:** 1370 lines (34316 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/verify_candidate_test_users.py`
- **Filename:** `verify_candidate_test_users.py` (.py)
- **Lines / Size:** 65 lines (2904 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/verify_final_state.py`
- **Filename:** `verify_final_state.py` (.py)
- **Lines / Size:** 67 lines (2562 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

#### `Backend/scripts/verify_first_cleanup.py`
- **Filename:** `verify_first_cleanup.py` (.py)
- **Lines / Size:** 39 lines (1261 bytes)
- **Primary Responsibility:** Database maintenance / seed utility script
- **Operational Status:** `Tooling`
- **Architectural Role:** Core component in `Backend Scripts & Maintenance`.

### Frontend Application Entry & Config (16 files)

#### `Frontend/.dockerignore`
- **Filename:** `.dockerignore` ((no ext))
- **Lines / Size:** 6 lines (53 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/.env.example`
- **Filename:** `.env.example` (.example)
- **Lines / Size:** 3 lines (113 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/Dockerfile`
- **Filename:** `Dockerfile` ((no ext))
- **Lines / Size:** 18 lines (533 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/eslint.config.js`
- **Filename:** `eslint.config.js` (.js)
- **Lines / Size:** 21 lines (354 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/index.html`
- **Filename:** `index.html` (.html)
- **Lines / Size:** 12 lines (300 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/package-lock.json`
- **Filename:** `package-lock.json` (.json)
- **Lines / Size:** 5329 lines (180038 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/package.json`
- **Filename:** `package.json` (.json)
- **Lines / Size:** 35 lines (866 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/postcss.config.js`
- **Filename:** `postcss.config.js` (.js)
- **Lines / Size:** 6 lines (98 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/tailwind.config.js`
- **Filename:** `tailwind.config.js` (.js)
- **Lines / Size:** 35 lines (979 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/vite.config.js`
- **Filename:** `vite.config.js` (.js)
- **Lines / Size:** 10 lines (202 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/src/App.jsx`
- **Filename:** `App.jsx` (.jsx)
- **Lines / Size:** 5 lines (112 bytes)
- **Primary Responsibility:** Root React application container & provider shell
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/src/index.css`
- **Filename:** `index.css` (.css)
- **Lines / Size:** 146 lines (3208 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/src/main.jsx`
- **Filename:** `main.jsx` (.jsx)
- **Lines / Size:** 19 lines (560 bytes)
- **Primary Responsibility:** React 19 DOM bootstrap & root mounting
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/src/api/axios.js`
- **Filename:** `axios.js` (.js)
- **Lines / Size:** 61 lines (1996 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/src/__tests__/App.test.jsx`
- **Filename:** `App.test.jsx` (.jsx)
- **Lines / Size:** 14 lines (481 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

#### `Frontend/src/__tests__/Component.test.jsx`
- **Filename:** `Component.test.jsx` (.jsx)
- **Lines / Size:** 32 lines (1412 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Application Entry & Config`.

### Frontend UI Components (18 files)

#### `Frontend/src/components/Badge.jsx`
- **Filename:** `Badge.jsx` (.jsx)
- **Lines / Size:** 26 lines (1339 bytes)
- **Primary Responsibility:** Reusable UI component (Badge)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Button.jsx`
- **Filename:** `Button.jsx` (.jsx)
- **Lines / Size:** 50 lines (2313 bytes)
- **Primary Responsibility:** Reusable UI component (Button)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Card.jsx`
- **Filename:** `Card.jsx` (.jsx)
- **Lines / Size:** 15 lines (589 bytes)
- **Primary Responsibility:** Reusable UI component (Card)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/ChatWindow.jsx`
- **Filename:** `ChatWindow.jsx` (.jsx)
- **Lines / Size:** 150 lines (4769 bytes)
- **Primary Responsibility:** Reusable UI component (ChatWindow)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/ConfirmDialog.jsx`
- **Filename:** `ConfirmDialog.jsx` (.jsx)
- **Lines / Size:** 26 lines (709 bytes)
- **Primary Responsibility:** Reusable UI component (ConfirmDialog)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/DashboardChart.jsx`
- **Filename:** `DashboardChart.jsx` (.jsx)
- **Lines / Size:** 181 lines (4466 bytes)
- **Primary Responsibility:** Reusable UI component (DashboardChart)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/EmptyState.jsx`
- **Filename:** `EmptyState.jsx` (.jsx)
- **Lines / Size:** 38 lines (1406 bytes)
- **Primary Responsibility:** Reusable UI component (EmptyState)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Input.jsx`
- **Filename:** `Input.jsx` (.jsx)
- **Lines / Size:** 70 lines (2861 bytes)
- **Primary Responsibility:** Reusable UI component (Input)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Loader.jsx`
- **Filename:** `Loader.jsx` (.jsx)
- **Lines / Size:** 25 lines (1197 bytes)
- **Primary Responsibility:** Reusable UI component (Loader)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Modal.jsx`
- **Filename:** `Modal.jsx` (.jsx)
- **Lines / Size:** 54 lines (2345 bytes)
- **Primary Responsibility:** Reusable UI component (Modal)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/PageHeader.jsx`
- **Filename:** `PageHeader.jsx` (.jsx)
- **Lines / Size:** 19 lines (709 bytes)
- **Primary Responsibility:** Reusable UI component (PageHeader)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/SearchBar.jsx`
- **Filename:** `SearchBar.jsx` (.jsx)
- **Lines / Size:** 15 lines (554 bytes)
- **Primary Responsibility:** Reusable UI component (SearchBar)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Select.jsx`
- **Filename:** `Select.jsx` (.jsx)
- **Lines / Size:** 30 lines (1283 bytes)
- **Primary Responsibility:** Reusable UI component (Select)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/StatCard.jsx`
- **Filename:** `StatCard.jsx` (.jsx)
- **Lines / Size:** 46 lines (1679 bytes)
- **Primary Responsibility:** Reusable UI component (StatCard)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Table.jsx`
- **Filename:** `Table.jsx` (.jsx)
- **Lines / Size:** 164 lines (7072 bytes)
- **Primary Responsibility:** Reusable UI component (Table)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/TableToolbar.jsx`
- **Filename:** `TableToolbar.jsx` (.jsx)
- **Lines / Size:** 62 lines (2035 bytes)
- **Primary Responsibility:** Reusable UI component (TableToolbar)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Textarea.jsx`
- **Filename:** `Textarea.jsx` (.jsx)
- **Lines / Size:** 28 lines (1146 bytes)
- **Primary Responsibility:** Reusable UI component (Textarea)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

#### `Frontend/src/components/Toast.jsx`
- **Filename:** `Toast.jsx` (.jsx)
- **Lines / Size:** 29 lines (1384 bytes)
- **Primary Responsibility:** Reusable UI component (Toast)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend UI Components`.

### Frontend View Pages (40 files)

#### `Frontend/src/pages/AccessDeniedPage.jsx`
- **Filename:** `AccessDeniedPage.jsx` (.jsx)
- **Lines / Size:** 31 lines (1247 bytes)
- **Primary Responsibility:** React view component rendering AccessDeniedPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/AnalyticsPage.jsx`
- **Filename:** `AnalyticsPage.jsx` (.jsx)
- **Lines / Size:** 530 lines (20320 bytes)
- **Primary Responsibility:** React view component rendering AnalyticsPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/AnnouncementPage.jsx`
- **Filename:** `AnnouncementPage.jsx` (.jsx)
- **Lines / Size:** 745 lines (28927 bytes)
- **Primary Responsibility:** React view component rendering AnnouncementPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/BackupManagementPage.jsx`
- **Filename:** `BackupManagementPage.jsx` (.jsx)
- **Lines / Size:** 500 lines (18263 bytes)
- **Primary Responsibility:** React view component rendering BackupManagementPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/FeedbackPage.jsx`
- **Filename:** `FeedbackPage.jsx` (.jsx)
- **Lines / Size:** 522 lines (19610 bytes)
- **Primary Responsibility:** React view component rendering FeedbackPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/GlobalSearchPage.jsx`
- **Filename:** `GlobalSearchPage.jsx` (.jsx)
- **Lines / Size:** 443 lines (16310 bytes)
- **Primary Responsibility:** React view component rendering GlobalSearchPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/LostFoundPage.jsx`
- **Filename:** `LostFoundPage.jsx` (.jsx)
- **Lines / Size:** 680 lines (26222 bytes)
- **Primary Responsibility:** React view component rendering LostFoundPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/NotFoundPage.jsx`
- **Filename:** `NotFoundPage.jsx` (.jsx)
- **Lines / Size:** 31 lines (1212 bytes)
- **Primary Responsibility:** React view component rendering NotFoundPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/NotificationsPage.jsx`
- **Filename:** `NotificationsPage.jsx` (.jsx)
- **Lines / Size:** 616 lines (25686 bytes)
- **Primary Responsibility:** React view component rendering NotificationsPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/ProfilePage.jsx`
- **Filename:** `ProfilePage.jsx` (.jsx)
- **Lines / Size:** 505 lines (20671 bytes)
- **Primary Responsibility:** React view component rendering ProfilePage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/ReportsPage.jsx`
- **Filename:** `ReportsPage.jsx` (.jsx)
- **Lines / Size:** 307 lines (11314 bytes)
- **Primary Responsibility:** React view component rendering ReportsPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/AdminDashboard.jsx`
- **Filename:** `AdminDashboard.jsx` (.jsx)
- **Lines / Size:** 318 lines (12587 bytes)
- **Primary Responsibility:** React view component rendering AdminDashboard UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/AuditLogPage.jsx`
- **Filename:** `AuditLogPage.jsx` (.jsx)
- **Lines / Size:** 439 lines (15451 bytes)
- **Primary Responsibility:** React view component rendering AuditLogPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/DataCleanupPage.jsx`
- **Filename:** `DataCleanupPage.jsx` (.jsx)
- **Lines / Size:** 497 lines (20546 bytes)
- **Primary Responsibility:** React view component rendering DataCleanupPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/DepartmentManagementPage.jsx`
- **Filename:** `DepartmentManagementPage.jsx` (.jsx)
- **Lines / Size:** 709 lines (24451 bytes)
- **Primary Responsibility:** React view component rendering DepartmentManagementPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/IssueManagementPage.jsx`
- **Filename:** `IssueManagementPage.jsx` (.jsx)
- **Lines / Size:** 263 lines (9779 bytes)
- **Primary Responsibility:** React view component rendering IssueManagementPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/LocationManagementPage.jsx`
- **Filename:** `LocationManagementPage.jsx` (.jsx)
- **Lines / Size:** 1499 lines (48447 bytes)
- **Primary Responsibility:** React view component rendering LocationManagementPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/SystemSettingsPage.jsx`
- **Filename:** `SystemSettingsPage.jsx` (.jsx)
- **Lines / Size:** 420 lines (14382 bytes)
- **Primary Responsibility:** React view component rendering SystemSettingsPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/TechnicalSupportPage.jsx`
- **Filename:** `TechnicalSupportPage.jsx` (.jsx)
- **Lines / Size:** 207 lines (7898 bytes)
- **Primary Responsibility:** React view component rendering TechnicalSupportPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/admin/UserManagementPage.jsx`
- **Filename:** `UserManagementPage.jsx` (.jsx)
- **Lines / Size:** 1764 lines (79653 bytes)
- **Primary Responsibility:** React view component rendering UserManagementPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/auth/ActivateAccountPage.jsx`
- **Filename:** `ActivateAccountPage.jsx` (.jsx)
- **Lines / Size:** 211 lines (8469 bytes)
- **Primary Responsibility:** React view component rendering ActivateAccountPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/auth/ChangePasswordPage.jsx`
- **Filename:** `ChangePasswordPage.jsx` (.jsx)
- **Lines / Size:** 131 lines (4335 bytes)
- **Primary Responsibility:** React view component rendering ChangePasswordPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/auth/ForgotPasswordPage.jsx`
- **Filename:** `ForgotPasswordPage.jsx` (.jsx)
- **Lines / Size:** 263 lines (9416 bytes)
- **Primary Responsibility:** React view component rendering ForgotPasswordPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/auth/LoginPage.jsx`
- **Filename:** `LoginPage.jsx` (.jsx)
- **Lines / Size:** 186 lines (7048 bytes)
- **Primary Responsibility:** React view component rendering LoginPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/chat/ChatPage.jsx`
- **Filename:** `ChatPage.jsx` (.jsx)
- **Lines / Size:** 672 lines (28445 bytes)
- **Primary Responsibility:** React view component rendering ChatPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/chat/InboxPage.jsx`
- **Filename:** `InboxPage.jsx` (.jsx)
- **Lines / Size:** 58 lines (1700 bytes)
- **Primary Responsibility:** React view component rendering InboxPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/complaints/ComplaintDetailsPage.jsx`
- **Filename:** `ComplaintDetailsPage.jsx` (.jsx)
- **Lines / Size:** 1649 lines (67348 bytes)
- **Primary Responsibility:** React view component rendering ComplaintDetailsPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/complaints/ComplaintListPage.jsx`
- **Filename:** `ComplaintListPage.jsx` (.jsx)
- **Lines / Size:** 809 lines (30874 bytes)
- **Primary Responsibility:** React view component rendering ComplaintListPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/complaints/PublicComplaintsPage.jsx`
- **Filename:** `PublicComplaintsPage.jsx` (.jsx)
- **Lines / Size:** 1102 lines (46784 bytes)
- **Primary Responsibility:** React view component rendering PublicComplaintsPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/complaints/ResolvedPage.jsx`
- **Filename:** `ResolvedPage.jsx` (.jsx)
- **Lines / Size:** 331 lines (12004 bytes)
- **Primary Responsibility:** React view component rendering ResolvedPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/complaints/WorkloadPage.jsx`
- **Filename:** `WorkloadPage.jsx` (.jsx)
- **Lines / Size:** 501 lines (18746 bytes)
- **Primary Responsibility:** React view component rendering WorkloadPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/coordinator/CoordinatorDashboard.jsx`
- **Filename:** `CoordinatorDashboard.jsx` (.jsx)
- **Lines / Size:** 328 lines (12622 bytes)
- **Primary Responsibility:** React view component rendering CoordinatorDashboard UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/location/LocationDashboard.jsx`
- **Filename:** `LocationDashboard.jsx` (.jsx)
- **Lines / Size:** 321 lines (12945 bytes)
- **Primary Responsibility:** React view component rendering LocationDashboard UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/manager/ManagerDashboard.jsx`
- **Filename:** `ManagerDashboard.jsx` (.jsx)
- **Lines / Size:** 312 lines (12319 bytes)
- **Primary Responsibility:** React view component rendering ManagerDashboard UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/student/CreateComplaintPage.jsx`
- **Filename:** `CreateComplaintPage.jsx` (.jsx)
- **Lines / Size:** 659 lines (25930 bytes)
- **Primary Responsibility:** React view component rendering CreateComplaintPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/student/StudentDashboard.jsx`
- **Filename:** `StudentDashboard.jsx` (.jsx)
- **Lines / Size:** 323 lines (12397 bytes)
- **Primary Responsibility:** React view component rendering StudentDashboard UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/superadmin/InstitutionRegistryPage.jsx`
- **Filename:** `InstitutionRegistryPage.jsx` (.jsx)
- **Lines / Size:** 195 lines (7306 bytes)
- **Primary Responsibility:** React view component rendering InstitutionRegistryPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/superadmin/PlatformHealthPage.jsx`
- **Filename:** `PlatformHealthPage.jsx` (.jsx)
- **Lines / Size:** 131 lines (5773 bytes)
- **Primary Responsibility:** React view component rendering PlatformHealthPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/superadmin/PlatformSupportPage.jsx`
- **Filename:** `PlatformSupportPage.jsx` (.jsx)
- **Lines / Size:** 209 lines (8127 bytes)
- **Primary Responsibility:** React view component rendering PlatformSupportPage UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

#### `Frontend/src/pages/superadmin/SuperAdminDashboard.jsx`
- **Filename:** `SuperAdminDashboard.jsx` (.jsx)
- **Lines / Size:** 162 lines (7145 bytes)
- **Primary Responsibility:** React view component rendering SuperAdminDashboard UI
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend View Pages`.

### Frontend API Services (19 files)

#### `Frontend/src/services/analyticsService.js`
- **Filename:** `analyticsService.js` (.js)
- **Lines / Size:** 19 lines (877 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for analyticsService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/announcementService.js`
- **Filename:** `announcementService.js` (.js)
- **Lines / Size:** 37 lines (1669 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for announcementService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/attachmentService.js`
- **Filename:** `attachmentService.js` (.js)
- **Lines / Size:** 25 lines (866 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for attachmentService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/auditService.js`
- **Filename:** `auditService.js` (.js)
- **Lines / Size:** 18 lines (672 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for auditService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/authService.js`
- **Filename:** `authService.js` (.js)
- **Lines / Size:** 19 lines (882 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for authService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/backupService.js`
- **Filename:** `backupService.js` (.js)
- **Lines / Size:** 15 lines (733 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for backupService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/chatService.js`
- **Filename:** `chatService.js` (.js)
- **Lines / Size:** 18 lines (719 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for chatService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/complaintService.js`
- **Filename:** `complaintService.js` (.js)
- **Lines / Size:** 50 lines (2496 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for complaintService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/departmentService.js`
- **Filename:** `departmentService.js` (.js)
- **Lines / Size:** 23 lines (1118 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for departmentService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/feedbackService.js`
- **Filename:** `feedbackService.js` (.js)
- **Lines / Size:** 19 lines (839 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for feedbackService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/locationService.js`
- **Filename:** `locationService.js` (.js)
- **Lines / Size:** 32 lines (1452 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for locationService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/lostFoundService.js`
- **Filename:** `lostFoundService.js` (.js)
- **Lines / Size:** 17 lines (679 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for lostFoundService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/notificationService.js`
- **Filename:** `notificationService.js` (.js)
- **Lines / Size:** 18 lines (827 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for notificationService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/programService.js`
- **Filename:** `programService.js` (.js)
- **Lines / Size:** 7 lines (246 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for programService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/reportService.js`
- **Filename:** `reportService.js` (.js)
- **Lines / Size:** 15 lines (713 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for reportService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/searchService.js`
- **Filename:** `searchService.js` (.js)
- **Lines / Size:** 15 lines (612 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for searchService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/settingsService.js`
- **Filename:** `settingsService.js` (.js)
- **Lines / Size:** 21 lines (1006 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for settingsService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/supervisorService.js`
- **Filename:** `supervisorService.js` (.js)
- **Lines / Size:** 5 lines (136 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for supervisorService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

#### `Frontend/src/services/userService.js`
- **Filename:** `userService.js` (.js)
- **Lines / Size:** 49 lines (2098 bytes)
- **Primary Responsibility:** Axios HTTP service wrapper for userService
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend API Services`.

### Frontend Routing & Layouts (6 files)

#### `Frontend/src/layouts/Footer.jsx`
- **Filename:** `Footer.jsx` (.jsx)
- **Lines / Size:** 47 lines (1670 bytes)
- **Primary Responsibility:** Application shell layout (Footer)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Routing & Layouts`.

#### `Frontend/src/layouts/MainLayout.jsx`
- **Filename:** `MainLayout.jsx` (.jsx)
- **Lines / Size:** 26 lines (973 bytes)
- **Primary Responsibility:** Application shell layout (MainLayout)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Routing & Layouts`.

#### `Frontend/src/layouts/Navbar.jsx`
- **Filename:** `Navbar.jsx` (.jsx)
- **Lines / Size:** 547 lines (23297 bytes)
- **Primary Responsibility:** Application shell layout (Navbar)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Routing & Layouts`.

#### `Frontend/src/layouts/Sidebar.jsx`
- **Filename:** `Sidebar.jsx` (.jsx)
- **Lines / Size:** 412 lines (15274 bytes)
- **Primary Responsibility:** Application shell layout (Sidebar)
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Routing & Layouts`.

#### `Frontend/src/routes/AppRoutes.jsx`
- **Filename:** `AppRoutes.jsx` (.jsx)
- **Lines / Size:** 399 lines (13371 bytes)
- **Primary Responsibility:** React client routing and RBAC guard
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Routing & Layouts`.

#### `Frontend/src/routes/ProtectedRoute.jsx`
- **Filename:** `ProtectedRoute.jsx` (.jsx)
- **Lines / Size:** 22 lines (793 bytes)
- **Primary Responsibility:** React client routing and RBAC guard
- **Operational Status:** `Active`
- **Architectural Role:** Core component in `Frontend Routing & Layouts`.

### Frontend Hooks, Context & Utilities (7 files)

#### `Frontend/src/context/AuthContext.jsx`
- **Filename:** `AuthContext.jsx` (.jsx)
- **Lines / Size:** 219 lines (6458 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Hooks, Context & Utilities`.

#### `Frontend/src/context/ThemeContext.jsx`
- **Filename:** `ThemeContext.jsx` (.jsx)
- **Lines / Size:** 94 lines (2813 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Hooks, Context & Utilities`.

#### `Frontend/src/hooks/useAsyncData.js`
- **Filename:** `useAsyncData.js` (.js)
- **Lines / Size:** 26 lines (728 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Hooks, Context & Utilities`.

#### `Frontend/src/utils/constants.js`
- **Filename:** `constants.js` (.js)
- **Lines / Size:** 20 lines (569 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Hooks, Context & Utilities`.

#### `Frontend/src/utils/dateFormatter.js`
- **Filename:** `dateFormatter.js` (.js)
- **Lines / Size:** 14 lines (417 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Hooks, Context & Utilities`.

#### `Frontend/src/utils/search.js`
- **Filename:** `search.js` (.js)
- **Lines / Size:** 9 lines (244 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Hooks, Context & Utilities`.

#### `Frontend/src/utils/statusColor.js`
- **Filename:** `statusColor.js` (.js)
- **Lines / Size:** 34 lines (1264 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Frontend Hooks, Context & Utilities`.

### Storage & Binary Assets (255 files)

#### `Backend/storage/campus_pulse.db`
- **Filename:** `campus_pulse.db` (.db)
- **Lines / Size:** 26556 lines (9216000 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/campus_pulse_audit_baseline.db`
- **Filename:** `campus_pulse_audit_baseline.db` (.db)
- **Lines / Size:** 24529 lines (7307264 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/campus_pulse_backup_pre_scope_baseline_20260813_195935.db`
- **Filename:** `campus_pulse_backup_pre_scope_baseline_20260813_195935.db` (.db)
- **Lines / Size:** 12877 lines (5181440 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/campus_pulse_backup_pre_superadmin.db`
- **Filename:** `campus_pulse_backup_pre_superadmin.db` (.db)
- **Lines / Size:** 21573 lines (6680576 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/pytest_isolated.db`
- **Filename:** `pytest_isolated.db` (.db)
- **Lines / Size:** 26567 lines (9216000 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/sqlite_repository.py`
- **Filename:** `sqlite_repository.py` (.py)
- **Lines / Size:** 3907 lines (176946 bytes)
- **Primary Responsibility:** Application configuration or script
- **Operational Status:** `Config`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-006390AA_additional_ATT-C0FC614A.jpg`
- **Filename:** `complaint_CMP-006390AA_additional_ATT-C0FC614A.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-00730FA3_additional_ATT-26936B3B.jpg`
- **Filename:** `complaint_CMP-00730FA3_additional_ATT-26936B3B.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-021B6A6A_additional_ATT-CC5700A8.jpg`
- **Filename:** `complaint_CMP-021B6A6A_additional_ATT-CC5700A8.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-03F79FD3_additional_ATT-DBE91803.jpg`
- **Filename:** `complaint_CMP-03F79FD3_additional_ATT-DBE91803.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-07045D9B_before_1.jpg`
- **Filename:** `complaint_CMP-07045D9B_before_1.jpg` (.jpg)
- **Lines / Size:** 1 lines (17 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-10CB0A82_additional_ATT-A39B9A49.jpg`
- **Filename:** `complaint_CMP-10CB0A82_additional_ATT-A39B9A49.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-19455093_additional_ATT-0C1FE7F1.jpg`
- **Filename:** `complaint_CMP-19455093_additional_ATT-0C1FE7F1.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-19A2A10C_additional_ATT-BC52D39F.jpg`
- **Filename:** `complaint_CMP-19A2A10C_additional_ATT-BC52D39F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-1AA7A74C_additional_ATT-35003CF7.jpg`
- **Filename:** `complaint_CMP-1AA7A74C_additional_ATT-35003CF7.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-1BBC68B2_additional_ATT-270885BE.jpg`
- **Filename:** `complaint_CMP-1BBC68B2_additional_ATT-270885BE.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-1E13E720_additional_ATT-88EAF964.jpg`
- **Filename:** `complaint_CMP-1E13E720_additional_ATT-88EAF964.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-25ACDCCD_additional_ATT-674B1176.jpg`
- **Filename:** `complaint_CMP-25ACDCCD_additional_ATT-674B1176.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-294BEC19_additional_ATT-B7AE9282.png`
- **Filename:** `complaint_CMP-294BEC19_additional_ATT-B7AE9282.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-2C5845FA_additional_ATT-B4ED4E5A.jpg`
- **Filename:** `complaint_CMP-2C5845FA_additional_ATT-B4ED4E5A.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-2EC1B544_additional_ATT-3276D3DC.jpg`
- **Filename:** `complaint_CMP-2EC1B544_additional_ATT-3276D3DC.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-2F266386_additional_ATT-9FD387B8.jpg`
- **Filename:** `complaint_CMP-2F266386_additional_ATT-9FD387B8.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-36851857_additional_ATT-6276F87E.jpg`
- **Filename:** `complaint_CMP-36851857_additional_ATT-6276F87E.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-36F9A657_additional_ATT-3231D140.jpg`
- **Filename:** `complaint_CMP-36F9A657_additional_ATT-3231D140.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-39CDCB33_additional_ATT-75484B6A.jpg`
- **Filename:** `complaint_CMP-39CDCB33_additional_ATT-75484B6A.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-3F7088A2_additional_ATT-0A05778F.jpg`
- **Filename:** `complaint_CMP-3F7088A2_additional_ATT-0A05778F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-4073B115_additional_ATT-7964010A.jpg`
- **Filename:** `complaint_CMP-4073B115_additional_ATT-7964010A.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-41823E8D_additional_ATT-95D5AC9F.jpg`
- **Filename:** `complaint_CMP-41823E8D_additional_ATT-95D5AC9F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-473D677E_additional_ATT-B637BE54.jpg`
- **Filename:** `complaint_CMP-473D677E_additional_ATT-B637BE54.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-489DF10C_additional_ATT-97A4DDC0.jpg`
- **Filename:** `complaint_CMP-489DF10C_additional_ATT-97A4DDC0.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-4CC39C5B_additional_ATT-F7C9B242.jpg`
- **Filename:** `complaint_CMP-4CC39C5B_additional_ATT-F7C9B242.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-4F16F65B_additional_ATT-AFC5CC52.jpg`
- **Filename:** `complaint_CMP-4F16F65B_additional_ATT-AFC5CC52.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-54F7C882_additional_ATT-54C9CDD2.jpg`
- **Filename:** `complaint_CMP-54F7C882_additional_ATT-54C9CDD2.jpg` (.jpg)
- **Lines / Size:** 1 lines (9 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-5518C7F5_additional_ATT-03E9C55A.jpg`
- **Filename:** `complaint_CMP-5518C7F5_additional_ATT-03E9C55A.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-55D02930_additional_ATT-20BC52B7.jpg`
- **Filename:** `complaint_CMP-55D02930_additional_ATT-20BC52B7.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-5BD30334_additional_ATT-9758A56A.jpg`
- **Filename:** `complaint_CMP-5BD30334_additional_ATT-9758A56A.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-5C5BFA2E_additional_ATT-758FEF4F.jpg`
- **Filename:** `complaint_CMP-5C5BFA2E_additional_ATT-758FEF4F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-5F938C38_additional_ATT-8E8D7BAF.jpg`
- **Filename:** `complaint_CMP-5F938C38_additional_ATT-8E8D7BAF.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-62708087_additional_ATT-B0A61D31.jpg`
- **Filename:** `complaint_CMP-62708087_additional_ATT-B0A61D31.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-64F2F65A_additional_ATT-174AEC5B.jpg`
- **Filename:** `complaint_CMP-64F2F65A_additional_ATT-174AEC5B.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-65587267_additional_ATT-F7416CFF.jpg`
- **Filename:** `complaint_CMP-65587267_additional_ATT-F7416CFF.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-65B7FA05_additional_ATT-25C0A759.jpg`
- **Filename:** `complaint_CMP-65B7FA05_additional_ATT-25C0A759.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-69B95907_additional_ATT-56C0F5C2.jpg`
- **Filename:** `complaint_CMP-69B95907_additional_ATT-56C0F5C2.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-6C69002E_additional_ATT-099B044B.jpg`
- **Filename:** `complaint_CMP-6C69002E_additional_ATT-099B044B.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-6D36A91C_additional_ATT-D799EDFD.jpg`
- **Filename:** `complaint_CMP-6D36A91C_additional_ATT-D799EDFD.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-6ED79E6C_additional_ATT-641D1BF1.jpg`
- **Filename:** `complaint_CMP-6ED79E6C_additional_ATT-641D1BF1.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-76BF6665_additional_ATT-FC5B95B5.jpg`
- **Filename:** `complaint_CMP-76BF6665_additional_ATT-FC5B95B5.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-773AD27A_additional_ATT-6E9BE534.jpg`
- **Filename:** `complaint_CMP-773AD27A_additional_ATT-6E9BE534.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-788EEAAE_additional_ATT-139C528F.jpg`
- **Filename:** `complaint_CMP-788EEAAE_additional_ATT-139C528F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-7DED7E3F_additional_ATT-50CFAD43.jpg`
- **Filename:** `complaint_CMP-7DED7E3F_additional_ATT-50CFAD43.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-7F15CC1F_additional_ATT-37D6967D.jpg`
- **Filename:** `complaint_CMP-7F15CC1F_additional_ATT-37D6967D.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-7F4AC77D_additional_ATT-7F298A25.jpg`
- **Filename:** `complaint_CMP-7F4AC77D_additional_ATT-7F298A25.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-813B5E74_additional_ATT-8905B58C.jpg`
- **Filename:** `complaint_CMP-813B5E74_additional_ATT-8905B58C.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-81E4264C_additional_ATT-A875A6C6.jpg`
- **Filename:** `complaint_CMP-81E4264C_additional_ATT-A875A6C6.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-8684052F_additional_ATT-DE8AE3A2.jpg`
- **Filename:** `complaint_CMP-8684052F_additional_ATT-DE8AE3A2.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-8AD32CB2_additional_ATT-AF28BF26.jpg`
- **Filename:** `complaint_CMP-8AD32CB2_additional_ATT-AF28BF26.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-8DE472E1_additional_ATT-D50E446C.jpg`
- **Filename:** `complaint_CMP-8DE472E1_additional_ATT-D50E446C.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-8FC51A0A_additional_ATT-4818F432.jpg`
- **Filename:** `complaint_CMP-8FC51A0A_additional_ATT-4818F432.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-90A8BB1F_additional_ATT-91C045F1.png`
- **Filename:** `complaint_CMP-90A8BB1F_additional_ATT-91C045F1.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-94B46FFF_additional_ATT-148C0021.jpg`
- **Filename:** `complaint_CMP-94B46FFF_additional_ATT-148C0021.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-9BBADC86_after_repair_ATT-86E228EE.png`
- **Filename:** `complaint_CMP-9BBADC86_after_repair_ATT-86E228EE.png` (.png)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-9C9893EE_additional_ATT-5014DBA9.jpg`
- **Filename:** `complaint_CMP-9C9893EE_additional_ATT-5014DBA9.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-9CA2A2F7_additional_ATT-D0216B3A.jpg`
- **Filename:** `complaint_CMP-9CA2A2F7_additional_ATT-D0216B3A.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-A06987D5_additional_ATT-06F7A5DF.jpg`
- **Filename:** `complaint_CMP-A06987D5_additional_ATT-06F7A5DF.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-A33EA1A6_additional_ATT-F85FD00C.jpg`
- **Filename:** `complaint_CMP-A33EA1A6_additional_ATT-F85FD00C.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-AA91F796_additional_ATT-6657563B.jpg`
- **Filename:** `complaint_CMP-AA91F796_additional_ATT-6657563B.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-AABE7D2B_additional_ATT-DC1AD001.jpg`
- **Filename:** `complaint_CMP-AABE7D2B_additional_ATT-DC1AD001.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-AC2DFE2A_additional_ATT-F8DC2267.jpg`
- **Filename:** `complaint_CMP-AC2DFE2A_additional_ATT-F8DC2267.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-B1DBF80E_additional_ATT-2034299F.jpg`
- **Filename:** `complaint_CMP-B1DBF80E_additional_ATT-2034299F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-BB419EFF_additional_ATT-6C7E7A5D.jpg`
- **Filename:** `complaint_CMP-BB419EFF_additional_ATT-6C7E7A5D.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-BC2429E2_additional_ATT-69363F42.jpg`
- **Filename:** `complaint_CMP-BC2429E2_additional_ATT-69363F42.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-BD4BCF33_additional_ATT-B43A021E.jpg`
- **Filename:** `complaint_CMP-BD4BCF33_additional_ATT-B43A021E.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-BDE14F0E_additional_ATT-63D2F1EF.jpg`
- **Filename:** `complaint_CMP-BDE14F0E_additional_ATT-63D2F1EF.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-BF94B8E9_additional_ATT-877792E2.jpg`
- **Filename:** `complaint_CMP-BF94B8E9_additional_ATT-877792E2.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-C6A3977D_additional_ATT-8D4AF28F.jpg`
- **Filename:** `complaint_CMP-C6A3977D_additional_ATT-8D4AF28F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-C74DB009_additional_ATT-82DC5051.jpg`
- **Filename:** `complaint_CMP-C74DB009_additional_ATT-82DC5051.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-C94CBD0D_additional_ATT-4C2A3CE3.jpg`
- **Filename:** `complaint_CMP-C94CBD0D_additional_ATT-4C2A3CE3.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-CB4FF33B_additional_ATT-9BDAE4E2.jpg`
- **Filename:** `complaint_CMP-CB4FF33B_additional_ATT-9BDAE4E2.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-CBBED864_additional_ATT-808B0E82.jpg`
- **Filename:** `complaint_CMP-CBBED864_additional_ATT-808B0E82.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-CD683AFF_additional_ATT-1A598990.jpg`
- **Filename:** `complaint_CMP-CD683AFF_additional_ATT-1A598990.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-CE604271_additional_ATT-CFE8D75B.jpg`
- **Filename:** `complaint_CMP-CE604271_additional_ATT-CFE8D75B.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-CF6D09A7_additional_ATT-6EF72ECF.jpg`
- **Filename:** `complaint_CMP-CF6D09A7_additional_ATT-6EF72ECF.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-D40917DC_additional_ATT-83B7EE40.jpg`
- **Filename:** `complaint_CMP-D40917DC_additional_ATT-83B7EE40.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-D41FE4B6_additional_ATT-19971D14.jpg`
- **Filename:** `complaint_CMP-D41FE4B6_additional_ATT-19971D14.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-D9569D81_additional_ATT-951C2A09.jpg`
- **Filename:** `complaint_CMP-D9569D81_additional_ATT-951C2A09.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-D97E94DC_additional_ATT-9FC3175D.jpg`
- **Filename:** `complaint_CMP-D97E94DC_additional_ATT-9FC3175D.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-DDFA5EB6_additional_ATT-6C9FF9F0.jpg`
- **Filename:** `complaint_CMP-DDFA5EB6_additional_ATT-6C9FF9F0.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-E18D6F9B_additional_ATT-DB86D65F.jpg`
- **Filename:** `complaint_CMP-E18D6F9B_additional_ATT-DB86D65F.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-E48EA261_additional_ATT-1328339B.jpg`
- **Filename:** `complaint_CMP-E48EA261_additional_ATT-1328339B.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-E59C69A4_additional_ATT-264F4494.jpg`
- **Filename:** `complaint_CMP-E59C69A4_additional_ATT-264F4494.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-E5C32B0D_additional_ATT-B5813948.jpg`
- **Filename:** `complaint_CMP-E5C32B0D_additional_ATT-B5813948.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-E684CBA9_additional_ATT-2063D4F2.jpg`
- **Filename:** `complaint_CMP-E684CBA9_additional_ATT-2063D4F2.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EADC4A32_additional_ATT-2DCA7743.jpg`
- **Filename:** `complaint_CMP-EADC4A32_additional_ATT-2DCA7743.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EB3BE10E_additional_ATT-86EE7083.jpg`
- **Filename:** `complaint_CMP-EB3BE10E_additional_ATT-86EE7083.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-05729DFE.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-05729DFE.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-0FE00299.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-0FE00299.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-2A46B37A.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-2A46B37A.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-30921C0F.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-30921C0F.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-438773C0.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-438773C0.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-4782043A.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-4782043A.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-4FA1ABFA.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-4FA1ABFA.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-5A0C6FCE.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-5A0C6FCE.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-5F3E68F4.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-5F3E68F4.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-63C0B2C3.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-63C0B2C3.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-683984B1.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-683984B1.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-68D3BC59.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-68D3BC59.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-776D1490.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-776D1490.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-8DC460E1.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-8DC460E1.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A2F0C2BD.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-A2F0C2BD.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A472EE4E.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-A472EE4E.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A7B46AC3.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-A7B46AC3.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-A82FFAD8.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-A82FFAD8.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-B0E47751.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-B0E47751.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-EC921885_additional_ATT-D0D53CCF.png`
- **Filename:** `complaint_CMP-EC921885_additional_ATT-D0D53CCF.png` (.png)
- **Lines / Size:** 1 lines (4 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-ED71F66F_additional_ATT-CF084E45.jpg`
- **Filename:** `complaint_CMP-ED71F66F_additional_ATT-CF084E45.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-F346592A_additional_ATT-961CA471.jpg`
- **Filename:** `complaint_CMP-F346592A_additional_ATT-961CA471.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/complaint_CMP-F590544A_additional_ATT-EA6957E0.jpg`
- **Filename:** `complaint_CMP-F590544A_additional_ATT-EA6957E0.jpg` (.jpg)
- **Lines / Size:** 1 lines (9 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/doc_7f7fd1af01df4102.pdf`
- **Filename:** `doc_7f7fd1af01df4102.pdf` (.pdf)
- **Lines / Size:** 1 lines (41 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/documents/Campus_Pulse_IT_Security_Policy_v1.pdf`
- **Filename:** `Campus_Pulse_IT_Security_Policy_v1.pdf` (.pdf)
- **Lines / Size:** 1 lines (74 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/audit_report_20261007_221926_RPT-5414C4E7.csv`
- **Filename:** `audit_report_20261007_221926_RPT-5414C4E7.csv` (.csv)
- **Lines / Size:** 501 lines (49220 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_180909_RPT-C4016439.csv`
- **Filename:** `complaint_report_20261011_180909_RPT-C4016439.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_181818_RPT-8F8F03B2.csv`
- **Filename:** `complaint_report_20261011_181818_RPT-8F8F03B2.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_182135_RPT-1CFBAA54.csv`
- **Filename:** `complaint_report_20261011_182135_RPT-1CFBAA54.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_183657_RPT-A65F773A.csv`
- **Filename:** `complaint_report_20261011_183657_RPT-A65F773A.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_183749_RPT-FD83C98C.csv`
- **Filename:** `complaint_report_20261011_183749_RPT-FD83C98C.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_184108_RPT-A41663FD.csv`
- **Filename:** `complaint_report_20261011_184108_RPT-A41663FD.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_184241_RPT-B637E21C.csv`
- **Filename:** `complaint_report_20261011_184241_RPT-B637E21C.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_184506_RPT-0515B29F.csv`
- **Filename:** `complaint_report_20261011_184506_RPT-0515B29F.csv` (.csv)
- **Lines / Size:** 74 lines (7492 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_190540_RPT-5AE20ECB.csv`
- **Filename:** `complaint_report_20261011_190540_RPT-5AE20ECB.csv` (.csv)
- **Lines / Size:** 9 lines (898 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_192742_RPT-06F15F80.csv`
- **Filename:** `complaint_report_20261011_192742_RPT-06F15F80.csv` (.csv)
- **Lines / Size:** 9 lines (898 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/attachments/reports/complaint_report_20261011_195154_RPT-AFE89501.csv`
- **Filename:** `complaint_report_20261011_195154_RPT-AFE89501.csv` (.csv)
- **Lines / Size:** 13 lines (1285 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/CampusPulse_Full_System_Backup_v1.db`
- **Filename:** `CampusPulse_Full_System_Backup_v1.db` (.db)
- **Lines / Size:** 2991 lines (2539520 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/campus_pulse_backup_pre_stage5_20260815_162700.db`
- **Filename:** `campus_pulse_backup_pre_stage5_20260815_162700.db` (.db)
- **Lines / Size:** 14371 lines (5181440 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/campus_pulse_pre_cleanup_backup_20261011_185028.db`
- **Filename:** `campus_pulse_pre_cleanup_backup_20261011_185028.db` (.db)
- **Lines / Size:** 26749 lines (9216000 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/campus_pulse_pre_user_cleanup_backup_20261011_191943.db`
- **Filename:** `campus_pulse_pre_user_cleanup_backup_20261011_191943.db` (.db)
- **Lines / Size:** 26516 lines (9216000 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_160253.db`
- **Filename:** `full_backup_20260922_160253.db` (.db)
- **Lines / Size:** 28350 lines (8581120 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_160510.db`
- **Filename:** `full_backup_20260922_160510.db` (.db)
- **Lines / Size:** 28351 lines (8581120 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_160628.db`
- **Filename:** `full_backup_20260922_160628.db` (.db)
- **Lines / Size:** 28408 lines (8634368 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_233701.db`
- **Filename:** `full_backup_20260922_233701.db` (.db)
- **Lines / Size:** 28643 lines (8663040 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_233945.db`
- **Filename:** `full_backup_20260922_233945.db` (.db)
- **Lines / Size:** 28643 lines (8663040 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_235021.db`
- **Filename:** `full_backup_20260922_235021.db` (.db)
- **Lines / Size:** 28628 lines (8654848 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_235604.db`
- **Filename:** `full_backup_20260922_235604.db` (.db)
- **Lines / Size:** 28641 lines (8663040 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_235703.db`
- **Filename:** `full_backup_20260922_235703.db` (.db)
- **Lines / Size:** 28627 lines (8658944 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260922_235839.db`
- **Filename:** `full_backup_20260922_235839.db` (.db)
- **Lines / Size:** 28627 lines (8658944 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_000019.db`
- **Filename:** `full_backup_20260923_000019.db` (.db)
- **Lines / Size:** 29141 lines (8777728 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_010935.db`
- **Filename:** `full_backup_20260923_010935.db` (.db)
- **Lines / Size:** 29189 lines (8818688 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_010938.db`
- **Filename:** `full_backup_20260923_010938.db` (.db)
- **Lines / Size:** 29191 lines (8822784 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_184708.db`
- **Filename:** `full_backup_20260923_184708.db` (.db)
- **Lines / Size:** 29180 lines (8814592 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_184713.db`
- **Filename:** `full_backup_20260923_184713.db` (.db)
- **Lines / Size:** 29183 lines (8818688 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_190249.db`
- **Filename:** `full_backup_20260923_190249.db` (.db)
- **Lines / Size:** 29212 lines (8822784 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_190252.db`
- **Filename:** `full_backup_20260923_190252.db` (.db)
- **Lines / Size:** 29206 lines (8822784 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_195603.db`
- **Filename:** `full_backup_20260923_195603.db` (.db)
- **Lines / Size:** 29228 lines (8822784 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_195607.db`
- **Filename:** `full_backup_20260923_195607.db` (.db)
- **Lines / Size:** 29224 lines (8822784 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_200945.db`
- **Filename:** `full_backup_20260923_200945.db` (.db)
- **Lines / Size:** 29251 lines (8826880 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_200950.db`
- **Filename:** `full_backup_20260923_200950.db` (.db)
- **Lines / Size:** 29254 lines (8826880 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_201047.db`
- **Filename:** `full_backup_20260923_201047.db` (.db)
- **Lines / Size:** 29214 lines (8818688 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_202446.db`
- **Filename:** `full_backup_20260923_202446.db` (.db)
- **Lines / Size:** 29182 lines (8802304 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_203954.db`
- **Filename:** `full_backup_20260923_203954.db` (.db)
- **Lines / Size:** 29201 lines (8822784 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_204040.db`
- **Filename:** `full_backup_20260923_204040.db` (.db)
- **Lines / Size:** 29254 lines (8835072 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_204047.db`
- **Filename:** `full_backup_20260923_204047.db` (.db)
- **Lines / Size:** 29292 lines (8851456 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_204202.db`
- **Filename:** `full_backup_20260923_204202.db` (.db)
- **Lines / Size:** 29248 lines (8835072 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_204208.db`
- **Filename:** `full_backup_20260923_204208.db` (.db)
- **Lines / Size:** 29281 lines (8851456 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_210544.db`
- **Filename:** `full_backup_20260923_210544.db` (.db)
- **Lines / Size:** 29198 lines (8826880 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_210549.db`
- **Filename:** `full_backup_20260923_210549.db` (.db)
- **Lines / Size:** 29259 lines (8847360 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260923_210620.db`
- **Filename:** `full_backup_20260923_210620.db` (.db)
- **Lines / Size:** 29243 lines (8826880 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260924_000742.db`
- **Filename:** `full_backup_20260924_000742.db` (.db)
- **Lines / Size:** 29274 lines (8839168 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260924_000802.db`
- **Filename:** `full_backup_20260924_000802.db` (.db)
- **Lines / Size:** 29273 lines (8839168 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260924_000808.db`
- **Filename:** `full_backup_20260924_000808.db` (.db)
- **Lines / Size:** 29389 lines (8863744 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260924_001115.db`
- **Filename:** `full_backup_20260924_001115.db` (.db)
- **Lines / Size:** 29288 lines (8839168 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260924_001122.db`
- **Filename:** `full_backup_20260924_001122.db` (.db)
- **Lines / Size:** 29350 lines (8859648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20260924_001158.db`
- **Filename:** `full_backup_20260924_001158.db` (.db)
- **Lines / Size:** 29310 lines (8843264 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_134144_BKP-5FA1B2B6.db`
- **Filename:** `full_backup_20261007_134144_BKP-5FA1B2B6.db` (.db)
- **Lines / Size:** 23320 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_134405_BKP-ADF14292.db`
- **Filename:** `full_backup_20261007_134405_BKP-ADF14292.db` (.db)
- **Lines / Size:** 23314 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_134641_BKP-ABAD9972.db`
- **Filename:** `full_backup_20261007_134641_BKP-ABAD9972.db` (.db)
- **Lines / Size:** 23213 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_141542_BKP-6BED7FF1.db`
- **Filename:** `full_backup_20261007_141542_BKP-6BED7FF1.db` (.db)
- **Lines / Size:** 23327 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_141807_BKP-0700D3BB.db`
- **Filename:** `full_backup_20261007_141807_BKP-0700D3BB.db` (.db)
- **Lines / Size:** 23266 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_145432_BKP-749621BB.db`
- **Filename:** `full_backup_20261007_145432_BKP-749621BB.db` (.db)
- **Lines / Size:** 23234 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_145704_BKP-6E584582.db`
- **Filename:** `full_backup_20261007_145704_BKP-6E584582.db` (.db)
- **Lines / Size:** 23252 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_145935_BKP-3C22724A.db`
- **Filename:** `full_backup_20261007_145935_BKP-3C22724A.db` (.db)
- **Lines / Size:** 23204 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_151555_BKP-4600A498.db`
- **Filename:** `full_backup_20261007_151555_BKP-4600A498.db` (.db)
- **Lines / Size:** 23221 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_151654_BKP-F05DEC9B.db`
- **Filename:** `full_backup_20261007_151654_BKP-F05DEC9B.db` (.db)
- **Lines / Size:** 23131 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_151812_BKP-C093D354.db`
- **Filename:** `full_backup_20261007_151812_BKP-C093D354.db` (.db)
- **Lines / Size:** 23255 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_152438_BKP-F659A629.db`
- **Filename:** `full_backup_20261007_152438_BKP-F659A629.db` (.db)
- **Lines / Size:** 23214 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_203018_BKP-CDEC9FA5.db`
- **Filename:** `full_backup_20261007_203018_BKP-CDEC9FA5.db` (.db)
- **Lines / Size:** 23577 lines (8409088 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_203909_BKP-707AFF8B.db`
- **Filename:** `full_backup_20261007_203909_BKP-707AFF8B.db` (.db)
- **Lines / Size:** 24242 lines (8540160 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_203956_BKP-7B256B7D.db`
- **Filename:** `full_backup_20261007_203956_BKP-7B256B7D.db` (.db)
- **Lines / Size:** 24677 lines (8654848 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_204102_BKP-93835A95.db`
- **Filename:** `full_backup_20261007_204102_BKP-93835A95.db` (.db)
- **Lines / Size:** 25165 lines (8781824 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_204202_BKP-564871AB.db`
- **Filename:** `full_backup_20261007_204202_BKP-564871AB.db` (.db)
- **Lines / Size:** 25467 lines (8851456 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_204216_BKP-EF134F3A.db`
- **Filename:** `full_backup_20261007_204216_BKP-EF134F3A.db` (.db)
- **Lines / Size:** 25652 lines (8904704 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_204431_BKP-163A9244.db`
- **Filename:** `full_backup_20261007_204431_BKP-163A9244.db` (.db)
- **Lines / Size:** 26139 lines (8994816 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_212022_BKP-1202D0C7.db`
- **Filename:** `full_backup_20261007_212022_BKP-1202D0C7.db` (.db)
- **Lines / Size:** 25940 lines (8974336 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_212236_BKP-0B519135.db`
- **Filename:** `full_backup_20261007_212236_BKP-0B519135.db` (.db)
- **Lines / Size:** 25977 lines (8978432 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_212249_BKP-A95E1B4B.db`
- **Filename:** `full_backup_20261007_212249_BKP-A95E1B4B.db` (.db)
- **Lines / Size:** 26238 lines (9031680 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_212454_BKP-F9430EBB.db`
- **Filename:** `full_backup_20261007_212454_BKP-F9430EBB.db` (.db)
- **Lines / Size:** 27308 lines (9269248 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_221917_BKP-EA8DA638.db`
- **Filename:** `full_backup_20261007_221917_BKP-EA8DA638.db` (.db)
- **Lines / Size:** 25931 lines (8974336 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_222057_BKP-06BEC92E.db`
- **Filename:** `full_backup_20261007_222057_BKP-06BEC92E.db` (.db)
- **Lines / Size:** 25962 lines (8978432 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261007_222312_BKP-64C117AE.db`
- **Filename:** `full_backup_20261007_222312_BKP-64C117AE.db` (.db)
- **Lines / Size:** 26717 lines (9125888 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261011_172917_BKP-CE9E28EB.db`
- **Filename:** `full_backup_20261011_172917_BKP-CE9E28EB.db` (.db)
- **Lines / Size:** 26971 lines (9265152 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/full_backup_20261011_173215_BKP-7B328E1A.db`
- **Filename:** `full_backup_20261011_173215_BKP-7B328E1A.db` (.db)
- **Lines / Size:** 27581 lines (9412608 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/pre_announcement_cleanup_20261007_124940.db`
- **Filename:** `pre_announcement_cleanup_20261007_124940.db` (.db)
- **Lines / Size:** 23128 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/pre_fk_cleanup_20260928_181037.db`
- **Filename:** `pre_fk_cleanup_20260928_181037.db` (.db)
- **Lines / Size:** 23166 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/pre_test_complaint_cleanup_20261007_125002.db`
- **Filename:** `pre_test_complaint_cleanup_20261007_125002.db` (.db)
- **Lines / Size:** 23128 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `Backend/storage/backups/pre_user_cleanup_20260924_232015.db`
- **Filename:** `pre_user_cleanup_20260924_232015.db` (.db)
- **Lines / Size:** 29187 lines (8851456 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/campus_pulse.db`
- **Filename:** `campus_pulse.db` (.db)
- **Lines / Size:** 8375 lines (3584000 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-04B62FCE_additional_ATT-F8EDF4A6.jpg`
- **Filename:** `complaint_CMP-04B62FCE_additional_ATT-F8EDF4A6.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-06742CB8_additional_ATT-978DF55C.jpg`
- **Filename:** `complaint_CMP-06742CB8_additional_ATT-978DF55C.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-0F8D3BBE_additional_ATT-B951DCD7.jpg`
- **Filename:** `complaint_CMP-0F8D3BBE_additional_ATT-B951DCD7.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-15A4D3B3_additional_ATT-E1F1B4A9.jpg`
- **Filename:** `complaint_CMP-15A4D3B3_additional_ATT-E1F1B4A9.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-4C57D5AB_additional_ATT-14A41803.jpg`
- **Filename:** `complaint_CMP-4C57D5AB_additional_ATT-14A41803.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-8F3281E8_additional_ATT-09AB4619.jpg`
- **Filename:** `complaint_CMP-8F3281E8_additional_ATT-09AB4619.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-9BC1835B_additional_ATT-BB391BE4.jpg`
- **Filename:** `complaint_CMP-9BC1835B_additional_ATT-BB391BE4.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-B3ED1D39_additional_ATT-64AE0C06.jpg`
- **Filename:** `complaint_CMP-B3ED1D39_additional_ATT-64AE0C06.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-C581A968_additional_ATT-110F5422.jpg`
- **Filename:** `complaint_CMP-C581A968_additional_ATT-110F5422.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-C94A24D5_additional_ATT-B1DB8751.jpg`
- **Filename:** `complaint_CMP-C94A24D5_additional_ATT-B1DB8751.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-CEB79F4D_additional_ATT-85992FFC.jpg`
- **Filename:** `complaint_CMP-CEB79F4D_additional_ATT-85992FFC.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-EBF77BDE_additional_ATT-8C4329F7.jpg`
- **Filename:** `complaint_CMP-EBF77BDE_additional_ATT-8C4329F7.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-F44B9F01_additional_ATT-B5E5D5D5.jpg`
- **Filename:** `complaint_CMP-F44B9F01_additional_ATT-B5E5D5D5.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-FD13B2FB_additional_ATT-B2B99489.jpg`
- **Filename:** `complaint_CMP-FD13B2FB_additional_ATT-B2B99489.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/complaint_CMP-FE6706BA_additional_ATT-C96651C8.jpg`
- **Filename:** `complaint_CMP-FE6706BA_additional_ATT-C96651C8.jpg` (.jpg)
- **Lines / Size:** 1 lines (11 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/attachments/documents/Campus_Pulse_IT_Security_Policy_v1.pdf`
- **Filename:** `Campus_Pulse_IT_Security_Policy_v1.pdf` (.pdf)
- **Lines / Size:** 1 lines (74 bytes)
- **Primary Responsibility:** Binary media attachment / evidence file
- **Operational Status:** `Asset`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/CampusPulse_Full_System_Backup_v1.db`
- **Filename:** `CampusPulse_Full_System_Backup_v1.db` (.db)
- **Lines / Size:** 3320 lines (2732032 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_011219_BKP-3A43A644.db`
- **Filename:** `full_backup_20260926_011219_BKP-3A43A644.db` (.db)
- **Lines / Size:** 23286 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_011243_BKP-65663AC8.db`
- **Filename:** `full_backup_20260926_011243_BKP-65663AC8.db` (.db)
- **Lines / Size:** 23557 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_011711_BKP-745CA56C.db`
- **Filename:** `full_backup_20260926_011711_BKP-745CA56C.db` (.db)
- **Lines / Size:** 23288 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_011735_BKP-276BB031.db`
- **Filename:** `full_backup_20260926_011735_BKP-276BB031.db` (.db)
- **Lines / Size:** 23570 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012407_BKP-CB2A1656.db`
- **Filename:** `full_backup_20260926_012407_BKP-CB2A1656.db` (.db)
- **Lines / Size:** 23287 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012432_BKP-61F56B7A.db`
- **Filename:** `full_backup_20260926_012432_BKP-61F56B7A.db` (.db)
- **Lines / Size:** 23396 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012612_BKP-C57541F8.db`
- **Filename:** `full_backup_20260926_012612_BKP-C57541F8.db` (.db)
- **Lines / Size:** 23287 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012647_BKP-54E1CD2C.db`
- **Filename:** `full_backup_20260926_012647_BKP-54E1CD2C.db` (.db)
- **Lines / Size:** 23654 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012707_BKP-29A6EB79.db`
- **Filename:** `full_backup_20260926_012707_BKP-29A6EB79.db` (.db)
- **Lines / Size:** 23629 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012734_BKP-22B7DBE2.db`
- **Filename:** `full_backup_20260926_012734_BKP-22B7DBE2.db` (.db)
- **Lines / Size:** 23738 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012901_BKP-A1A3D273.db`
- **Filename:** `full_backup_20260926_012901_BKP-A1A3D273.db` (.db)
- **Lines / Size:** 23292 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_012927_BKP-33B0CA66.db`
- **Filename:** `full_backup_20260926_012927_BKP-33B0CA66.db` (.db)
- **Lines / Size:** 23586 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_015428_BKP-B6898655.db`
- **Filename:** `full_backup_20260926_015428_BKP-B6898655.db` (.db)
- **Lines / Size:** 23288 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_015455_BKP-0C3F38F5.db`
- **Filename:** `full_backup_20260926_015455_BKP-0C3F38F5.db` (.db)
- **Lines / Size:** 23499 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_145226_BKP-F7015641.db`
- **Filename:** `full_backup_20260926_145226_BKP-F7015641.db` (.db)
- **Lines / Size:** 23308 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_145252_BKP-89B2EBD5.db`
- **Filename:** `full_backup_20260926_145252_BKP-89B2EBD5.db` (.db)
- **Lines / Size:** 23578 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_145611_BKP-6B0701D9.db`
- **Filename:** `full_backup_20260926_145611_BKP-6B0701D9.db` (.db)
- **Lines / Size:** 23313 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260926_145636_BKP-999C4CC7.db`
- **Filename:** `full_backup_20260926_145636_BKP-999C4CC7.db` (.db)
- **Lines / Size:** 23520 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260927_131108_BKP-4C271C51.db`
- **Filename:** `full_backup_20260927_131108_BKP-4C271C51.db` (.db)
- **Lines / Size:** 23310 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20260927_131241_BKP-2DE4A3E3.db`
- **Filename:** `full_backup_20260927_131241_BKP-2DE4A3E3.db` (.db)
- **Lines / Size:** 23586 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261005_194224_BKP-D2372B41.db`
- **Filename:** `full_backup_20261005_194224_BKP-D2372B41.db` (.db)
- **Lines / Size:** 23209 lines (8347648 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261007_150812_BKP-DA803C59.db`
- **Filename:** `full_backup_20261007_150812_BKP-DA803C59.db` (.db)
- **Lines / Size:** 3897 lines (2818048 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261007_152154_BKP-7DB1D875.db`
- **Filename:** `full_backup_20261007_152154_BKP-7DB1D875.db` (.db)
- **Lines / Size:** 5102 lines (2981888 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261007_194337_BKP-B9E26B32.db`
- **Filename:** `full_backup_20261007_194337_BKP-B9E26B32.db` (.db)
- **Lines / Size:** 6122 lines (3145728 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261007_202518_BKP-8841AF66.db`
- **Filename:** `full_backup_20261007_202518_BKP-8841AF66.db` (.db)
- **Lines / Size:** 6725 lines (3264512 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261007_205812_BKP-CC5C3F1E.db`
- **Filename:** `full_backup_20261007_205812_BKP-CC5C3F1E.db` (.db)
- **Lines / Size:** 7590 lines (3383296 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261007_223837_BKP-4C471D2D.db`
- **Filename:** `full_backup_20261007_223837_BKP-4C471D2D.db` (.db)
- **Lines / Size:** 8127 lines (3514368 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261008_110241_BKP-A25D867B.db`
- **Filename:** `full_backup_20261008_110241_BKP-A25D867B.db` (.db)
- **Lines / Size:** 25928 lines (8978432 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261008_110350_BKP-4842A573.db`
- **Filename:** `full_backup_20261008_110350_BKP-4842A573.db` (.db)
- **Lines / Size:** 26717 lines (9134080 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261008_134056_BKP-D5E5D081.db`
- **Filename:** `full_backup_20261008_134056_BKP-D5E5D081.db` (.db)
- **Lines / Size:** 25893 lines (8974336 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261008_134213_BKP-C42568CC.db`
- **Filename:** `full_backup_20261008_134213_BKP-C42568CC.db` (.db)
- **Lines / Size:** 26731 lines (9129984 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261009_010357_BKP-A0828B0F.db`
- **Filename:** `full_backup_20261009_010357_BKP-A0828B0F.db` (.db)
- **Lines / Size:** 26360 lines (9109504 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261011_001742_BKP-F78ABE5A.db`
- **Filename:** `full_backup_20261011_001742_BKP-F78ABE5A.db` (.db)
- **Lines / Size:** 26291 lines (9129984 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

#### `storage/backups/full_backup_20261011_014017_BKP-BF920ADE.db`
- **Filename:** `full_backup_20261011_014017_BKP-BF920ADE.db` (.db)
- **Lines / Size:** 26922 lines (9240576 bytes)
- **Primary Responsibility:** SQLite persistence database file
- **Operational Status:** `Storage`
- **Architectural Role:** Core component in `Storage & Binary Assets`.

### Documentation Directory (2 files)

#### `docs/TENANT_ISOLATION_ARCHITECTURE.md`
- **Filename:** `TENANT_ISOLATION_ARCHITECTURE.md` (.md)
- **Lines / Size:** 51 lines (3527 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Documentation Directory`.

#### `docs/WORKFLOW_DIAGRAMS.md`
- **Filename:** `WORKFLOW_DIAGRAMS.md` (.md)
- **Lines / Size:** 382 lines (14985 bytes)
- **Primary Responsibility:** Project documentation & architectural guide
- **Operational Status:** `Docs`
- **Architectural Role:** Core component in `Documentation Directory`.


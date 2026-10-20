import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./ProtectedRoute.jsx";
import Loader from "../components/Loader.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { ROLES } from "../utils/constants";

// Lazy-loaded page components for route-level code splitting
const LoginPage = lazy(() => import("../pages/auth/LoginPage.jsx"));
const ForgotPasswordPage = lazy(() => import("../pages/auth/ForgotPasswordPage.jsx"));
const ActivateAccountPage = lazy(() => import("../pages/auth/ActivateAccountPage.jsx"));
const ChangePasswordPage = lazy(() => import("../pages/auth/ChangePasswordPage.jsx"));
const ProfilePage = lazy(() => import("../pages/ProfilePage.jsx"));
const StudentDashboard = lazy(() => import("../pages/student/StudentDashboard.jsx"));
const CreateComplaintPage = lazy(() => import("../pages/student/CreateComplaintPage.jsx"));
const ComplaintListPage = lazy(() => import("../pages/complaints/ComplaintListPage.jsx"));
const PublicComplaintsPage = lazy(() => import("../pages/complaints/PublicComplaintsPage.jsx"));
const ComplaintDetailsPage = lazy(() => import("../pages/complaints/ComplaintDetailsPage.jsx"));
const CoordinatorDashboard = lazy(() => import("../pages/coordinator/CoordinatorDashboard.jsx"));
const LocationDashboard = lazy(() => import("../pages/location/LocationDashboard.jsx"));
const ManagerDashboard = lazy(() => import("../pages/manager/ManagerDashboard.jsx"));
const AdminDashboard = lazy(() => import("../pages/admin/AdminDashboard.jsx"));
const UserManagementPage = lazy(() => import("../pages/admin/UserManagementPage.jsx"));
const DepartmentManagementPage = lazy(() => import("../pages/admin/DepartmentManagementPage.jsx"));
const LocationManagementPage = lazy(() => import("../pages/admin/LocationManagementPage.jsx"));
const IssueManagementPage = lazy(() => import("../pages/admin/IssueManagementPage.jsx"));
const DataCleanupPage = lazy(() => import("../pages/admin/DataCleanupPage.jsx"));
const SystemSettingsPage = lazy(() => import("../pages/admin/SystemSettingsPage.jsx"));
const AuditLogPage = lazy(() => import("../pages/admin/AuditLogPage.jsx"));
const NotificationsPage = lazy(() => import("../pages/NotificationsPage.jsx"));
const ChatPage = lazy(() => import("../pages/chat/ChatPage.jsx"));
const InboxPage = lazy(() => import("../pages/chat/InboxPage.jsx"));
const AnalyticsPage = lazy(() => import("../pages/AnalyticsPage.jsx"));
const AccessDeniedPage = lazy(() => import("../pages/AccessDeniedPage.jsx"));
const NotFoundPage = lazy(() => import("../pages/NotFoundPage.jsx"));
const LostFoundPage = lazy(() => import("../pages/LostFoundPage.jsx"));
const AnnouncementPage = lazy(() => import("../pages/AnnouncementPage.jsx"));
const FeedbackPage = lazy(() => import("../pages/FeedbackPage.jsx"));
const ReportsPage = lazy(() => import("../pages/ReportsPage.jsx"));
const GlobalSearchPage = lazy(() => import("../pages/GlobalSearchPage.jsx"));
const BackupManagementPage = lazy(() => import("../pages/BackupManagementPage.jsx"));
const SuperAdminDashboard = lazy(() => import("../pages/superadmin/SuperAdminDashboard.jsx"));
const InstitutionRegistryPage = lazy(() => import("../pages/superadmin/InstitutionRegistryPage.jsx"));
const PlatformSupportPage = lazy(() => import("../pages/superadmin/PlatformSupportPage.jsx"));
const PlatformHealthPage = lazy(() => import("../pages/superadmin/PlatformHealthPage.jsx"));
const TechnicalSupportPage = lazy(() => import("../pages/admin/TechnicalSupportPage.jsx"));
const WorkloadPage = lazy(() => import("../pages/complaints/WorkloadPage.jsx"));
const ResolvedPage = lazy(() => import("../pages/complaints/ResolvedPage.jsx"));
const CoordinatorPerformancePage = lazy(() => import("../pages/coordinator/CoordinatorPerformancePage.jsx"));
const HealthMapPage = lazy(() => import("../pages/admin/HealthMapPage.jsx"));
const SafetyReportPage = lazy(() => import("../pages/student/SafetyReportPage.jsx"));
const SafetyReportsAdminPage = lazy(() => import("../pages/admin/SafetyReportsAdminPage.jsx"));
const CoverageGapsPage = lazy(() => import("../pages/admin/CoverageGapsPage.jsx"));
const EmergencyManagementPage = lazy(() => import("../pages/admin/EmergencyManagementPage.jsx"));


function RoleHome() {
  const { initializing, isAuthenticated, user } = useAuth();

  if (initializing) {
    return (
      <main className="grid min-h-screen place-items-center">
        <Loader label="Restoring session" />
      </main>
    );
  }
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (user?.role === ROLES.SUPER_ADMIN)
    return <Navigate to="/superadmin" replace />;
  if (user?.role === ROLES.STUDENT) return <Navigate to="/student" replace />;
  if (user?.role === ROLES.COORDINATOR)
    return <Navigate to="/coordinator" replace />;
  if (user?.role === ROLES.APP_MANAGER)
    return <Navigate to="/manager" replace />;
  if (user?.role === ROLES.ADMINISTRATOR)
    return <Navigate to="/admin" replace />;
  if (user?.role === ROLES.LOCATION_IN_CHARGE)
    return <Navigate to="/location" replace />;

  return <Navigate to="/403" replace />;
}


export default function AppRoutes() {
  return (
    <Suspense
      fallback={
        <main className="grid min-h-screen place-items-center">
          <Loader label="Loading module..." />
        </main>
      }
    >
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/activate" element={<ActivateAccountPage />} />
        <Route path="/403" element={<AccessDeniedPage />} />
        <Route path="/" element={<RoleHome />} />
        <Route
          path="/student"
          element={
            <ProtectedRoute roles={[ROLES.STUDENT]}>
              <StudentDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/change-password"
          element={
            <ProtectedRoute>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <ProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/complaints"
          element={
            <ProtectedRoute>
              <ComplaintListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/workload"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER, ROLES.LOCATION_IN_CHARGE, ROLES.COORDINATOR]}>
              <WorkloadPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/coordinators/performance"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER, ROLES.LOCATION_IN_CHARGE, ROLES.COORDINATOR]}>
              <CoordinatorPerformancePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/resolved"
          element={
            <ProtectedRoute>
              <ResolvedPage />
            </ProtectedRoute>
          }
        />

        <Route
          path="/public-complaints"
          element={
            <ProtectedRoute>
              <PublicComplaintsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/complaints/new"
          element={
            <ProtectedRoute roles={[ROLES.STUDENT, ROLES.LOCATION_IN_CHARGE]}>
              <CreateComplaintPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/complaints/create"
          element={
            <ProtectedRoute roles={[ROLES.STUDENT, ROLES.LOCATION_IN_CHARGE]}>
              <CreateComplaintPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/complaints/:complaintId"
          element={
            <ProtectedRoute>
              <ComplaintDetailsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/lost-found"
          element={
            <ProtectedRoute>
              <LostFoundPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/announcements"
          element={
            <ProtectedRoute>
              <AnnouncementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/feedback"
          element={
            <ProtectedRoute>
              <FeedbackPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/reports"
          element={
            <ProtectedRoute>
              <ReportsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <GlobalSearchPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/backups"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <BackupManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/backup"
          element={<Navigate to="/backups" replace />}
        />
        <Route
          path="/system/settings"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR]}>
              <SystemSettingsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/employee"
          element={<Navigate to="/coordinator" replace />}
        />
        <Route
          path="/admin/employee-assignments"
          element={<Navigate to="/admin/departments" replace />}
        />
        <Route
          path="/admin/teams"
          element={<Navigate to="/admin/departments" replace />}
        />
        <Route
          path="/admin/coverage-gaps"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <CoverageGapsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/emergency"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <EmergencyManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/coordinator"
          element={
            <ProtectedRoute roles={[ROLES.COORDINATOR]}>
              <CoordinatorDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/location"
          element={
            <ProtectedRoute roles={[ROLES.LOCATION_IN_CHARGE]}>
              <LocationDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/manager"
          element={
            <ProtectedRoute roles={[ROLES.APP_MANAGER]}>
              <ManagerDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <UserManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/departments"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <DepartmentManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/locations"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <LocationManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/issues"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR]}>
              <IssueManagementPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/cleanup"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR]}>
              <DataCleanupPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/superadmin"
          element={
            <ProtectedRoute roles={[ROLES.SUPER_ADMIN]}>
              <SuperAdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/superadmin/institutions"
          element={
            <ProtectedRoute roles={[ROLES.SUPER_ADMIN]}>
              <InstitutionRegistryPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/superadmin/support"
          element={
            <ProtectedRoute roles={[ROLES.SUPER_ADMIN]}>
              <PlatformSupportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/superadmin/health"
          element={
            <ProtectedRoute roles={[ROLES.SUPER_ADMIN]}>
              <PlatformHealthPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/support"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR]}>
              <TechnicalSupportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/audit"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <AuditLogPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/safety-reports"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR]}>
              <SafetyReportsAdminPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/health-map"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER, ROLES.LOCATION_IN_CHARGE, ROLES.STUDENT]}>
              <HealthMapPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/health-map/tv"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER, ROLES.LOCATION_IN_CHARGE, ROLES.COORDINATOR]}>
              <HealthMapPage tvModeOverride={true} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/safety"
          element={
            <ProtectedRoute>
              <SafetyReportPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/notifications"
          element={
            <ProtectedRoute>
              <NotificationsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute
              roles={[
                ROLES.ADMINISTRATOR,
                ROLES.APP_MANAGER,
                ROLES.LOCATION_IN_CHARGE,
                ROLES.COORDINATOR,
              ]}
            >
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat/item/:itemId"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inbox"
          element={
            <ProtectedRoute>
              <InboxPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analytics"
          element={
            <ProtectedRoute roles={[ROLES.ADMINISTRATOR, ROLES.APP_MANAGER]}>
              <AnalyticsPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}

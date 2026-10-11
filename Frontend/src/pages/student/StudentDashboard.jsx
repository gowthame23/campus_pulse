import { useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FileText,
  ArrowRight,
  Megaphone,
  Bell,
  Clock,
  Plus,
  CheckCircle2,
  AlertCircle,
  MapPin,
  ChevronRight,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import StatCard from "../../components/StatCard.jsx";
import Badge from "../../components/Badge.jsx";
import Card from "../../components/Card.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { complaintService } from "../../services/complaintService.js";
import { announcementService } from "../../services/announcementService.js";
import { notificationService } from "../../services/notificationService.js";
import { locationService } from "../../services/locationService.js";
import { COMPLAINT_STATUS } from "../../utils/constants.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone, getPriorityTone } from "../../utils/statusColor.js";

const getLocationName = (locId, locations = []) => {
  if (!locId) return "";
  const match = (locations || []).find((l) => l.location_id === locId || l.name === locId);
  if (match && match.name) return match.name;
  const idStr = String(locId).trim();
  const knownMap = {
    LOC_HOSTEL_A: "Hostel Block A",
    LOC_HOSTEL_B: "Hostel Block B",
    LOC_HOSTEL_C: "Hostel Block C",
    LOC_ACADEMIC: "Academic Block",
    LOC_MESS: "Mess Hall",
    LOC_SAC: "Student Activity Center",
    LOC_SPORTS: "Sports Complex",
    LOC_OTHER: "Other Campus Location",
  };
  if (knownMap[idStr]) return knownMap[idStr];
  if (idStr.startsWith("LOC_")) {
    return idStr
      .replace(/^LOC_/, "")
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return idStr;
};

export default function StudentDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const {
    data: dashboardData,
    loading,
    error,
  } = useAsyncData(
    async () => {
      const [compRes, ancRes, notifRes, locRes] = await Promise.all([
        complaintService.list().catch(() => ({ data: [] })),
        announcementService.list().catch(() => ({ data: [] })),
        notificationService
          .listPaginated({ limit: 5 })
          .then((res) => ({ data: res.data.items }))
          .catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
      ]);
      return {
        complaints: compRes.data || [],
        announcements: ancRes.data || [],
        notifications: notifRes.data || [],
        locations: locRes.data || [],
      };
    },
    { complaints: [], announcements: [], notifications: [], locations: [] },
  );

  const complaints = dashboardData?.complaints || [];
  const announcements = dashboardData?.announcements || [];
  const notifications = dashboardData?.notifications || [];
  const locations = dashboardData?.locations || [];

  const myComplaints = useMemo(
    () =>
      complaints.filter(
        (c) => c.created_by === user?.user_id || c.student_id === user?.user_id,
      ),
    [complaints, user],
  );

  const needAttentionComplaints = useMemo(() => {
    return myComplaints.filter(
      (c) =>
        c.status === "Waiting for Verification" ||
        c.status === COMPLAINT_STATUS.WAITING_VERIFICATION ||
        c.status === "Reopened",
    );
  }, [myComplaints]);

  const activeComplaints = useMemo(() => {
    return myComplaints.filter(
      (c) => !["Closed", "Closed (Auto Closed)", "Rejected"].includes(c.status),
    );
  }, [myComplaints]);

  const closedCount = useMemo(() => {
    return myComplaints.filter((c) =>
      ["Closed", "Closed (Auto Closed)"].includes(c.status),
    ).length;
  }, [myComplaints]);

  if (loading)
    return <Loader label="Loading student dashboard..." variant="skeleton" />;
  if (error)
    return <EmptyState title="Dashboard Unavailable" description={error} />;

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Good morning, {user?.name || "Student"}
          </h1>
          <p className="text-xs font-normal text-slate-500 dark:text-slate-400 mt-1">
            Track your reported campus problems and check live announcements.
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            onClick={() => navigate("/complaints/create")}
            variant="primary"
            size="md"
            className="font-medium shrink-0 flex items-center gap-1.5"
          >
            <Plus className="h-4 w-4" />
            Report a Problem
          </Button>
          <Button
            onClick={() => navigate("/complaints")}
            variant="outline"
            size="md"
            className="font-medium shrink-0"
          >
            All Complaints
          </Button>
        </div>
      </div>

      {/* 3 Key Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <StatCard
          label="Need Attention"
          value={needAttentionComplaints.length}
          accent={needAttentionComplaints.length > 0}
          subtext={
            needAttentionComplaints.length > 0
              ? "Requires verification to close"
              : "All verifications complete"
          }
          onClick={() =>
            navigate("/complaints", {
              state: { status: "Waiting for Verification" },
            })
          }
        />
        <StatCard
          label="Active Problems"
          value={activeComplaints.length}
          subtext="Currently open or in progress"
          onClick={() =>
            navigate("/complaints", { state: { status: "active" } })
          }
        />
        <StatCard
          label="Resolved & Closed"
          value={closedCount}
          subtext="Completed tickets archive"
          onClick={() =>
            navigate("/complaints", { state: { status: "Closed" } })
          }
        />
      </div>

      {/* Urgent Attention Alert Banner */}
      {needAttentionComplaints.length > 0 && (
        <div className="flex items-center justify-between gap-4 p-4 rounded-xl border border-amber-200/80 dark:border-amber-900/40 bg-amber-50/70 dark:bg-amber-950/20 text-amber-900 dark:text-amber-200 text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400 shrink-0">
              <AlertCircle className="h-4 w-4" />
            </div>
            <div>
              <span className="font-semibold">
                {needAttentionComplaints.length} problem(s) resolved by campus staff.
              </span>
              <p className="text-[11px] text-amber-800/80 dark:text-amber-300/80 mt-0.5">
                Please verify if the issue was solved properly so it can be closed.
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() =>
              navigate(`/complaints/${needAttentionComplaints[0].complaint_id}`)
            }
            className="!h-8 text-xs font-semibold shrink-0 border-amber-300 dark:border-amber-800 text-amber-900 dark:text-amber-200 hover:bg-amber-100/60"
          >
            Review Now
            <ArrowRight className="h-3 w-3 ml-1" />
          </Button>
        </div>
      )}

      {/* Main Operations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Announcements & Live Updates */}
          {/* Announcements Card */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Megaphone className="h-3.5 w-3.5 text-amber-500" />
                Campus Notices
              </h2>
              <Link
                to="/announcements"
                className="text-xs font-medium text-primary hover:underline"
              >
                View All
              </Link>
            </div>

            {announcements.length === 0 ? (
              <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">
                No active announcements today.
              </p>
            ) : (
              <div className="space-y-2.5">
                {announcements.slice(0, 3).map((a) => (
                  <div
                    key={a.announcement_id || a.id}
                    className="p-3 rounded-xl bg-white dark:bg-[#101726] border border-slate-200/80 dark:border-slate-800/80 text-xs shadow-2xs space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2 font-medium text-slate-900 dark:text-slate-100">
                      <span className="truncate">{a.title}</span>
                      <Badge tone={a.priority === "Critical" ? "danger" : "warning"}>
                        {a.priority || "Normal"}
                      </Badge>
                    </div>
                    <p className="text-slate-500 dark:text-slate-400 line-clamp-2 text-[11px] leading-relaxed">
                      {a.content || a.description}
                    </p>
                    <div className="text-[10px] text-slate-400 dark:text-slate-500 pt-1 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(a.created_at)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Activity Card */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Bell className="h-3.5 w-3.5 text-primary" />
                Recent Activity
              </h2>
              <Link
                to="/notifications"
                className="text-xs font-medium text-primary hover:underline"
              >
                View All
              </Link>
            </div>

            {notifications.length === 0 ? (
              <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">
                No recent activity.
              </p>
            ) : (
              <div className="space-y-2">
                {notifications.slice(0, 4).map((n) => (
                  <div
                    key={n.notification_id || n.id}
                    onClick={() => {
                      if (n.reference_id && n.reference_type === "Complaint") {
                        navigate(`/complaints/${n.reference_id}`);
                      } else {
                        navigate("/notifications");
                      }
                    }}
                    className="flex items-start justify-between gap-2 p-2.5 rounded-xl bg-white dark:bg-[#101726] border border-slate-200/70 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer transition-colors text-xs"
                  >
                    <div className="space-y-0.5 min-w-0 pr-1">
                      <div className="font-medium text-slate-800 dark:text-slate-200 truncate">
                        {n.title || n.message}
                      </div>
                      <div className="text-[11px] text-slate-400 dark:text-slate-500 line-clamp-1">
                        {n.message}
                      </div>
                    </div>
                    <span className="text-[10px] text-slate-400 shrink-0">
                      {formatDate(n.created_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
  );
}

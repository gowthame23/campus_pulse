import { useState, useEffect } from "react";
import {
  Shield,
  RotateCw,
  Filter,
  Search,
  Eye,
  Download,
  Archive,
  Clock,
  AlertOctagon,
  UserX,
  Activity,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import StatCard from "../../components/StatCard.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Table from "../../components/Table.jsx";
import Modal from "../../components/Modal.jsx";
import Toast from "../../components/Toast.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { auditService } from "../../services/auditService.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { useAuth } from "../../context/AuthContext.jsx";

export default function AuditLogPage() {
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [moduleFilter, setModuleFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [viewLog, setViewLog] = useState(null);
  const [timelineEntity, setTimelineEntity] = useState(null);
  const [timelineData, setTimelineData] = useState([]);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [dashboardMetrics, setDashboardMetrics] = useState(null);

  const { data, loading, reload } = useAsyncData(async () => {
    const res = await auditService.list({
      q: query,
      module: moduleFilter,
      action: actionFilter,
      status: statusFilter,
      limit: 100,
    });
    return res.data.items || res.data;
  }, [query, moduleFilter, actionFilter, statusFilter]);

  useEffect(() => {
    auditService
      .getDashboard()
      .then((res) => setDashboardMetrics(res.data))
      .catch(() => {});
  }, []);

  const logs = data || [];

  const handleExport = async (format = "csv") => {
    try {
      const response = await auditService.exportLogs(format, {
        module: moduleFilter,
        action: actionFilter,
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `audit_logs_${new Date().toISOString().slice(0, 10)}.${format}`,
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      setMessage(
        `Audit logs exported to ${format.toUpperCase()} successfully.`,
      );
    } catch (err) {
      setError("Failed to export audit logs.");
    }
  };

  const handleArchive = async () => {
    if (!window.confirm("Archive audit logs older than 180 days?")) return;
    try {
      const res = await auditService.archiveLogs(180);
      setMessage(`Archived ${res.data.archived_count} old audit log records.`);
      reload();
    } catch (err) {
      setError("Failed to archive audit logs.");
    }
  };

  const openTimeline = async (entityType, entityId) => {
    setTimelineEntity({ entityType, entityId });
    try {
      const res = await auditService.getEntityTimeline(entityType, entityId);
      setTimelineData(res.data);
    } catch (err) {
      setTimelineData([]);
    }
  };

  const columns = [
    {
      key: "created_at",
      header: "Timestamp",
      render: (row) => formatDate(row.created_at),
    },
    {
      key: "module",
      header: "Module",
      render: (row) => (
        <span className="font-bold text-slate-700 text-xs">
          {row.module || "Complaint"}
        </span>
      ),
    },
    {
      key: "action",
      header: "Action",
      render: (row) => (
        <span className="rounded-md bg-primary/10 px-2 py-0.5 text-[11px] font-bold text-primary">
          {row.action}
        </span>
      ),
    },
    {
      key: "entity_id",
      header: "Entity",
      render: (row) => (
        <button
          onClick={() => openTimeline(row.entity_type, row.entity_id)}
          className="font-mono text-xs font-bold text-primary underline hover:text-primary-dark"
        >
          {row.entity_type}: {row.entity_id}
        </button>
      ),
    },
    {
      key: "performed_by",
      header: "Actor / Role",
      render: (row) => (
        <div className="text-xs">
          <div className="font-bold text-slate-800">
            {row.performed_by || "system"}
          </div>
          <div className="text-[10px] text-slate-400 font-semibold uppercase">
            {row.performed_role || "System"}
          </div>
        </div>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row) => (
        <span
          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
            row.status === "SUCCESS"
              ? "bg-emerald-100 text-emerald-800"
              : "bg-rose-100 text-rose-800"
          }`}
        >
          {row.status}
        </span>
      ),
    },
    {
      key: "ip_address",
      header: "IP Address",
      render: (row) => (
        <span className="font-mono text-slate-500 text-xs">
          {row.ip_address || "127.0.0.1"}
        </span>
      ),
    },
    {
      key: "details",
      header: "Details",
      render: (row) => (
        <Button
          variant="subtle"
          size="sm"
          onClick={() => setViewLog(row)}
          className="!py-1 !px-2.5 !text-xs font-semibold"
        >
          <Eye className="h-3.5 w-3.5 mr-1" />
          Diff
        </Button>
      ),
    },
  ];

  return (
    <div className="grid gap-6 max-w-6xl">
      <PageHeader
        title="Audit Log & Activity Monitoring"
        description="Immutable compliance trail for accountability, security investigations, and record timelines."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="subtle"
              size="sm"
              onClick={reload}
              className="h-9 font-semibold"
            >
              <RotateCw className="h-4 w-4 mr-1 shrink-0" />
              Refresh
            </Button>
            {user?.role === "administrator" && (
              <Button
                variant="secondary"
                size="sm"
                onClick={handleArchive}
                className="h-9 font-semibold flex items-center gap-1"
              >
                <Archive className="h-4 w-4" />
                Archive Old Logs
              </Button>
            )}
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleExport("csv")}
              className="h-9 font-bold flex items-center gap-1.5"
            >
              <Download className="h-4 w-4" />
              Export CSV
            </Button>
          </div>
        }
      />

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Audit Dashboard Overview Cards */}
      {dashboardMetrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <StatCard
            label="TOTAL LOGS"
            value={dashboardMetrics.total_logs}
            accent
          />
          <StatCard
            label="FAILED ACTIONS"
            value={dashboardMetrics.failed_actions}
          />
          <StatCard
            label="LOGIN FAILURES"
            value={dashboardMetrics.login_failures}
          />
          <StatCard
            label="TODAY ACTIVITY"
            value={dashboardMetrics.today_activity}
          />
          <StatCard
            label="ACTIVE MODULE"
            value={dashboardMetrics.most_active_module}
          />
        </div>
      )}

      {/* Search & Multi-Filter Toolbar */}
      <Card className="flex flex-wrap items-center justify-between gap-4 bg-slate-50/50">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by ID, user, IP, or keyword..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-100 rounded-lg text-xs font-semibold focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
          <select
            value={moduleFilter}
            onChange={(e) => setModuleFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none"
          >
            <option value="">All Modules</option>
            <option value="Complaint">Complaint</option>
            <option value="User">User</option>
            <option value="Notification">Notification</option>
            <option value="Settings">Settings</option>
            <option value="Location">Location</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2.5 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILED">FAILED</option>
          </select>
        </div>
      </Card>

      {/* Main Audit Table */}
      <div>
        {loading && <Loader label="Loading audit logs..." variant="skeleton" />}
        {!loading && logs.length === 0 && (
          <EmptyState
            title="No audit events found"
            description="All system activities, security events, and record edits will automatically log here."
          />
        )}
        {!loading && logs.length > 0 && (
          <Table
            columns={columns}
            rows={logs}
            getRowKey={(row, i) => `${row.audit_id}-${i}`}
          />
        )}
      </div>

      {/* Audit Log Detail Drawer / Modal */}
      {viewLog && (
        <Modal
          open={!!viewLog}
          title={`Audit Details: ${viewLog.audit_id}`}
          onClose={() => setViewLog(null)}
        >
          <div className="grid gap-4 text-xs font-mono">
            <div className="p-3 bg-slate-900 text-slate-100 rounded-xl grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate-400">Action:</span> {viewLog.action}
              </div>
              <div>
                <span className="text-slate-400">Module:</span> {viewLog.module}
              </div>
              <div>
                <span className="text-slate-400">Actor:</span>{" "}
                {viewLog.performed_by} ({viewLog.performed_role})
              </div>
              <div>
                <span className="text-slate-400">Entity:</span>{" "}
                {viewLog.entity_type} #{viewLog.entity_id}
              </div>
              <div>
                <span className="text-slate-400">IP:</span> {viewLog.ip_address}
              </div>
              <div>
                <span className="text-slate-400">Status:</span> {viewLog.status}
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl text-slate-800 font-sans font-medium text-xs">
              <span className="text-slate-400 font-bold uppercase block text-[10px] mb-0.5">
                Description
              </span>
              {viewLog.description}
            </div>

            {viewLog.failure_reason && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 font-sans rounded-xl text-xs">
                <span className="font-bold block uppercase text-[10px] text-rose-600">
                  Failure Reason
                </span>
                {viewLog.failure_reason}
              </div>
            )}

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <span className="text-rose-500 font-bold block mb-1 uppercase text-[10px]">
                  Previous State (Old Value)
                </span>
                <pre className="p-3 bg-rose-50/50 border border-rose-200 text-slate-800 rounded-xl overflow-x-auto max-h-60 text-[11px]">
                  {JSON.stringify(viewLog.old_value, null, 2) || "null"}
                </pre>
              </div>
              <div>
                <span className="text-emerald-600 font-bold block mb-1 uppercase text-[10px]">
                  New State (Updated Value)
                </span>
                <pre className="p-3 bg-emerald-50/50 border border-emerald-200 text-slate-800 rounded-xl overflow-x-auto max-h-60 text-[11px]">
                  {JSON.stringify(viewLog.new_value, null, 2) || "null"}
                </pre>
              </div>
            </div>

            <div className="flex justify-end">
              <Button variant="subtle" onClick={() => setViewLog(null)}>
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Entity Timeline Drawer / Modal */}
      {timelineEntity && (
        <Modal
          open={!!timelineEntity}
          title={`Timeline: ${timelineEntity.entityType} ${timelineEntity.entityId}`}
          onClose={() => setTimelineEntity(null)}
        >
          <div className="grid gap-4 text-xs font-sans">
            <p className="text-slate-500">
              Chronological lifecycle history reconstructed from immutable audit
              logs.
            </p>

            <div className="relative border-l-2 border-primary/30 pl-4 grid gap-4 py-2">
              {timelineData.map((ev, idx) => (
                <div key={ev.audit_id || idx} className="relative">
                  <div className="absolute -left-[21px] top-0.5 h-3 w-3 rounded-full bg-primary border-2 border-white" />
                  <div className="font-bold text-slate-900">{ev.action}</div>
                  <div className="text-slate-600 text-[11px] mt-0.5">
                    {ev.description}
                  </div>
                  <div className="text-[10px] text-slate-400 font-semibold mt-1">
                    By {ev.performed_by} ({ev.performed_role}) • {ev.created_at}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="subtle" onClick={() => setTimelineEntity(null)}>
                Close Timeline
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

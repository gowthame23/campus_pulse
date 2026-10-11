import { useState, useEffect } from "react";
import {
  Database,
  Download,
  ShieldCheck,
  RefreshCw,
  HardDrive,
  Clock,
  Plus,
  CheckCircle2,
  AlertTriangle,
  FileArchive,
  Server,
  ShieldAlert,
  History,
} from "lucide-react";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import StatCard from "../components/StatCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Loader from "../components/Loader.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Modal from "../components/Modal.jsx";
import Toast from "../components/Toast.jsx";
import Input from "../components/Input.jsx";
import { useAsyncData } from "../hooks/useAsyncData.js";
import { backupService } from "../services/backupService.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../utils/dateFormatter.js";

export default function BackupManagementPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("archives"); // 'archives' | 'schedules' | 'restores'
  const [typeFilter, setTypeFilter] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Backup Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [backupName, setBackupName] = useState("");
  const [backupType, setBackupType] = useState("Full");
  const [remarks, setRemarks] = useState("");
  const [creating, setCreating] = useState(false);

  // Restore Modal State
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [restoring, setRestoring] = useState(false);

  // Verification Results State
  const [verificationResult, setVerificationResult] = useState(null);

  const [summaryMetrics, setSummaryMetrics] = useState(null);

  const isAdministrator = user?.role === "administrator";

  const {
    data: backups,
    loading: loadingBackups,
    reload: reloadBackups,
  } = useAsyncData(
    async () =>
      (await backupService.listBackups({ backup_type: typeFilter })).data,
    [typeFilter],
  );

  const { data: schedules } = useAsyncData(
    async () => (await backupService.listSchedules()).data,
    [],
  );

  const { data: restores, reload: reloadRestores } = useAsyncData(
    async () => (await backupService.listRestoreHistory()).data,
    [],
  );

  useEffect(() => {
    backupService
      .getSummary()
      .then((res) => setSummaryMetrics(res.data))
      .catch(() => {});
  }, [backups]);

  const handleCreateBackup = async (e) => {
    e.preventDefault();
    setCreating(true);
    setMessage("");
    setError("");

    try {
      const res = await backupService.createBackup({
        backup_name: backupName || `Manual_Backup_${Date.now()}`,
        backup_type: backupType,
        remarks,
      });
      setMessage(
        `Backup archive '${res.data.backup_name}' generated successfully.`,
      );
      setShowCreateModal(false);
      setBackupName("");
      setRemarks("");
      reloadBackups();
    } catch (err) {
      setError(err?.response?.data?.detail || "Backup creation failed.");
    } finally {
      setCreating(false);
    }
  };

  const handleVerifyBackup = async (backupId) => {
    try {
      const res = await backupService.verifyBackup(backupId);
      setVerificationResult(res.data);
      if (res.data.valid) {
        setMessage(`SHA-256 Checksum verified! Backup archive is intact.`);
      } else {
        setError(
          `Backup checksum verification failed! File corrupted or missing.`,
        );
      }
    } catch (err) {
      setError("Verification failed.");
    }
  };

  const handleDownloadBackup = async (backup) => {
    try {
      const response = await backupService.downloadBackup(backup.backup_id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", backup.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err?.response?.data?.detail || "Backup download failed.");
    }
  };

  const handleRestoreBackup = async () => {
    if (!selectedBackup) return;
    setRestoring(true);
    setMessage("");
    setError("");

    try {
      await backupService.restoreBackup(selectedBackup.backup_id);
      setMessage(
        `Database restored successfully from '${selectedBackup.backup_name}'.`,
      );
      setSelectedBackup(null);
      reloadRestores();
    } catch (err) {
      setError(err?.response?.data?.detail || "Database restore failed.");
    } finally {
      setRestoring(false);
    }
  };

  const listBackups = backups || [];
  const listSchedules = schedules || [];
  const listRestores = restores || [];

  return (
    <div className="grid gap-6 max-w-6xl">
      <PageHeader
        title="Backup & Restore Management"
        description="Data recovery engine generating SHA-256 verified database snapshots and file archive backups."
        actions={
          isAdministrator && (
            <Button
              onClick={() => setShowCreateModal(true)}
              size="sm"
              className="font-bold flex items-center gap-1.5"
            >
              <Database className="h-4 w-4" />
              Create System Backup
            </Button>
          )
        }
      />

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Dashboard Overview Cards */}
      {summaryMetrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="TOTAL SYSTEM BACKUPS"
            value={summaryMetrics.total_backups}
            accent
          />
          <StatCard
            label="SUCCESSFUL ARCHIVES"
            value={summaryMetrics.successful_backups}
          />
          <StatCard
            label="FAILED BACKUPS"
            value={summaryMetrics.failed_backups}
          />
          <StatCard
            label="BACKUP STORAGE (MB)"
            value={`${summaryMetrics.storage_used_mb} MB`}
          />
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab("archives")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 ${
            activeTab === "archives"
              ? "border-primary text-primary"
              : "border-transparent text-slate-400 hover:text-slate-600"
          }`}
        >
          Backup Archives ({listBackups.length})
        </button>
        <button
          onClick={() => setActiveTab("schedules")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 ${
            activeTab === "schedules"
              ? "border-primary text-primary"
              : "border-transparent text-slate-400 hover:text-slate-600"
          }`}
        >
          Automated Schedules ({listSchedules.length})
        </button>
        <button
          onClick={() => setActiveTab("restores")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 ${
            activeTab === "restores"
              ? "border-primary text-primary"
              : "border-transparent text-slate-400 hover:text-slate-600"
          }`}
        >
          Restore History ({listRestores.length})
        </button>
      </div>

      {activeTab === "archives" && (
        <>
          {/* Backup List */}
          {loadingBackups ? (
            <Loader label="Loading backup archives..." variant="skeleton" />
          ) : listBackups.length === 0 ? (
            <EmptyState
              title="No backup archives found"
              description="Generated database snapshots will appear here."
            />
          ) : (
            <div className="grid gap-3">
              {listBackups.map((b) => (
                <Card
                  key={b.backup_id}
                  className="flex flex-col sm:flex-row items-start justify-between gap-4"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-bold text-slate-900 text-base">
                        {b.backup_name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-700">
                        {b.backup_type}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800">
                        {b.status}
                      </span>
                      <span className="text-xs font-mono font-semibold text-slate-500">
                        ({roundMb(b.file_size)} MB)
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 font-mono font-semibold mt-1 flex flex-wrap items-center gap-4">
                      <span>Created by: {b.created_by}</span>
                      <span>Date: {formatDate(b.created_at)}</span>
                      <span>SHA-256: {b.checksum?.substring(0, 16)}...</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                    <Button
                      variant="subtle"
                      size="sm"
                      onClick={() => handleVerifyBackup(b.backup_id)}
                      className="font-bold text-xs"
                    >
                      Verify SHA-256
                    </Button>
                    {user?.role === "administrator" && (
                      <Button
                        size="sm"
                        onClick={() => handleDownloadBackup(b)}
                        className="font-bold flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700"
                      >
                        <Download className="h-4 w-4" /> Download
                      </Button>
                    )}
                    {user?.role === "administrator" && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setSelectedBackup(b)}
                        className="font-bold text-xs text-rose-600 hover:bg-rose-50 border-rose-200"
                      >
                        Restore DB
                      </Button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === "schedules" && (
        <Card className="grid gap-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" /> Configured Backup
            Schedules
          </h3>
          {listSchedules.length === 0 ? (
            <EmptyState
              title="No active schedules"
              description="Automated daily/weekly backup schedules will be listed here."
            />
          ) : (
            <div className="grid gap-3">
              {listSchedules.map((s) => (
                <div
                  key={s.schedule_id}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-900">
                      {s.backup_type} Backup ({s.frequency})
                    </div>
                    <div className="text-slate-500 font-mono text-[11px] mt-0.5">
                      Retention: {s.retention_days} Days | Storage:{" "}
                      {s.storage_provider}
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px] uppercase">
                    Active Schedule
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {activeTab === "restores" && (
        <Card className="grid gap-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <History className="h-5 w-5 text-slate-700" /> System Restore
            Operations Log
          </h3>
          {listRestores.length === 0 ? (
            <EmptyState
              title="No database restores recorded"
              description="Historical database restore operations will display here."
            />
          ) : (
            <div className="grid gap-3">
              {listRestores.map((r) => (
                <div
                  key={r.restore_id}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-900">
                      Restored from: {r.backup_name}
                    </div>
                    <div className="text-slate-500 text-[11px] mt-0.5">
                      Restored by: {r.restored_by} | Date:{" "}
                      {formatDate(r.started_at)}
                    </div>
                  </div>
                  <span className="px-2.5 py-1 rounded bg-emerald-100 text-emerald-800 font-bold text-[10px] uppercase">
                    {r.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* Restore Confirmation Modal */}
      {selectedBackup && (
        <Modal
          title={`Restore Database: ${selectedBackup.backup_name}`}
          isOpen={!!selectedBackup}
          onClose={() => setSelectedBackup(null)}
        >
          <div className="grid gap-4 text-xs font-sans">
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 flex items-start gap-2">
              <ShieldAlert className="h-5 w-5 shrink-0 text-rose-600 mt-0.5" />
              <div>
                <div className="font-bold text-rose-900">
                  WARNING: Database Restoration Action
                </div>
                <div>
                  Restoring this backup will replace current database tables
                  with data from {formatDate(selectedBackup.created_at)}.
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button
                variant="secondary"
                onClick={() => setSelectedBackup(null)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleRestoreBackup}
                disabled={restoring}
                className="font-bold bg-rose-600 hover:bg-rose-700"
              >
                {restoring ? "Restoring Database..." : "Confirm System Restore"}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Create Backup Modal */}
      {showCreateModal && (
        <Modal
          title="Create System Backup Archive"
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
        >
          <form onSubmit={handleCreateBackup} className="grid gap-4 text-xs">
            <Input
              label="Backup Archive Name"
              placeholder="e.g. Weekly_Pre_Deployment_Backup"
              value={backupName}
              onChange={(e) => setBackupName(e.target.value)}
              required
            />

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Backup Type
              </label>
              <select
                value={backupType}
                onChange={(e) => setBackupType(e.target.value)}
                className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-semibold text-slate-800 dark:text-slate-100"
              >
                <option value="Full">Full (Database & Files)</option>
                <option value="DatabaseOnly">Database Only</option>
                <option value="FilesOnly">Files Only</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Remarks / Release Notes
              </label>
              <textarea
                rows={2}
                placeholder="Reason for backup..."
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg font-semibold focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button
                variant="secondary"
                type="button"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={creating} className="font-bold">
                {creating ? "Generating Archive..." : "Generate Backup"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

function roundMb(bytes) {
  if (!bytes) return "0";
  return (bytes / (1024 * 1024)).toFixed(2);
}

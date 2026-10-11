import { useState } from "react";
import {
  Database,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Download,
  Upload,
} from "lucide-react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import Toast from "../../components/Toast.jsx";
import Loader from "../../components/Loader.jsx";
import Modal from "../../components/Modal.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { settingsService } from "../../services/settingsService.js";
import apiClient from "../../api/axios.js";

export default function DataCleanupPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Selection states for departments & locations
  const [selectedKeeps, setSelectedKeeps] = useState({}); // { groupName: keep_id }

  // Modal confirmation states
  const [confirmTarget, setConfirmTarget] = useState(null); // { type, name, keep_id, delete_ids, keepRecord, deleteRecords }
  const [resolving, setResolving] = useState(false);

  const { data, loading, reload } = useAsyncData(async () => {
    const res = await settingsService.getDuplicates();
    return res.data;
  }, []);

  const handleKeepSelect = (groupName, recordId) => {
    setSelectedKeeps((prev) => ({
      ...prev,
      [groupName]: recordId,
    }));
  };

  const handleBackupExport = async () => {
    setMessage("");
    setError("");
    try {
      const res = await apiClient.get("/settings/backup");
      const jsonStr = JSON.stringify(res.data, null, 2);
      const blob = new Blob([jsonStr], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `campus_pulse_backup_${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setMessage("Database backup exported successfully.");
    } catch (err) {
      setError(err?.response?.data?.detail || "Export failed.");
    }
  };

  const handleRestoreImport = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const payload = JSON.parse(e.target.result);
        await apiClient.post("/settings/restore", payload);
        setMessage("Database restored successfully from backup.");
        reload();
      } catch (err) {
        setError(
          err?.response?.data?.detail ||
            "Failed to parse or restore backup file.",
        );
      }
    };
    reader.readAsText(file);
  };

  const startResolve = (type, group) => {
    const keepId = selectedKeeps[group.name];
    if (!keepId) {
      setError(`Please select a record to keep for group "${group.name}".`);
      return;
    }

    const keepRecord = group.records.find(
      (r) =>
        (type === "department" ? r.department_id : r.location_id) === keepId,
    );
    const deleteRecords = group.records.filter(
      (r) =>
        (type === "department" ? r.department_id : r.location_id) !== keepId,
    );
    const deleteIds = deleteRecords.map((r) =>
      type === "department" ? r.department_id : r.location_id,
    );

    setConfirmTarget({
      type,
      name: group.name,
      keep_id: keepId,
      delete_ids: deleteIds,
      keepRecord,
      deleteRecords,
    });
  };

  const executeResolve = async () => {
    if (!confirmTarget) return;
    setResolving(true);
    setMessage("");
    setError("");

    try {
      const res = await settingsService.resolveDuplicate({
        type: confirmTarget.type,
        keep_id: confirmTarget.keep_id,
        delete_ids: confirmTarget.delete_ids,
      });
      setMessage(
        `Resolved duplicates successfully! Deleted ${res.data.deleted_count} stale record(s), migrated ${res.data.consolidated_complaints} complaint(s) and ${res.data.consolidated_users} user(s).`,
      );
      setConfirmTarget(null);
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to resolve duplicates.");
    } finally {
      setResolving(false);
    }
  };

  if (loading)
    return (
      <Loader label="Scanning database for duplicates" variant="skeleton" />
    );

  const hasDeps = data?.departments && data.departments.length > 0;
  const hasLocs = data?.locations && data.locations.length > 0;

  return (
    <div className="grid gap-8">
      {/* Header */}
      <div>
        <nav className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-2">
          <span>Dashboard</span>
          <span>&gt;</span>
          <span className="text-slate-800 font-bold">
            Data Cleanup & Backup
          </span>
        </nav>
        <PageHeader
          title="Data Integrity & Backup Maintenance"
          description="Review and consolidate duplicate entities, or export/restore full system database snapshots."
        />
      </div>

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Backup & Restore Controls */}
      <Card className="flex flex-wrap items-center justify-between gap-4 bg-slate-900 text-white p-6">
        <div>
          <h3 className="text-base font-bold flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            Database Backup & Recovery
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Export a full JSON snapshot of all system tables or restore state
            from a previous backup file.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            onClick={handleBackupExport}
            className="flex items-center gap-2 font-bold"
          >
            <Download className="h-4 w-4" />
            Export Backup
          </Button>
          <label className="cursor-pointer inline-flex items-center gap-2 rounded-xl bg-slate-800 px-4 py-2 text-xs font-bold text-slate-200 hover:bg-slate-700 transition-colors border border-slate-700">
            <Upload className="h-4 w-4" />
            Restore Backup
            <input
              type="file"
              accept=".json"
              onChange={handleRestoreImport}
              className="hidden"
            />
          </label>
        </div>
      </Card>

      {/* Info Warning Banner */}
      <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 flex gap-3 text-amber-850 text-xs font-medium leading-relaxed">
        <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
        <div>
          <span className="font-bold text-amber-900 block mb-0.5">
            Database Consistency Policy
          </span>
          When resolving duplicates, the system will migrate all active/closed
          complaints and registered users pointing to the stale record(s) to
          your chosen kept record before removing them. This guarantees foreign
          key integrity and ensures no complaints are lost.
        </div>
      </div>

      {/* Main Content */}
      <div className="grid gap-6">
        {!hasDeps && !hasLocs ? (
          <Card className="text-center py-12 flex flex-col items-center justify-center">
            <CheckCircle className="h-12 w-12 text-emerald-500 mb-4" />
            <h3 className="text-base font-bold text-slate-900">
              Database is Consistent
            </h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm">
              All department and location records are unique. No duplicate
              records detected!
            </p>
          </Card>
        ) : (
          <>
            {/* Departments Section */}
            {hasDeps && (
              <div className="grid gap-4">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                  Duplicate Departments
                </h3>
                {data.departments.map((group) => {
                  const keepId = selectedKeeps[group.name];
                  return (
                    <Card key={group.name} className="grid gap-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-base font-bold text-slate-900">
                            {group.name}
                          </h4>
                          <p className="text-[11px] font-semibold text-slate-400 mt-0.5">
                            {group.records.length} duplicate definitions found
                          </p>
                        </div>
                        <Button
                          size="sm"
                          disabled={!keepId}
                          onClick={() => startResolve("department", group)}
                        >
                          Resolve & Consolidate
                        </Button>
                      </div>

                      <div className="overflow-x-auto border border-slate-100 rounded-xl">
                        <table className="min-w-full text-left border-collapse text-xs font-semibold">
                          <thead>
                            <tr className="bg-slate-50 border-b border-slate-100 text-slate-500">
                              <th className="p-3 w-16 text-center">Keep</th>
                              <th className="p-3">Department ID</th>
                              <th className="p-3">Name</th>
                              <th className="p-3">Coordinator</th>
                              <th className="p-3 text-center">
                                Active Complaints
                              </th>
                              <th className="p-3 text-center">Mapped Users</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.records.map((r) => (
                              <tr
                                key={r.department_id}
                                className={`border-b border-slate-100 last:border-0 hover:bg-slate-50/50 ${
                                  keepId === r.department_id
                                    ? "bg-primary/5 text-primary"
                                    : "text-slate-650"
                                }`}
                              >
                                <td className="p-3 text-center">
                                  <input
                                    type="radio"
                                    name={`keep-dept-${group.name}`}
                                    checked={keepId === r.department_id}
                                    onChange={() =>
                                      handleKeepSelect(
                                        group.name,
                                        r.department_id,
                                      )
                                    }
                                    className="h-4 w-4 text-primary focus:ring-primary border-slate-300"
                                  />
                                </td>
                                <td className="p-3 font-mono">
                                  {r.department_id}
                                </td>
                                <td className="p-3 font-bold">{r.name}</td>
                                <td className="p-3">{r.coordinator_name}</td>
                                <td className="p-3 text-center font-bold">
                                  {r.complaints_count}
                                </td>
                                <td className="p-3 text-center font-bold">
                                  {r.users_count}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Locations Section */}
            {hasLocs && (
              <div className="grid gap-4 mt-4">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">
                  Duplicate Locations
                </h3>
                {data.locations.map((group) => {
                  const keepId = selectedKeeps[group.name];
                  return (
                    <Card key={group.name} className="grid gap-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="text-base font-bold text-slate-900">
                            {group.name}
                          </h4>
                          <p className="text-[11px] font-semibold text-slate-400 mt-0.5">
                            {group.records.length} duplicate definitions found
                          </p>
                        </div>
                        <Button
                          size="sm"
                          disabled={!keepId}
                          onClick={() => startResolve("location", group)}
                        >
                          Resolve & Consolidate
                        </Button>
                      </div>

                      <div className="overflow-x-auto border border-slate-100 rounded-xl">
                        <table className="min-w-full text-left border-collapse text-xs font-semibold">
                          <thead>
                            <tr className="bg-slate-50 border-b border-slate-100 text-slate-500">
                              <th className="p-3 w-16 text-center">Keep</th>
                              <th className="p-3">Location ID</th>
                              <th className="p-3">Name</th>
                              <th className="p-3">In-Charge</th>
                              <th className="p-3 text-center">
                                Active Complaints
                              </th>
                              <th className="p-3 text-center">Mapped Users</th>
                            </tr>
                          </thead>
                          <tbody>
                            {group.records.map((r) => (
                              <tr
                                key={r.location_id}
                                className={`border-b border-slate-100 last:border-0 hover:bg-slate-50/50 ${
                                  keepId === r.location_id
                                    ? "bg-primary/5 text-primary"
                                    : "text-slate-650"
                                }`}
                              >
                                <td className="p-3 text-center">
                                  <input
                                    type="radio"
                                    name={`keep-loc-${group.name}`}
                                    checked={keepId === r.location_id}
                                    onChange={() =>
                                      handleKeepSelect(
                                        group.name,
                                        r.location_id,
                                      )
                                    }
                                    className="h-4 w-4 text-primary focus:ring-primary border-slate-300"
                                  />
                                </td>
                                <td className="p-3 font-mono">
                                  {r.location_id}
                                </td>
                                <td className="p-3 font-bold">{r.name}</td>
                                <td className="p-3">{r.in_charge_name}</td>
                                <td className="p-3 text-center font-bold">
                                  {r.complaints_count}
                                </td>
                                <td className="p-3 text-center font-bold">
                                  {r.users_count}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </>
        )}
      </div>

      {/* Confirmation Modal */}
      <Modal
        open={!!confirmTarget}
        title="Confirm Duplicate Consolidation"
        onClose={() => setConfirmTarget(null)}
      >
        {confirmTarget && (
          <div className="grid gap-4 text-xs font-semibold">
            <p className="text-sm text-slate-600 leading-normal">
              You are consolidating duplicate records for{" "}
              <strong>{confirmTarget.name}</strong>.
            </p>
            <div className="rounded-xl border border-slate-100 bg-slate-50 p-4 grid gap-2">
              <div>
                <span className="text-emerald-600 block uppercase font-bold text-[9px] tracking-wide">
                  Record to Keep
                </span>
                <span className="font-mono text-slate-700">
                  {confirmTarget.keep_id}
                </span>{" "}
                (
                {confirmTarget.keepRecord?.coordinator_name ||
                  confirmTarget.keepRecord?.in_charge_name}
                )
              </div>
              <hr className="border-slate-200" />
              <div>
                <span className="text-red-500 block uppercase font-bold text-[9px] tracking-wide">
                  Records to Delete
                </span>
                {confirmTarget.deleteRecords.map((r) => (
                  <div
                    key={r.department_id || r.location_id}
                    className="font-mono text-slate-500"
                  >
                    {r.department_id || r.location_id} (
                    {r.coordinator_name || r.in_charge_name})
                  </div>
                ))}
              </div>
            </div>

            {/* Merge Stats Summary */}
            <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 flex gap-3 text-primary leading-normal">
              <HelpCircle className="h-5 w-5 shrink-0" />
              <div>
                <span className="font-bold block text-primary/90">
                  Consolidation Impact:
                </span>
                This action will migrate:{" "}
                <strong>
                  {confirmTarget.deleteRecords.reduce(
                    (acc, r) => acc + r.complaints_count,
                    0,
                  )}{" "}
                  complaints
                </strong>{" "}
                and{" "}
                <strong>
                  {confirmTarget.deleteRecords.reduce(
                    (acc, r) => acc + r.users_count,
                    0,
                  )}{" "}
                  users
                </strong>{" "}
                associated with the deleted records to the kept record. Stale
                references will be purged safely.
              </div>
            </div>

            <div className="mt-4 flex justify-end gap-3">
              <Button
                variant="subtle"
                onClick={() => setConfirmTarget(null)}
                disabled={resolving}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={executeResolve}
                disabled={resolving}
              >
                {resolving ? "Merging & Cleaning..." : "Confirm Consolidation"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

import { useState, useEffect } from "react";
import {
  Users,
  Plus,
  Edit2,
  Trash2,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  Layers,
  MapPin,
  Building,
  Shield,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Modal from "../../components/Modal.jsx";
import Badge from "../../components/Badge.jsx";
import { teamService } from "../../services/teamService.js";
import { departmentService } from "../../services/departmentService.js";
import { locationService } from "../../services/locationService.js";
import { userService } from "../../services/userService.js";

export default function TeamsManagementPage() {
  const [teams, setTeams] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  // Form Fields (C1)
  const [name, setName] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [coordinatorId, setCoordinatorId] = useState("");
  const [backupCoordinatorId, setBackupCoordinatorId] = useState("");
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [active, setActive] = useState(true);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError("");
    try {
      const [teamsRes, deptRes, locRes, usersRes] = await Promise.all([
        teamService.list({ active_only: false }),
        departmentService.list({ include_archived: false }),
        locationService.list(),
        userService.list(),
      ]);
      setTeams(teamsRes.data || teamsRes || []);
      setDepartments(deptRes.data || deptRes || []);
      setLocations(locRes.data || locRes || []);
      setUsers(usersRes.data || usersRes || []);
    } catch (err) {
      setError("Failed to load teams data.");
    } finally {
      setLoading(false);
    }
  };

  const candidateCoordinators = users.filter((u) =>
    ["coordinator", "employee", "administrator"].includes((u.role || "").toLowerCase())
  );

  const candidateMembers = users.filter((u) =>
    ["coordinator", "employee"].includes((u.role || "").toLowerCase())
  );

  const handleOpenCreate = () => {
    setEditingTeam(null);
    setName("");
    setDepartmentId(departments[0]?.department_id || "");
    setCoordinatorId(candidateCoordinators[0]?.user_id || "");
    setBackupCoordinatorId("");
    setSelectedLocations([]);
    setSelectedMembers([]);
    setActive(true);
    setFormError("");
    setModalOpen(true);
  };

  const handleOpenEdit = (team) => {
    setEditingTeam(team);
    setName(team.name || "");
    setDepartmentId(team.department_id || "");
    setCoordinatorId(team.coordinator_id || "");
    setBackupCoordinatorId(team.backup_coordinator_id || "");
    setSelectedLocations(team.location_ids || []);
    setSelectedMembers(team.member_ids || []);
    setActive(Boolean(team.active));
    setFormError("");
    setModalOpen(true);
  };

  const handleToggleLocation = (locId) => {
    setSelectedLocations((prev) =>
      prev.includes(locId) ? prev.filter((id) => id !== locId) : [...prev, locId]
    );
  };

  const handleToggleMember = (userId) => {
    setSelectedMembers((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const handleSaveTeam = async (e) => {
    e.preventDefault();
    if (!name.trim()) {
      setFormError("Team name is required.");
      return;
    }
    if (!departmentId) {
      setFormError("Department is required.");
      return;
    }
    if (!coordinatorId) {
      setFormError("Coordinator is required.");
      return;
    }
    if (selectedLocations.length === 0) {
      setFormError("At least one location must be selected.");
      return;
    }

    setSaving(true);
    setFormError("");
    try {
      if (editingTeam) {
        await teamService.update(editingTeam.team_id, {
          name: name.trim(),
          department_id: departmentId,
          coordinator_id: coordinatorId,
          backup_coordinator_id: backupCoordinatorId || null,
          location_ids: selectedLocations,
          member_ids: selectedMembers,
          active: active,
        });
        setSuccess(`Team '${name}' updated successfully.`);
      } else {
        await teamService.create({
          name: name.trim(),
          department_id: departmentId,
          coordinator_id: coordinatorId,
          backup_coordinator_id: backupCoordinatorId || null,
          location_ids: selectedLocations,
          member_ids: selectedMembers,
        });
        setSuccess(`Team '${name}' created successfully.`);
      }
      setModalOpen(false);
      loadAllData();
    } catch (err) {
      setFormError(err.response?.data?.detail || "Failed to save team.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeactivate = async (team) => {
    if (!confirm(`Are you sure you want to deactivate team '${team.name}'?`)) return;
    try {
      await teamService.deactivate(team.team_id);
      setSuccess(`Team '${team.name}' deactivated.`);
      loadAllData();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to deactivate team.");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Layers className="h-6 w-6 text-blue-600" />
            Teams Management
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure teams, coordinators, locations, and member workforces. Rule C2: each (location, dept) pair belongs to exactly one active team.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="primary" onClick={handleOpenCreate} className="flex items-center gap-1.5 text-xs font-bold">
            <Plus className="h-4 w-4" />
            New Team
          </Button>
          <Button variant="ghost" onClick={loadAllData} className="p-2" title="Refresh">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200">
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 text-sm bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 rounded-lg border border-emerald-200">
          {success}
        </div>
      )}

      {/* Teams Table */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
        {loading ? (
          <div className="p-12 text-center text-sm text-slate-500">Loading teams...</div>
        ) : teams.length === 0 ? (
          <div className="p-12 text-center text-sm text-slate-500">No teams configured yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase font-semibold">
                <tr>
                  <th className="py-3 px-4">Team Name</th>
                  <th className="py-3 px-4">Department</th>
                  <th className="py-3 px-4">Coordinator</th>
                  <th className="py-3 px-4">Backup Coordinator</th>
                  <th className="py-3 px-4">Locations</th>
                  <th className="py-3 px-4">Members</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {teams.map((t) => {
                  const dept = departments.find((d) => d.department_id === t.department_id);
                  const coord = users.find((u) => u.user_id === t.coordinator_id);
                  const backup = users.find((u) => u.user_id === t.backup_coordinator_id);

                  return (
                    <tr key={t.team_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-bold text-slate-900 dark:text-slate-100">
                        {t.name}
                      </td>
                      <td className="py-3 px-4 text-slate-700 dark:text-slate-300">
                        {dept ? dept.name : t.department_id}
                      </td>
                      <td className="py-3 px-4 font-medium text-slate-800 dark:text-slate-200">
                        {coord ? coord.name : t.coordinator_id}
                      </td>
                      <td className="py-3 px-4 text-slate-500">
                        {backup ? backup.name : t.backup_coordinator_id || "None (Warning)"}
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-300">
                        <span className="font-semibold">{t.location_ids?.length || 0}</span> locations
                      </td>
                      <td className="py-3 px-4 text-slate-600 dark:text-slate-300">
                        <span className="font-semibold">{t.member_ids?.length || 0}</span> workers
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                            t.active
                              ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300"
                              : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                          }`}
                        >
                          {t.active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => handleOpenEdit(t)} className="p-1">
                            <Edit2 className="h-4 w-4" />
                          </Button>
                          {t.active && (
                            <Button size="sm" variant="ghost" onClick={() => handleDeactivate(t)} className="p-1 text-rose-500 hover:text-rose-700">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Team Create / Edit Modal (covers all C1 fields in one screen) */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingTeam ? `Edit Team: ${editingTeam.name}` : "Create New Team"}
      >
        <form onSubmit={handleSaveTeam} className="space-y-4 max-h-[80vh] overflow-y-auto pr-1">
          {formError && (
            <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200">
              {formError}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
              Team Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Block A – Electrical Team"
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                Department <span className="text-rose-500">*</span>
              </label>
              <select
                value={departmentId}
                onChange={(e) => setDepartmentId(e.target.value)}
                className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {departments.map((d) => (
                  <option key={d.department_id} value={d.department_id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
                Coordinator <span className="text-rose-500">*</span>
              </label>
              <select
                value={coordinatorId}
                onChange={(e) => setCoordinatorId(e.target.value)}
                className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                {candidateCoordinators.map((u) => (
                  <option key={u.user_id} value={u.user_id}>
                    {u.name} ({u.role})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
              Backup Coordinator (Optional)
            </label>
            <select
              value={backupCoordinatorId}
              onChange={(e) => setBackupCoordinatorId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">None</option>
              {candidateMembers
                .filter((u) => u.user_id !== coordinatorId)
                .map((u) => (
                  <option key={u.user_id} value={u.user_id}>
                    {u.name} ({u.role})
                  </option>
                ))}
            </select>
          </div>

          {/* Locations Multi-select */}
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
              Assigned Locations <span className="text-rose-500">*</span>
            </label>
            <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 max-h-36 overflow-y-auto space-y-1.5">
              {locations.map((loc) => (
                <label key={loc.location_id} className="flex items-center gap-2 text-xs cursor-pointer text-slate-800 dark:text-slate-200">
                  <input
                    type="checkbox"
                    checked={selectedLocations.includes(loc.location_id)}
                    onChange={() => handleToggleLocation(loc.location_id)}
                    className="rounded text-blue-600"
                  />
                  <span>{loc.name}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Members Multi-select */}
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
              Team Members (Workers)
            </label>
            <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 max-h-36 overflow-y-auto space-y-1.5">
              {candidateMembers.map((m) => (
                <label key={m.user_id} className="flex items-center gap-2 text-xs cursor-pointer text-slate-800 dark:text-slate-200">
                  <input
                    type="checkbox"
                    checked={
                      selectedMembers.includes(m.user_id) ||
                      m.user_id === coordinatorId ||
                      m.user_id === backupCoordinatorId
                    }
                    disabled={m.user_id === coordinatorId || m.user_id === backupCoordinatorId}
                    onChange={() => handleToggleMember(m.user_id)}
                    className="rounded text-blue-600"
                  />
                  <span>{m.name} ({m.role})</span>
                </label>
              ))}
            </div>
          </div>

          {editingTeam && (
            <div className="pt-1">
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={active}
                  onChange={(e) => setActive(e.target.checked)}
                  className="rounded text-blue-600"
                />
                Team Active
              </label>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-200 dark:border-slate-800">
            <Button variant="secondary" onClick={() => setModalOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={saving}>
              {saving ? "Saving..." : "Save Team"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}


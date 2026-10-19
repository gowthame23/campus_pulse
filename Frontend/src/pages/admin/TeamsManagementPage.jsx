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
  Upload,
  Briefcase,
  X,
  UserCheck,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Modal from "../../components/Modal.jsx";
import Badge from "../../components/Badge.jsx";
import BulkImportModal from "../../components/BulkImportModal.jsx";
import CredentialSlipModal from "../../components/CredentialSlipModal.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { teamService } from "../../services/teamService.js";
import { departmentService } from "../../services/departmentService.js";
import { locationService } from "../../services/locationService.js";
import { userService } from "../../services/userService.js";
import { setupService } from "../../services/setupService.js";

export default function TeamsManagementPage() {
  const { user: currentUser } = useAuth();
  const isAppManager = (currentUser?.role || "").toLowerCase() === "app_manager";

  // Tab State: "teams" | "assignments"
  const [activeTab, setActiveTab] = useState("teams");

  const [teams, setTeams] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [users, setUsers] = useState([]);
  const [employeesOverview, setEmployeesOverview] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showBulkImport, setShowBulkImport] = useState(false);
  const [slipData, setSlipData] = useState(null);

  // Team Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [eligibleCoordinators, setEligibleCoordinators] = useState([]);

  // Form Fields (C1)
  const [name, setName] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [coordinatorId, setCoordinatorId] = useState("");
  const [backupCoordinatorId, setBackupCoordinatorId] = useState("");
  const [selectedLocations, setSelectedLocations] = useState([]);
  const [selectedMembers, setSelectedMembers] = useState([]);
  const [active, setActive] = useState(true);

  // Membership Modal State (Phase 2)
  const [membershipModalOpen, setMembershipModalOpen] = useState(false);
  const [selectedEmployeeForMembership, setSelectedEmployeeForMembership] = useState(null);
  const [membershipDepartmentId, setMembershipDepartmentId] = useState("");
  const [membershipLocationId, setMembershipLocationId] = useState("");
  const [membershipSaving, setMembershipSaving] = useState(false);
  const [membershipError, setMembershipError] = useState("");

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    setLoading(true);
    setError("");
    try {
      const [teamsRes, deptRes, locRes, usersRes, empRes] = await Promise.all([
        teamService.list({ active_only: false }),
        departmentService.list({ include_archived: false }),
        locationService.list(),
        userService.list(),
        teamService.getEmployeesOverview(),
      ]);
      setTeams(teamsRes.data || teamsRes || []);
      setDepartments(deptRes.data || deptRes || []);
      setLocations(locRes.data || locRes || []);
      setUsers(usersRes.data || usersRes || []);
      setEmployeesOverview(empRes.data || empRes || []);
    } catch (err) {
      setError("Failed to load teams and assignments data.");
    } finally {
      setLoading(false);
    }
  };

  const allowedLocations = isAppManager
    ? locations.filter((loc) => {
        const assigned = currentUser?.assigned_locations || [];
        const userLoc = currentUser?.location_id;
        return (
          loc.app_manager_id === currentUser?.user_id ||
          assigned.includes(loc.location_id) ||
          assigned.includes(loc.name) ||
          loc.location_id === userLoc ||
          loc.name === userLoc
        );
      })
    : locations;

  const candidateMembers = users.filter((u) =>
    ["coordinator", "employee"].includes((u.role || "").toLowerCase())
  );

  const fetchEligibleCoordinators = async (teamId) => {
    try {
      const res = await teamService.getEligibleCoordinators(teamId);
      setEligibleCoordinators(res.data || res || []);
    } catch (err) {
      console.error("Failed to fetch eligible coordinators:", err);
      // Fallback
      setEligibleCoordinators([]);
    }
  };

  const handleOpenCreate = async () => {
    setEditingTeam(null);
    setName("");
    setDepartmentId(departments[0]?.department_id || "");
    setCoordinatorId("");
    setBackupCoordinatorId("");
    setSelectedLocations([]);
    setSelectedMembers([]);
    setActive(true);
    setFormError("");

    await fetchEligibleCoordinators(null);
    setModalOpen(true);
  };

  const handleOpenEdit = async (team) => {
    setEditingTeam(team);
    setName(team.name || "");
    setDepartmentId(team.department_id || "");
    setCoordinatorId(team.coordinator_id || "");
    setBackupCoordinatorId(team.backup_coordinator_id || "");
    setSelectedLocations(team.location_ids || []);
    setSelectedMembers(team.member_ids || []);
    setActive(Boolean(team.active));
    setFormError("");

    await fetchEligibleCoordinators(team.team_id);
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
      setFormError("Coordinator 1 is required.");
      return;
    }
    if (coordinatorId === backupCoordinatorId) {
      setFormError("The same employee cannot be both Coordinator 1 and Coordinator 2.");
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

  // -------------------------------------------------------------
  // Phase 2: Work Membership Handlers
  // -------------------------------------------------------------
  const handleOpenAddMembership = (emp) => {
    setSelectedEmployeeForMembership(emp);
    setMembershipDepartmentId(departments[0]?.department_id || "");
    setMembershipLocationId(allowedLocations[0]?.location_id || "");
    setMembershipError("");
    setMembershipModalOpen(true);
  };

  const handleSaveMembership = async (e) => {
    e.preventDefault();
    if (!selectedEmployeeForMembership) return;
    if (!membershipDepartmentId) {
      setMembershipError("Please select a department.");
      return;
    }
    if (!membershipLocationId) {
      setMembershipError("Please select a location.");
      return;
    }

    setMembershipSaving(true);
    setMembershipError("");
    try {
      await teamService.assignWorkMembership({
        user_id: selectedEmployeeForMembership.user_id,
        department_id: membershipDepartmentId,
        location_id: membershipLocationId,
      });
      setSuccess(
        `Added work assignment for ${selectedEmployeeForMembership.name} successfully.`
      );
      setMembershipModalOpen(false);
      loadAllData();
    } catch (err) {
      setMembershipError(
        err.response?.data?.detail || "Failed to assign work membership."
      );
    } finally {
      setMembershipSaving(false);
    }
  };

  const handleRemoveMembership = async (empName, membershipId) => {
    if (!confirm(`Remove this work assignment from ${empName}?`)) return;
    try {
      await teamService.removeWorkMembership(membershipId);
      setSuccess(`Removed work assignment for ${empName}.`);
      loadAllData();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to remove work membership.");
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Layers className="h-6 w-6 text-blue-600" />
            Teams & Workforce Management
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure active teams, department coordinators, and multi-department/multi-location employee assignments.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === "teams" && (
            <>
              <Button
                variant="outline"
                onClick={() => setShowBulkImport(true)}
                className="flex items-center gap-1.5 text-xs font-bold border-indigo-200 text-indigo-700 dark:border-indigo-800 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/40"
              >
                <Upload className="h-4 w-4" />
                Bulk Import Teams
              </Button>
              <Button
                variant="primary"
                onClick={handleOpenCreate}
                className="flex items-center gap-1.5 text-xs font-bold"
              >
                <Plus className="h-4 w-4" />
                New Team
              </Button>
            </>
          )}
          <Button variant="ghost" onClick={loadAllData} className="p-2" title="Refresh">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 gap-4 sm:gap-6 overflow-x-auto max-w-full scrollbar-none">
        <button
          onClick={() => setActiveTab("teams")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap shrink-0 ${
            activeTab === "teams"
              ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Layers className="h-4 w-4" />
          Teams Directory
          <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold">
            {teams.length}
          </span>
        </button>
        <button
          onClick={() => setActiveTab("assignments")}
          className={`pb-3 text-sm font-semibold border-b-2 flex items-center gap-2 transition-colors whitespace-nowrap shrink-0 ${
            activeTab === "assignments"
              ? "border-blue-600 text-blue-600 dark:border-blue-400 dark:text-blue-400"
              : "border-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
          }`}
        >
          <Briefcase className="h-4 w-4" />
          Employee Assignments (Multi-Dept / Multi-Location)
          <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold">
            {employeesOverview.length}
          </span>
        </button>
      </div>

      {error && (
        <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200">
          {error}
        </div>
      )}
      {success && (
        <div className="p-3 text-sm bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 rounded-lg border border-emerald-200 flex items-center justify-between">
          <span>{success}</span>
          <button onClick={() => setSuccess("")} className="text-emerald-800 dark:text-emerald-200 font-bold">
            ×
          </button>
        </div>
      )}

      {/* TAB 1: Teams Directory */}
      {activeTab === "teams" && (
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
                    <th className="py-3 px-4">Coordinator 1 (Primary)</th>
                    <th className="py-3 px-4">Coordinator 2 (Backup)</th>
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
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-300 font-semibold text-[11px]">
                            {coord ? coord.name : t.coordinator_id}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-slate-500">
                          {backup ? (
                            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 font-semibold text-[11px]">
                              {backup.name}
                            </span>
                          ) : (
                            <span className="text-amber-600 dark:text-amber-400 italic">None (Warning)</span>
                          )}
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
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => handleDeactivate(t)}
                                className="p-1 text-rose-500 hover:text-rose-700"
                              >
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
      )}

      {/* TAB 2: Employee Assignments (Phase 2) */}
      {activeTab === "assignments" && (
        <div className="space-y-4">
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 rounded-xl p-3.5 text-xs text-blue-800 dark:text-blue-300 flex items-start gap-2.5">
            <Briefcase className="h-4 w-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Multi-Department & Multi-Location Assignments: </span>
              Employees can be assigned to multiple (Department, Location) work memberships (e.g., Electrical in Hostel 1, Plumbing in Hostel 2).
              {isAppManager && (
                <span className="ml-1 text-amber-700 dark:text-amber-300 font-semibold">
                  (You are managing facilities within your authorized App Manager scope).
                </span>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 overflow-hidden shadow-sm">
            {loading ? (
              <div className="p-12 text-center text-sm text-slate-500">Loading employees...</div>
            ) : employeesOverview.length === 0 ? (
              <div className="p-12 text-center text-sm text-slate-500">No employees found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase font-semibold">
                    <tr>
                      <th className="py-3 px-4">Employee</th>
                      <th className="py-3 px-4">Coordinator Position</th>
                      <th className="py-3 px-4">Active Work Memberships (Dept • Location)</th>
                      <th className="py-3 px-4">Open Jobs</th>
                      <th className="py-3 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {employeesOverview.map((emp) => {
                      const coord = emp.coordinator_role;

                      return (
                        <tr key={emp.user_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                          <td className="py-3 px-4">
                            <div className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                              {emp.name}
                              {emp.on_leave && (
                                <span className="text-[10px] px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300 font-semibold">
                                  On Leave
                                </span>
                              )}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                              {emp.email || emp.phone || emp.user_id}
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            {emp.coordinator_roles && emp.coordinator_roles.length > 0 ? (
                              <div className="flex flex-col gap-1">
                                {emp.coordinator_roles.map((cr, idx) => (
                                  <span key={idx} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                                    <Shield className="h-3 w-3" />
                                    {cr.position}
                                  </span>
                                ))}
                              </div>
                            ) : coord ? (
                              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800">
                                <Shield className="h-3 w-3" />
                                {coord.position}: {coord.team_name}
                              </span>
                            ) : (
                              <span className="text-slate-400 italic">None (Regular Worker)</span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex flex-wrap gap-1.5 max-w-lg">
                              {emp.memberships && emp.memberships.length > 0 ? (
                                emp.memberships.map((m) => (
                                  <span
                                    key={m.membership_id}
                                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700"
                                  >
                                    <span className="font-semibold text-blue-600 dark:text-blue-400">
                                      {m.department_name}
                                    </span>
                                    <span className="text-slate-400">•</span>
                                    <span>{m.location_name}</span>
                                    <button
                                      type="button"
                                      onClick={() => handleRemoveMembership(emp.name, m.membership_id)}
                                      className="ml-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 font-bold"
                                      title="Remove assignment"
                                    >
                                      <X className="h-3 w-3" />
                                    </button>
                                  </span>
                                ))
                              ) : (
                                <span className="text-slate-400 italic">No memberships assigned yet</span>
                              )}
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                                emp.open_jobs > 0
                                  ? "bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-300"
                                  : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                              }`}
                            >
                              {emp.open_jobs} active
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleOpenAddMembership(emp)}
                              className="text-xs font-semibold flex items-center gap-1 ml-auto"
                            >
                              <Plus className="h-3.5 w-3.5" />
                              Add Assignment
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Team Create / Edit Modal (Phase 3: Global One-Coordinator Rule) */}
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
                Coordinator 1 (Primary) <span className="text-rose-500">*</span>
              </label>
              <select
                value={coordinatorId}
                onChange={(e) => setCoordinatorId(e.target.value)}
                className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Select Coordinator 1...</option>
                {eligibleCoordinators.map((u) => {
                  const isCurrent = u.user_id === coordinatorId;
                  const isSelectedAsBackup = u.user_id === backupCoordinatorId;
                  const isAvailable = u.is_eligible || isCurrent;

                  let label = `${u.name} (${u.role})`;
                  if (!isAvailable) {
                    label += ` — Unavailable (${u.current_position} on ${u.current_team_name})`;
                  } else if (isSelectedAsBackup) {
                    label += ` — (Selected as Backup Coordinator)`;
                  }

                  return (
                    <option
                      key={u.user_id}
                      value={u.user_id}
                      disabled={!isAvailable || isSelectedAsBackup}
                    >
                      {label}
                    </option>
                  );
                })}
              </select>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Rule: An employee cannot hold both Coordinator 1 and Coordinator 2 on the same team, but can coordinate multiple teams/departments.
              </p>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
              Coordinator 2 (Backup — Optional)
            </label>
            <select
              value={backupCoordinatorId}
              onChange={(e) => setBackupCoordinatorId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">None</option>
              {eligibleCoordinators.map((u) => {
                const isCurrent = u.user_id === backupCoordinatorId;
                const isSelectedAsPrimary = u.user_id === coordinatorId;
                const isAvailable = u.is_eligible || isCurrent;

                let label = `${u.name} (${u.role})`;
                if (!isAvailable) {
                  label += ` — Unavailable (${u.current_position} on ${u.current_team_name})`;
                } else if (isSelectedAsPrimary) {
                  label += ` — (Selected as Coordinator 1)`;
                }

                return (
                  <option
                    key={u.user_id}
                    value={u.user_id}
                    disabled={!isAvailable || isSelectedAsPrimary}
                  >
                    {label}
                  </option>
                );
              })}
            </select>
          </div>

          {/* Locations Multi-select (Scoped for App Manager) */}
          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
              Assigned Locations <span className="text-rose-500">*</span>
            </label>
            <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-2.5 max-h-36 overflow-y-auto space-y-1.5">
              {allowedLocations.map((loc) => (
                <label
                  key={loc.location_id}
                  className="flex items-center gap-2 text-xs cursor-pointer text-slate-800 dark:text-slate-200"
                >
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
                <label
                  key={m.user_id}
                  className="flex items-center gap-2 text-xs cursor-pointer text-slate-800 dark:text-slate-200"
                >
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
                  <span>
                    {m.name} ({m.role})
                  </span>
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

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button type="button" variant="ghost" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={saving}>
              {saving ? "Saving..." : editingTeam ? "Update Team" : "Create Team"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Modal: Add Department-Location Work Membership (Phase 2) */}
      <Modal
        isOpen={membershipModalOpen}
        onClose={() => setMembershipModalOpen(false)}
        title={
          selectedEmployeeForMembership
            ? `Assign Work Membership: ${selectedEmployeeForMembership.name}`
            : "Assign Work Membership"
        }
      >
        <form onSubmit={handleSaveMembership} className="space-y-4">
          {membershipError && (
            <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200">
              {membershipError}
            </div>
          )}

          <div className="bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200 dark:border-slate-700 text-xs">
            <div className="font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Current Assignments for {selectedEmployeeForMembership?.name}:
            </div>
            {selectedEmployeeForMembership?.memberships?.length > 0 ? (
              <div className="flex flex-wrap gap-1 mt-1">
                {selectedEmployeeForMembership.memberships.map((m) => (
                  <span
                    key={m.membership_id}
                    className="px-2 py-0.5 rounded bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-300 font-medium"
                  >
                    {m.department_name} • {m.location_name}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-slate-400 italic">None</span>
            )}
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase text-slate-700 dark:text-slate-300 mb-1">
              Department <span className="text-rose-500">*</span>
            </label>
            <select
              value={membershipDepartmentId}
              onChange={(e) => setMembershipDepartmentId(e.target.value)}
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
              Facility Location <span className="text-rose-500">*</span>
            </label>
            <select
              value={membershipLocationId}
              onChange={(e) => setMembershipLocationId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              {allowedLocations.map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name} ({loc.location_type || "Facility"})
                </option>
              ))}
            </select>
            {isAppManager && (
              <p className="text-[11px] text-slate-500 mt-1">
                Scoped to locations within your App Manager authority.
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-slate-200 dark:border-slate-800">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setMembershipModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" disabled={membershipSaving}>
              {membershipSaving ? "Assigning..." : "Assign Membership"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Bulk Import Modal */}
      <BulkImportModal
        isOpen={showBulkImport}
        onClose={() => setShowBulkImport(false)}
        onImportSuccess={() => {
          setShowBulkImport(false);
          loadAllData();
        }}
      />

      {/* Credential Slip Modal */}
      {slipData && (
        <CredentialSlipModal
          isOpen={Boolean(slipData)}
          onClose={() => setSlipData(null)}
          slip={slipData}
        />
      )}
    </div>
  );
}

import React, { useState, useEffect, useMemo } from "react";
import { 
  Users, 
  MapPin, 
  Building, 
  Plus, 
  Trash2, 
  Search, 
  Filter, 
  Briefcase, 
  ShieldCheck, 
  CheckCircle2, 
  AlertCircle,
  X
} from "lucide-react";
import { teamService } from "../../services/teamService.js";
import { departmentService } from "../../services/departmentService.js";
import { userService } from "../../services/userService.js";
import { useAuth } from "../../context/AuthContext.jsx";
import Button from "../../components/Button.jsx";
import Modal from "../../components/Modal.jsx";
import Badge from "../../components/Badge.jsx";
import Card from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import Select from "../../components/Select.jsx";

export default function EmployeeAssignmentsPage() {
  const { user } = useAuth();

  // Data states
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterDept, setFilterDept] = useState("");

  // Assign modal state
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [assignUserId, setAssignUserId] = useState("");
  const [assignDeptId, setAssignDeptId] = useState("");
  const [assigning, setAssigning] = useState(false);
  const [modalError, setModalError] = useState("");
  const [toastMessage, setToastMessage] = useState("");

  const loadData = async () => {
    setLoading(true);
    try {
      const [empRes, deptRes] = await Promise.all([
        teamService.listEmployeesOverview().catch(() => ({ data: [] })),
        departmentService.list({ include_archived: false }).catch(() => ({ data: [] }))
      ]);

      setEmployees(empRes.data || empRes || []);
      setDepartments(deptRes.data || deptRes || []);
    } catch (err) {
      console.error("Failed to load employee assignment data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(""), 4000);
  };

  const handleOpenAssignModal = (prefillUserId = "") => {
    setAssignUserId(prefillUserId || (employees.length > 0 ? employees[0].user_id : ""));
    setAssignDeptId(departments.length > 0 ? departments[0].department_id : "");
    setModalError("");
    setIsAssignModalOpen(true);
  };

  const handleSaveAssignment = async (e) => {
    e.preventDefault();
    if (!assignUserId || !assignDeptId) {
      setModalError("Please select an employee and a department.");
      return;
    }

    setAssigning(true);
    setModalError("");
    try {
      const emp = employees.find(e => e.user_id === assignUserId);
      const currentDeptIds = (emp?.memberships || []).map(m => m.department_id);
      if (emp?.department_id) currentDeptIds.push(emp.department_id);
      const newDeptIds = Array.from(new Set([...currentDeptIds, assignDeptId]));

      await userService.assignDepartments(assignUserId, newDeptIds);
      showToast("Employee department assignment updated successfully (Campus-wide).");
      setIsAssignModalOpen(false);
      await loadData();
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || "Failed to update assignment.";
      setModalError(detail);
    } finally {
      setAssigning(false);
    }
  };

  const handleRemoveDepartmentAssignment = async (userId, deptId, deptName, employeeName) => {
    if (!window.confirm(`Remove ${deptName} eligibility for ${employeeName}?`)) return;
    try {
      const emp = employees.find(e => e.user_id === userId);
      const currentDeptIds = (emp?.memberships || []).map(m => m.department_id);
      if (emp?.department_id) currentDeptIds.push(emp.department_id);
      const updatedDeptIds = Array.from(new Set(currentDeptIds)).filter(id => id !== deptId);

      await userService.assignDepartments(userId, updatedDeptIds);
      showToast(`Removed ${deptName} eligibility for ${employeeName}.`);
      await loadData();
    } catch (err) {
      alert(err.response?.data?.detail || err.message || "Failed to remove assignment.");
    }
  };

  const filteredEmployees = useMemo(() => {
    return employees.filter(emp => {
      const q = searchQuery.toLowerCase();
      const matchesSearch = !q || 
        emp.name?.toLowerCase().includes(q) || 
        emp.email?.toLowerCase().includes(q) ||
        emp.phone?.includes(q);

      const matchesDept = !filterDept || 
        emp.department_id === filterDept || 
        (emp.memberships || []).some(m => m.department_id === filterDept);

      return matchesSearch && matchesDept;
    });
  }, [employees, searchQuery, filterDept]);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Toast */}
      {toastMessage && (
        <div className="fixed top-5 right-5 z-50 bg-emerald-600 text-white px-4 py-3 rounded-xl shadow-lg flex items-center gap-2 text-sm font-medium animate-in fade-in slide-in-from-top-3">
          <CheckCircle2 className="h-4 w-4" />
          {toastMessage}
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <Briefcase className="h-6 w-6 text-primary" />
            Employee Department Assignments
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage campus-wide department eligibility for technicians and staff. Every employee is eligible to work across all campus locations.
          </p>
        </div>
        <Button onClick={() => handleOpenAssignModal()} className="flex items-center gap-2 self-start sm:self-auto">
          <Plus className="h-4 w-4" />
          Assign Department
        </Button>
      </div>

      {/* Search and Filters */}
      <Card className="p-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              placeholder="Search by employee name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs"
            />
          </div>
          <Select
            value={filterDept}
            onChange={(e) => setFilterDept(e.target.value)}
            className="text-xs"
          >
            <option value="">All Departments</option>
            {departments.map((d) => (
              <option key={d.department_id} value={d.department_id}>
                {d.name}
              </option>
            ))}
          </Select>
        </div>
      </Card>

      {/* Employees Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 font-semibold border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Employee</th>
                <th className="py-3.5 px-4">Role & Coordinator Scope</th>
                <th className="py-3.5 px-4">Eligible Departments (Campus-wide)</th>
                <th className="py-3.5 px-4 text-center">Open Jobs</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    Loading employee assignments...
                  </td>
                </tr>
              ) : filteredEmployees.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-slate-400">
                    No employees matching the current filters.
                  </td>
                </tr>
              ) : (
                filteredEmployees.map((emp) => {
                  const coord = emp.coordinator_role;
                  
                  // Extract unique departments for this employee
                  const deptMap = new Map();
                  (emp.memberships || []).forEach(m => {
                    if (m.department_id && !deptMap.has(m.department_id)) {
                      deptMap.set(m.department_id, m.department_name);
                    }
                  });
                  if (emp.department_id && !deptMap.has(emp.department_id)) {
                    const dObj = departments.find(d => d.department_id === emp.department_id);
                    deptMap.set(emp.department_id, dObj?.name || emp.department_name || emp.department_id);
                  }

                  const deptEntries = Array.from(deptMap.entries());

                  return (
                    <tr key={emp.user_id} className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900 dark:text-slate-100">
                          {emp.name}
                        </div>
                        <div className="text-[11px] text-slate-500">{emp.email}</div>
                      </td>
                      <td className="py-3 px-4">
                        {coord ? (
                          <div className="flex flex-col gap-1 items-start">
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
                              <ShieldCheck className="h-3 w-3" />
                              {coord.position || "Coordinator"}
                            </span>
                          </div>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                            Technician
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {deptEntries.length === 0 ? (
                          <span className="text-[11px] italic text-slate-400">
                            No assigned departments
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1.5 max-w-lg">
                            {deptEntries.map(([deptId, deptName]) => (
                              <span
                                key={deptId}
                                className="inline-flex items-center gap-1.5 pl-2.5 pr-1.5 py-1 rounded-lg text-[11px] bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900 font-medium"
                              >
                                <Building className="h-3 w-3 text-blue-500" />
                                <span>{deptName}</span>
                                <span className="px-1.5 py-0.2 rounded text-[9px] bg-blue-100 dark:bg-blue-900/60 text-blue-800 dark:text-blue-200 font-semibold">
                                  Campus-wide
                                </span>
                                <button
                                  type="button"
                                  onClick={() => handleRemoveDepartmentAssignment(emp.user_id, deptId, deptName, emp.name)}
                                  className="ml-0.5 p-0.5 hover:bg-blue-200 dark:hover:bg-blue-800 rounded text-blue-600 dark:text-blue-400 hover:text-red-600 dark:hover:text-red-400 transition"
                                  title={`Remove ${deptName} eligibility`}
                                >
                                  <X className="h-3 w-3" />
                                </button>
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${
                          emp.open_jobs > 0
                            ? "bg-amber-100 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                        }`}>
                          {emp.open_jobs}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenAssignModal(emp.user_id)}
                          className="text-[11px] text-primary"
                        >
                          + Assign
                        </Button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Modal: Add Assignment */}
      <Modal
        isOpen={isAssignModalOpen}
        onClose={() => setIsAssignModalOpen(false)}
        title="Assign Employee to Department"
      >
        <form onSubmit={handleSaveAssignment} className="space-y-4 text-xs">
          {modalError && (
            <div className="p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 rounded-lg flex items-center gap-2">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{modalError}</span>
            </div>
          )}

          <div>
            <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
              Select Employee *
            </label>
            <Select
              value={assignUserId}
              onChange={(e) => setAssignUserId(e.target.value)}
              required
            >
              <option value="">-- Choose Employee --</option>
              {employees.map((e) => (
                <option key={e.user_id} value={e.user_id}>
                  {e.name} ({e.email})
                </option>
              ))}
            </Select>
          </div>

          <div>
            <label className="block text-slate-700 dark:text-slate-300 font-semibold mb-1">
              Department *
            </label>
            <Select
              value={assignDeptId}
              onChange={(e) => setAssignDeptId(e.target.value)}
              required
            >
              <option value="">-- Choose Department --</option>
              {departments.map((d) => (
                <option key={d.department_id} value={d.department_id}>
                  {d.name}
                </option>
              ))}
            </Select>
            <p className="text-[11px] text-slate-500 mt-1.5 flex items-center gap-1">
              <Building className="h-3 w-3 text-emerald-500" />
              Every employee assigned to this department is eligible across all campus locations.
            </p>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsAssignModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={assigning}>
              {assigning ? "Saving..." : "Save Department Assignment"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

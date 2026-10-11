import { useState, useEffect } from "react";
import { Plus, CheckCircle, XCircle } from "lucide-react";
// Rendered inside global MainLayout via ProtectedRoute
import Toast from "../../components/Toast.jsx";
import Loader from "../../components/Loader.jsx";
import apiClient from "../../api/axios.js";

export default function IssueManagementPage() {
  const [locations, setLocations] = useState([]);
  const [selectedLoc, setSelectedLoc] = useState("");
  const [departments, setDepartments] = useState([]);
  const [selectedDept, setSelectedDept] = useState("");
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [newIssueName, setNewIssueName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  useEffect(() => {
    fetchLocations();
  }, []);

  useEffect(() => {
    if (selectedLoc) {
      fetchDepartments(selectedLoc);
    } else {
      setDepartments([]);
      setSelectedDept("");
    }
  }, [selectedLoc]);

  useEffect(() => {
    if (selectedDept) {
      fetchIssues(selectedDept);
    } else {
      setIssues([]);
    }
  }, [selectedDept]);

  const fetchLocations = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/locations");
      setLocations(res.data || []);
      if (res.data?.length > 0) {
        setSelectedLoc(res.data[0].location_id);
      }
    } catch (err) {
      setToast({ type: "error", message: "Failed to load locations" });
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartments = async (locId) => {
    try {
      setLoading(true);
      const res = await apiClient.get("/departments?location_id=" + locId);
      setDepartments(res.data || []);
      if (res.data?.length > 0) {
        setSelectedDept(res.data[0].department_id);
      } else {
        setSelectedDept("");
      }
    } catch (err) {
      setToast({ type: "error", message: "Failed to load departments" });
    } finally {
      setLoading(false);
    }
  };

  const fetchIssues = async (deptId) => {
    try {
      setLoading(true);
      const res = await apiClient.get("/issues?department_id=" + deptId);
      setIssues(res.data || []);
    } catch (err) {
      setIssues([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateIssue = async (e) => {
    e.preventDefault();
    if (!newIssueName.trim()) return;
    try {
      await apiClient.post("/issues", {
        department_id: selectedDept,
        issue_name: newIssueName,
        description: newDesc,
      });
      setToast({ type: "success", message: "Issue added successfully" });
      setShowModal(false);
      setNewIssueName("");
      setNewDesc("");
      fetchIssues(selectedDept);
    } catch (err) {
      setToast({ type: "error", message: "Failed to add issue" });
    }
  };

  return (
    <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">
              Department Issue Management
            </h1>
            <p className="text-sm text-slate-500">
              Manage predefined issue types per department for guided complaint
              creation.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-primary/90"
          >
            <Plus className="h-4 w-4" /> Add Issue Type
          </button>
        </div>

        {toast && (
          <Toast
            tone={toast.type}
            message={toast.message}
            onClose={() => setToast(null)}
          />
        )}

        <div className="flex flex-wrap items-center gap-6 bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <label className="text-sm font-bold text-slate-700 dark:text-slate-200">
              Select Location:
            </label>
            <select
              value={selectedLoc}
              onChange={(e) => setSelectedLoc(e.target.value)}
              className="rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 px-3 py-2 text-sm min-w-56"
            >
              {locations.map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm font-bold text-slate-700 dark:text-slate-200">
              Select Department:
            </label>
            <select
              value={selectedDept}
              onChange={(e) => setSelectedDept(e.target.value)}
              className="rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100 px-3 py-2 text-sm min-w-56"
              disabled={departments.length === 0}
            >
              {departments.map((d) => (
                <option
                  key={d.department_id}
                  value={d.department_id}
                >
                  {d.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <Loader label="Loading issues..." />
        ) : (
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">
              Configured Issues ({issues.length})
            </h2>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
              {issues.map((i) => (
                <div
                  key={i.issue_id}
                  className="flex items-center justify-between rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 p-4"
                >
                  <div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100">
                      {i.issue_name}
                    </div>
                    <div className="text-xs text-slate-500">
                      {i.description || "No description"}
                    </div>
                  </div>
                  {i.active ? (
                    <CheckCircle className="h-5 w-5 text-emerald-500" />
                  ) : (
                    <XCircle className="h-5 w-5 text-slate-400" />
                  )}
                </div>
              ))}
              {issues.length === 0 && (
                <div className="col-span-full py-8 text-center text-sm text-slate-500">
                  No issue types defined for this department. Click Add Issue
                  Type to create one.
                </div>
              )}
            </div>
          </div>
        )}

        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-slate-900 dark:text-slate-100 mb-4">
                Add New Issue Type
              </h3>
              <form onSubmit={handleCreateIssue} className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Issue Name
                  </label>
                  <input
                    type="text"
                    value={newIssueName}
                    onChange={(e) => setNewIssueName(e.target.value)}
                    required
                    className="w-full rounded-xl border border-slate-300 p-2.5 text-sm"
                    placeholder="e.g. Power Failure, Fan Not Working"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Description (Optional)
                  </label>
                  <textarea
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                    className="w-full rounded-xl border border-slate-300 p-2.5 text-sm"
                    rows="3"
                    placeholder="Brief explanation"
                  ></textarea>
                </div>
                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="rounded-xl px-4 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-100"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-primary/90"
                  >
                    Create Issue
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
    </div>
  );
}

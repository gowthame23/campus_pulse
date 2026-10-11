import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  FileText,
  AlertCircle,
  UserCheck,
  Clock,
  CheckCircle2,
  User,
  MapPin,
  Building,
  RotateCw,
  UserPlus,
  Layers,
} from "lucide-react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Table from "../../components/Table.jsx";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Loader from "../../components/Loader.jsx";
import Toast from "../../components/Toast.jsx";
import Modal from "../../components/Modal.jsx";
import { complaintService } from "../../services/complaintService.js";
import { userService } from "../../services/userService.js";
import { getApiError } from "../../api/axios.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone, getSlaTone } from "../../utils/statusColor.js";

export default function WorkloadPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toastMessage, setToastMessage] = useState("");

  // Assignment Modal state
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [staffList, setStaffList] = useState([]);
  const [selectedStaffId, setSelectedStaffId] = useState("");
  const [assigning, setAssigning] = useState(false);

  const fetchWorkload = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await complaintService.getWorkload();
      setData(res.data || res);
    } catch (err) {
      setError(getApiError(err, "Failed to load workload summary."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkload();
  }, []);

  const openAssignModal = async (complaint) => {
    setSelectedComplaint(complaint);
    setSelectedStaffId("");
    try {
      const usersRes = await userService.list();
      const rawUsers = usersRes.data || usersRes;
      const validUsers = (Array.isArray(rawUsers) ? rawUsers : rawUsers.items || []).filter(
        (u) => u.role !== "student" && u.role !== "super_admin"
      );
      setStaffList(validUsers);
    } catch (err) {
      // Fall back to staff in data
      if (data) {
        const combined = [
          ...(data.app_managers || []),
          ...(data.wardens || []),
          ...(data.coordinators || []),
        ];
        setStaffList(combined);
      }
    }
  };

  const handleAssign = async () => {
    if (!selectedComplaint || !selectedStaffId) return;
    setAssigning(true);
    try {
      await complaintService.assign(selectedComplaint.complaint_id, selectedStaffId);
      setToastMessage(`Complaint ${selectedComplaint.complaint_id} assigned successfully.`);
      setSelectedComplaint(null);
      fetchWorkload();
    } catch (err) {
      setToastMessage(getApiError(err, "Failed to assign complaint."));
    } finally {
      setAssigning(false);
    }
  };

  if (loading && !data) {
    return (
      <main className="grid min-h-[60vh] place-items-center">
        <Loader label="Loading operational workload data..." />
      </main>
    );
  }

  const summary = data?.summary || {
    total: 0,
    unassigned: 0,
    assigned: 0,
    left: 0,
    resolved: 0,
  };

  return (
    <div className="space-y-6">
      {toastMessage && (
        <Toast
          message={toastMessage}
          type={toastMessage.includes("Failed") ? "error" : "success"}
          onClose={() => setToastMessage("")}
        />
      )}

      <PageHeader
        title="Workload & Assignments"
        description="Monitor staff operational workload, track active open complaints, and process unassigned tickets."
      >
        <Button
          variant="outline"
          size="sm"
          onClick={fetchWorkload}
          leftIcon={<RotateCw className="h-4 w-4" />}
        >
          Refresh
        </Button>
      </PageHeader>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Total Scope</span>
            <div className="rounded-lg bg-slate-100 p-2 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              <FileText className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{summary.total}</p>
        </Card>

        <Card className="p-4 border-amber-200 bg-amber-50/40 dark:border-amber-900/40 dark:bg-amber-950/10">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-700 dark:text-amber-400">Unassigned Pool</span>
            <div className="rounded-lg bg-amber-100 p-2 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">
              <AlertCircle className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-amber-900 dark:text-amber-200">{summary.unassigned}</p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Assigned</span>
            <div className="rounded-lg bg-blue-100 p-2 text-blue-600 dark:bg-blue-900/50 dark:text-blue-300">
              <UserCheck className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{summary.assigned}</p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Left (Active)</span>
            <div className="rounded-lg bg-orange-100 p-2 text-orange-600 dark:bg-orange-900/50 dark:text-orange-300">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-orange-600 dark:text-orange-400">{summary.left}</p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Resolved</span>
            <div className="rounded-lg bg-emerald-100 p-2 text-emerald-600 dark:bg-emerald-900/50 dark:text-emerald-300">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{summary.resolved}</p>
        </Card>
      </div>

      {/* Staff Workload Sections */}
      {data?.app_managers?.length > 0 && (
        <Card className="p-5">
          <h3 className="mb-4 text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Building className="h-4 w-4 text-primary" />
            App Managers Workload
          </h3>
          <Table
            columns={[
              {
                header: "App Manager",
                accessor: "name",
                render: (row) => (
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">{row.name}</div>
                    <div className="text-xs text-slate-400">{row.email}</div>
                  </div>
                ),
              },
              {
                header: "Assigned",
                accessor: "assigned",
                render: (row) => (
                  <span className="font-semibold text-blue-600 dark:text-blue-400">{row.assigned}</span>
                ),
              },
              {
                header: "Left (Active)",
                accessor: "left",
                render: (row) => (
                  <span className="font-semibold text-orange-600 dark:text-orange-400">{row.left}</span>
                ),
              },
              {
                header: "Resolved",
                accessor: "resolved",
                render: (row) => (
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">{row.resolved}</span>
                ),
              },
            ]}
            rows={data?.app_managers || []}
            data={data?.app_managers || []}
          />
        </Card>
      )}

      {data?.wardens?.length > 0 && (
        <Card className="p-5">
          <h3 className="mb-4 text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <MapPin className="h-4 w-4 text-indigo-500" />
            Wardens / Location In-Charges Workload
          </h3>
          <Table
            columns={[
              {
                header: "Warden / Location In-Charge",
                accessor: "name",
                render: (row) => (
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">{row.name}</div>
                    <div className="text-xs text-slate-400">{row.email}</div>
                  </div>
                ),
              },
              {
                header: "Location Block",
                accessor: "location_name",
                render: (row) => (
                  <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                    {row.location_name || row.location_id || "Unspecified"}
                  </span>
                ),
              },
              {
                header: "Assigned",
                accessor: "assigned",
                render: (row) => (
                  <span className="font-semibold text-blue-600 dark:text-blue-400">{row.assigned}</span>
                ),
              },
              {
                header: "Left (Active)",
                accessor: "left",
                render: (row) => (
                  <span className="font-semibold text-orange-600 dark:text-orange-400">{row.left}</span>
                ),
              },
              {
                header: "Resolved",
                accessor: "resolved",
                render: (row) => (
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">{row.resolved}</span>
                ),
              },
            ]}
            rows={data?.wardens || []}
            data={data?.wardens || []}
          />
        </Card>
      )}

      {data?.coordinators?.length > 0 && (
        <Card className="p-5">
          <h3 className="mb-4 text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Layers className="h-4 w-4 text-teal-500" />
            Coordinators Workload
          </h3>
          <Table
            columns={[
              {
                header: "Coordinator",
                accessor: "name",
                render: (row) => (
                  <div>
                    <div className="font-semibold text-slate-900 dark:text-white">{row.name}</div>
                    <div className="text-xs text-slate-400">{row.email}</div>
                  </div>
                ),
              },
              {
                header: "Department",
                accessor: "department_name",
                render: (row) => (
                  <span className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                    {row.department_name || row.department_id || "Unspecified"}
                  </span>
                ),
              },
              {
                header: "Assigned",
                accessor: "assigned",
                render: (row) => (
                  <span className="font-semibold text-blue-600 dark:text-blue-400">{row.assigned}</span>
                ),
              },
              {
                header: "Left (Active)",
                accessor: "left",
                render: (row) => (
                  <span className="font-semibold text-orange-600 dark:text-orange-400">{row.left}</span>
                ),
              },
              {
                header: "Resolved",
                accessor: "resolved",
                render: (row) => (
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">{row.resolved}</span>
                ),
              },
            ]}
            rows={data?.coordinators || []}
            data={data?.coordinators || []}
          />
        </Card>
      )}

      {/* Unassigned Complaints Pool */}
      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-amber-500" />
              Unassigned Complaint Pool
            </h3>
            <p className="text-xs text-slate-500">
              Complaints requiring assignment to a responsible Warden or Coordinator.
            </p>
          </div>
          <Badge tone="warning">{data?.unassigned_complaints?.length || 0} Unassigned</Badge>
        </div>

        {data?.unassigned_complaints?.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 py-8 text-center dark:border-slate-800">
            <CheckCircle2 className="mx-auto h-8 w-8 text-emerald-500" />
            <p className="mt-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
              All complaints are currently assigned!
            </p>
            <p className="text-xs text-slate-400">No pending unassigned complaints in your operational pool.</p>
          </div>
        ) : (
          <Table
            columns={[
              {
                header: "Complaint Details",
                accessor: "title",
                render: (c) => (
                  <div>
                    <Link
                      to={`/complaints/${c.complaint_id}`}
                      className="font-semibold text-primary hover:underline"
                    >
                      {c.title || c.category || c.complaint_id}
                    </Link>
                    <div className="text-xs text-slate-500 line-clamp-1">{c.description}</div>
                    <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                      <span>ID: {c.complaint_id}</span>
                      <span>•</span>
                      <span>Filed: {formatDate(c.created_at)}</span>
                    </div>
                  </div>
                ),
              },
              {
                header: "Location & Dept",
                accessor: "location_name",
                render: (c) => (
                  <div className="text-xs">
                    <div className="font-medium text-slate-800 dark:text-slate-200">
                      {c.location_name || c.location_id}
                    </div>
                    <div className="text-slate-500">{c.department_name || c.department_id}</div>
                  </div>
                ),
              },
              {
                header: "Priority / SLA",
                accessor: "priority",
                render: (c) => (
                  <div className="flex flex-col gap-1">
                    <Badge tone={c.priority === "Urgent" ? "danger" : c.priority === "High" ? "warning" : "neutral"}>
                      {c.priority || "Medium"}
                    </Badge>
                    <Badge tone={getSlaTone(c.sla_status)}>
                      {c.sla_status || "🟢 On Time"}
                    </Badge>
                  </div>
                ),
              },
              {
                header: "Action",
                accessor: "complaint_id",
                render: (c) => (
                  <Button
                    size="xs"
                    variant="primary"
                    onClick={() => openAssignModal(c)}
                    leftIcon={<UserPlus className="h-3.5 w-3.5" />}
                  >
                    Assign Work
                  </Button>
                ),
              },
            ]}
            rows={data?.unassigned_complaints || []}
            data={data?.unassigned_complaints || []}
          />
        )}
      </Card>

      {/* Assignment Modal */}
      {selectedComplaint && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedComplaint(null)}
          title={`Assign Complaint: ${selectedComplaint.complaint_id}`}
        >
          <div className="space-y-4">
            <div className="rounded-lg bg-slate-50 p-3 text-xs dark:bg-slate-800">
              <div className="font-semibold text-slate-800 dark:text-slate-200">
                {selectedComplaint.title || selectedComplaint.category}
              </div>
              <div className="text-slate-500">{selectedComplaint.description}</div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Select Staff Member
              </label>
              <select
                value={selectedStaffId}
                onChange={(e) => setSelectedStaffId(e.target.value)}
                className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              >
                <option value="">-- Choose Staff Member --</option>
                {staffList.map((st) => (
                  <option key={st.user_id} value={st.user_id}>
                    {st.name} ({st.role?.replace("_", " ")}) - {st.department_name || st.location_name || st.email}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedComplaint(null)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                disabled={!selectedStaffId || assigning}
                onClick={handleAssign}
              >
                {assigning ? "Assigning..." : "Confirm Assignment"}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

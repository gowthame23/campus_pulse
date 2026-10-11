import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import {
  PlusCircle,
  RotateCw,
  Edit2,
  Archive,
  Trash2,
  RefreshCw,
  MapPin,
  Building,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import Toast from "../../components/Toast.jsx";
import Modal from "../../components/Modal.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { departmentService } from "../../services/departmentService.js";
import { userService } from "../../services/userService.js";
import { locationService } from "../../services/locationService.js";
import { ROLES } from "../../utils/constants.js";
import { getApiError } from "../../api/axios.js";

export default function DepartmentManagementPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState("");

  // Edit State
  const [editTarget, setEditTarget] = useState(null);
  const [editName, setEditName] = useState("");
  const [editSla, setEditSla] = useState("");
  const [editComplaintTypes, setEditComplaintTypes] = useState("");

  // Delete Confirmation State
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteInput, setDeleteInput] = useState("");
  const [deleteDependencyError, setDeleteDependencyError] = useState("");

  // Categories Modal State
  const [viewCategoriesTarget, setViewCategoriesTarget] = useState(null);

  const { data, loading, reload } = useAsyncData(async () => {
    const [locationsRes, coordinatorsRes] = await Promise.all([
      locationService.list(),
      userService.list(ROLES.COORDINATOR),
    ]);

    const departmentsRes = await departmentService.list({
      include_archived: showArchived,
      location_id: selectedLocation || undefined,
    });

    return {
      locations: locationsRes.data || [],
      departments: departmentsRes.data || [],
      coordinators: coordinatorsRes.data || [],
    };
  }, [showArchived, selectedLocation]);

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  const createDepartment = async (values) => {
    setMessage("");
    setError("");

    const targetLocId = values.location_id || selectedLocation || (data?.locations?.length > 0 ? data.locations[0].location_id : null);
    if (!targetLocId) {
      setError("Please select a valid campus location for the department.");
      return;
    }

    // Local duplicate check within target location
    const normalized = values.name.trim().toLowerCase();
    const duplicate = (data?.departments || []).some(
      (d) =>
        (d.location_id === targetLocId || !selectedLocation) &&
        d.name.trim().toLowerCase() === normalized,
    );
    if (duplicate) {
      setError(
        `Department "${values.name.trim()}" already exists in this location. Please choose another name.`,
      );
      return;
    }

    try {
      await departmentService.create({
        name: values.name,
        sla_days: Number(values.sla_days),
        complaint_types: values.complaint_types
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        location_id: targetLocId,
      });
      reset();
      setMessage("Department created successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to create department."));
    }
  };

  const assignCoordinator = async (departmentId, coordinatorId) => {
    setMessage("");
    setError("");
    try {
      await departmentService.assignCoordinator(departmentId, coordinatorId);
      setMessage("Coordinator assigned successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to assign coordinator."));
    }
  };

  const startEdit = (department) => {
    setEditTarget(department);
    setEditName(department.name);
    setEditSla(department.sla_days);
    setEditComplaintTypes(department.complaint_types.join(", "));
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!editName.trim()) {
      setError("Department name is required.");
      return;
    }

    // Local duplicate check
    const normalized = editName.trim().toLowerCase();
    const duplicate = (data?.departments || []).some(
      (d) =>
        d.department_id !== editTarget.department_id &&
        d.location_id === editTarget.location_id &&
        d.name.trim().toLowerCase() === normalized,
    );
    if (duplicate) {
      setError(
        `Department "${editName.trim()}" already exists in this location. Please choose another name.`,
      );
      return;
    }

    try {
      await departmentService.update(editTarget.department_id, {
        name: editName,
        sla_days: Number(editSla),
        complaint_types: editComplaintTypes
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      setEditTarget(null);
      setMessage("Department updated successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to update department."));
    }
  };

  const archiveDepartment = async (departmentId) => {
    setMessage("");
    setError("");
    try {
      await departmentService.update(departmentId, { archived: true });
      setMessage("Department archived successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to archive department."));
    }
  };

  const restoreDepartment = async (departmentId) => {
    setMessage("");
    setError("");
    try {
      await departmentService.update(departmentId, { archived: false });
      setMessage("Department restored successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to restore department."));
    }
  };

  const startDelete = (department) => {
    setDeleteTarget(department);
    setDeleteInput("");
  };

  const handleDelete = async () => {
    if (!deleteTarget || deleteInput !== "DELETE") return;
    const targetId = deleteTarget.department_id;
    setDeleteTarget(null);
    setMessage("");
    setError("");

    try {
      await departmentService.delete(targetId);
      setMessage("Department deleted successfully.");
      reload();
    } catch (err) {
      const errMsg = getApiError(err, "Unable to delete department.");
      if (errMsg.includes("Cannot delete department.")) {
        setDeleteDependencyError(errMsg);
      } else {
        setError(errMsg);
      }
    }
  };

  const handleArchiveFromError = async () => {
    const targetId =
      deleteDependencyError.match(/DEPT-[A-F0-9]+/i)?.[0] ||
      deleteTarget?.department_id;
    setDeleteDependencyError("");
    if (!targetId) return;

    try {
      await departmentService.update(targetId, { archived: true });
      setMessage("Department archived successfully.");
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to archive department.");
    }
  };

  // Loaded departments filtered by location API
  const filteredDepartments = useMemo(() => {
    return data?.departments || [];
  }, [data]);

  const columns = [
    { key: "name", header: "Department" },
    {
      key: "location",
      header: "Location",
      render: (row) => {
        const locObj = (data?.locations || []).find(
          (l) => l.location_id === row.location_id,
        );
        const locName = locObj ? locObj.name : row.location_id;
        return locName ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
            <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
            {locName}
          </span>
        ) : (
          "-"
        );
      },
    },
    {
      key: "sla_days",
      header: "SLA Limit",
      render: (row) => `${row.sla_days} days`,
    },
    {
      key: "complaint_types",
      header: "Complaint Categories",
      render: (row) => {
        const types = row.complaint_types || [];
        if (types.length === 0) return "-";

        const fullText = types.join(", ");
        const firstTwo = types.slice(0, 2);
        const extraCount = types.length - 2;

        return (
          <div
            className="flex items-center gap-1.5 whitespace-nowrap overflow-hidden max-w-xs md:max-w-sm"
            title={fullText}
          >
            {firstTwo.map((t, idx) => (
              <span
                key={idx}
                className="inline-block truncate max-w-[130px] px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700/60 shrink-0"
              >
                {t}
              </span>
            ))}
            {extraCount > 0 && (
              <button
                type="button"
                onClick={() => setViewCategoriesTarget(row)}
                className="shrink-0 px-2 py-0.5 rounded-md text-[11px] font-bold bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 transition-colors cursor-pointer"
                title="Click to view all categories"
              >
                +{extraCount} more
              </button>
            )}
          </div>
        );
      },
    },
    {
      key: "coordinator_id",
      header: "Coordinator In-Charge",
      render: (row) => (
        <Select
          value={row.coordinator_id || ""}
          onChange={(event) =>
            assignCoordinator(row.department_id, event.target.value)
          }
          aria-label="Assign coordinator"
          className="!min-h-9 !py-1 !text-xs"
          disabled={row.archived}
        >
          <option value="">Unassigned</option>
          {(data?.coordinators || [])
            .filter(
              (user) => user.active || user.user_id === row.coordinator_id,
            )
            .map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.name}
                {!user.active ? " (Disabled)" : ""}
              </option>
            ))}
        </Select>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex items-center gap-1.5">
          {row.archived ? (
            <Button
              variant="subtle"
              size="sm"
              onClick={() => restoreDepartment(row.department_id)}
              className="!p-1.5"
              title="Restore"
            >
              <RefreshCw className="h-4 w-4 text-slate-500" />
            </Button>
          ) : (
            <>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => startEdit(row)}
                className="!p-1.5"
                title="Edit"
              >
                <Edit2 className="h-4 w-4 text-slate-500" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => archiveDepartment(row.department_id)}
                className="!p-1.5"
                title="Archive"
              >
                <Archive className="h-4 w-4 text-slate-500" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => startDelete(row)}
                className="!p-1.5 hover:!bg-red-50 text-red-500"
                title="Delete"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="grid gap-8">
      {/* Page Title & Breadcrumbs */}
      <div>
        <nav className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-2">
          <span>Dashboard</span>
          <span>&gt;</span>
          <span className="text-slate-800 dark:text-slate-200 font-bold">Departments</span>
        </nav>
        <PageHeader
          title="Department Configuration"
          description="Configure department profiles, filter by location, set resolution SLAs, and assign coordinators."
        />
      </div>

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Register form card */}
      <Card>
        <div className="mb-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <PlusCircle className="h-5 w-5 text-primary" />
            Configure New Department
          </h2>
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mt-1">
            Configure a new department and map complaint routing rules for a campus location.
          </p>
        </div>

        <hr className="border-slate-100 dark:border-slate-800 my-4" />

        <form
          className="grid gap-5 md:grid-cols-2 lg:grid-cols-4"
          onSubmit={handleSubmit(createDepartment)}
        >
          <Input
            label="Department Name"
            placeholder="Electrical"
            error={errors.name?.message}
            {...register("name", { required: "Department name is required." })}
          />
          <Input
            label="SLA Resolution Days"
            type="number"
            min="1"
            placeholder="3"
            error={errors.sla_days?.message}
            {...register("sla_days", { required: "SLA is required." })}
          />
          <Input
            label="Complaint Types (comma separated)"
            placeholder="Door, Window, Chair"
            error={errors.complaint_types?.message}
            {...register("complaint_types", {
              required: "At least one type is required.",
            })}
          />
          <Select
            label="Target Campus Location"
            {...register("location_id")}
          >
            {(data?.locations || []).map((loc) => (
              <option key={loc.location_id} value={loc.location_id}>
                {loc.name}
              </option>
            ))}
          </Select>

          <div className="flex items-end lg:col-span-4">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="font-semibold px-6 w-full lg:w-auto"
            >
              Create Department
            </Button>
          </div>
        </form>
      </Card>

      {/* Location-Grouped Department Hierarchy */}
      <Card>
        {/* Toolbar: Location Filter Dropdown + Show Archived Checkbox + Refresh */}
        <div className="flex flex-wrap items-center justify-between gap-3 my-2">
          {/* Location Dropdown Filter */}
          <div className="flex items-center gap-2 flex-1 min-w-[260px]">
            <label className="text-xs font-bold text-slate-700 dark:text-slate-300 shrink-0">
              📍 Filter by Location:
            </label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shadow-xs cursor-pointer"
            >
              <option value="">All Locations Overview</option>
              {(data?.locations || []).map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {/* Show Archived Checkbox */}
            <label className="flex items-center gap-2 cursor-pointer select-none px-2 shrink-0">
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary"
              />
              <span className="text-xs font-bold text-slate-600 dark:text-slate-300">
                Archived
              </span>
            </label>

            {/* Refresh Button */}
            <Button
              variant="subtle"
              size="sm"
              onClick={reload}
              className="h-10 px-3.5 rounded-xl text-xs font-bold shrink-0"
            >
              <RotateCw className="h-4 w-4 mr-1.5 shrink-0" />
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      {loading && (
        <Loader label="Loading location hierarchy and departments" variant="skeleton" />
      )}

      {/* Render Location Hierarchy Cards with Departments inside each Location */}
      {!loading && (
        <div className="grid gap-6">
          {(() => {
            const rawLocations = data?.locations || [];
            const allDepartments = data?.departments || [];
            const rawDepartments = showArchived
              ? allDepartments.filter((d) => d.archived === true)
              : allDepartments.filter((d) => !d.archived);

            const targetLocations = selectedLocation
              ? rawLocations.filter((l) => l.location_id === selectedLocation)
              : rawLocations;

            if (targetLocations.length === 0 || rawDepartments.length === 0) {
              return (
                <EmptyState
                  title={showArchived ? "No archived departments found" : "No departments found"}
                  description={showArchived ? "There are currently no archived departments." : "Try selecting another location or toggling 'Archived'."}
                />
              );
            }

            return targetLocations.map((loc) => {
              const locDepts = rawDepartments.filter(
                (d) => d.location_id === loc.location_id
              );

              return (
                <Card key={loc.location_id} className="!p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                        <MapPin className="h-5 w-5" />
                      </div>
                      <div>
                        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                          🏢 {loc.name}
                        </h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
                          {locDepts.length} department{locDepts.length === 1 ? "" : "s"} configured under this location
                        </p>
                      </div>
                    </div>
                  </div>

                  {locDepts.length === 0 ? (
                    <div className="py-6 text-center text-xs font-medium text-slate-400 dark:text-slate-500 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
                      No departments configured under {loc.name} yet. Use the form above to register one.
                    </div>
                  ) : (
                    <Table
                      columns={columns}
                      rows={locDepts}
                      getRowKey={(row) => row.department_id}
                    />
                  )}
                </Card>
              );
            });
          })()}
        </div>
      )}

      {/* Edit Modal */}
      <Modal
        open={!!editTarget}
        title="Edit Department"
        onClose={() => setEditTarget(null)}
      >
        <form onSubmit={handleEditSubmit} className="grid gap-5">
          <Input
            label="Department Name"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            required
          />
          <Input
            label="SLA Resolution Days"
            type="number"
            min="1"
            value={editSla}
            onChange={(e) => setEditSla(e.target.value)}
            required
          />
          <Input
            label="Complaint Types (comma separated)"
            value={editComplaintTypes}
            onChange={(e) => setEditComplaintTypes(e.target.value)}
            required
          />
          <div className="mt-6 flex justify-end gap-3">
            <Button variant="subtle" onClick={() => setEditTarget(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteTarget}
        title="Delete Department?"
        onClose={() => setDeleteTarget(null)}
      >
        <div className="text-sm text-slate-600 dark:text-slate-300 leading-normal">
          This action cannot be undone. To permanently delete the department{" "}
          <strong>{deleteTarget?.name}</strong>, type <strong>DELETE</strong> in
          the box below:
        </div>
        <input
          type="text"
          className="mt-4 h-11 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs outline-none focus:border-red-500 text-slate-800 dark:text-slate-100"
          placeholder="Type DELETE to confirm"
          value={deleteInput}
          onChange={(e) => setDeleteInput(e.target.value)}
        />
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="subtle" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            disabled={deleteInput !== "DELETE"}
            onClick={handleDelete}
          >
            Delete permanently
          </Button>
        </div>
      </Modal>

      {/* Delete Dependency Warning Modal */}
      <Modal
        open={!!deleteDependencyError}
        title="Cannot Delete Department"
        onClose={() => setDeleteDependencyError("")}
      >
        <div className="text-sm text-slate-600 dark:text-slate-300 leading-normal">
          {deleteDependencyError}
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="subtle" onClick={() => setDeleteDependencyError("")}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleArchiveFromError}>
            Archive Department Instead
          </Button>
        </div>
      </Modal>

      {/* View All Categories Modal */}
      <Modal
        open={!!viewCategoriesTarget}
        title={`Categories — ${viewCategoriesTarget?.name || ""}`}
        onClose={() => setViewCategoriesTarget(null)}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            All complaint categories registered for this department:
          </p>
          <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto p-1">
            {(viewCategoriesTarget?.complaint_types || []).map((cat, idx) => (
              <span
                key={idx}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary/10 text-primary border border-primary/20"
              >
                {cat}
              </span>
            ))}
          </div>
          <div className="mt-6 flex justify-end">
            <Button variant="subtle" onClick={() => setViewCategoriesTarget(null)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

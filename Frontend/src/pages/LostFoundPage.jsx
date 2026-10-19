import { useState, useMemo, useEffect } from "react";
import {
  Plus,
  MapPin,
  Calendar,
  CheckCircle2,
  Eye,
  Trash2,
  Camera,
  ArrowLeft,
  Package,
} from "lucide-react";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Loader from "../components/Loader.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Modal from "../components/Modal.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import Toast from "../components/Toast.jsx";
import { useAsyncData } from "../hooks/useAsyncData.js";
import { lostFoundService } from "../services/lostFoundService.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../utils/dateFormatter.js";

function ItemPhotoImg({ itemId, photo, alt, className }) {
  const [blobUrl, setBlobUrl] = useState(null);
  const isServerPhoto =
    typeof photo === "string" && photo.startsWith("/static/lost_found_photos/");

  useEffect(() => {
    if (!isServerPhoto) return;
    let active = true;
    let url = null;
    const filename = photo.split("/").pop();
    lostFoundService
      .getPhotoBlob(itemId, filename)
      .then((res) => {
        url = URL.createObjectURL(res.data);
        if (active) {
          setBlobUrl(url);
        } else {
          URL.revokeObjectURL(url);
        }
      })
      .catch(() => {});
    return () => {
      active = false;
      if (url) URL.revokeObjectURL(url);
    };
  }, [itemId, photo, isServerPhoto]);

  const src = isServerPhoto ? blobUrl : photo;
  if (!src) return null;
  return <img src={src} alt={alt} className={className} />;
}

function getLocalTodayDate() {
  const d = new Date();
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function LostFoundPage() {
  const { user } = useAuth();

  // Tab State: 'my_reports' | 'returned'
  const [activeTab, setActiveTab] = useState("my_reports");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Report Modal State
  const [showReportModal, setShowReportModal] = useState(false);
  const [reportStep, setReportStep] = useState("choose"); // 'choose' | 'form'
  const [reportType, setReportType] = useState("Lost"); // 'Lost' | 'Found'

  // Form Fields
  const [description, setDescription] = useState("");
  const [exactLocation, setExactLocation] = useState("");
  const [lostDate, setLostDate] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [photoPreview, setPhotoPreview] = useState("");
  const [saving, setSaving] = useState(false);

  // Detail Modal & Confirm Dialog State
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [confirmAction, setConfirmAction] = useState(null);

  const handlePhotoFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError("Image file size must be under 5MB.");
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhotoUrl(reader.result);
        setPhotoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  // Fetch Items
  const {
    data: rawItems,
    loading,
    reload,
  } = useAsyncData(
    async () => {
      const statusParam = activeTab === "returned" ? "returned" : "active";
      const res = await lostFoundService.listItems({
        my_reports: true,
        status: statusParam,
      });
      return res.data || res;
    },
    [activeTab],
  );

  const items = useMemo(() => {
    if (!rawItems) return [];
    const list = Array.isArray(rawItems) ? rawItems : rawItems.items || [];
    if (activeTab === "returned") {
      return list.filter((i) =>
        ["Returned", "Resolved", "Closed"].includes(i.status),
      );
    }
    return list.filter(
      (i) => !["Returned", "Resolved", "Closed"].includes(i.status),
    );
  }, [rawItems, activeTab]);

  const openReportModal = (type = null) => {
    setMessage("");
    setError("");
    setDescription("");
    setExactLocation("");
    setLostDate("");
    setPhotoUrl("");
    setPhotoPreview("");
    if (type) {
      setReportType(type);
      setReportStep("form");
    } else {
      setReportStep("choose");
    }
    setShowReportModal(true);
  };

  const handleCreateReport = async (e) => {
    e.preventDefault();
    if (!description.trim()) {
      setError("Description is required.");
      return;
    }
    if (reportType === "Found" && !exactLocation.trim()) {
      setError("Found location is required for found items.");
      return;
    }

    setSaving(true);
    setMessage("");
    setError("");

    try {
      await lostFoundService.createItem({
        report_type: reportType,
        description: description.trim(),
        exact_location: exactLocation.trim(),
        lost_date: lostDate || null,
        photo_url: photoUrl.trim(),
      });
      setMessage(`${reportType} item reported successfully.`);
      setShowReportModal(false);
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to submit report.");
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteItem = (itemId) => {
    setConfirmAction({
      title: "Delete Report",
      message:
        "Are you sure you want to delete this report? It will be removed from your reports.",
      confirmLabel: "Delete Report",
      tone: "danger",
      action: async () => {
        try {
          await lostFoundService.deleteItem(itemId);
          setMessage("Report deleted successfully.");
          reload();
        } catch (err) {
          setError(err?.response?.data?.detail || "Failed to delete report.");
        }
      },
    });
  };

  const handleMarkReturned = async (itemId) => {
    setConfirmAction({
      title: "Mark Item as Returned",
      message:
        "Are you sure you want to mark this item as returned? It will move to the Returned tab.",
      confirmLabel: "Mark Returned",
      tone: "success",
      action: async () => {
        try {
          await lostFoundService.markReturned(itemId);
          setMessage("Item marked as returned successfully.");
          reload();
        } catch (err) {
          setError(err?.response?.data?.detail || "Failed to update status.");
        }
      },
    });
  };

  return (
    <div className="space-y-6">
      {message && <Toast message={message} type="success" onClose={() => setMessage("")} />}
      {error && <Toast message={error} type="error" onClose={() => setError("")} />}

      <PageHeader
        title="Campus Lost & Found"
        description="Report lost or found items on campus and manage your reports."
      >
        <Button
          variant="primary"
          onClick={() => openReportModal()}
          leftIcon={<Plus className="h-4 w-4" />}
        >
          Report Item
        </Button>
      </PageHeader>

      {/* Main Simplified Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 overflow-x-auto max-w-full scrollbar-none">
        <button
          type="button"
          onClick={() => setActiveTab("my_reports")}
          className={`py-2.5 px-4 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap shrink-0 ${
            activeTab === "my_reports"
              ? "border-primary text-primary dark:text-primary font-bold"
              : "border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200 font-semibold"
          }`}
        >
          My Reports
        </button>
        <button
          type="button"
          onClick={() => setActiveTab("returned")}
          className={`py-2.5 px-4 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap shrink-0 ${
            activeTab === "returned"
              ? "border-primary text-primary dark:text-primary font-bold"
              : "border-transparent text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-200 font-semibold"
          }`}
        >
          Returned
        </button>
      </div>

      {/* Reports Grid */}
      {loading ? (
        <div className="py-12">
          <Loader label="Loading reports..." />
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          title={activeTab === "my_reports" ? "No active reports" : "No returned reports"}
          description={
            activeTab === "my_reports"
              ? "You haven't reported any lost or found items yet."
              : "No returned or resolved reports found."
          }
          actionLabel={activeTab === "my_reports" ? "+ Report Item" : undefined}
          onAction={activeTab === "my_reports" ? () => openReportModal() : undefined}
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((item) => {
            const isOwner =
              item.reported_by === user?.user_id || item.reported_by === user?.email;
            const isResolvedStatus = ["Returned", "Resolved", "Closed"].includes(
              item.status,
            );
            const canDelete = isOwner && !isResolvedStatus;
            const photos =
              (item.unique_identifiers || {}).photos ||
              (item.photo_url ? [item.photo_url] : []);

            return (
              <Card
                key={item.item_id}
                className="p-4 flex flex-col justify-between hover:shadow-md transition-shadow"
              >
                <div>
                  {photos.length > 0 && (
                    <ItemPhotoImg
                      itemId={item.item_id}
                      photo={photos[0]}
                      alt={item.title || item.description}
                      className="w-full h-44 object-cover rounded-xl mb-3 border border-slate-200/80 dark:border-slate-800"
                    />
                  )}

                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide ${
                          item.report_type === "Lost"
                            ? "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300"
                            : "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300"
                        }`}
                      >
                        {item.report_type}
                      </span>
                      <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 mt-1">
                        {item.report_type === "Found" ? "Found by: " : "Reported by: "}
                        <strong className="text-slate-800 dark:text-slate-200">
                          {item.reported_by_name || item.reported_by || "Me"}
                        </strong>
                      </div>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        isResolvedStatus
                          ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300"
                          : "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>

                  {/* Open-ended Description */}
                  <p className="text-xs text-slate-700 dark:text-slate-300 mt-3 whitespace-pre-line font-normal">
                    {item.description}
                  </p>

                  {/* Location Context */}
                  {item.exact_location && (
                    <div className="mt-3 text-xs text-slate-600 dark:text-slate-400 flex items-center gap-1 font-medium">
                      <MapPin className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <span>
                        {item.report_type === "Lost" ? "Last seen: " : "Found at: "}
                        <strong className="text-slate-800 dark:text-slate-200">
                          {item.exact_location}
                        </strong>
                      </span>
                    </div>
                  )}

                  {/* Date Context */}
                  {item.date_lost_found && (
                    <div className="mt-1 text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 font-medium">
                      <Calendar className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                      <span>
                        {item.report_type === "Lost" ? "Lost on: " : "Found on: "}
                        {item.date_lost_found}
                      </span>
                    </div>
                  )}

                  {/* Returned / Resolved Banner */}
                  {isResolvedStatus && (
                    <div className="mt-3 text-xs font-bold text-emerald-700 dark:text-emerald-400 flex items-center gap-1.5 bg-emerald-50 dark:bg-emerald-950/40 px-3 py-1.5 rounded-lg border border-emerald-200/60 dark:border-emerald-900/50">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                      <span>Returned / Resolved</span>
                    </div>
                  )}
                </div>

                {/* Card Actions */}
                <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
                  <Button
                    variant="subtle"
                    size="sm"
                    onClick={() => {
                      setSelectedItem(item);
                      setShowDetailModal(true);
                    }}
                    className="text-xs font-semibold text-slate-600 dark:text-slate-400"
                    leftIcon={<Eye className="h-3.5 w-3.5" />}
                  >
                    View Details
                  </Button>

                  <div className="flex items-center gap-2">
                    {!isResolvedStatus && isOwner && (
                      <Button
                        size="xs"
                        variant="primary"
                        onClick={() => handleMarkReturned(item.item_id)}
                        className="bg-emerald-600 hover:bg-emerald-700"
                      >
                        Mark Returned
                      </Button>
                    )}

                    {canDelete && (
                      <button
                        type="button"
                        onClick={() => handleDeleteItem(item.item_id)}
                        className="p-1.5 text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg transition-colors cursor-pointer"
                        title="Delete Report"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Simplified Report Modal */}
      {showReportModal && (
        <Modal
          open={showReportModal}
          title={
            reportStep === "choose"
              ? "What happened?"
              : reportType === "Lost"
              ? "I Lost Something"
              : "I Found Something"
          }
          onClose={() => setShowReportModal(false)}
        >
          {reportStep === "choose" ? (
            <div className="space-y-4 py-2">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Select whether you are reporting an item you lost or an item you found on campus.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setReportType("Lost");
                    setReportStep("form");
                  }}
                  className="p-5 rounded-2xl border-2 border-rose-200 bg-rose-50/50 hover:bg-rose-100/60 dark:border-rose-900/50 dark:bg-rose-950/20 text-left transition-all cursor-pointer group"
                >
                  <div className="text-base font-bold text-rose-700 dark:text-rose-300">
                    I Lost Something
                  </div>
                  <div className="mt-1 text-xs text-rose-600/80 dark:text-rose-400">
                    Report an item you misplaced so others can help identify it.
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setReportType("Found");
                    setReportStep("form");
                  }}
                  className="p-5 rounded-2xl border-2 border-emerald-200 bg-emerald-50/50 hover:bg-emerald-100/60 dark:border-emerald-900/50 dark:bg-emerald-950/20 text-left transition-all cursor-pointer group"
                >
                  <div className="text-base font-bold text-emerald-700 dark:text-emerald-300">
                    I Found Something
                  </div>
                  <div className="mt-1 text-xs text-emerald-600/80 dark:text-emerald-400">
                    Report an item you found on campus to help locate its owner.
                  </div>
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleCreateReport} className="space-y-4">
              <button
                type="button"
                onClick={() => setReportStep("choose")}
                className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 mb-1"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Change Selection
              </button>

              {/* Photo Upload */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Item Photo (Optional)
                </label>
                <div className="flex items-center gap-3">
                  <label className="flex h-20 w-24 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800">
                    <Camera className="h-5 w-5 text-slate-400" />
                    <span className="mt-1 text-[10px] text-slate-500">Upload</span>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handlePhotoFileChange}
                      className="hidden"
                    />
                  </label>

                  {photoPreview && (
                    <div className="relative h-20 w-24 overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
                      <img
                        src={photoPreview}
                        alt="Preview"
                        className="h-full w-full object-cover"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* Description Field (Open-ended Identifying Field) */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Description <span className="text-rose-500">*</span>
                </label>
                <textarea
                  required
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={
                    reportType === "Lost"
                      ? "Describe what you lost and any identifying details (e.g., Black leather wallet with student ID inside, scratch on back)..."
                      : "Describe what you found (e.g., Blue Milton water bottle found near library entrance)..."
                  }
                  className="w-full rounded-xl border border-slate-300 bg-white p-3 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                />
              </div>

              {/* Location Field */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  {reportType === "Lost" ? "Last Known Location (Optional)" : "Found Location *"}
                </label>
                <input
                  type="text"
                  required={reportType === "Found"}
                  value={exactLocation}
                  onChange={(e) => setExactLocation(e.target.value)}
                  placeholder={
                    reportType === "Lost" ? "e.g. Hostel B, Room 204" : "e.g. Library 1st Floor"
                  }
                  className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                />
              </div>

              {/* Date Field */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Date / Time (Optional)
                  </label>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setLostDate(getLocalTodayDate())}
                      className="text-[11px] font-semibold text-primary hover:underline cursor-pointer"
                    >
                      Set Today
                    </button>
                    {lostDate && (
                      <button
                        type="button"
                        onClick={() => setLostDate("")}
                        className="text-[11px] font-semibold text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer"
                      >
                        Clear
                      </button>
                    )}
                  </div>
                </div>
                <input
                  type="date"
                  value={lostDate}
                  max={getLocalTodayDate()}
                  onChange={(e) => setLostDate(e.target.value)}
                  onClick={(e) => {
                    try {
                      if (e.target.showPicker) e.target.showPicker();
                    } catch (err) {}
                  }}
                  onFocus={(e) => {
                    try {
                      if (e.target.showPicker) e.target.showPicker();
                    } catch (err) {}
                  }}
                  className="w-full rounded-xl border border-slate-300 bg-white p-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:[color-scheme:dark] cursor-pointer"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowReportModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={saving}
                >
                  {saving
                    ? "Submitting..."
                    : reportType === "Lost"
                    ? "Report Lost"
                    : "Report Found"}
                </Button>
              </div>
            </form>
          )}
        </Modal>
      )}

      {/* Item Details Modal */}
      {showDetailModal && selectedItem && (
        <Modal
          open={showDetailModal && !!selectedItem}
          title={`Report Details: ${selectedItem.report_type}`}
          onClose={() => setShowDetailModal(false)}
        >
          <div className="space-y-4 text-xs">
            {((selectedItem.unique_identifiers || {}).photos || []).length > 0 && (
              <ItemPhotoImg
                itemId={selectedItem.item_id}
                photo={(selectedItem.unique_identifiers.photos || [])[0]}
                alt={selectedItem.title || selectedItem.description}
                className="w-full h-52 object-cover rounded-xl border border-slate-200 dark:border-slate-700"
              />
            )}

            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  selectedItem.report_type === "Lost"
                    ? "bg-rose-100 text-rose-800"
                    : "bg-emerald-100 text-emerald-800"
                }`}
              >
                {selectedItem.report_type}
              </span>
              <span className="font-bold text-slate-700 dark:text-slate-300">
                Status: {selectedItem.status}
              </span>
            </div>

            <div>
              <div className="font-semibold text-slate-500 dark:text-slate-400">Description</div>
              <p className="mt-1 text-slate-800 dark:text-slate-200 whitespace-pre-line">
                {selectedItem.description}
              </p>
            </div>

            {selectedItem.exact_location && (
              <div>
                <div className="font-semibold text-slate-500 dark:text-slate-400">
                  {selectedItem.report_type === "Lost" ? "Last Known Location" : "Found Location"}
                </div>
                <div className="mt-0.5 text-slate-800 dark:text-slate-200 font-medium">
                  {selectedItem.exact_location}
                </div>
              </div>
            )}

            <div>
              <div className="font-semibold text-slate-500 dark:text-slate-400">Reported By</div>
              <div className="mt-0.5 text-slate-800 dark:text-slate-200 font-medium">
                {selectedItem.reported_by_name || selectedItem.reported_by}
              </div>
            </div>

            <div>
              <div className="font-semibold text-slate-500 dark:text-slate-400">Report Date</div>
              <div className="mt-0.5 text-slate-500">
                {formatDate(selectedItem.created_at)}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDetailModal(false)}
              >
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Confirmation Dialog */}
      {confirmAction && (
        <ConfirmDialog
          isOpen={true}
          onClose={() => setConfirmAction(null)}
          onConfirm={async () => {
            await confirmAction.action();
            setConfirmAction(null);
          }}
          title={confirmAction.title}
          message={confirmAction.message}
          confirmLabel={confirmAction.confirmLabel}
          tone={confirmAction.tone}
        />
      )}
    </div>
  );
}

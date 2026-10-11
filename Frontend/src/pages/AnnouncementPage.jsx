import { useState, useMemo, useEffect } from "react";
import {
  Megaphone,
  Pin,
  AlertOctagon,
  CheckCircle2,
  Clock,
  Filter,
  Search,
  Plus,
  Eye,
  CheckSquare,
  Layers,
  Sparkles,
  Mail,
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
import { announcementService } from "../services/announcementService.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../utils/dateFormatter.js";

export default function AnnouncementPage() {
  const { user } = useAuth();
  const [categoryFilter, setCategoryFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [quickFilter, setQuickFilter] = useState("");
  const [query, setQuery] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Modals state
  const [showComposerModal, setShowComposerModal] = useState(false);
  const [selectedAnnouncement, setSelectedAnnouncement] = useState(null);
  const [readershipMetrics, setReadershipMetrics] = useState(null);

  // Composer Form State
  const [title, setTitle] = useState("");
  const [summary, setSummary] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("General");
  const [priority, setPriority] = useState("Normal");
  const [reqAck, setReqAck] = useState(false);
  const [targetType, setTargetType] = useState("Campus");
  const [targetVal, setTargetVal] = useState("All");
  const [saving, setSaving] = useState(false);

  // Admin Contact Info for Students / Non-staff
  const [adminContact, setAdminContact] = useState(null);
  const [loadingContact, setLoadingContact] = useState(false);

  const userRole = (user?.role || "").toLowerCase();
  const canCreate = [
    "administrator",
    "admin",
    "app_manager",
    "location_in_charge",
    "warden",
  ].includes(userRole);

  useEffect(() => {
    if (!canCreate) {
      setLoadingContact(true);
      announcementService
        .getAdminContact()
        .then((res) => {
          setAdminContact(res?.data || null);
        })
        .catch(() => {
          setAdminContact({
            available: false,
            message:
              "Administrator contact email is currently unavailable. Please visit the campus administrative office.",
          });
        })
        .finally(() => {
          setLoadingContact(false);
        });
    }
  }, [canCreate]);

  const {
    data: announcements,
    loading,
    reload,
  } = useAsyncData(
    async () =>
      (
        await announcementService.list({
          category: categoryFilter,
          priority: priorityFilter,
          query,
        })
      ).data,
    [categoryFilter, priorityFilter, query],
  );

  const rawList = announcements || [];

  const metrics = useMemo(() => {
    const totalActive = rawList.filter((a) => a?.status === "Published").length;
    const unread = rawList.filter((a) => !a?.is_read).length;
    const critical = rawList.filter((a) => a?.priority === "Critical").length;
    const pendingAck = rawList.filter(
      (a) => Boolean(a?.requires_acknowledgement) && !a?.is_acknowledged,
    ).length;
    return { totalActive, unread, critical, pendingAck };
  }, [rawList]);

  const list = useMemo(() => {
    if (quickFilter === "active") {
      return rawList.filter((a) => a?.status === "Published");
    }
    if (quickFilter === "unread") {
      return rawList.filter((a) => !a?.is_read);
    }
    if (quickFilter === "critical") {
      return rawList.filter((a) => a?.priority === "Critical");
    }
    if (quickFilter === "pendingAck") {
      return rawList.filter(
        (a) => Boolean(a?.requires_acknowledgement) && !a?.is_acknowledged,
      );
    }
    return rawList;
  }, [rawList, quickFilter]);

  const handleMarkReadDirectly = async (e, annId) => {
    e.stopPropagation();
    try {
      await announcementService.markRead(annId);
      setMessage("Notice marked as read.");
      reload();
    } catch (err) {
      setError("Failed to mark notice as read.");
    }
  };

  const handleCreateAnnouncement = async (e) => {
    e.preventDefault();
    if (!canCreate) {
      setError(
        "Only Administrators, App Managers, and Location Wardens are authorized to publish official broadcast announcements.",
      );
      return;
    }
    setSaving(true);
    setMessage("");
    setError("");

    try {
      const cleanTitle = title.trim();
      const bodyContent = (content || summary).trim();
      const cleanSummary = (summary || bodyContent.slice(0, 100)).trim();

      await announcementService.create({
        title: cleanTitle,
        summary: cleanSummary,
        content: bodyContent,
        description: bodyContent,
        category,
        priority,
        requires_acknowledgement: Boolean(reqAck),
        is_pinned: priority === "High" || priority === "Critical",
        targets: [{ target_type: targetType, target_value: targetVal || "All" }],
      });
      setMessage(`Announcement '${cleanTitle}' published successfully.`);
      setShowComposerModal(false);
      setTitle("");
      setSummary("");
      setContent("");
      setReqAck(false);
      reload();
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const errMsg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d) => d.msg).join(", ")
            : "Failed to publish announcement.";
      setError(errMsg);
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAnnouncement = async (e, annId) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this announcement?")) return;
    try {
      await announcementService.delete(annId);
      setMessage("Announcement deleted successfully.");
      if (selectedAnnouncement?.announcement_id === annId) {
        setSelectedAnnouncement(null);
      }
      reload();
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Failed to delete announcement.",
      );
    }
  };

  const handleOpenAnnouncement = async (ann) => {
    setSelectedAnnouncement(ann);
    setReadershipMetrics(null);
    try {
      await announcementService.markRead(ann.announcement_id);
      if (canCreate || userRole === "coordinator") {
        const stats = await announcementService.getReadership(
          ann.announcement_id,
        );
        setReadershipMetrics(stats?.data || null);
      }
      reload();
    } catch (err) {
      // Non-blocking read tracking
    }
  };

  const handleAcknowledge = async (annId) => {
    try {
      await announcementService.acknowledge(annId);
      setMessage("Mandatory announcement acknowledged.");
      if (selectedAnnouncement) {
        setSelectedAnnouncement((prev) => ({ ...prev, is_acknowledged: true }));
      }
      reload();
    } catch (err) {
      setError("Acknowledgement failed.");
    }
  };

  return (
    <div className="grid gap-6 max-w-6xl">
      <PageHeader
        title="Announcements & Official Notices"
        description="Official campus circulars, academic notices, exam timetables, emergency alerts, and events."
        actions={
          canCreate ? (
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowComposerModal(true)}
                size="sm"
                className="font-bold flex items-center gap-1.5"
              >
                <Megaphone className="h-4 w-4" />
                Compose Notice
              </Button>
            </div>
          ) : null
        }
      />

      {!canCreate && (
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl text-xs text-slate-700 dark:text-slate-300">
          <div className="flex items-center gap-2.5">
            <Megaphone className="h-4 w-4 text-primary shrink-0" />
            <div>
              <p className="font-semibold text-slate-900 dark:text-slate-100">
                Official Campus Notices & Broadcast Feed
              </p>
              <p className="text-slate-500 dark:text-slate-400 text-[11px]">
                Notices are officially published by College Administration and Location Wardens.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-200 dark:border-slate-800">
            {adminContact?.available && adminContact?.email ? (
              <div className="flex items-center gap-2 text-xs bg-white dark:bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 shadow-2xs">
                <Mail className="h-3.5 w-3.5 text-primary shrink-0" />
                <span className="text-slate-500 dark:text-slate-400">Admin Contact:</span>
                <a
                  href={`mailto:${adminContact.email}`}
                  className="font-medium text-primary hover:underline"
                >
                  {adminContact.email}
                </a>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 italic">
                <Mail className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                <span>
                  {adminContact?.message || (loadingContact ? "Loading contact..." : "Administrator contact information unavailable.")}
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Dashboard Overview Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div
          className={`cursor-pointer transition-all rounded-2xl ${
            quickFilter === "active"
              ? "ring-2 ring-primary border-l-4 border-l-primary"
              : ""
          }`}
          onClick={() =>
            setQuickFilter((prev) => (prev === "active" ? "" : "active"))
          }
        >
          <StatCard label="ACTIVE NOTICES" value={metrics.totalActive} accent />
        </div>
        <div
          className={`cursor-pointer transition-all rounded-2xl ${
            quickFilter === "unread"
              ? "ring-2 ring-primary border-l-4 border-l-primary"
              : ""
          }`}
          onClick={() =>
            setQuickFilter((prev) => (prev === "unread" ? "" : "unread"))
          }
        >
          <StatCard label="UNREAD CIRCULARS" value={metrics.unread} />
        </div>
        <div
          className={`cursor-pointer transition-all rounded-2xl ${
            quickFilter === "critical"
              ? "ring-2 ring-primary border-l-4 border-l-primary"
              : ""
          }`}
          onClick={() =>
            setQuickFilter((prev) => (prev === "critical" ? "" : "critical"))
          }
        >
          <StatCard label="CRITICAL ALERTS" value={metrics.critical} />
        </div>
        <div
          className={`cursor-pointer transition-all rounded-2xl ${
            quickFilter === "pendingAck"
              ? "ring-2 ring-primary border-l-4 border-l-primary"
              : ""
          }`}
          onClick={() =>
            setQuickFilter((prev) => (prev === "pendingAck" ? "" : "pendingAck"))
          }
        >
          <StatCard label="PENDING ACKS" value={metrics.pendingAck} />
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <Card className="flex flex-wrap items-center justify-between gap-4 bg-slate-50/50">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search notices by title, content, or keyword..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none"
          >
            <option value="">All Categories</option>
            <option value="Academic">Academic</option>
            <option value="Examination">Examination</option>
            <option value="Placement">Placement</option>
            <option value="Hostel">Hostel</option>
            <option value="Events">Events</option>
            <option value="Emergency">Emergency</option>
            <option value="Maintenance">Maintenance</option>
          </select>

          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none"
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical Only</option>
            <option value="High">High Priority</option>
            <option value="Normal">Normal</option>
          </select>
        </div>
      </Card>

      {/* Announcement Feed */}
      {loading ? (
        <Loader label="Loading campus notices..." variant="skeleton" />
      ) : list.length === 0 ? (
        <EmptyState
          title="No announcements found"
          description="Official broadcast notices will display here."
        />
      ) : (
        <div className="grid gap-4">
          {list.map((ann) => {
            const isCritical = ann.priority === "Critical";
            const isHigh = ann.priority === "High";

            return (
              <Card
                key={ann.announcement_id}
                className={`relative transition-all border-l-4 ${
                  isCritical
                    ? "border-l-rose-600 bg-rose-50/20"
                    : isHigh
                      ? "border-l-amber-500 bg-amber-50/10"
                      : "border-l-primary"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      {(isCritical || isHigh) && (
                        <span className="flex items-center gap-1 text-[10px] font-bold uppercase text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
                          <Pin className="h-3 w-3" /> Pinned
                        </span>
                      )}
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          isCritical
                            ? "bg-rose-100 text-rose-800"
                            : "bg-sky-100 text-sky-800"
                        }`}
                      >
                        {ann.priority}
                      </span>
                      <span className="text-xs font-semibold text-slate-400">
                        {ann.category}
                      </span>
                      {!ann.is_read && (
                        <span
                          className="h-2 w-2 rounded-full bg-primary inline-block"
                          title="Unread"
                        />
                      )}
                    </div>

                    <h3
                      onClick={() => handleOpenAnnouncement(ann)}
                      className="text-base font-bold text-slate-900 hover:text-primary cursor-pointer transition-colors"
                    >
                      {ann.title}
                    </h3>

                    <p className="text-xs text-slate-600 mt-1 line-clamp-2">
                      {ann.summary || ann.content}
                    </p>

                    <div className="mt-3 flex flex-wrap items-center gap-4 text-slate-400 text-[11px] font-semibold">
                      <span>Published by: {ann.created_by}</span>
                      <span>Date: {formatDate(ann.created_at)}</span>
                      {Boolean(ann.requires_acknowledgement) && (
                        <span
                          className={`font-bold ${ann.is_acknowledged ? "text-emerald-600" : "text-rose-600"}`}
                        >
                          {ann.is_acknowledged
                            ? "✓ Acknowledged"
                            : "⚠ Mandatory Acknowledgement Pending"}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <Button
                      variant="subtle"
                      size="sm"
                      onClick={() => handleOpenAnnouncement(ann)}
                      className="font-bold text-xs"
                    >
                      Read Full Notice
                    </Button>
                    {!ann.is_read && (
                      <Button
                        variant="subtle"
                        size="sm"
                        onClick={(e) => handleMarkReadDirectly(e, ann.announcement_id)}
                        className="font-bold text-xs text-sky-600 hover:text-sky-700 bg-sky-50 hover:bg-sky-100"
                      >
                        Mark as Read
                      </Button>
                    )}
                    {Boolean(ann.requires_acknowledgement) &&
                      !ann.is_acknowledged && (
                        <Button
                          size="sm"
                          onClick={() => handleAcknowledge(ann.announcement_id)}
                          className="font-bold text-xs bg-emerald-600 hover:bg-emerald-700"
                        >
                          I Acknowledge
                        </Button>
                      )}
                    {canCreate && (
                      <Button
                        variant="subtle"
                        size="sm"
                        onClick={(e) => handleDeleteAnnouncement(e, ann.announcement_id)}
                        className="font-bold text-xs text-rose-600 hover:text-rose-700 bg-rose-50 hover:bg-rose-100"
                      >
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Announcement Detail Modal */}
      {selectedAnnouncement && (
        <Modal
          title={selectedAnnouncement.title}
          isOpen={!!selectedAnnouncement}
          onClose={() => setSelectedAnnouncement(null)}
        >
          <div className="grid gap-4 text-xs font-sans">
            <div className="p-3 bg-slate-50 rounded-xl flex flex-wrap items-center justify-between gap-2 text-slate-600">
              <div>
                Category:{" "}
                <span className="font-bold text-slate-900">
                  {selectedAnnouncement.category}
                </span>
              </div>
              <div>
                Priority:{" "}
                <span className="font-bold text-primary">
                  {selectedAnnouncement.priority}
                </span>
              </div>
              <div>
                Date:{" "}
                <span className="font-bold">
                  {formatDate(selectedAnnouncement.created_at)}
                </span>
              </div>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-xl text-slate-800 leading-relaxed font-normal whitespace-pre-wrap">
              {selectedAnnouncement.content}
            </div>

            {Boolean(selectedAnnouncement.requires_acknowledgement) && (
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl flex items-center justify-between text-amber-900">
                <span className="font-semibold">
                  This official circular requires mandatory acknowledgment of
                  receipt.
                </span>
                {!selectedAnnouncement.is_acknowledged ? (
                  <Button
                    size="sm"
                    onClick={() =>
                      handleAcknowledge(selectedAnnouncement.announcement_id)
                    }
                    className="font-bold bg-emerald-600"
                  >
                    I Acknowledge
                  </Button>
                ) : (
                  <span className="font-bold text-emerald-700">
                    ✓ Confirmed
                  </span>
                )}
              </div>
            )}

            {readershipMetrics && (
              <div className="p-3 bg-slate-900 text-slate-100 rounded-xl flex justify-between font-mono text-[11px]">
                <div>
                  Reads Count:{" "}
                  <span className="font-bold text-sky-400">
                    {readershipMetrics?.reads_count ?? 0}
                  </span>
                </div>
                <div>
                  Acknowledgements:{" "}
                  <span className="font-bold text-emerald-400">
                    {readershipMetrics?.acknowledgements_count ?? 0}
                  </span>
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-slate-100">
              <Button
                variant="subtle"
                onClick={() => setSelectedAnnouncement(null)}
              >
                Close
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Composer Modal - Authorized Staff Only */}
      {canCreate && showComposerModal && (
        <Modal
          title="Compose & Publish Notice"
          isOpen={showComposerModal}
          onClose={() => setShowComposerModal(false)}
        >
          <form
            onSubmit={handleCreateAnnouncement}
            className="grid gap-4 text-xs"
          >

            <Input
              label="Notice Title"
              placeholder="e.g. Mid-Semester Exam Schedule Released"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            <Input
              label="Short Summary"
              placeholder="Brief 1-line overview..."
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
            />

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Full Content
              </label>
              <textarea
                rows={4}
                placeholder="Type official announcement body text..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg font-semibold focus:outline-none"
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-semibold text-slate-800 dark:text-slate-100"
                >
                  <option value="Academic">Academic</option>
                  <option value="Examination">Examination</option>
                  <option value="Placement">Placement</option>
                  <option value="Hostel">Hostel</option>
                  <option value="Events">Events</option>
                  <option value="Emergency">Emergency</option>
                  <option value="Maintenance">Maintenance</option>
                  <option value="General">General</option>
                </select>
              </div>

              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Priority Level
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-semibold text-slate-800 dark:text-slate-100"
                >
                  <option value="Normal">Normal (Blue)</option>
                  <option value="High">High (Orange Pinned)</option>
                  <option value="Critical">
                    Critical (Red Pinned & Notification)
                  </option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Target Audience Type
                </label>
                <select
                  value={targetType}
                  onChange={(e) => setTargetType(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-semibold text-slate-800 dark:text-slate-100"
                >
                  <option value="Campus">Campus Wide (All)</option>
                  <option value="Role">Role Specific</option>
                  <option value="Department">Department</option>
                  <option value="Hostel">Hostel</option>
                </select>
              </div>

              <Input
                label="Target Value"
                placeholder="e.g. All, Student, CSE"
                value={targetVal}
                onChange={(e) => setTargetVal(e.target.value)}
                required
              />
            </div>

            <label className="flex items-center gap-2 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={reqAck}
                onChange={(e) => setReqAck(e.target.checked)}
                className="h-4 w-4 text-primary rounded"
              />
              <span className="font-bold text-slate-700">
                Require Mandatory Student Acknowledgement
              </span>
            </label>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button
                variant="secondary"
                type="button"
                onClick={() => setShowComposerModal(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={saving || !canCreate} className="font-bold">
                {saving ? "Publishing..." : "Publish Notice"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

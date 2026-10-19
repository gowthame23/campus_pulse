import { useState, useMemo, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Trash2,
  CheckCircle2,
  CheckCheck,
  Filter,
  ArrowRight,
  Settings,
  Bell,
  Mail,
  Smartphone,
  AlertTriangle,
  Inbox,
  Clock,
  Layers,
} from "lucide-react";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Loader from "../components/Loader.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Toast from "../components/Toast.jsx";
import Modal from "../components/Modal.jsx";
import { useAsyncData } from "../hooks/useAsyncData.js";
import { notificationService } from "../services/notificationService.js";
import { getApiError } from "../api/axios.js";

export default function NotificationsPage() {
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [filterModule, setFilterModule] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterUnreadOnly, setFilterUnreadOnly] = useState(false);
  const [activeTab, setActiveTab] = useState("notifications"); // 'notifications' | 'preferences'
  const [selectedNotif, setSelectedNotif] = useState(null);

  // Preference states
  const [prefs, setPrefs] = useState({
    in_app_enabled: true,
    email_enabled: false,
    push_enabled: false,
  });
  const [prefSaving, setPrefSaving] = useState(false);

  const { data, loading, reload } = useAsyncData(
    async () => (await notificationService.list()).data,
    [],
  );

  useEffect(() => {
    notificationService
      .getPreferences()
      .then((res) => setPrefs(res.data))
      .catch(() => {});
  }, []);

  const unreadCount = useMemo(() => {
    return (data || []).filter((n) => !n.is_read && !n.read).length;
  }, [data]);

  const filteredNotifications = useMemo(() => {
    let list = data || [];
    if (filterUnreadOnly) {
      list = list.filter((n) => !n.is_read && !n.read);
    }
    if (filterModule) {
      list = list.filter(
        (n) => (n.module || "").toLowerCase() === filterModule.toLowerCase(),
      );
    }
    if (filterPriority) {
      list = list.filter(
        (n) =>
          (n.priority || "").toLowerCase() === filterPriority.toLowerCase(),
      );
    }
    return list;
  }, [data, filterUnreadOnly, filterModule, filterPriority]);

  const clear = async () => {
    setMessage("");
    setError("");
    try {
      await notificationService.clear();
      setMessage("Notifications cleared successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to clear notifications."));
    }
  };

  const markAllRead = async () => {
    setMessage("");
    setError("");
    try {
      const res = await notificationService.markAllRead();
      setMessage(res.data.message || "All notifications marked as read.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to mark all notifications as read."));
    }
  };

  const markRead = async (notificationId) => {
    setMessage("");
    setError("");
    try {
      await notificationService.markRead(notificationId);
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to mark notification as read."));
    }
  };

  const deleteSingle = async (notificationId) => {
    setMessage("");
    setError("");
    try {
      await notificationService.delete(notificationId);
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to delete notification."));
    }
  };

  const handleSavePreferences = async () => {
    setPrefSaving(true);
    setMessage("");
    setError("");
    try {
      const res = await notificationService.updatePreferences(prefs);
      setPrefs(res.data);
      setMessage("Notification preferences updated successfully.");
    } catch (err) {
      setError(getApiError(err, "Failed to save preferences."));
    } finally {
      setPrefSaving(false);
    }
  };

  const openDetails = (notif) => {
    setSelectedNotif(notif);
    deleteSingle(notif.notification_id);
  };

  const navigateToRelated = (notif) => {
    const refId = notif.reference_id || notif.complaint_id;
    const refType = (notif.reference_type || "complaint").toLowerCase();
    notificationService.delete(notif.notification_id).catch(() => {});
    if (refType === "complaint" && refId) {
      navigate(`/complaints/${refId}`);
    }
    setSelectedNotif(null);
  };

  const getPriorityBadgeClass = (priority) => {
    switch ((priority || "").toLowerCase()) {
      case "critical":
        return "bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-900/60 font-bold";
      case "high":
        return "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-900/60 font-semibold";
      case "medium":
        return "bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-900/60 font-medium";
      default:
        return "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 font-normal";
    }
  };

  return (
    <div className="grid gap-6 max-w-4xl">
      <PageHeader
        title={
          unreadCount > 0
            ? `Notification Center (${unreadCount} New)`
            : "Notification Center"
        }
        description="Deliver, track, and configure system alerts, complaint updates, and operational broadcast notices."
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() =>
                setActiveTab(
                  activeTab === "notifications"
                    ? "preferences"
                    : "notifications",
                )
              }
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all shadow-2xs cursor-pointer"
            >
              <Settings className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
              {activeTab === "notifications" ? "Preferences" : "View Alerts"}
            </button>
            {activeTab === "notifications" && unreadCount > 0 && (
              <Button
                variant="subtle"
                size="sm"
                onClick={markAllRead}
                className="font-semibold flex items-center gap-1.5"
              >
                <CheckCheck className="h-3.5 w-3.5 text-primary" />
                Mark All Read
              </Button>
            )}
            {activeTab === "notifications" && data && data.length > 0 && (
              <Button
                variant="danger"
                size="sm"
                onClick={clear}
                className="font-semibold flex items-center gap-1.5"
              >
                <Trash2 className="h-3.5 w-3.5" />
                Clear All
              </Button>
            )}
          </div>
        }
      />

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Segmented Pill Tabs */}
      <div className="inline-flex items-center p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl gap-1 overflow-x-auto max-w-full scrollbar-none">
        <button
          onClick={() => setActiveTab("notifications")}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer whitespace-nowrap shrink-0 ${
            activeTab === "notifications"
              ? "bg-white dark:bg-slate-900 text-primary shadow-2xs font-semibold"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <Inbox className="h-3.5 w-3.5 text-slate-400" />
          <span>Alerts & Messages</span>
          <span
            className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
              activeTab === "notifications"
                ? "bg-primary/10 text-primary"
                : "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
            }`}
          >
            {data?.length || 0}
          </span>
        </button>

        <button
          onClick={() => setActiveTab("preferences")}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer whitespace-nowrap shrink-0 ${
            activeTab === "preferences"
              ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs font-semibold"
              : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
          }`}
        >
          <Settings className="h-3.5 w-3.5 text-slate-400" />
          <span>Delivery Preferences</span>
        </button>
      </div>

      {activeTab === "preferences" ? (
        /* Notification Preferences Form */
        <Card className="grid gap-6">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              Notification Delivery Channels
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Control how you receive system alerts, complaint updates, and operational notices.
            </p>
          </div>

          <div className="grid gap-3">
            <label className="flex items-center justify-between p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg text-primary">
                  <Bell className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-800 dark:text-slate-100">
                    In-App Notifications
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Receive immediate updates in your browser header drawer and operations list.
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={prefs.in_app_enabled}
                onChange={(e) =>
                  setPrefs({ ...prefs, in_app_enabled: e.target.checked })
                }
                className="h-4 w-4 accent-primary rounded cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-50 dark:bg-blue-950/40 rounded-lg text-blue-600 dark:text-blue-400">
                  <Mail className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-800 dark:text-slate-100">
                    Email Notifications
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Receive emails for critical escalations, SLA breaches, and security alerts.
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={prefs.email_enabled}
                onChange={(e) =>
                  setPrefs({ ...prefs, email_enabled: e.target.checked })
                }
                className="h-4 w-4 accent-primary rounded cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between p-4 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 transition-all cursor-pointer opacity-60">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-500 dark:text-slate-400">
                  <Smartphone className="h-5 w-5" />
                </div>
                <div>
                  <div className="text-sm font-bold text-slate-800 dark:text-slate-100">
                    Mobile Push Notifications
                  </div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">
                    Reserved for mobile device integration (Phase 2).
                  </div>
                </div>
              </div>
              <input
                type="checkbox"
                checked={prefs.push_enabled}
                onChange={(e) =>
                  setPrefs({ ...prefs, push_enabled: e.target.checked })
                }
                className="h-4 w-4 accent-primary rounded cursor-pointer"
              />
            </label>
          </div>

          <div className="flex justify-end pt-2">
            <Button
              onClick={handleSavePreferences}
              disabled={prefSaving}
              className="font-bold text-xs"
            >
              {prefSaving ? "Saving..." : "Save Preferences"}
            </Button>
          </div>
        </Card>
      ) : (
        /* Notifications List View */
        <>
          {/* Filter Toolbar */}
          {data && data.length > 0 && (
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3 text-xs">
              <div className="flex flex-wrap items-center gap-2">
                <Filter className="h-3.5 w-3.5 text-slate-400" />
                <span className="font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-[10px]">
                  Filter:
                </span>

                <select
                  value={filterModule}
                  onChange={(e) => setFilterModule(e.target.value)}
                  className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-xl font-medium text-slate-700 dark:text-slate-200 outline-none focus:border-primary text-xs"
                >
                  <option value="">All Modules</option>
                  <option value="Complaint">Complaint</option>
                  <option value="User">User</option>
                  <option value="System">System</option>
                  <option value="Lost & Found">Lost & Found</option>
                </select>

                <select
                  value={filterPriority}
                  onChange={(e) => setFilterPriority(e.target.value)}
                  className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 rounded-xl font-medium text-slate-700 dark:text-slate-200 outline-none focus:border-primary text-xs"
                >
                  <option value="">All Priorities</option>
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => setFilterUnreadOnly(false)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    !filterUnreadOnly
                      ? "bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-slate-100 font-semibold"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                  }`}
                >
                  All ({data.length})
                </button>
                <button
                  onClick={() => setFilterUnreadOnly(true)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    filterUnreadOnly
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                  }`}
                >
                  Unread ({unreadCount})
                </button>
              </div>
            </div>
          )}

          {loading && (
            <Loader label="Loading notifications..." variant="skeleton" />
          )}
          {!loading && (!data || data.length === 0) && (
            <EmptyState
              title="No alerts logged"
              description="System notices, SLA warnings, and complaint updates will appear here in real-time."
            />
          )}
          {!loading &&
            data &&
            data.length > 0 &&
            filteredNotifications.length === 0 && (
              <EmptyState
                title="No matching alerts"
                description="No notifications match your current filter selections."
              />
            )}

          <div className="grid gap-2.5">
            {filteredNotifications.map((notification) => {
              const isUnread = !notification.is_read && !notification.read;
              const isCritical =
                (notification.priority || "").toLowerCase() === "critical";
              const refId =
                notification.reference_id || notification.complaint_id;

              return (
                <div
                  key={notification.notification_id}
                  className={`flex flex-col sm:flex-row items-start justify-between gap-4 p-4 rounded-xl border transition-all duration-150 ${
                    isCritical
                      ? "bg-rose-50/20 dark:bg-rose-950/20 border-rose-200/80 dark:border-rose-900/50"
                      : isUnread
                        ? "bg-blue-50/20 dark:bg-blue-950/15 border-blue-200/80 dark:border-blue-900/50"
                        : "bg-white dark:bg-[#101726] border-slate-200/80 dark:border-slate-800/80"
                  }`}
                >
                  <div
                    className="flex items-start gap-3.5 cursor-pointer flex-1"
                    onClick={() => openDetails(notification)}
                  >
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-xl shrink-0 mt-0.5 ${
                        isCritical
                          ? "bg-rose-100 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400"
                          : isUnread
                            ? "bg-primary/10 text-primary"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500"
                      }`}
                    >
                      {isCritical ? (
                        <AlertTriangle className="h-4 w-4" />
                      ) : (
                        <Bell className="h-4 w-4" />
                      )}
                    </div>

                    <div>
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="text-xs font-semibold text-slate-900 dark:text-slate-100">
                          {notification.title || notification.module || "Alert"}
                        </span>
                        <span className="text-[10px] font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800">
                          {notification.module || "Complaint"}
                        </span>
                        <span
                          className={`text-[10px] px-2 py-0.5 rounded-md border uppercase tracking-wider ${getPriorityBadgeClass(notification.priority)}`}
                        >
                          {notification.priority || "Medium"}
                        </span>
                        {isUnread && (
                          <span className="rounded-md bg-primary/15 px-2 py-0.5 text-[9px] font-bold text-primary">
                            NEW
                          </span>
                        )}
                      </div>

                      <div className="mt-1 text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-normal">
                        {notification.message}
                      </div>
                      <div className="mt-1.5 text-[10px] font-medium text-slate-400 dark:text-slate-500 flex items-center gap-2">
                        <span>{notification.created_at}</span>
                        {notification.sender_id && (
                          <span>• From: {notification.sender_id}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0 self-end sm:self-center">
                    {refId && (
                      <Button
                        variant="subtle"
                        size="sm"
                        onClick={() => navigateToRelated(notification)}
                        className="!h-7 !px-2.5 text-xs font-medium flex items-center gap-1 text-primary hover:bg-primary/10"
                        title="Go to related issue"
                      >
                        View Item
                        <ArrowRight className="h-3 w-3" />
                      </Button>
                    )}
                    {isUnread && (
                      <button
                        type="button"
                        onClick={() => markRead(notification.notification_id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-primary hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                        title="Mark as read"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => deleteSingle(notification.notification_id)}
                      className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
                      title="Delete notification"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* Notification Details Modal */}
      {selectedNotif && (
        <Modal
          title={
            selectedNotif.title ||
            selectedNotif.module ||
            "Notification Details"
          }
          isOpen={!!selectedNotif}
          onClose={() => setSelectedNotif(null)}
        >
          <div className="grid gap-4 text-xs">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <span
                className={`text-[10px] px-2 py-0.5 rounded border font-bold uppercase ${getPriorityBadgeClass(selectedNotif.priority)}`}
              >
                {selectedNotif.priority || "Medium"} Priority
              </span>
              <span className="text-[11px] font-medium text-slate-400">
                {selectedNotif.created_at}
              </span>
            </div>

            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                Message Content
              </div>
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl text-slate-800 dark:text-slate-100 font-normal leading-relaxed text-xs">
                {selectedNotif.message}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 bg-slate-50/60 dark:bg-slate-800/40 p-3 rounded-xl border border-slate-100 dark:border-slate-800">
              <div>
                <span className="text-slate-400 font-medium uppercase text-[10px]">
                  Module:
                </span>
                <div className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                  {selectedNotif.module || "Complaint"}
                </div>
              </div>
              <div>
                <span className="text-slate-400 font-medium uppercase text-[10px]">
                  Reference ID:
                </span>
                <div className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                  {selectedNotif.reference_id ||
                    selectedNotif.complaint_id ||
                    "N/A"}
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              {(selectedNotif.reference_id || selectedNotif.complaint_id) && (
                <Button
                  onClick={() => navigateToRelated(selectedNotif)}
                  className="font-bold flex items-center gap-1.5 text-xs"
                >
                  Go to Related Item
                  <ArrowRight className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

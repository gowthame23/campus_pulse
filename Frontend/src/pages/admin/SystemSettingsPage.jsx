import { useEffect, useState } from "react";
import {
  Settings,
  ArrowLeft,
  Save,
  RotateCcw,
  AlertTriangle,
  ShieldCheck,
  Database,
  FileText,
  Bell,
  BarChart2,
  Wrench,
  Lock,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Toast from "../../components/Toast.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Loader from "../../components/Loader.jsx";
import Modal from "../../components/Modal.jsx";
import { settingsService } from "../../services/settingsService.js";

export default function SystemSettingsPage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [groupedSettings, setGroupedSettings] = useState({});
  const [activeCategory, setActiveCategory] = useState("General");
  const [stagedChanges, setStagedChanges] = useState({});

  const [toastMessage, setToastMessage] = useState("");
  const [toastTone, setToastTone] = useState("success");
  const [saving, setSaving] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [adminPassword, setAdminPassword] = useState("");

  const categoryIcons = {
    General: Settings,
    Complaint: FileText,
    Security: ShieldCheck,
    Notification: Bell,
    "File Upload": Database,
    Authentication: Lock,
    Analytics: BarChart2,
    Maintenance: Wrench,
  };

  const loadSettings = async () => {
    setLoading(true);
    try {
      const response = await settingsService.getAll();
      setGroupedSettings(response.data);
      setStagedChanges({});
    } catch (err) {
      showToast(
        err?.response?.data?.detail || "Failed to load system settings.",
        "danger",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSettings();
  }, []);

  const showToast = (message, tone = "success") => {
    setToastMessage(message);
    setToastTone(tone);
  };

  const handleFieldChange = (key, val) => {
    setStagedChanges((prev) => ({
      ...prev,
      [key]: val,
    }));
  };

  const getCurrentVal = (setting) => {
    if (stagedChanges[setting.setting_key] !== undefined) {
      return stagedChanges[setting.setting_key];
    }
    return setting.setting_value !== undefined
      ? setting.setting_value
      : setting.value;
  };

  const handleBulkSave = async () => {
    if (Object.keys(stagedChanges).length === 0) {
      showToast("No setting changes staged.", "warning");
      return;
    }
    setShowConfirmModal(true);
  };

  const executeBulkSave = async () => {
    setSaving(true);
    try {
      const bulkPayload = Object.entries(stagedChanges).map(([key, val]) => ({
        setting_key: key,
        setting_value: val,
      }));
      await settingsService.bulkUpdate({
        settings: bulkPayload,
        admin_password: adminPassword || undefined,
      });
      showToast("System configuration changes saved successfully.");
      setShowConfirmModal(false);
      setAdminPassword("");
      loadSettings();
    } catch (err) {
      showToast(
        err?.response?.data?.detail || "Failed to save settings.",
        "danger",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleResetCategory = async () => {
    if (
      !window.confirm(
        `Reset all settings in ${activeCategory} to factory defaults?`,
      )
    )
      return;
    setSaving(true);
    try {
      await settingsService.resetCategory(activeCategory);
      showToast(`Category '${activeCategory}' reset to default values.`);
      loadSettings();
    } catch (err) {
      showToast(
        err?.response?.data?.detail || "Failed to reset category.",
        "danger",
      );
    } finally {
      setSaving(false);
    }
  };

  const handleResetAll = async () => {
    if (
      !window.confirm(
        "WARNING: Reset ALL system configurations across all categories to defaults?",
      )
    )
      return;
    setSaving(true);
    try {
      await settingsService.resetAll();
      showToast("All system settings reset to factory defaults.");
      loadSettings();
    } catch (err) {
      showToast(
        err?.response?.data?.detail || "Failed to reset settings.",
        "danger",
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading)
    return (
      <Loader label="Loading administration settings..." variant="skeleton" />
    );

  const currentCategorySettings = groupedSettings[activeCategory] || [];
  const categoriesList = Object.keys(groupedSettings);
  const hasStaged = Object.keys(stagedChanges).length > 0;

  return (
    <div className="grid gap-6 max-w-5xl">
      <div className="flex items-center justify-between border-b border-slate-200/60 pb-4">
        <div className="flex items-center gap-3">
          <button
            onClick={() =>
              // Fall back to the dashboard when this is the first page in the
              // session, so Back never leaves the app to a blank tab.
              window.history.state?.idx > 0 ? navigate(-1) : navigate("/")
            }
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <PageHeader
            title="System Configuration & Administration"
            description="Centralized settings panel for SLA days, security policies, uploads, and maintenance mode."
          />
        </div>

        <div className="flex items-center gap-2">
          {hasStaged && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setStagedChanges({})}
              className="font-semibold"
            >
              Discard Changes
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={handleBulkSave}
            disabled={!hasStaged}
            className="font-bold flex items-center gap-1.5"
          >
            <Save className="h-4 w-4" />
            Save Staged ({Object.keys(stagedChanges).length})
          </Button>
        </div>
      </div>

      <Toast
        message={toastMessage}
        tone={toastTone}
        onClose={() => setToastMessage("")}
      />

      {/* Category Selection Grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {categoriesList.map((cat) => {
          const IconComponent = categoryIcons[cat] || Settings;
          const isActive = activeCategory === cat;

          return (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`flex items-center gap-3 p-3.5 rounded-xl border text-left transition-all ${
                isActive
                  ? "border-primary bg-primary/5 shadow-xs"
                  : "border-slate-200 bg-white hover:border-slate-300"
              }`}
            >
              <div
                className={`p-2 rounded-lg ${isActive ? "bg-primary text-white" : "bg-slate-100 text-slate-500"}`}
              >
                <IconComponent className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xs font-bold text-slate-900">{cat}</div>
                <div className="text-[10px] font-semibold text-slate-400">
                  {groupedSettings[cat]?.length || 0} Configs
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Category Settings Form */}
      <Card className="grid gap-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              {activeCategory} Settings
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Configure system parameters for {activeCategory} behavior.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="subtle"
              size="sm"
              onClick={handleResetCategory}
              className="text-xs font-semibold text-slate-600"
            >
              <RotateCcw className="h-3.5 w-3.5 mr-1" />
              Reset Category
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={handleResetAll}
              className="text-xs font-semibold"
            >
              Reset All System Defaults
            </Button>
          </div>
        </div>

        <div className="grid gap-5">
          {currentCategorySettings.map((setting) => {
            const val = getCurrentVal(setting);
            const isStaged = stagedChanges[setting.setting_key] !== undefined;

            return (
              <div
                key={setting.setting_key}
                className={`p-4 rounded-xl border transition-all ${isStaged ? "border-amber-300 bg-amber-50/20" : "border-slate-100 bg-slate-50/30"}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-2 mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">
                      {setting.setting_key}
                    </span>
                    {setting.requires_restart === 1 && (
                      <span className="px-2 py-0.5 rounded bg-rose-100 text-rose-700 text-[9px] font-bold uppercase tracking-wider">
                        Restart Required
                      </span>
                    )}
                    {isStaged && (
                      <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-[9px] font-bold uppercase tracking-wider">
                        Modified
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                    {setting.setting_type}
                  </span>
                </div>

                <p className="text-xs text-slate-500 mb-3">
                  {setting.description}
                </p>

                {setting.setting_type === "Boolean" ? (
                  <select
                    value={String(val).toLowerCase()}
                    onChange={(e) =>
                      handleFieldChange(setting.setting_key, e.target.value)
                    }
                    className="w-full max-w-xs px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs font-bold text-slate-800 dark:text-slate-100 focus:outline-none"
                  >
                    <option value="true">Enabled (true)</option>
                    <option value="false">Disabled (false)</option>
                  </select>
                ) : (
                  <Input
                    type={
                      setting.setting_type === "Integer" ||
                      setting.setting_type === "Float"
                        ? "number"
                        : "text"
                    }
                    value={val}
                    onChange={(e) =>
                      handleFieldChange(setting.setting_key, e.target.value)
                    }
                    className="max-w-md bg-white text-xs font-bold text-slate-800"
                  />
                )}
              </div>
            );
          })}
        </div>

        <div className="flex justify-end pt-2 border-t border-slate-100">
          <Button
            onClick={handleBulkSave}
            disabled={!hasStaged}
            className="font-bold flex items-center gap-1.5"
          >
            <Save className="h-4 w-4" />
            Save Staged Settings ({Object.keys(stagedChanges).length})
          </Button>
        </div>
      </Card>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <Modal
          title="Confirm System Configuration Update"
          isOpen={showConfirmModal}
          onClose={() => setShowConfirmModal(false)}
        >
          <div className="grid gap-4 text-xs">
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 flex items-start gap-2.5 text-amber-800">
              <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600 mt-0.5" />
              <div>
                <div className="font-bold">Save Configuration Changes?</div>
                <div className="mt-0.5">
                  You are applying {Object.keys(stagedChanges).length}{" "}
                  configuration change(s). Sensitive security settings require
                  Administrator authentication.
                </div>
              </div>
            </div>

            <Input
              label="Confirm Administrator Password"
              type="password"
              placeholder="Enter your admin password..."
              value={adminPassword}
              onChange={(e) => setAdminPassword(e.target.value)}
            />

            <div className="flex justify-end gap-2 pt-2">
              <Button
                variant="secondary"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={executeBulkSave}
                disabled={saving}
                className="font-bold"
              >
                {saving ? "Applying..." : "Confirm & Apply"}
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}

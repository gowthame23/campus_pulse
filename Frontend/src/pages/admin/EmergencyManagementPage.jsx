import { useState, useEffect } from "react";
import {
  AlertTriangle,
  Plus,
  Phone,
  Trash2,
  Edit,
  Clock,
  Shield,
  Moon,
  Sun,
  CheckCircle,
  RefreshCw,
  Upload,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import Modal from "../../components/Modal.jsx";
import Input from "../../components/Input.jsx";
import Select from "../../components/Select.jsx";
import Toast from "../../components/Toast.jsx";
import Loader from "../../components/Loader.jsx";
import BulkImportModal from "../../components/BulkImportModal.jsx";
import { emergencyService } from "../../services/emergencyService.js";
import { departmentService } from "../../services/departmentService.js";
import { locationService } from "../../services/locationService.js";
import { settingsService } from "../../services/settingsService.js";

export default function EmergencyManagementPage() {
  const [activeTab, setActiveTab] = useState("categories"); // "categories" | "contacts" | "settings"
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  // Data
  const [categories, setCategories] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);

  // Settings
  const [securityName, setSecurityName] = useState("Campus Security");
  const [securityPhone, setSecurityPhone] = useState("+91 98765 43210");
  const [nightStart, setNightStart] = useState("20:00");
  const [nightEnd, setNightEnd] = useState("08:00");
  const [savingSettings, setSavingSettings] = useState(false);

  // Category Modal
  const [showCatModal, setShowCatModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState(null);
  const [catName, setCatName] = useState("");
  const [catDeptId, setCatDeptId] = useState("");
  const [catSortOrder, setCatSortOrder] = useState(0);
  const [catIsActive, setCatIsActive] = useState(true);

  // Contact Modal
  const [showContactModal, setShowContactModal] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [cntName, setCntName] = useState("");
  const [cntPhone, setCntPhone] = useState("");
  const [cntDeptId, setCntDeptId] = useState("");
  const [cntLocId, setCntLocId] = useState("");
  const [cntSortOrder, setCntSortOrder] = useState(0);
  const [cntActive, setCntActive] = useState(true);
  const [cntTimeWindow, setCntTimeWindow] = useState("all"); // "all" | "day" | "night"
  const [showBulkImportModal, setShowBulkImportModal] = useState(false);

  useEffect(() => {
    loadAll();
  }, []);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [catsRes, cntsRes, deptsRes, locsRes, settingsRes] = await Promise.all([
        emergencyService.getCategories(false).catch(() => ({ data: [] })),
        emergencyService.getContacts({ active_only: false }).catch(() => ({ data: [] })),
        departmentService.list().catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        settingsService.getAll().catch(() => ({ data: {} })),
      ]);
      setCategories(catsRes.data || []);
      setContacts(cntsRes.data || []);
      setDepartments(deptsRes.data || []);
      setLocations(locsRes.data || []);

      // Parse security settings
      const allSettings = settingsRes.data || {};
      const secList = allSettings.Security || [];
      const genList = allSettings.General || [];
      const sNameObj = secList.find((s) => s.setting_key === "campus_security_name");
      const sPhoneObj = secList.find((s) => s.setting_key === "campus_security_phone");
      const nStartObj = genList.find((s) => s.setting_key === "night_hours_start");
      const nEndObj = genList.find((s) => s.setting_key === "night_hours_end");

      if (sNameObj) setSecurityName(sNameObj.setting_value || sNameObj.value || "Campus Security");
      if (sPhoneObj) setSecurityPhone(sPhoneObj.setting_value || sPhoneObj.value || "+91 98765 43210");
      if (nStartObj) setNightStart(nStartObj.setting_value || nStartObj.value || "20:00");
      if (nEndObj) setNightEnd(nEndObj.setting_value || nEndObj.value || "08:00");
    } catch (err) {
      console.error("Error loading emergency settings:", err);
      setToast({ type: "danger", message: "Failed to load emergency data." });
    } finally {
      setLoading(false);
    }
  };

  // Category Handlers
  const handleOpenCatModal = (cat = null) => {
    setEditingCategory(cat);
    if (cat) {
      setCatName(cat.name);
      setCatDeptId(cat.department_id || "");
      setCatSortOrder(cat.sort_order || 0);
      setCatIsActive(Boolean(cat.is_active));
    } else {
      setCatName("");
      setCatDeptId("");
      setCatSortOrder(categories.length + 1);
      setCatIsActive(true);
    }
    setShowCatModal(true);
  };

  const handleSaveCategory = async (e) => {
    e.preventDefault();
    if (!catName.trim()) return;
    try {
      if (editingCategory) {
        await emergencyService.updateCategory(editingCategory.category_id, {
          name: catName.trim(),
          department_id: catDeptId || null,
          sort_order: parseInt(catSortOrder, 10),
          is_active: catIsActive,
        });
        setToast({ type: "success", message: "Emergency category updated." });
      } else {
        await emergencyService.createCategory({
          name: catName.trim(),
          department_id: catDeptId || null,
          sort_order: parseInt(catSortOrder, 10),
          is_active: catIsActive,
        });
        setToast({ type: "success", message: "Emergency category created." });
      }
      setShowCatModal(false);
      loadAll();
    } catch (err) {
      setToast({ type: "danger", message: err?.response?.data?.detail || "Failed to save category." });
    }
  };

  const handleDeleteCategory = async (catId) => {
    if (!window.confirm("Are you sure you want to delete this emergency category?")) return;
    try {
      await emergencyService.deleteCategory(catId);
      setToast({ type: "success", message: "Category deleted." });
      loadAll();
    } catch (err) {
      setToast({ type: "danger", message: "Failed to delete category." });
    }
  };

  // Contact Handlers
  const handleOpenContactModal = (contact = null) => {
    setEditingContact(contact);
    if (contact) {
      setCntName(contact.name);
      setCntPhone(contact.phone);
      setCntDeptId(contact.department_id || "");
      setCntLocId(contact.location_id || "");
      setCntSortOrder(contact.sort_order || 0);
      setCntActive(Boolean(contact.active));
      if (contact.night_only) setCntTimeWindow("night");
      else if (contact.day_only) setCntTimeWindow("day");
      else setCntTimeWindow("all");
    } else {
      setCntName("");
      setCntPhone("");
      setCntDeptId("");
      setCntLocId("");
      setCntSortOrder(contacts.length + 1);
      setCntActive(true);
      setCntTimeWindow("all");
    }
    setShowContactModal(true);
  };

  const handleSaveContact = async (e) => {
    e.preventDefault();
    if (!cntName.trim() || !cntPhone.trim()) return;
    const payload = {
      name: cntName.trim(),
      phone: cntPhone.trim(),
      department_id: cntDeptId || null,
      location_id: cntLocId || null,
      sort_order: parseInt(cntSortOrder, 10),
      active: cntActive,
      night_only: cntTimeWindow === "night",
      day_only: cntTimeWindow === "day",
    };

    try {
      if (editingContact) {
        await emergencyService.updateContact(editingContact.contact_id, payload);
        setToast({ type: "success", message: "Emergency contact updated." });
      } else {
        await emergencyService.createContact(payload);
        setToast({ type: "success", message: "Emergency contact created." });
      }
      setShowContactModal(false);
      loadAll();
    } catch (err) {
      setToast({ type: "danger", message: err?.response?.data?.detail || "Failed to save contact." });
    }
  };

  const handleDeleteContact = async (cntId) => {
    if (!window.confirm("Are you sure you want to delete this emergency contact?")) return;
    try {
      await emergencyService.deleteContact(cntId);
      setToast({ type: "success", message: "Contact deleted." });
      loadAll();
    } catch (err) {
      setToast({ type: "danger", message: "Failed to delete contact." });
    }
  };

  // Settings Save
  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSavingSettings(true);
    try {
      await settingsService.bulkUpdate({
        settings: [
          { setting_key: "campus_security_name", setting_value: securityName.trim() },
          { setting_key: "campus_security_phone", setting_value: securityPhone.trim() },
          { setting_key: "night_hours_start", setting_value: nightStart.trim() },
          { setting_key: "night_hours_end", setting_value: nightEnd.trim() },
        ],
        reason: "Emergency settings update",
      });
      setToast({ type: "success", message: "Emergency security & night hours settings saved." });
      loadAll();
    } catch (err) {
      setToast({ type: "danger", message: "Failed to save settings." });
    } finally {
      setSavingSettings(false);
    }
  };

  if (loading) return <Loader label="Loading emergency management..." />;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {toast && (
        <Toast
          message={toast.message}
          tone={toast.type}
          onClose={() => setToast(null)}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
            <span className="p-2 bg-rose-600 text-white rounded-xl shadow-md shadow-rose-600/30">
              <AlertTriangle className="h-5 w-5" />
            </span>
            Emergency System Setup
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Configure emergency categories, prioritized staff phone lines, campus security desk, and night hour filters.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={loadAll}>
            <RefreshCw className="h-4 w-4 mr-1.5" /> Refresh
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 gap-2 overflow-x-auto max-w-full scrollbar-none">
        <button
          onClick={() => setActiveTab("categories")}
          className={`py-2.5 px-4 font-bold text-xs rounded-t-xl transition-colors border-b-2 whitespace-nowrap shrink-0 ${
            activeTab === "categories"
              ? "border-rose-600 text-rose-600 dark:text-rose-400 bg-rose-50/50 dark:bg-rose-950/20"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Categories ({categories.length})
        </button>
        <button
          onClick={() => setActiveTab("contacts")}
          className={`py-2.5 px-4 font-bold text-xs rounded-t-xl transition-colors border-b-2 whitespace-nowrap shrink-0 ${
            activeTab === "contacts"
              ? "border-rose-600 text-rose-600 dark:text-rose-400 bg-rose-50/50 dark:bg-rose-950/20"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Staff Emergency Contacts ({contacts.length})
        </button>
        <button
          onClick={() => setActiveTab("settings")}
          className={`py-2.5 px-4 font-bold text-xs rounded-t-xl transition-colors border-b-2 whitespace-nowrap shrink-0 ${
            activeTab === "settings"
              ? "border-rose-600 text-rose-600 dark:text-rose-400 bg-rose-50/50 dark:bg-rose-950/20"
              : "border-transparent text-slate-500 hover:text-slate-700"
          }`}
        >
          Security & Night Hours
        </button>
      </div>

      {/* Tab 1: Categories */}
      {activeTab === "categories" && (
        <Card className="!p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Emergency Problem Categories
              </h2>
              <p className="text-xs text-slate-500">
                Categories shown on the student's 3-tap emergency sheet.
              </p>
            </div>
            <Button
              onClick={() => handleOpenCatModal()}
              variant="primary"
              size="sm"
              className="bg-rose-600 hover:bg-rose-700 font-bold"
            >
              <Plus className="h-4 w-4 mr-1" /> Add Category
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-bold border-y border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="py-2.5 px-3">Order</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Mapped Department</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {categories.map((cat) => (
                  <tr key={cat.category_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="py-3 px-3 font-semibold text-slate-400">{cat.sort_order}</td>
                    <td className="py-3 px-3 font-bold text-slate-900 dark:text-slate-100">{cat.name}</td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">
                      {cat.department_name ? (
                        <span className="px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-300 font-semibold text-[11px]">
                          {cat.department_name}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">None (Direct Hotline & Security Priority)</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        cat.is_active ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"
                      }`}>
                        {cat.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right space-x-2">
                      <button
                        onClick={() => handleOpenCatModal(cat)}
                        className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 font-semibold"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteCategory(cat.category_id)}
                        className="text-rose-500 hover:text-rose-700 font-semibold"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 2: Contacts */}
      {activeTab === "contacts" && (
        <Card className="!p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Department Emergency Contacts
              </h2>
              <p className="text-xs text-slate-500">
                Staff lines displayed when an emergency occurs. Ordered location-specific first, day/night filtered.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button
                onClick={() => setShowBulkImportModal(true)}
                variant="outline"
                size="sm"
                className="font-bold border-rose-200 text-rose-700 dark:border-rose-900/60 dark:text-rose-300 hover:bg-rose-50 dark:hover:bg-rose-950/40"
              >
                <Upload className="h-4 w-4 mr-1" /> Bulk Import Contacts
              </Button>
              <Button
                onClick={() => handleOpenContactModal()}
                variant="primary"
                size="sm"
                className="bg-rose-600 hover:bg-rose-700 font-bold"
              >
                <Plus className="h-4 w-4 mr-1" /> Add Contact
              </Button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-bold border-y border-slate-200 dark:border-slate-700">
                <tr>
                  <th className="py-2.5 px-3">Order</th>
                  <th className="py-2.5 px-3">Name</th>
                  <th className="py-2.5 px-3">Phone</th>
                  <th className="py-2.5 px-3">Department</th>
                  <th className="py-2.5 px-3">Location Scope</th>
                  <th className="py-2.5 px-3">Shift Hours</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {contacts.map((cnt) => (
                  <tr key={cnt.contact_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="py-3 px-3 font-semibold text-slate-400">{cnt.sort_order}</td>
                    <td className="py-3 px-3 font-bold text-slate-900 dark:text-slate-100">{cnt.name}</td>
                    <td className="py-3 px-3 font-mono font-bold text-emerald-700 dark:text-emerald-400">{cnt.phone}</td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">{cnt.department_name || "All"}</td>
                    <td className="py-3 px-3 text-slate-600 dark:text-slate-300">
                      {cnt.location_name ? (
                        <span className="font-semibold text-purple-700 dark:text-purple-300">
                          {cnt.location_name}
                        </span>
                      ) : (
                        <span className="text-slate-400">All locations</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      {cnt.night_only ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-100 text-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">
                          <Moon className="h-3 w-3" /> Night only
                        </span>
                      ) : cnt.day_only ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300">
                          <Sun className="h-3 w-3" /> Day only
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                          24 / 7
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-right space-x-2">
                      <button
                        onClick={() => handleOpenContactModal(cnt)}
                        className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 font-semibold"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteContact(cnt.contact_id)}
                        className="text-rose-500 hover:text-rose-700 font-semibold"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Tab 3: Security & Night Hours Settings */}
      {activeTab === "settings" && (
        <Card className="!p-5 space-y-4">
          <form onSubmit={handleSaveSettings} className="space-y-4 max-w-xl">
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Shield className="h-4 w-4 text-rose-600" />
                Campus Security Desk Line
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Always included in emergency call lists right after Warden / Hotline.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Security Desk Name"
                value={securityName}
                onChange={(e) => setSecurityName(e.target.value)}
                required
              />
              <Input
                label="Security Phone Number"
                value={securityPhone}
                onChange={(e) => setSecurityPhone(e.target.value)}
                required
              />
            </div>

            <div className="pt-3 border-t border-slate-100 dark:border-slate-800">
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Clock className="h-4 w-4 text-indigo-600" />
                Night Hours Window
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Controls automatic filtering for Day-Only and Night-Only staff contacts.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input
                label="Night Window Start (HH:MM)"
                value={nightStart}
                onChange={(e) => setNightStart(e.target.value)}
                placeholder="20:00"
                required
              />
              <Input
                label="Night Window End (HH:MM)"
                value={nightEnd}
                onChange={(e) => setNightEnd(e.target.value)}
                placeholder="08:00"
                required
              />
            </div>

            <Button
              type="submit"
              variant="primary"
              size="md"
              loading={savingSettings}
              className="bg-rose-600 hover:bg-rose-700 font-bold"
            >
              Save Emergency Settings
            </Button>
          </form>
        </Card>
      )}

      {/* Category Modal */}
      {showCatModal && (
        <Modal
          isOpen={showCatModal}
          onClose={() => setShowCatModal(false)}
          title={editingCategory ? "Edit Emergency Category" : "Add Emergency Category"}
        >
          <form onSubmit={handleSaveCategory} className="space-y-4">
            <Input
              label="Category Name"
              value={catName}
              onChange={(e) => setCatName(e.target.value)}
              placeholder="e.g. Electrical, Lift, Flooding"
              required
            />

            <Select
              label="Mapped Department (Optional)"
              value={catDeptId}
              onChange={(e) => setCatDeptId(e.target.value)}
              options={[
                { value: "", label: "None (Direct Hotline 112 / Campus Security Priority)" },
                ...departments.map((d) => ({ value: d.department_id, label: d.name })),
              ]}
            />

            <Input
              label="Display Sort Order"
              type="number"
              value={catSortOrder}
              onChange={(e) => setCatSortOrder(e.target.value)}
            />

            <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={catIsActive}
                onChange={(e) => setCatIsActive(e.target.checked)}
                className="rounded text-rose-600 focus:ring-rose-500"
              />
              <span>Active (Visible on Emergency Button)</span>
            </label>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button type="button" variant="outline" size="sm" onClick={() => setShowCatModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" className="bg-rose-600 hover:bg-rose-700">
                Save Category
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Contact Modal */}
      {showContactModal && (
        <Modal
          isOpen={showContactModal}
          onClose={() => setShowContactModal(false)}
          title={editingContact ? "Edit Emergency Contact" : "Add Emergency Contact"}
        >
          <form onSubmit={handleSaveContact} className="space-y-4">
            <Input
              label="Contact / Worker Name"
              value={cntName}
              onChange={(e) => setCntName(e.target.value)}
              placeholder="e.g. Duty Electrician"
              required
            />

            <Input
              label="Phone Number"
              value={cntPhone}
              onChange={(e) => setCntPhone(e.target.value)}
              placeholder="e.g. +91 98765 43210"
              required
            />

            <Select
              label="Department"
              value={cntDeptId}
              onChange={(e) => setCntDeptId(e.target.value)}
              options={[
                { value: "", label: "All Departments" },
                ...departments.map((d) => ({ value: d.department_id, label: d.name })),
              ]}
            />

            <Select
              label="Location Specific (Optional)"
              value={cntLocId}
              onChange={(e) => setCntLocId(e.target.value)}
              options={[
                { value: "", label: "All Locations (Department-wide)" },
                ...locations.map((l) => ({ value: l.location_id, label: l.name })),
              ]}
            />

            <Select
              label="Shift Hours Window"
              value={cntTimeWindow}
              onChange={(e) => setCntTimeWindow(e.target.value)}
              options={[
                { value: "all", label: "24/7 (Shown Day and Night)" },
                { value: "day", label: "Day Shift Only (Hidden during night)" },
                { value: "night", label: "Night Shift Only (Hidden during day)" },
              ]}
            />

            <Input
              label="Sort Order"
              type="number"
              value={cntSortOrder}
              onChange={(e) => setCntSortOrder(e.target.value)}
            />

            <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={cntActive}
                onChange={(e) => setCntActive(e.target.checked)}
                className="rounded text-rose-600 focus:ring-rose-500"
              />
              <span>Active Contact</span>
            </label>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button type="button" variant="outline" size="sm" onClick={() => setShowContactModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" className="bg-rose-600 hover:bg-rose-700">
                Save Contact
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Bulk Import Emergency Contacts Modal (Part 3.2c) */}
      <BulkImportModal
        isOpen={showBulkImportModal}
        onClose={() => setShowBulkImportModal(false)}
        type="emergency_contacts"
        onSuccess={() => {
          loadAll();
          setToast({ type: "success", message: "Emergency contacts imported successfully." });
        }}
      />
    </div>
  );
}

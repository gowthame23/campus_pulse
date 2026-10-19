import React, { useState, useEffect } from "react";
import { createPortal } from "react-dom";
import {
  Phone,
  AlertTriangle,
  Zap,
  Droplets,
  Flame,
  HeartPulse,
  Building,
  HelpCircle,
  X,
  CheckCircle,
  Clock,
  Shield,
  Loader2,
  RefreshCw,
} from "lucide-react";
import Button from "./Button.jsx";
import { emergencyService } from "../services/emergencyService.js";
import { useLanguage } from "../context/LanguageContext.jsx";

const CATEGORY_ICONS = {
  electrical: Zap,
  plumbing: Droplets,
  water: Droplets,
  lift: Building,
  fire: Flame,
  smoke: Flame,
  medical: HeartPulse,
  other: HelpCircle,
};

export function getCategoryIcon(name = "") {
  const lower = name.toLowerCase();
  for (const [key, Icon] of Object.entries(CATEGORY_ICONS)) {
    if (lower.includes(key)) return Icon;
  }
  return AlertTriangle;
}

export function getCategoryLabel(name = "", t) {
  if (!t) return name;
  const lower = name.toLowerCase();
  if (lower.includes("elec")) return t("emergency.cat_electrical", name);
  if (lower.includes("plumb") || lower.includes("water")) return t("emergency.cat_plumbing", name);
  if (lower.includes("lift")) return t("emergency.cat_lift", name);
  if (lower.includes("fire") || lower.includes("smoke")) return t("emergency.cat_fire", name);
  if (lower.includes("med")) return t("emergency.cat_medical", name);
  if (lower.includes("oth")) return t("emergency.cat_other", name);
  return name;
}

export default function EmergencySheet({ isOpen, onClose, userLocationId, onEmergencyCreated }) {
  const { t } = useLanguage();
  const [step, setStep] = useState("categories"); // "categories" | "calling"
  const [categories, setCategories] = useState([]);
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [callList, setCallList] = useState([]);
  const [loadingCallList, setLoadingCallList] = useState(false);
  const [createdComplaintId, setCreatedComplaintId] = useState(null);
  const [reachedState, setReachedState] = useState(null); // null | true | false
  const [submittingReached, setSubmittingReached] = useState(false);
  const [reAlertMessage, setReAlertMessage] = useState("");

  useEffect(() => {
    if (isOpen) {
      setStep("categories");
      setSelectedCategory(null);
      setCallList([]);
      setCreatedComplaintId(null);
      setReachedState(null);
      setReAlertMessage("");
      loadCategories();
    }
  }, [isOpen]);

  const loadCategories = async () => {
    setLoadingCategories(true);
    try {
      const res = await emergencyService.getCategories(true);
      const raw = res.data || [];
      const seen = new Set();
      const unique = [];
      for (const cat of raw) {
        const key = (cat.name || "").trim().toLowerCase();
        if (key && !seen.has(key)) {
          seen.add(key);
          unique.push(cat);
        }
      }
      setCategories(unique);
    } catch (err) {
      console.error("Failed to load emergency categories:", err);
    } finally {
      setLoadingCategories(false);
    }
  };

  const handleSelectCategory = async (cat) => {
    setSelectedCategory(cat);
    setLoadingCallList(true);
    setStep("calling");

    try {
      // 1. Auto-create Critical complaint (Rule 2.3e)
      const compRes = await emergencyService.createEmergency({
        category: cat.category_id || cat.name,
        location_id: userLocationId || null,
      });
      const cid = compRes.data?.complaint_id;
      setCreatedComplaintId(cid);
      if (onEmergencyCreated) onEmergencyCreated(compRes.data);

      // 2. Fetch prioritized call list (Rule 2.3d)
      const callRes = await emergencyService.getCallList(
        cat.category_id || cat.name,
        userLocationId || null,
      );
      setCallList(callRes.data || []);
    } catch (err) {
      console.error("Error creating emergency or loading call list:", err);
      // Fallback call list even if API complaint creation fails
      try {
        const callRes = await emergencyService.getCallList(
          cat.category_id || cat.name,
          userLocationId || null,
        );
        setCallList(callRes.data || []);
      } catch (e2) {
        setCallList([{ name: "National Emergency", role: "Emergency Services", phone: "112", is_hotline: true }]);
      }
    } finally {
      setLoadingCallList(false);
    }
  };

  const handleReached = async (reached) => {
    if (!createdComplaintId) {
      if (reached) onClose();
      return;
    }
    setSubmittingReached(true);
    try {
      await emergencyService.recordReached(createdComplaintId, reached);
      setReachedState(reached);
      if (reached) {
        setTimeout(() => {
          onClose();
        }, 800);
      } else {
        setReAlertMessage("All emergency staff alerted again immediately! Please call another person below.");
      }
    } catch (err) {
      console.error("Failed to record reached status:", err);
    } finally {
      setSubmittingReached(false);
    }
  };

  if (!isOpen) return null;

  const sheetModal = (
    <div
      className="fixed inset-0 z-[100] overflow-y-auto bg-black/75 backdrop-blur-sm flex flex-col justify-end sm:justify-center p-0 sm:p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-white dark:bg-slate-900 w-full sm:max-w-lg mx-auto rounded-t-3xl sm:rounded-3xl shadow-2xl border border-rose-200 dark:border-rose-950/60 overflow-hidden flex flex-col max-h-[88vh] sm:max-h-[85vh] my-0 sm:my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="bg-rose-600 px-5 py-4 text-white flex items-center justify-between shrink-0 shadow-sm">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 bg-white/20 rounded-xl backdrop-blur-md">
              <AlertTriangle className="h-5 w-5 text-white animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-extrabold tracking-tight">
                {step === "categories"
                  ? `🚨 ${t("emergency.sheet_title", "What's the emergency?")}`
                  : `🚨 ${t("emergency.emergency_badge", "Emergency")}: ${selectedCategory ? getCategoryLabel(selectedCategory.name, t) : "Incident"}`}
              </h2>
              <p className="text-xs text-rose-100 font-medium">
                {step === "categories"
                  ? t("emergency.sheet_desc", "Select a category to immediately connect and alert staff")
                  : "Critical complaint logged. Staff alerted."}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full bg-white/10 hover:bg-white/25 text-white transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 overflow-y-auto flex-1 space-y-4">
          {step === "categories" ? (
            <div>
              {loadingCategories ? (
                <div className="py-12 flex flex-col items-center justify-center gap-2 text-slate-500">
                  <Loader2 className="h-8 w-8 animate-spin text-rose-600" />
                  <span className="text-sm">Loading emergency services...</span>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-3">
                  {categories.map((cat) => {
                    const IconComponent = getCategoryIcon(cat.name);
                    const isFireOrMedical = /fire|smoke|medical/i.test(cat.name);
                    const label = getCategoryLabel(cat.name, t);
                    const hasSubtext =
                      cat.department_name &&
                      cat.department_name.toLowerCase() !== cat.name.toLowerCase() &&
                      !cat.department_name.startsWith("DEPT");
                    return (
                      <button
                        key={cat.category_id || cat.name}
                        onClick={() => handleSelectCategory(cat)}
                        className={`flex flex-col items-center justify-center text-center p-4 rounded-2xl border-2 transition-all active:scale-95 ${
                          isFireOrMedical
                            ? "bg-rose-50/80 hover:bg-rose-100/80 dark:bg-rose-950/20 dark:hover:bg-rose-950/40 border-rose-300 dark:border-rose-900 text-rose-900 dark:text-rose-100"
                            : "bg-slate-50/80 hover:bg-slate-100/80 dark:bg-slate-800/40 dark:hover:bg-slate-800/80 border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100"
                        }`}
                      >
                        <div
                          className={`p-3 rounded-2xl mb-2.5 ${
                            isFireOrMedical
                              ? "bg-rose-600 text-white shadow-md shadow-rose-600/30"
                              : "bg-slate-800 dark:bg-slate-700 text-white"
                          }`}
                        >
                          <IconComponent className="h-6 w-6" />
                        </div>
                        <span className="text-sm font-bold line-clamp-1">{label}</span>
                        {hasSubtext && (
                          <span className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                            {cat.department_name}
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}

              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5 text-rose-500" />
                  {t("emergency.national_hotline", "National Hotline 112 always accessible")}
                </span>
                <a
                  href="tel:112"
                  className="font-bold text-rose-600 dark:text-rose-400 hover:underline flex items-center gap-1"
                >
                  <Phone className="h-3 w-3" /> {t("emergency.call_112", "Call 112")}
                </a>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Alert Feedback Banner */}
              {reAlertMessage ? (
                <div className="p-3 bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900 rounded-xl text-amber-900 dark:text-amber-200 text-xs font-semibold flex items-center gap-2 animate-in fade-in">
                  <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
                  <span>{reAlertMessage}</span>
                </div>
              ) : (
                <div className="p-3 bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900 rounded-xl text-rose-900 dark:text-rose-200 text-xs font-semibold flex items-center gap-2">
                  <Clock className="h-4 w-4 text-rose-600 shrink-0" />
                  <span>Complaint #{createdComplaintId} filed with Critical priority. Call responder directly:</span>
                </div>
              )}

              {/* Call List (Rule 2.3d) */}
              {loadingCallList ? (
                <div className="py-8 flex flex-col items-center justify-center gap-2 text-slate-500">
                  <Loader2 className="h-6 w-6 animate-spin text-rose-600" />
                  <span className="text-xs">Preparing emergency call lines...</span>
                </div>
              ) : (
                <div className="space-y-2.5">
                  {callList.map((contact, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/80 hover:border-rose-300 transition-all"
                    >
                      <div className="min-w-0 pr-3">
                        <div className="font-bold text-sm text-slate-900 dark:text-slate-100 truncate">
                          {contact.name}
                        </div>
                        <div className="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">
                          {contact.role}
                        </div>
                      </div>
                      <a
                        href={`tel:${contact.phone}`}
                        className="shrink-0 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white rounded-xl font-bold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-600/25 transition-all"
                      >
                        <Phone className="h-3.5 w-3.5 fill-current" />
                        Call
                      </a>
                    </div>
                  ))}
                </div>
              )}

              {/* "Did you reach someone?" (Rule 2.3f) */}
              <div className="pt-3 border-t border-slate-200 dark:border-slate-800">
                <div className="text-xs font-bold text-slate-700 dark:text-slate-300 mb-2">
                  {t("emergency.did_you_reach", "Did you reach someone?")}
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    disabled={submittingReached}
                    onClick={() => handleReached(true)}
                    className="py-2.5 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-900 dark:text-slate-100 font-bold text-xs flex items-center justify-center gap-1.5 transition-all"
                  >
                    <CheckCircle className="h-4 w-4 text-emerald-600" />
                    {t("emergency.yes_reached", "Yes, I spoke to them")}
                  </button>
                  <button
                    disabled={submittingReached}
                    onClick={() => handleReached(false)}
                    className="py-2.5 px-3 rounded-xl bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/40 dark:hover:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-900 font-bold text-xs flex items-center justify-center gap-1.5 transition-all"
                  >
                    <RefreshCw className="h-4 w-4 text-rose-600" />
                    {t("emergency.no_answer", "No answer / Couldn't reach")}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return typeof document !== "undefined" ? createPortal(sheetModal, document.body) : sheetModal;
}

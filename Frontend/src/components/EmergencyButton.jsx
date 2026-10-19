import React, { useState, useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { AlertTriangle, Phone, Shield } from "lucide-react";
import { emergencyService } from "../services/emergencyService.js";
import EmergencySheet from "./EmergencySheet.jsx";

export default function EmergencyButton({ userLocationId, compact = false }) {
  const [tapCount, setTapCount] = useState(0);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [status, setStatus] = useState(null); // { is_locked, locked_until, strikes_count }
  const [fallbackOpen, setFallbackOpen] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const res = await emergencyService.getStatus();
      setStatus(res.data);
    } catch (err) {
      console.error("Failed to load emergency status:", err);
    }
  };

  const handleTap = () => {
    if (status?.is_locked) {
      setFallbackOpen(true);
      return;
    }

    if (tapCount === 0) {
      setTapCount(1);
      timerRef.current = setTimeout(() => {
        setTapCount(0);
      }, 3000);
    } else if (tapCount === 1) {
      setTapCount(2);
    } else if (tapCount === 2) {
      // 3 taps completed within 3 seconds!
      if (timerRef.current) clearTimeout(timerRef.current);
      setTapCount(0);
      setSheetOpen(true);
    }
  };

  // Label text progression
  const getButtonLabel = () => {
    if (tapCount === 1) return "1… Tap 2 more";
    if (tapCount === 2) return "2… Tap once more";
    return "Emergency";
  };

  if (status?.is_locked) {
    const pauseDate = status.locked_until ? status.locked_until.slice(0, 10) : "soon";
    return (
      <div className="flex flex-col items-start gap-1">
        <div className="px-3 py-1.5 rounded-xl bg-amber-100 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 text-xs font-bold border border-amber-300 dark:border-amber-800 flex items-center gap-1.5">
          <AlertTriangle className="h-3.5 w-3.5 text-amber-600" />
          <span>Emergency shortcut paused until {pauseDate}</span>
        </div>
        <button
          onClick={() => setFallbackOpen(true)}
          className="text-xs text-rose-600 dark:text-rose-400 font-bold underline hover:text-rose-700 flex items-center gap-1 ml-1"
        >
          <Phone className="h-3 w-3" /> Emergency numbers
        </button>

        {fallbackOpen &&
          typeof document !== "undefined" &&
          createPortal(
            <div
              className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200"
              onClick={() => setFallbackOpen(false)}
            >
              <div
                className="bg-white dark:bg-slate-900 rounded-2xl max-w-sm w-full p-5 shadow-2xl border border-slate-200 dark:border-slate-800 space-y-4"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm flex items-center gap-2">
                    <Shield className="h-4 w-4 text-rose-600" />
                    Emergency Numbers
                  </h3>
                  <button
                    onClick={() => setFallbackOpen(false)}
                    className="text-slate-400 hover:text-slate-600 text-xs font-bold"
                  >
                    ✕
                  </button>
                </div>
                <div className="space-y-2">
                  <a
                    href="tel:112"
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-bold text-slate-900 dark:text-slate-100"
                  >
                    <span>112 National Emergency</span>
                    <span className="text-rose-600">📞 Call</span>
                  </a>
                  <a
                    href="tel:+919876543210"
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-sm font-bold text-slate-900 dark:text-slate-100"
                  >
                    <span>Campus Security Desk</span>
                    <span className="text-emerald-600">📞 Call</span>
                  </a>
                </div>
                <button
                  onClick={() => setFallbackOpen(false)}
                  className="w-full py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-bold"
                >
                  Close
                </button>
              </div>
            </div>,
            document.body
          )}
      </div>
    );
  }

  return (
    <>
      <button
        onClick={handleTap}
        title="Tap 3 times within 3 seconds to open Emergency dialer"
        className={`bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-extrabold rounded-2xl shadow-lg shadow-rose-600/30 flex items-center gap-1.5 transition-all select-none active:scale-95 ${
          compact
            ? "px-3 py-1.5 text-xs"
            : "px-4 py-2.5 text-sm"
        } ${tapCount > 0 ? "ring-4 ring-rose-400/50 animate-pulse bg-rose-700" : ""}`}
      >
        <span className="animate-bounce">🚨</span>
        <span>{getButtonLabel()}</span>
      </button>

      <EmergencySheet
        isOpen={sheetOpen}
        onClose={() => setSheetOpen(false)}
        userLocationId={userLocationId}
      />
    </>
  );
}

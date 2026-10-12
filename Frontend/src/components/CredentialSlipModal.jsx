import { useState } from "react";
import { Printer, Copy, Check, X, Shield, KeyRound, Phone, User } from "lucide-react";
import Button from "./Button.jsx";

export default function CredentialSlipModal({ slip, slips = [], onClose }) {
  const [copied, setCopied] = useState(false);
  const items = slip ? [slip] : slips;

  if (!items || items.length === 0) return null;

  const handleCopy = (item) => {
    const text = `Campus Pulse Login Slip\nName: ${item.name}\nRole: ${item.role || "Employee"}\nPhone: ${item.phone}\nTemporary Password: ${item.temporary_password}\nLogin at: ${window.location.origin}/login`;
    navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white font-bold text-sm">
              CP
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Worker Login Credentials Slip
              </h3>
              <p className="text-xs text-slate-500">
                Hand this temporary password slip to the employee
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Slips List (Printable) */}
        <div className="overflow-y-auto flex-1 space-y-4 print:p-0">
          {items.map((item, idx) => (
            <div
              key={item.user_id || idx}
              className="p-4 rounded-xl border-2 border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/40 space-y-3 relative print:border-solid print:border-black"
            >
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                    Campus Pulse &bull; Staff Access
                  </span>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-0.5">
                    {item.name}
                  </h4>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 dark:bg-blue-950/60 dark:text-blue-300">
                  {item.role || "Employee"}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold block flex items-center gap-1">
                    <Phone className="h-3 w-3" /> Login Phone (Username)
                  </span>
                  <span className="font-mono font-bold text-slate-800 dark:text-slate-200">
                    {item.phone || "-"}
                  </span>
                </div>

                <div className="p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
                  <span className="text-[10px] text-slate-400 font-semibold block flex items-center gap-1">
                    <KeyRound className="h-3 w-3" /> Temporary Password
                  </span>
                  <span className="font-mono font-bold text-amber-600 dark:text-amber-400 text-sm">
                    {item.temporary_password}
                  </span>
                </div>
              </div>

              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
                Instructions: Log in using your 10-digit mobile number and this temporary password. You will be required to choose a new password on your first login.
              </p>

              <div className="pt-1 flex items-center justify-end gap-2 print:hidden">
                <Button
                  size="sm"
                  variant="subtle"
                  onClick={() => handleCopy(item)}
                  className="!h-7 text-xs font-semibold"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3 text-emerald-500 mr-1" /> Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3 mr-1" /> Copy Slip
                    </>
                  )}
                </Button>
              </div>
            </div>
          ))}
        </div>

        {/* Modal Actions */}
        <div className="flex justify-between items-center pt-3 border-t border-slate-100 dark:border-slate-800 shrink-0 print:hidden">
          <Button
            variant="subtle"
            size="sm"
            onClick={handlePrint}
            className="flex items-center gap-1.5 font-semibold text-xs"
          >
            <Printer className="h-4 w-4" /> Print Slips
          </Button>

          <Button variant="primary" size="sm" onClick={onClose}>
            Done
          </Button>
        </div>
      </div>
    </div>
  );
}


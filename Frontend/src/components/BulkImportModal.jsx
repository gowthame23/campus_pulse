import { useState, useRef } from "react";
import {
  Upload,
  Download,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  X,
  FileText,
  Printer,
  RotateCcw,
  Check,
} from "lucide-react";
import Button from "./Button.jsx";
import Loader from "./Loader.jsx";
import CredentialSlipModal from "./CredentialSlipModal.jsx";
import { setupService } from "../services/setupService.js";

const TYPE_CONFIG = {
  locations: {
    title: "Bulk Import Locations",
    description: "Import rooms, blocks, hostels, and academic buildings with parents and wardens.",
    templateFilename: "locations_template",
    columns: ["name", "parent", "type", "warden_email_or_phone"],
  },
  staff: {
    title: "Bulk Import Staff",
    description: "Import Employees, Coordinators, Wardens, and App Managers. Workers without email get temporary passwords.",
    templateFilename: "staff_template",
    columns: ["name", "role", "email", "phone", "teams"],
  },
  teams: {
    title: "Bulk Import Teams",
    description: "Import teams with department, assigned places, coordinator, backup, and workers.",
    templateFilename: "teams_template",
    columns: ["team name", "department", "places", "coordinator", "backup", "members"],
  },
  emergency_contacts: {
    title: "Bulk Import Emergency Contacts",
    description: "Import department and location emergency contacts with day/night hours and order.",
    templateFilename: "emergency_contacts_template",
    columns: ["department", "location", "name", "phone", "order", "day_only", "night_only"],
  },
};

export default function BulkImportModal({ type = "locations", isOpen, onClose, onSuccess }) {
  const config = TYPE_CONFIG[type] || TYPE_CONFIG.locations;
  const fileInputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [previewData, setPreviewData] = useState(null);
  const [importResult, setImportResult] = useState(null);
  const [showSlipModal, setShowSlipModal] = useState(false);

  if (!isOpen) return null;

  const handleDownloadTemplate = async (format) => {
    try {
      const blob = await setupService.getTemplateBlob(type, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${config.templateFilename}.${format === "xlsx" ? "xlsx" : "csv"}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to download template.");
    }
  };

  const handleFileChange = async (e) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setError("");
    setPreviewData(null);
    setImportResult(null);

    // Automatically trigger preview
    setLoading(true);
    try {
      const preview = await setupService.previewImport(type, selected);
      setPreviewData(preview);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to parse and validate file.");
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteImport = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const result = await setupService.executeImport(type, file);
      setImportResult(result);
      if (onSuccess) onSuccess(result);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to execute bulk import.");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreviewData(null);
    setImportResult(null);
    setError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-4xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <FileSpreadsheet className="h-5 w-5 text-primary" />
              {config.title}
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">{config.description}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 text-xs bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-xl border border-rose-200 dark:border-rose-900 font-semibold shrink-0">
            {error}
          </div>
        )}

        {/* Step 1: File selection & Template Download */}
        {!importResult && (
          <div className="shrink-0 space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-50 dark:bg-slate-850 border border-slate-200 dark:border-slate-800">
              <div>
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200 block">
                  1. Download Template
                </span>
                <span className="text-[11px] text-slate-500">
                  Pre-formatted columns: {config.columns.join(", ")}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="subtle"
                  onClick={() => handleDownloadTemplate("csv")}
                  className="!h-8 text-xs font-semibold flex items-center gap-1.5"
                >
                  <Download className="h-3.5 w-3.5" /> CSV Template
                </Button>
                <Button
                  size="sm"
                  variant="subtle"
                  onClick={() => handleDownloadTemplate("xlsx")}
                  className="!h-8 text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5"
                >
                  <FileSpreadsheet className="h-3.5 w-3.5" /> Excel Template (.xlsx)
                </Button>
              </div>
            </div>

            <div className="p-4 rounded-xl border-2 border-dashed border-slate-200 dark:border-slate-800 hover:border-primary transition-colors text-center">
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv, .xlsx, .xls"
                onChange={handleFileChange}
                className="hidden"
                id="bulk-import-file-input"
              />
              <label
                htmlFor="bulk-import-file-input"
                className="cursor-pointer block space-y-1.5"
              >
                <Upload className="h-6 w-6 text-slate-400 mx-auto" />
                <p className="text-xs font-bold text-slate-700 dark:text-slate-200">
                  {file ? file.name : "Click to select or drop CSV or Excel spreadsheet"}
                </p>
                <p className="text-[11px] text-slate-400">
                  Supports .csv, .xlsx, and .xls files
                </p>
              </label>
            </div>
          </div>
        )}

        {loading && <Loader label="Processing spreadsheet..." />}

        {/* Step 2: Preview with Row-by-Row Error Validation */}
        {!loading && previewData && !importResult && (
          <div className="overflow-hidden flex-1 flex flex-col border border-slate-200 dark:border-slate-800 rounded-xl">
            <div className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-xs shrink-0">
              <div className="flex items-center gap-3">
                <span className="font-bold text-slate-800 dark:text-slate-200">
                  Validation Preview ({previewData.total_rows} rows)
                </span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                  ✓ {previewData.valid_count} Valid
                </span>
                {previewData.invalid_count > 0 && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                    ✕ {previewData.invalid_count} Invalid
                  </span>
                )}
              </div>
              <Button size="sm" variant="ghost" onClick={handleReset} className="!h-7 text-xs">
                <RotateCcw className="h-3 w-3 mr-1" /> Choose Different File
              </Button>
            </div>

            <div className="overflow-y-auto flex-1 text-xs">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-100/60 dark:bg-slate-800/40 text-slate-500 font-semibold sticky top-0">
                  <tr>
                    <th className="p-2.5">Row</th>
                    <th className="p-2.5">Status</th>
                    {config.columns.map((c) => (
                      <th key={c} className="p-2.5 capitalize">{c.replace(/_/g, " ")}</th>
                    ))}
                    <th className="p-2.5">Validation Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {previewData.rows.map((r) => {
                    const isValid = r.is_valid;
                    return (
                      <tr
                        key={r.row_index}
                        className={isValid ? "hover:bg-slate-50 dark:hover:bg-slate-800/30" : "bg-rose-50/70 dark:bg-rose-950/30"}
                      >
                        <td className="p-2.5 font-mono text-slate-400">{r.row_index}</td>
                        <td className="p-2.5">
                          {isValid ? (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                              Valid
                            </span>
                          ) : (
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300">
                              Error
                            </span>
                          )}
                        </td>
                        {config.columns.map((c) => {
                          const val = r.raw_data[c] || r.raw_data[c.replace(/_/g, " ")] || "-";
                          return (
                            <td key={c} className="p-2.5 text-slate-700 dark:text-slate-300">
                              {val}
                            </td>
                          );
                        })}
                        <td className="p-2.5">
                          {isValid ? (
                            <span className="text-emerald-600 dark:text-emerald-400 font-medium text-[11px]">
                              Ready to import
                            </span>
                          ) : (
                            <span className="text-rose-600 dark:text-rose-400 font-bold text-[11px]">
                              {r.errors.join("; ")}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            <div className="p-3 bg-slate-50 dark:bg-slate-850 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center shrink-0">
              <span className="text-xs text-slate-500">
                {previewData.invalid_count > 0
                  ? `Clicking import will proceed with the ${previewData.valid_count} valid rows and safely skip the ${previewData.invalid_count} bad rows.`
                  : "All rows passed validation and are ready to import."}
              </span>
              <Button
                variant="primary"
                size="sm"
                onClick={handleExecuteImport}
                disabled={previewData.valid_count === 0}
                className="font-bold text-xs"
              >
                Import {previewData.valid_count} Valid Rows
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Execution Summary Report */}
        {!loading && importResult && (
          <div className="overflow-y-auto flex-1 space-y-4 text-xs">
            <div className="p-4 rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-200 space-y-1">
              <div className="flex items-center gap-2 font-bold text-sm">
                <CheckCircle2 className="h-4.5 w-4.5 text-emerald-600 dark:text-emerald-400" />
                Import Complete
              </div>
              <p className="text-xs font-semibold">
                Successfully processed {importResult.total_rows} rows:{" "}
                <span className="underline">{importResult.imported_count || 0} imported</span>,{" "}
                <span className="underline">{importResult.updated_count || 0} updated</span>, and{" "}
                <span className="underline">{importResult.failed_count || 0} skipped</span>.
              </p>
            </div>

            {/* If staff import generated worker temporary password slips */}
            {importResult.credentials_slips?.length > 0 && (
              <div className="p-4 rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/30 space-y-3">
                <div className="flex justify-between items-center">
                  <div>
                    <h4 className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                      <Printer className="h-4 w-4 text-amber-600" />
                      Worker Credential Slips Generated ({importResult.credentials_slips.length})
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      Temporary passwords generated for workers without email. Print or copy slips now.
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={() => setShowSlipModal(true)}
                    className="!h-8 text-xs font-bold"
                  >
                    View & Print Slips
                  </Button>
                </div>
              </div>
            )}

            {/* Row Report Table */}
            <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden">
              <div className="p-2.5 bg-slate-50 dark:bg-slate-800/60 font-bold text-slate-700 dark:text-slate-300">
                Row-by-Row Execution Summary
              </div>
              <div className="max-h-60 overflow-y-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead className="bg-slate-100/60 dark:bg-slate-800/40 text-slate-500 font-semibold sticky top-0">
                    <tr>
                      <th className="p-2.5">Row</th>
                      <th className="p-2.5">Name</th>
                      <th className="p-2.5">Result</th>
                      <th className="p-2.5">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                    {importResult.report?.map((r, i) => (
                      <tr key={i} className={r.status === "Success" ? "hover:bg-slate-50 dark:hover:bg-slate-800/20" : "bg-rose-50/50 dark:bg-rose-950/20"}>
                        <td className="p-2.5 font-mono text-slate-400">{r.row_index}</td>
                        <td className="p-2.5 font-bold text-slate-800 dark:text-slate-200">{r.name}</td>
                        <td className="p-2.5">
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            r.status === "Success" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300" : "bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
                          }`}>
                            {r.action || r.status}
                          </span>
                        </td>
                        <td className="p-2.5 text-slate-500">{r.reason || "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="primary" size="sm" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        )}

        {/* Modal footer when not in preview/result */}
        {!previewData && !importResult && (
          <div className="flex justify-end pt-3 border-t border-slate-100 dark:border-slate-800 shrink-0">
            <Button variant="subtle" size="sm" onClick={onClose}>
              Cancel
            </Button>
          </div>
        )}
      </div>

      {showSlipModal && importResult?.credentials_slips && (
        <CredentialSlipModal
          slips={importResult.credentials_slips}
          onClose={() => setShowSlipModal(false)}
        />
      )}
    </div>
  );
}


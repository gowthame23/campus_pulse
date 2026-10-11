import { useState, useEffect } from "react";
import {
  FileText,
  Download,
  Calendar,
  Clock,
  Search,
  Filter,
  FileSpreadsheet,
} from "lucide-react";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import StatCard from "../components/StatCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Loader from "../components/Loader.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Toast from "../components/Toast.jsx";
import Input from "../components/Input.jsx";
import { useAsyncData } from "../hooks/useAsyncData.js";
import { reportService } from "../services/reportService.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../utils/dateFormatter.js";

export default function ReportsPage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("generator"); // 'generator' | 'schedules'
  const [typeFilter, setTypeFilter] = useState("");
  const [query, setQuery] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Generator Form State
  const [reportName, setReportName] = useState("");
  const [reportType, setReportType] = useState("Complaint");
  const [fileFormat, setFileFormat] = useState("CSV");
  const [generating, setGenerating] = useState(false);

  const [summaryMetrics, setSummaryMetrics] = useState(null);

  const isStaffAdmin = [
    "administrator",
    "app_manager",
    "location_in_charge",
    "coordinator",
  ].includes(user?.role);

  const {
    data: reports,
    loading: loadingReports,
    reload: reloadReports,
  } = useAsyncData(
    async () =>
      (await reportService.listReports({ report_type: typeFilter, q: query }))
        .data,
    [typeFilter, query],
  );

  const { data: schedules } = useAsyncData(
    async () => (await reportService.getSchedules()).data,
    [],
  );

  useEffect(() => {
    reportService
      .getSummary()
      .then((res) => setSummaryMetrics(res.data))
      .catch(() => {});
  }, [reports]);

  const handleGenerateReport = async (e) => {
    e.preventDefault();
    setGenerating(true);
    setMessage("");
    setError("");

    try {
      const res = await reportService.generateReport({
        report_name: reportName || `${reportType} Export Report`,
        report_type: reportType,
        file_format: fileFormat,
      });
      setMessage(`Report '${res.data.report_name}' generated successfully.`);
      setReportName("");
      reloadReports();
    } catch (err) {
      setError(err?.response?.data?.detail || "Report generation failed.");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadReport = async (report) => {
    try {
      const response = await reportService.downloadReport(report.report_id);
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", report.file_name);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError(err?.response?.data?.detail || "Report download failed.");
    }
  };

  const listRpt = reports || [];
  const listSch = schedules || [];

  return (
    <div className="grid gap-6 max-w-6xl">
      <PageHeader
        title="Reports & Analytics Center"
        description="Centralized report generation engine and scheduled analytics exports."
      />

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Dashboard Overview Cards */}
      {summaryMetrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="TOTAL REPORTS"
            value={summaryMetrics.total_reports}
            accent
          />
          <StatCard
            label="SCHEDULED RECURRING"
            value={summaryMetrics.scheduled_reports}
          />
          <StatCard
            label="GENERATED TODAY"
            value={summaryMetrics.generated_today}
          />
          <StatCard
            label="STORAGE USED (MB)"
            value={`${summaryMetrics.storage_used_mb} MB`}
          />
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab("generator")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 ${
            activeTab === "generator"
              ? "border-primary text-primary"
              : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          Report Generator & History
        </button>
        <button
          onClick={() => setActiveTab("schedules")}
          className={`px-4 py-2.5 text-xs font-bold transition-all border-b-2 ${
            activeTab === "schedules"
              ? "border-primary text-primary"
              : "border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          }`}
        >
          Scheduled Reports ({listSch.length})
        </button>
      </div>

      {activeTab === "generator" && (
        <>
          {/* Report Generator Panel */}
          {isStaffAdmin && (
            <Card className="grid gap-4 bg-slate-50/50 dark:bg-slate-800/40">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <FileSpreadsheet className="h-4 w-4 text-primary" /> On-Demand
                Report Generator
              </h3>

              <form
                onSubmit={handleGenerateReport}
                className="grid sm:grid-cols-4 gap-3 text-xs"
              >
                <Input
                  placeholder="Report Name (Optional)"
                  value={reportName}
                  onChange={(e) => setReportName(e.target.value)}
                  className="sm:col-span-2"
                />

                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value)}
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-semibold text-slate-800 dark:text-slate-100"
                >
                  <option value="Complaint">Complaint Resolution</option>
                  <option value="WorkOrder">Work Order Repair</option>
                  <option value="Visitor">Visitor Log</option>
                  <option value="Asset">Asset Inventory</option>
                  <option value="Audit">Audit Trail</option>
                </select>

                <select
                  value={fileFormat}
                  onChange={(e) => setFileFormat(e.target.value)}
                  className="px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-semibold text-slate-800 dark:text-slate-100"
                >
                  <option value="CSV">CSV Format</option>
                  <option value="JSON">JSON Format</option>
                </select>

                <Button
                  type="submit"
                  disabled={generating}
                  className="sm:col-span-4 font-bold flex items-center justify-center gap-1.5"
                >
                  <FileText className="h-4 w-4" />
                  {generating ? "Generating File..." : "Generate & Save Report"}
                </Button>
              </form>
            </Card>
          )}

          {/* Generated Reports History */}
          {loadingReports ? (
            <Loader label="Loading report history..." variant="skeleton" />
          ) : listRpt.length === 0 ? (
            <EmptyState
              title="No generated reports"
              description="Generated CSV/JSON reports will appear here."
            />
          ) : (
            <div className="grid gap-3">
              {listRpt.map((r) => (
                <Card
                  key={r.report_id}
                  className="flex items-center justify-between gap-4"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">
                        {r.report_name}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {r.report_type}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-sky-100 dark:bg-sky-950 text-sky-800 dark:text-sky-300">
                        {r.file_format}
                      </span>
                    </div>

                    <div className="text-xs text-slate-400 dark:text-slate-400 font-semibold mt-1 flex items-center gap-4">
                      <span>Generated by: {r.generated_by}</span>
                      <span>Date: {formatDate(r.generated_at)}</span>
                      <span>Downloads: {r.download_count}</span>
                    </div>
                  </div>

                  <Button
                    size="sm"
                    onClick={() => handleDownloadReport(r)}
                    className="shrink-0 font-bold flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700"
                  >
                    <Download className="h-4 w-4" /> Download
                  </Button>
                </Card>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === "schedules" && (
        <Card className="grid gap-4">
          <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
            Active Scheduled Recurring Reports
          </h3>
          {listSch.length === 0 ? (
            <EmptyState
              title="No active schedules"
              description="Automated daily/weekly background reports will be listed here."
            />
          ) : (
            <div className="grid gap-3">
              {listSch.map((s) => (
                <div
                  key={s.schedule_id}
                  className="p-3 bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 rounded-xl flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-900 dark:text-slate-100">
                      {s.template_name} ({s.frequency})
                    </div>
                    <div className="text-slate-500 dark:text-slate-400 mt-0.5">
                      Recipients: {s.email_recipients || "Coordinator Group"}
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 font-bold text-[10px] uppercase">
                    Active Schedule
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

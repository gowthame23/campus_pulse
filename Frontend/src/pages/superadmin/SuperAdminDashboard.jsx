import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import StatCard from "../../components/StatCard.jsx";
import Card from "../../components/Card.jsx";
import Loader from "../../components/Loader.jsx";
import Button from "../../components/Button.jsx";
import Badge from "../../components/Badge.jsx";
import { Shield, CheckCircle, Server, Activity, HelpCircle } from "lucide-react";
import apiClient from "../../api/axios.js";

export default function SuperAdminDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        setLoading(true);
        const res = await apiClient.get("/platform/dashboard");
        setData(res.data);
      } catch (err) {
        setError(err?.response?.data?.detail || "Failed to load platform dashboard.");
      } finally {
        setLoading(false);
      }
    }
    fetchDashboard();
  }, []);

  if (loading) return <Loader label="Loading Platform Dashboard..." />;

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            Campus Pulse
          </h1>
          <p className="text-sm font-semibold text-slate-500 dark:text-slate-400 mt-1">
            Platform Overview • Super Admin
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            onClick={() => navigate("/superadmin/health")}
            variant="primary"
            size="md"
            className="font-bold shrink-0"
          >
            <Activity className="h-4 w-4" />
            Platform Health
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 rounded-xl text-xs font-semibold">
          {error}
        </div>
      )}

      {data && (
        <>
          {/* 4 Key Metrics Row */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Institutions"
              value={data.total_registered_institutions}
              subtext={`${data.active_institutions} active`}
              onClick={() => navigate("/superadmin/institutions")}
            />
            <StatCard
              label="System Status"
              value="Healthy"
              subtext={`${data.healthy_deployments} active nodes`}
              onClick={() => navigate("/superadmin/health")}
            />
            <StatCard
              label="Support Requests"
              value={data.open_support_issues}
              accent={data.open_support_issues > 0}
              subtext="Platform support tickets"
              onClick={() => navigate("/superadmin/support")}
            />
            <StatCard
              label="Version"
              value={`v${data.platform_version}`}
              subtext="Release build"
              onClick={() => navigate("/superadmin/health")}
            />
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="!p-5">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Server className="h-4 w-4 text-emerald-500" />
                  System Platform Health
                </h2>
                <Link
                  to="/superadmin/health"
                  className="text-xs font-semibold text-primary hover:underline"
                >
                  Diagnostics
                </Link>
              </div>
              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                  <span className="text-slate-600 dark:text-slate-400 flex items-center gap-2">
                    <Server className="w-3.5 h-3.5 text-slate-400" /> Platform Core Version
                  </span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    v{data.platform_version}
                  </span>
                </div>
                <div className="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-slate-800/60">
                  <span className="text-slate-600 dark:text-slate-400 flex items-center gap-2">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-500" /> Tenant Deployments
                  </span>
                  <span className="font-bold text-slate-900 dark:text-slate-100">
                    {data.active_institutions} / {data.total_registered_institutions} Active
                  </span>
                </div>
                <div className="flex justify-between items-center py-1.5">
                  <span className="text-slate-600 dark:text-slate-400 flex items-center gap-2">
                    <Shield className="w-3.5 h-3.5 text-indigo-500" /> Operational Data Boundary
                  </span>
                  <Badge tone="success">Isolated</Badge>
                </div>
              </div>
            </Card>

            <Card className="!p-5">
              <div className="pb-3 border-b border-slate-100 dark:border-slate-800 mb-3">
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Shield className="h-4 w-4 text-indigo-500" />
                  Data Privacy & Boundary Scope
                </h2>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed mb-3">
                Super Admin operates strictly at the platform infrastructure level. Institutional operational data (complaints, student records, staff profiles, location bookings) is strictly isolated and inaccessible.
              </p>
              <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl border border-slate-100 dark:border-slate-800 text-[11px] space-y-1 text-slate-700 dark:text-slate-300">
                <p className="font-bold text-slate-900 dark:text-slate-100">Platform Capabilities:</p>
                <ul className="list-disc list-inside space-y-0.5 text-slate-600 dark:text-slate-400">
                  <li>Tenant Institution Registry & Onboarding</li>
                  <li>Platform Technical Support Ticket Resolution</li>
                  <li>Application System Health Diagnostics</li>
                  <li>Version & Release Metadata Management</li>
                </ul>
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

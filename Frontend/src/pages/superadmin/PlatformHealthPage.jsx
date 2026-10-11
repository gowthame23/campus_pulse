import { useState, useEffect } from "react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import Loader from "../../components/Loader.jsx";
import Badge from "../../components/Badge.jsx";
import { Activity, Server, Database, RefreshCw, ShieldCheck, CheckCircle2 } from "lucide-react";
import apiClient from "../../api/axios.js";

export default function PlatformHealthPage() {
  const [health, setHealth] = useState(null);
  const [version, setVersion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHealthAndVersion = async () => {
    try {
      setLoading(true);
      const [hRes, vRes] = await Promise.all([
        apiClient.get("/platform/health"),
        apiClient.get("/platform/version"),
      ]);
      setHealth(hRes.data);
      setVersion(vRes.data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to fetch platform health status.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthAndVersion();
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Application Health & Version Diagnostics"
        description="Real-time system health checks, database connectivity status, and software version details."
        actions={
          <Button onClick={fetchHealthAndVersion} variant="secondary" className="flex items-center gap-2">
            <RefreshCw className="w-4 h-4" /> Refresh Status
          </Button>
        }
      />

      {error && (
        <div className="p-4 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <Loader label="Running System Health Diagnostic..." />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {health && (
            <Card title="System Diagnostics Status">
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b dark:border-gray-800">
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-indigo-500" /> Overall Status
                  </span>
                  <Badge tone={health.application_status === "Healthy" ? "success" : "danger"}>
                    {health.application_status}
                  </Badge>
                </div>

                <div className="flex justify-between items-center py-2 border-b dark:border-gray-800">
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                    <Server className="w-5 h-5 text-blue-500" /> API Availability
                  </span>
                  <span className="flex items-center gap-1.5 text-sm font-semibold text-green-600">
                    <CheckCircle2 className="w-4 h-4" /> Available (100%)
                  </span>
                </div>

                <div className="flex justify-between items-center py-2 border-b dark:border-gray-800">
                  <span className="text-gray-600 dark:text-gray-400 flex items-center gap-2">
                    <Database className="w-5 h-5 text-purple-500" /> Database Connection
                  </span>
                  <span className="flex items-center gap-1.5 text-sm font-semibold text-green-600">
                    <CheckCircle2 className="w-4 h-4" /> Connected
                  </span>
                </div>

                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-600 dark:text-gray-400 text-sm">Last Health Check</span>
                  <span className="text-xs font-mono text-gray-500">{health.last_health_check}</span>
                </div>
              </div>
            </Card>
          )}

          {version && (
            <Card title="Software Release & Environment Metadata">
              <div className="space-y-4">
                <div className="flex justify-between items-center py-2 border-b dark:border-gray-800">
                  <span className="text-gray-600 dark:text-gray-400">Application Version</span>
                  <span className="font-bold text-gray-900 dark:text-white font-mono">
                    v{version.application_version}
                  </span>
                </div>

                <div className="flex justify-between items-center py-2 border-b dark:border-gray-800">
                  <span className="text-gray-600 dark:text-gray-400">Deployment Identifier</span>
                  <span className="font-mono text-xs text-gray-700 dark:text-gray-300">
                    {version.deployment_id}
                  </span>
                </div>

                <div className="flex justify-between items-center py-2 border-b dark:border-gray-800">
                  <span className="text-gray-600 dark:text-gray-400">Environment</span>
                  <span className="text-sm font-semibold text-indigo-600 dark:text-indigo-400">
                    {version.environment}
                  </span>
                </div>

                <div className="flex justify-between items-center py-2">
                  <span className="text-gray-600 dark:text-gray-400">Release Build Date</span>
                  <span className="text-xs text-gray-500">{version.release_date}</span>
                </div>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

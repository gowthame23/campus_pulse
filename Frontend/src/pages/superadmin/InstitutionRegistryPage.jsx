import { useState, useEffect } from "react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Modal from "../../components/Modal.jsx";
import Loader from "../../components/Loader.jsx";
import Badge from "../../components/Badge.jsx";
import { Plus, Building, Mail, Phone, Calendar, Server, Power } from "lucide-react";
import apiClient from "../../api/axios.js";

export default function InstitutionRegistryPage() {
  const [institutions, setInstitutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    admin_name: "",
    admin_email: "",
    contact_info: "",
    admin_password: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  // Deactivate / reactivate (OTP-verified) state
  const [statusTarget, setStatusTarget] = useState(null); // { inst, action }
  const [otpInfo, setOtpInfo] = useState(null); // response from request-otp
  const [otpCode, setOtpCode] = useState("");
  const [statusReason, setStatusReason] = useState("");
  const [statusBusy, setStatusBusy] = useState(false);
  const [statusError, setStatusError] = useState(null);

  const openStatusModal = (inst) => {
    setStatusTarget({ inst, action: inst.status === "Active" ? "deactivate" : "reactivate" });
    setOtpInfo(null);
    setOtpCode("");
    setStatusReason("");
    setStatusError(null);
  };

  const closeStatusModal = () => {
    if (statusBusy) return;
    setStatusTarget(null);
  };

  const requestStatusOtp = async () => {
    const { inst, action } = statusTarget;
    setStatusError(null);
    try {
      setStatusBusy(true);
      const res = await apiClient.post(`/platform/institutions/${inst.institution_id}/${action}/request-otp`);
      setOtpInfo(res.data);
    } catch (err) {
      setStatusError(err?.response?.data?.detail || "Could not send the verification code.");
    } finally {
      setStatusBusy(false);
    }
  };

  const confirmStatusChange = async (e) => {
    e.preventDefault();
    const { inst, action } = statusTarget;
    setStatusError(null);
    try {
      setStatusBusy(true);
      await apiClient.post(`/platform/institutions/${inst.institution_id}/${action}/confirm`, {
        action,
        otp_code: otpCode.trim(),
        reason: statusReason,
      });
      setStatusTarget(null);
      fetchInstitutions();
    } catch (err) {
      setStatusError(err?.response?.data?.detail || "Verification failed.");
    } finally {
      setStatusBusy(false);
    }
  };

  const fetchInstitutions = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/platform/institutions");
      setInstitutions(res.data || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load institution registry.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstitutions();
  }, []);

  const handleOnboardSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      setSubmitting(true);
      await apiClient.post("/platform/institutions", formData);
      setModalOpen(false);
      setFormData({
        name: "",
        code: "",
        admin_name: "",
        admin_email: "",
        contact_info: "",
        admin_password: "",
      });
      fetchInstitutions();
    } catch (err) {
      setFormError(err?.response?.data?.detail || "Failed to onboard institution.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Platform Institution Registry"
        description="Manage registered institution tenants, platform metadata, and initial admin onboarding."
        actions={
          <Button onClick={() => setModalOpen(true)} className="flex items-center gap-2">
            <Plus className="w-4 h-4" /> Onboard Institution
          </Button>
        }
      />

      {error && (
        <div className="p-4 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <Loader label="Loading Registry..." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {institutions.map((inst) => (
            <Card key={inst.institution_id} className="hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-semibold text-lg text-gray-900 dark:text-white flex items-center gap-2">
                    <Building className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                    {inst.name}
                  </h3>
                  <span className="text-xs text-gray-500 font-mono">Code: {inst.code}</span>
                </div>
                <Badge tone={inst.status === "Active" ? "success" : "default"}>
                  {inst.status}
                </Badge>
              </div>

              <div className="space-y-2 text-sm text-gray-600 dark:text-gray-300 border-t border-gray-100 dark:border-gray-800 pt-3">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gray-400" />
                  <span className="truncate">{inst.admin_email} ({inst.admin_name})</span>
                </div>
                {inst.contact_info && (
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span>{inst.contact_info}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Server className="w-4 h-4 text-gray-400" />
                  <span>Deployment: <strong className="font-mono text-xs">{inst.deployment_id}</strong></span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span className="text-xs">Version: v{inst.application_version}</span>
                </div>
              </div>

              <div className="flex justify-end pt-3 mt-3 border-t border-gray-100 dark:border-gray-800">
                <Button
                  size="sm"
                  variant={inst.status === "Active" ? "danger" : "success"}
                  onClick={() => openStatusModal(inst)}
                  className="flex items-center gap-1.5"
                >
                  <Power className="w-3.5 h-3.5" />
                  {inst.status === "Active" ? "Deactivate" : "Reactivate"}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Deactivate / Reactivate Modal */}
      <Modal
        isOpen={Boolean(statusTarget)}
        onClose={closeStatusModal}
        title={statusTarget ? `${statusTarget.action === "deactivate" ? "Deactivate" : "Reactivate"} ${statusTarget.inst.name}` : ""}
      >
        {statusTarget && (
          <div className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-gray-300">
              {statusTarget.action === "deactivate"
                ? "Everyone at this institution will be signed out and blocked until it is reactivated. No data is deleted."
                : "Users at this institution will be able to sign in again. All existing data is kept."}
            </p>

            {statusError && (
              <div className="p-3 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 text-sm rounded-md">{statusError}</div>
            )}

            {!otpInfo ? (
              <div className="flex justify-end gap-3 pt-3 border-t">
                <Button type="button" variant="secondary" onClick={closeStatusModal}>
                  Cancel
                </Button>
                <Button type="button" onClick={requestStatusOtp} disabled={statusBusy}>
                  {statusBusy ? "Sending..." : "Send verification code"}
                </Button>
              </div>
            ) : (
              <form onSubmit={confirmStatusChange} className="space-y-4">
                <div className="p-3 bg-slate-50 dark:bg-slate-800/60 text-sm rounded-md text-gray-700 dark:text-gray-200">
                  {otpInfo.message}
                  {otpInfo.demo_otp && (
                    <div className="mt-2">
                      Demo code: <strong className="font-mono text-base tracking-widest">{otpInfo.demo_otp}</strong>
                    </div>
                  )}
                </div>
                <Input
                  label="Verification code"
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="6-digit code"
                  inputMode="numeric"
                  required
                />
                <Input
                  label="Reason (optional)"
                  value={statusReason}
                  onChange={(e) => setStatusReason(e.target.value)}
                  placeholder={statusTarget.action === "deactivate" ? "e.g. Subscription ended" : "e.g. Payment received"}
                />
                <div className="flex justify-between gap-3 pt-3 border-t">
                  <Button type="button" variant="ghost" onClick={requestStatusOtp} disabled={statusBusy}>
                    Resend code
                  </Button>
                  <div className="flex gap-3">
                    <Button type="button" variant="secondary" onClick={closeStatusModal}>
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      variant={statusTarget.action === "deactivate" ? "danger" : "success"}
                      disabled={statusBusy || otpCode.length !== 6}
                    >
                      {statusBusy ? "Verifying..." : statusTarget.action === "deactivate" ? "Deactivate" : "Reactivate"}
                    </Button>
                  </div>
                </div>
              </form>
            )}
          </div>
        )}
      </Modal>

      {/* Onboarding Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Onboard New Institution">
        <form onSubmit={handleOnboardSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-md">
              {formError}
            </div>
          )}

          <Input
            label="Institution Name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="e.g. ABC Institute of Technology"
            required
          />
          <Input
            label="Institution Code (Short)"
            value={formData.code}
            onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
            placeholder="e.g. ABC"
            required
          />
          <Input
            label="Institution Admin Name"
            value={formData.admin_name}
            onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
            placeholder="Full Name"
            required
          />
          <Input
            label="Institution Admin Email"
            type="email"
            value={formData.admin_email}
            onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
            placeholder="admin@institution.edu"
            required
          />
          <Input
            label="Contact Information"
            value={formData.contact_info}
            onChange={(e) => setFormData({ ...formData, contact_info: e.target.value })}
            placeholder="Phone number / address"
          />
          <Input
            label="Initial Admin Password"
            type="password"
            value={formData.admin_password}
            onChange={(e) => setFormData({ ...formData, admin_password: e.target.value })}
            required
          />

          <div className="flex justify-end gap-3 pt-3 border-t">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Onboarding..." : "Onboard Institution"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

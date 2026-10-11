import { useState, useEffect } from "react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Modal from "../../components/Modal.jsx";
import Loader from "../../components/Loader.jsx";
import Badge from "../../components/Badge.jsx";
import { Plus, Building, Mail, Phone, Calendar, Server } from "lucide-react";
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
        description="Manage registered institution tenants, platform metadata, and initial administrator onboarding."
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
            </Card>
          ))}
        </div>
      )}

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
            label="Institution Administrator Name"
            value={formData.admin_name}
            onChange={(e) => setFormData({ ...formData, admin_name: e.target.value })}
            placeholder="Full Name"
            required
          />
          <Input
            label="Institution Administrator Email"
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

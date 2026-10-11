import { useState, useEffect } from "react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Select from "../../components/Select.jsx";
import Textarea from "../../components/Textarea.jsx";
import Modal from "../../components/Modal.jsx";
import Loader from "../../components/Loader.jsx";
import Badge from "../../components/Badge.jsx";
import { Plus, HelpCircle, AlertCircle, FileText, CheckCircle2 } from "lucide-react";
import apiClient from "../../api/axios.js";

export default function TechnicalSupportPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    module: "General",
    title: "",
    description: "",
    error_reference: "",
    priority: "Medium",
  });
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/platform/support");
      setTickets(res.data || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load support issues.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    try {
      setSubmitting(true);
      await apiClient.post("/platform/support", formData);
      setModalOpen(false);
      setFormData({
        module: "General",
        title: "",
        description: "",
        error_reference: "",
        priority: "Medium",
      });
      fetchTickets();
    } catch (err) {
      setFormError(err?.response?.data?.detail || "Failed to submit technical support issue.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Technical Support & Platform Escalation"
        description="Report technical issues, error references, or platform queries directly to Campus Pulse Super Admin."
        actions={
          <Button onClick={() => setModalOpen(true)} className="flex items-center gap-2">
            <Plus className="w-4 h-4" /> Report Technical Issue
          </Button>
        }
      />

      {error && (
        <div className="p-4 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <Loader label="Loading Support Tickets..." />
      ) : (
        <Card title="Submitted Technical Support Tickets">
          <div className="space-y-4">
            {tickets.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-6">
                No technical support issues submitted for this institution.
              </p>
            ) : (
              tickets.map((t) => (
                <div
                  key={t.issue_id}
                  className="p-4 border border-gray-100 dark:border-gray-800 rounded-lg space-y-2 bg-gray-50/50 dark:bg-gray-800/30"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs text-gray-500 font-semibold">{t.issue_id}</span>
                        <h4 className="font-semibold text-gray-900 dark:text-white">{t.title}</h4>
                      </div>
                      <span className="text-xs text-gray-500">Module: {t.module} | Submitted: {t.created_at}</span>
                    </div>
                    <Badge tone={t.status === 'Resolved' || t.status === 'Closed' ? 'success' : 'warning'}>
                      {t.status}
                    </Badge>
                  </div>

                  <p className="text-sm text-gray-700 dark:text-gray-300">{t.description}</p>

                  {t.error_reference && (
                    <div className="text-xs font-mono bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300 p-2 rounded">
                      Error Reference: {t.error_reference}
                    </div>
                  )}

                  {t.resolution_notes && (
                    <div className="text-sm bg-green-50 dark:bg-green-950/40 text-green-800 dark:text-green-200 p-3 rounded-md mt-2 space-y-1">
                      <p className="font-semibold text-xs flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Resolution Notes from Super Admin:
                      </p>
                      <p>{t.resolution_notes}</p>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </Card>
      )}

      {/* Create Support Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Report Technical Problem">
        <form onSubmit={handleSubmit} className="space-y-4">
          {formError && (
            <div className="p-3 bg-red-50 text-red-700 text-sm rounded-md">{formError}</div>
          )}

          <Select
            label="Module / Area"
            value={formData.module}
            onChange={(e) => setFormData({ ...formData, module: e.target.value })}
            options={[
              { value: "General", label: "General System" },
              { value: "Complaints", label: "Complaint Workflow" },
              { value: "SLA", label: "SLA & Escalation Engine" },
              { value: "Users", label: "User Management / Auth" },
              { value: "Notifications", label: "Notification Push System" },
              { value: "Database", label: "Database Backup / Restore" },
            ]}
          />

          <Input
            label="Issue Title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Brief summary of technical issue"
            required
          />

          <Textarea
            label="Technical Description"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Provide technical details or symptoms observed..."
            rows={4}
            required
          />

          <Input
            label="Error Reference Identifier (Optional)"
            value={formData.error_reference}
            onChange={(e) => setFormData({ ...formData, error_reference: e.target.value })}
            placeholder="e.g. ERR-123456"
          />

          <Select
            label="Priority"
            value={formData.priority}
            onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
            options={[
              { value: "Low", label: "Low" },
              { value: "Medium", label: "Medium" },
              { value: "High", label: "High" },
              { value: "Critical", label: "Critical" },
            ]}
          />

          <div className="flex justify-end gap-3 pt-3 border-t">
            <Button type="button" variant="secondary" onClick={() => setModalOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Submitting..." : "Submit Technical Issue"}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

import { useState, useEffect } from "react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import Select from "../../components/Select.jsx";
import Textarea from "../../components/Textarea.jsx";
import Modal from "../../components/Modal.jsx";
import Loader from "../../components/Loader.jsx";
import Badge from "../../components/Badge.jsx";
import { AlertCircle, CheckCircle, Clock, FileText } from "lucide-react";
import apiClient from "../../api/axios.js";

export default function PlatformSupportPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Update Modal
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [statusVal, setStatusVal] = useState("Open");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [updating, setUpdating] = useState(false);
  const [modalError, setModalError] = useState(null);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get("/platform/support");
      setTickets(res.data || []);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load support tickets.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, []);

  const openUpdateModal = (ticket) => {
    setSelectedTicket(ticket);
    setStatusVal(ticket.status || "Open");
    setResolutionNotes(ticket.resolution_notes || "");
    setModalError(null);
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    if (!selectedTicket) return;
    try {
      setUpdating(true);
      await apiClient.patch(`/platform/support/${selectedTicket.issue_id}`, {
        status: statusVal,
        resolution_notes: resolutionNotes,
      });
      setSelectedTicket(null);
      fetchTickets();
    } catch (err) {
      setModalError(err?.response?.data?.detail || "Failed to update support ticket.");
    } finally {
      setUpdating(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case "Open":
        return <Badge tone="warning">Open</Badge>;
      case "Investigating":
        return <Badge tone="info">Investigating</Badge>;
      case "Resolved":
        return <Badge tone="success">Resolved</Badge>;
      case "Closed":
        return <Badge tone="default">Closed</Badge>;
      default:
        return <Badge tone="default">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Technical Support Center — Super Admin"
        description="Investigate and resolve platform technical issues reported by Institution Administrators."
      />

      {error && (
        <div className="p-4 bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <Loader label="Loading Support Issues..." />
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                <tr>
                  <th className="p-3">Issue ID</th>
                  <th className="p-3">Institution</th>
                  <th className="p-3">Module</th>
                  <th className="p-3">Title & Error Ref</th>
                  <th className="p-3">Priority</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Created</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                {tickets.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-6 text-center text-gray-500">
                      No technical support tickets reported.
                    </td>
                  </tr>
                ) : (
                  tickets.map((t) => (
                    <tr key={t.issue_id} className="hover:bg-gray-50/50 dark:hover:bg-gray-800/50">
                      <td className="p-3 font-mono font-medium">{t.issue_id}</td>
                      <td className="p-3 font-medium text-gray-900 dark:text-white">{t.institution_id}</td>
                      <td className="p-3">{t.module}</td>
                      <td className="p-3">
                        <div className="font-medium text-gray-900 dark:text-white">{t.title}</div>
                        {t.error_reference && (
                          <span className="text-xs font-mono text-red-600 dark:text-red-400">
                            Ref: {t.error_reference}
                          </span>
                        )}
                      </td>
                      <td className="p-3">
                        <span className={`text-xs font-semibold ${t.priority === 'High' ? 'text-red-600' : 'text-gray-600'}`}>
                          {t.priority}
                        </span>
                      </td>
                      <td className="p-3">{getStatusBadge(t.status)}</td>
                      <td className="p-3 text-xs text-gray-500">{t.created_at}</td>
                      <td className="p-3 text-right">
                        <Button size="sm" variant="secondary" onClick={() => openUpdateModal(t)}>
                          Manage
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Ticket Update Modal */}
      {selectedTicket && (
        <Modal
          isOpen={!!selectedTicket}
          onClose={() => setSelectedTicket(null)}
          title={`Manage Support Issue — ${selectedTicket.issue_id}`}
        >
          <form onSubmit={handleUpdateSubmit} className="space-y-4">
            {modalError && (
              <div className="p-3 bg-red-50 text-red-700 text-sm rounded-md">{modalError}</div>
            )}

            <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md space-y-1 text-sm">
              <p><strong>Title:</strong> {selectedTicket.title}</p>
              <p><strong>Description:</strong> {selectedTicket.description}</p>
              {selectedTicket.error_reference && (
                <p className="text-xs text-red-600 font-mono">
                  <strong>Error Ref:</strong> {selectedTicket.error_reference}
                </p>
              )}
            </div>

            <Select
              label="Support Status"
              value={statusVal}
              onChange={(e) => setStatusVal(e.target.value)}
              options={[
                { value: "Open", label: "Open" },
                { value: "Investigating", label: "Investigating" },
                { value: "Resolved", label: "Resolved" },
                { value: "Closed", label: "Closed" },
              ]}
            />

            <Textarea
              label="Technical Resolution Notes"
              value={resolutionNotes}
              onChange={(e) => setResolutionNotes(e.target.value)}
              placeholder="Enter technical resolution steps or response to Institution Administrator..."
              rows={4}
            />

            <div className="flex justify-end gap-3 pt-3 border-t">
              <Button type="button" variant="secondary" onClick={() => setSelectedTicket(null)}>
                Cancel
              </Button>
              <Button type="submit" disabled={updating}>
                {updating ? "Saving..." : "Update Support Ticket"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

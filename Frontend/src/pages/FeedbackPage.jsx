import { useState, useEffect } from "react";
import {
  Star,
  MessageSquare,
  AlertTriangle,
  CheckCircle2,
  ThumbsUp,
  ThumbsDown,
  Search,
  Plus,
  Filter,
  Send,
  User,
  ShieldAlert,
  BarChart3,
  HelpCircle,
} from "lucide-react";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import StatCard from "../components/StatCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import Loader from "../components/Loader.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Modal from "../components/Modal.jsx";
import Toast from "../components/Toast.jsx";
import Input from "../components/Input.jsx";
import { useAsyncData } from "../hooks/useAsyncData.js";
import { feedbackService } from "../services/feedbackService.js";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../utils/dateFormatter.js";

export default function FeedbackPage() {
  const { user } = useAuth();
  const [typeFilter, setTypeFilter] = useState("");
  const [ratingFilter, setRatingFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [query, setQuery] = useState("");

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // Submission Wizard State
  const [showSubmitModal, setShowSubmitModal] = useState(false);
  const [targetType, setTargetType] = useState("Complaint");
  const [referenceId, setReferenceId] = useState("");
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [comments, setComments] = useState("");
  const [anonymous, setAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Staff Response State
  const [selectedFeedback, setSelectedFeedback] = useState(null);
  const [responseText, setResponseText] = useState("");
  const [responding, setResponding] = useState(false);

  const [analytics, setAnalytics] = useState(null);

  const isStaffAdmin = [
    "administrator",
    "app_manager",
    "location_in_charge",
    "coordinator",
  ].includes(user?.role);

  const {
    data: feedbackList,
    loading,
    reload,
  } = useAsyncData(
    async () =>
      (
        await feedbackService.listFeedback({
          feedback_type: typeFilter,
          rating: ratingFilter || undefined,
          status: statusFilter,
          q: query,
        })
      ).data,
    [typeFilter, ratingFilter, statusFilter, query],
  );

  const { data: pendingServices, reload: reloadPending } = useAsyncData(
    async () => (await feedbackService.getPendingServices()).data,
    [],
  );

  useEffect(() => {
    feedbackService
      .getAnalytics()
      .then((res) => setAnalytics(res.data))
      .catch(() => {});
  }, [feedbackList]);

  const handleSubmitFeedback = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setMessage("");
    setError("");

    try {
      await feedbackService.submit({
        feedback_type: targetType,
        reference_id: referenceId,
        rating: Number(rating),
        title,
        comments,
        anonymous,
      });
      setMessage("Feedback submitted successfully. Thank you for your review!");
      setShowSubmitModal(false);
      setTitle("");
      setComments("");
      setReferenceId("");
      reload();
      reloadPending();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to submit feedback.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddResponse = async (e) => {
    e.preventDefault();
    if (!selectedFeedback) return;
    setResponding(true);
    try {
      await feedbackService.addResponse(selectedFeedback.feedback_id, {
        response: responseText,
      });
      setMessage("Staff response added to feedback.");
      setSelectedFeedback(null);
      setResponseText("");
      reload();
    } catch (err) {
      setError("Failed to add response.");
    } finally {
      setResponding(false);
    }
  };

  const list = feedbackList || [];
  const pending = pendingServices || [];

  return (
    <div className="grid gap-6 max-w-6xl">
      <PageHeader
        title="Feedback & Satisfaction Management"
        description="Rate service resolution quality, review campus staff performance, and respond to low-rating alerts."
        actions={
          <Button
            onClick={() => setShowSubmitModal(true)}
            size="sm"
            className="font-bold flex items-center gap-1.5"
          >
            <Star className="h-4 w-4" />
            Submit Feedback
          </Button>
        }
      />

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Analytics Overview Cards */}
      {analytics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            label="AVERAGE SATISFACTION RATING"
            value={`${analytics.average_rating} / 5.0`}
            accent
          />
          <StatCard
            label="TOTAL FEEDBACK SUBMITTED"
            value={analytics.total_feedback}
          />
          <StatCard
            label="STAFF RESPONSE RATE"
            value={`${analytics.response_rate}%`}
          />
          <StatCard
            label="LOW RATING ALERTS (1-2 STAR)"
            value={analytics.low_ratings_count}
          />
        </div>
      )}

      {/* Pending Feedback Requests Notification Banner */}
      {pending.length > 0 && (
        <Card className="bg-amber-50/70 border-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Star className="h-5 w-5 text-amber-600 shrink-0" />
            <div>
              <div className="font-bold text-amber-900 text-sm">
                You have {pending.length} completed service(s) awaiting
                feedback!
              </div>
              <div className="text-xs text-amber-700">
                Please take 30 seconds to rate your resolution experience.
              </div>
            </div>
          </div>
          <Button
            size="sm"
            onClick={() => {
              const p = pending[0];
              setTargetType(p.feedback_type);
              setReferenceId(p.reference_id);
              setShowSubmitModal(true);
            }}
            className="font-bold bg-amber-600 hover:bg-amber-700 text-xs shrink-0"
          >
            Rate #{pending[0].reference_id}
          </Button>
        </Card>
      )}

      {/* Filter Toolbar */}
      <Card className="flex flex-wrap items-center justify-between gap-4 bg-slate-50/50">
        <div className="flex items-center gap-2 flex-1 min-w-[240px]">
          <Search className="h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by title, comments, or reference ID..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-semibold focus:outline-none"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none"
          >
            <option value="">All Types</option>
            <option value="Complaint">Complaint</option>
            <option value="WorkOrder">Work Order</option>
            <option value="Booking">Booking</option>
            <option value="Visitor">Visitor</option>
          </select>

          <select
            value={ratingFilter}
            onChange={(e) => setRatingFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none"
          >
            <option value="">All Ratings</option>
            <option value="5">5 Stars (Excellent)</option>
            <option value="4">4 Stars (Good)</option>
            <option value="3">3 Stars (Average)</option>
            <option value="2">2 Stars (Poor)</option>
            <option value="1">1 Star (Critical)</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-800 dark:text-slate-100 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="Pending Review">Pending Review</option>
            <option value="Responded">Responded</option>
          </select>
        </div>
      </Card>

      {/* Feedback Feed */}
      {loading ? (
        <Loader label="Loading feedback reviews..." variant="skeleton" />
      ) : list.length === 0 ? (
        <EmptyState
          title="No feedback entries found"
          description="Submitted service ratings will display here."
        />
      ) : (
        <div className="grid gap-3">
          {list.map((fb) => {
            const isLowRating = fb.rating <= 2;

            return (
              <Card
                key={fb.feedback_id}
                className={`flex flex-col gap-3 border-l-4 ${
                  isLowRating
                    ? "border-l-rose-600 bg-rose-50/20"
                    : "border-l-amber-500"
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2">
                  <div className="flex items-center gap-2">
                    <div className="flex items-center text-amber-500">
                      {[...Array(5)].map((_, i) => (
                        <Star
                          key={i}
                          className={`h-4 w-4 ${i < fb.rating ? "fill-amber-400 text-amber-400" : "text-slate-200"}`}
                        />
                      ))}
                    </div>
                    <span className="font-bold text-slate-900 text-sm">
                      {fb.title || `${fb.feedback_type} Feedback`}
                    </span>
                    <span className="text-xs font-mono text-slate-500">
                      ({fb.feedback_type} #{fb.reference_id})
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        fb.status === "Responded"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-slate-100 text-slate-700"
                      }`}
                    >
                      {fb.status}
                    </span>
                    <span className="text-[11px] font-semibold text-slate-400">
                      {formatDate(fb.submitted_at)}
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-700 font-medium">
                  {fb.comments || "No written comments provided."}
                </p>

                <div className="flex items-center justify-between gap-2 pt-1 text-[11px] font-semibold text-slate-400">
                  <span>
                    Submitted by:{" "}
                    {fb.anonymous === 1 ? "Anonymous User" : fb.submitted_by}
                  </span>
                  {isStaffAdmin && (
                    <Button
                      variant="subtle"
                      size="sm"
                      onClick={() => setSelectedFeedback(fb)}
                      className="font-bold text-xs"
                    >
                      {fb.responses && fb.responses.length > 0
                        ? "View Staff Responses"
                        : "Respond to Feedback"}
                    </Button>
                  )}
                </div>

                {/* Render Staff Responses */}
                {fb.responses && fb.responses.length > 0 && (
                  <div className="mt-2 p-2.5 bg-slate-50 border border-slate-200 rounded-lg text-xs grid gap-1">
                    <div className="font-bold text-slate-900 flex items-center gap-1">
                      <MessageSquare className="h-3.5 w-3.5 text-primary" />{" "}
                      Staff Response ({fb.responses[0].responded_by}):
                    </div>
                    <div className="text-slate-700">
                      {fb.responses[0].response}
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Staff Response Modal */}
      {selectedFeedback && (
        <Modal
          title={`Respond to Feedback: #${selectedFeedback.reference_id}`}
          isOpen={!!selectedFeedback}
          onClose={() => setSelectedFeedback(null)}
        >
          <form
            onSubmit={handleAddResponse}
            className="grid gap-4 text-xs font-sans"
          >
            <div className="p-3 bg-slate-50 rounded-xl text-slate-700">
              <div className="font-bold text-slate-900 mb-1">
                Rating: {selectedFeedback.rating} / 5 Stars
              </div>
              <div>"{selectedFeedback.comments}"</div>
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Staff Resolution / Explanation
              </label>
              <textarea
                rows={3}
                placeholder="Type official staff response to user..."
                value={responseText}
                onChange={(e) => setResponseText(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg font-semibold focus:outline-none"
                required
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button
                variant="secondary"
                type="button"
                onClick={() => setSelectedFeedback(null)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={responding} className="font-bold">
                {responding ? "Submitting..." : "Submit Response"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Submit Feedback Modal */}
      {showSubmitModal && (
        <Modal
          title="Submit Service Feedback"
          isOpen={showSubmitModal}
          onClose={() => setShowSubmitModal(false)}
        >
          <form onSubmit={handleSubmitFeedback} className="grid gap-4 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  Service Type
                </label>
                <select
                  value={targetType}
                  onChange={(e) => setTargetType(e.target.value)}
                  className="w-full px-3 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-semibold text-slate-800 dark:text-slate-100"
                >
                  <option value="Complaint">Complaint Resolution</option>
                  <option value="WorkOrder">Work Order Repair</option>
                  <option value="Booking">Facility Booking</option>
                  <option value="Visitor">Visitor Gate Pass</option>
                </select>
              </div>

              <Input
                label="Target Reference ID"
                placeholder="e.g. CP-1001"
                value={referenceId}
                onChange={(e) => setReferenceId(e.target.value)}
                required
              />
            </div>

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
                Overall Satisfaction Rating
              </label>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    type="button"
                    key={star}
                    onClick={() => setRating(star)}
                    className="p-1 text-amber-400 hover:scale-110 transition-transform"
                  >
                    <Star
                      className={`h-7 w-7 ${star <= rating ? "fill-amber-400 text-amber-400" : "text-slate-300"}`}
                    />
                  </button>
                ))}
                <span className="font-bold text-slate-700 text-sm ml-2">
                  {rating} / 5 Stars
                </span>
              </div>
            </div>

            <Input
              label="Title / Headline"
              placeholder="e.g. Fast & Courteous Service"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Comments & Suggestions
              </label>
              <textarea
                rows={3}
                placeholder="Share specific feedback regarding staff behavior or resolution quality..."
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg font-semibold focus:outline-none"
              />
            </div>

            <label className="flex items-center gap-2 cursor-pointer pt-1">
              <input
                type="checkbox"
                checked={anonymous}
                onChange={(e) => setAnonymous(e.target.checked)}
                className="h-4 w-4 text-primary rounded"
              />
              <span className="font-bold text-slate-700">
                Submit Anonymously
              </span>
            </label>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button
                variant="secondary"
                type="button"
                onClick={() => setShowSubmitModal(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="font-bold">
                {submitting ? "Submitting..." : "Submit Review"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

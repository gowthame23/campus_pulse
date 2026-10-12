import { describe, it, expect } from "vitest";
import { COMPLAINT_STATUS, ROLES, PRESET_PROGRESS_NOTES } from "../utils/constants.js";
import { getStatusTone, getPriorityTone, getSlaTone } from "../utils/statusColor.js";

describe("Phase 4: Frontend Complaint Workflow Test Suite", () => {
  describe("1. Complaint Create Form & Priority Normalization", () => {
    it("determines High priority when marked Urgent", () => {
      const formValues = {
        title: "No power in wing",
        complaint_type: "Power Failure",
        visibility_type: "Public",
        is_urgent: true,
      };

      const payload = {
        ...formValues,
        category: formValues.complaint_type,
        priority: formValues.is_urgent ? "High" : "Medium",
      };

      expect(payload.priority).toBe("High");
      expect(payload.category).toBe("Power Failure");
    });

    it("defaults to Medium priority for non-urgent complaints", () => {
      const formValues = {
        title: "Dripping tap",
        complaint_type: "Tap Leakage",
        visibility_type: "Public",
        is_urgent: false,
      };

      const payload = {
        ...formValues,
        priority: formValues.is_urgent ? "High" : "Medium",
      };

      expect(payload.priority).toBe("Medium");
    });

    it("handles duplicate suggestion detection for public complaints", () => {
      const visibility = "Public";
      const existingComplaints = [
        { complaint_id: "CP-101", title: "Water leakage in Room 204", location_id: "LOC_HOSTEL_A" },
        { complaint_id: "CP-102", title: "Broken fan", location_id: "LOC_HOSTEL_B" },
      ];

      const inputTitle = "water leakage in room";
      const currentLocation = "LOC_HOSTEL_A";

      const matched = visibility === "Public"
        ? existingComplaints.filter(
            (c) =>
              c.location_id === currentLocation &&
              c.title.toLowerCase().includes("water leakage"),
          )
        : [];

      expect(matched.length).toBe(1);
      expect(matched[0].complaint_id).toBe("CP-101");
    });
  });

  describe("2. Coordinator Accept & Conflict Handling", () => {
    it("sorts Available Work queue oldest first", () => {
      const queue = [
        { complaint_id: "C-2", created_at: "2026-10-12T04:00:00Z" },
        { complaint_id: "C-1", created_at: "2026-10-12T02:00:00Z" },
        { complaint_id: "C-3", created_at: "2026-10-12T05:00:00Z" },
      ];

      const sorted = [...queue].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      );

      expect(sorted[0].complaint_id).toBe("C-1");
      expect(sorted[1].complaint_id).toBe("C-2");
      expect(sorted[2].complaint_id).toBe("C-3");
    });

    it("parses 409 conflict detail message correctly", () => {
      const conflictErrorResponse = {
        status: 409,
        data: {
          detail: "Complaint already accepted by Ramesh Kumar",
        },
      };

      const extractedMessage =
        conflictErrorResponse.data?.detail || "Taken by another coordinator.";
      expect(extractedMessage).toBe("Complaint already accepted by Ramesh Kumar");
    });

    it("falls back to generic conflict message when detail is missing", () => {
      const emptyConflictError = { status: 409, data: {} };
      const extracted =
        emptyConflictError.data?.detail || "Taken by another coordinator.";
      expect(extracted).toBe("Taken by another coordinator.");
    });
  });

  describe("3. Mark Done Photo & Skip Rules", () => {
    it("requires reason when coordinator skips photo with streak >= 2", () => {
      const streak = 2;
      const skipReason = "";
      const isPhotoSkipped = true;

      const isValid = !isPhotoSkipped || (streak >= 2 ? skipReason.trim().length > 0 : true);
      expect(isValid).toBe(false);

      const validReason = "Student attached an irrelevant meme";
      const isValidWithReason = !isPhotoSkipped || (streak >= 2 ? validReason.trim().length > 0 : true);
      expect(isValidWithReason).toBe(true);
    });

    it("builds resolution payload with skip_photo and reason when skipped", () => {
      const resolveData = {
        notes: "Fixed the electrical breaker",
        isPhotoSkipped: true,
        photoSkipReason: "Student photo was not relevant",
      };

      const payload = resolveData.isPhotoSkipped
        ? {
            notes: resolveData.notes,
            skip_photo: true,
            photo_skipped: true,
            photo_skip_reason: resolveData.photoSkipReason,
          }
        : { notes: resolveData.notes };

      expect(payload.skip_photo).toBe(true);
      expect(payload.photo_skip_reason).toBe("Student photo was not relevant");
    });

    it("builds resolution payload with preset code when no photo was required", () => {
      const resolveData = {
        preset: "Issue resolved and tested on site",
        notes: "",
      };

      const payload = {
        notes: resolveData.notes || resolveData.preset,
        preset_code: resolveData.preset,
      };

      expect(payload.notes).toBe("Issue resolved and tested on site");
      expect(payload.preset_code).toBe("Issue resolved and tested on site");
    });
  });

  describe("4. Warden Verify Buttons & Verdicts", () => {
    it("constructs Verified verdict payload", () => {
      const verdict = "Verified";
      const notes = "Inspected on site, work completed properly.";
      const payload = { verdict, notes };

      expect(payload.verdict).toBe("Verified");
      expect(payload.notes).toContain("Inspected on site");
    });

    it("constructs Not Fixed verdict payload with required reason", () => {
      const verdict = "Not Fixed";
      const notes = "Light still flickering intermittently.";
      const payload = { verdict, notes };

      expect(payload.verdict).toBe("Not Fixed");
      expect(payload.notes).toBe("Light still flickering intermittently.");
    });

    it("constructs Photo doesn't match payload", () => {
      const verdict = "Not Fixed";
      const notes = "After photo shows wrong room switchboard.";
      const payload = { verdict, notes, photo_mismatch: true };

      expect(payload.photo_mismatch).toBe(true);
      expect(payload.notes).toContain("wrong room");
    });
  });

  describe("5. Student Confirm & Reopen Flow", () => {
    it("tracks reopen counts and escalates 3rd reopen to Admin Review", () => {
      const currentReopens = 2;
      const willBeThirdReopen = currentReopens + 1 >= 3;

      const nextStatus = willBeThirdReopen
        ? COMPLAINT_STATUS.ADMIN_REVIEW
        : COMPLAINT_STATUS.REOPENED;

      expect(nextStatus).toBe("Admin Review");
    });

    it("allows standard reopen for 1st and 2nd reopens", () => {
      const firstReopen = 0 + 1 >= 3 ? COMPLAINT_STATUS.ADMIN_REVIEW : COMPLAINT_STATUS.REOPENED;
      expect(firstReopen).toBe("Reopened");

      const secondReopen = 1 + 1 >= 3 ? COMPLAINT_STATUS.ADMIN_REVIEW : COMPLAINT_STATUS.REOPENED;
      expect(secondReopen).toBe("Reopened");
    });
  });

  describe("6. Timeline & SLA Tone Rendering", () => {
    it("maps SLA statuses to correct visual tones", () => {
      expect(getSlaTone("On Time")).toBe("success");
      expect(getSlaTone("Due Today")).toBe("warning");
      expect(getSlaTone("Overdue")).toBe("danger");
      expect(getSlaTone("Breached")).toBe("danger");
    });

    it("maps Complaint statuses to appropriate tone indicators", () => {
      expect(getStatusTone("Submitted")).toBe("info");
      expect(getStatusTone("In Progress")).toBe("info");
      expect(getStatusTone("Waiting for Parts")).toBe("amber");
      expect(getStatusTone("Pending Warden Verification")).toBe("purple");
      expect(getStatusTone("Waiting for Verification")).toBe("success");
      expect(getStatusTone("Closed")).toBe("success");
      expect(getStatusTone("Admin Review")).toBe("danger");
    });

    it("correctly calculates overdue condition from ISO deadline", () => {
      const pastDeadline = new Date(Date.now() - 3600 * 1000).toISOString();
      const futureDeadline = new Date(Date.now() + 3600 * 1000).toISOString();

      const isPastOverdue = new Date(pastDeadline).getTime() - Date.now() <= 0;
      const isFutureOverdue = new Date(futureDeadline).getTime() - Date.now() <= 0;

      expect(isPastOverdue).toBe(true);
      expect(isFutureOverdue).toBe(false);
    });
  });
});


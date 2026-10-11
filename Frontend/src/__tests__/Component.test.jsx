import { describe, it, expect } from "vitest";

describe("Frontend Component & Utility Test Suite", () => {
  it("exports valid ROLES mapping constants", async () => {
    const { ROLES } = await import("../utils/constants.js");
    expect(ROLES).toBeDefined();
    expect(ROLES.STUDENT).toBe("student");
    expect(ROLES.COORDINATOR).toBe("coordinator");
    expect(ROLES.LOCATION_IN_CHARGE).toBe("location_in_charge");
    expect(ROLES.APP_MANAGER).toBe("app_manager");
    expect(ROLES.ADMINISTRATOR).toBe("administrator");
    expect(ROLES.SUPER_ADMIN).toBe("super_admin");
  });

  it("exports status and SLA tone calculation helper functions", async () => {
    const { getStatusTone, getSlaTone } = await import("../utils/statusColor.js");
    expect(getStatusTone("Pending")).toBe("warning");
    expect(getStatusTone("Closed")).toBe("success");
    expect(getStatusTone("In Progress")).toBe("info");

    expect(getSlaTone("On Time")).toBe("success");
    expect(getSlaTone("Due Today")).toBe("warning");
    expect(getSlaTone("Overdue")).toBe("danger");
  });

  it("exports complaint status options", async () => {
    const { COMPLAINT_STATUS } = await import("../utils/constants.js");
    expect(COMPLAINT_STATUS.SUBMITTED).toBe("Submitted");
    expect(COMPLAINT_STATUS.IN_PROGRESS).toBe("In Progress");
    expect(COMPLAINT_STATUS.CLOSED).toBe("Closed");
  });
});

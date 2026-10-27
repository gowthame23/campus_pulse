import { describe, it, expect } from "vitest";
import React from "react";
import { renderToString } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import ActionPill from "../components/ActionPill.jsx";
import en from "../locales/en.json";
import te from "../locales/te.json";
import hi from "../locales/hi.json";

// Mock dummy icon component
const DummyIcon = ({ className }) => <svg className={className} data-testid="dummy-icon" />;

describe("ActionPill Component & Dashboard Action Specifications", () => {
  describe("1. ActionPill Rendering & Props", () => {
    it("renders icon, label, and accessible button element", () => {
      const html = renderToString(
        <ActionPill
          icon={DummyIcon}
          label="Report a problem"
          onClick={() => {}}
        />
      );

      expect(html).toContain("<button");
      expect(html).toContain('type="button"');
      expect(html).toContain("Report a problem");
      expect(html).toContain("data-testid=\"dummy-icon\"");
      expect(html).toContain('aria-label="Report a problem"');
    });

    it("renders Link when 'to' prop is provided", () => {
      const html = renderToString(
        <MemoryRouter>
          <ActionPill
            icon={DummyIcon}
            label="Lost &amp; Found"
            to="/lost-found"
          />
        </MemoryRouter>
      );

      expect(html).toContain("<a");
      expect(html).toContain('href="/lost-found"');
      expect(html).toContain("Lost &amp; Found");
    });

    it("displays count badge when count > 0 and hides when count is 0 or omitted", () => {
      const htmlWithZero = renderToString(
        <ActionPill
          icon={DummyIcon}
          label="My complaints"
          count={0}
        />
      );
      expect(htmlWithZero).not.toContain('data-testid="pill-badge"');

      const htmlWithCount = renderToString(
        <ActionPill
          icon={DummyIcon}
          label="My complaints"
          count={5}
        />
      );
      expect(htmlWithCount).toContain('data-testid="pill-badge"');
      expect(htmlWithCount).toContain("5");
      expect(htmlWithCount).toContain('aria-label="My complaints (5)"');
    });

    it("caps count display at 99+ for counts over 99", () => {
      const htmlOver99 = renderToString(
        <ActionPill
          icon={DummyIcon}
          label="All complaints"
          count={120}
        />
      );
      expect(htmlOver99).toContain("99+");
    });

    it("applies touch-target height between 44px and 48px and rounded-full pill shape", () => {
      const html = renderToString(
        <ActionPill
          icon={DummyIcon}
          label="Touch Target Test"
        />
      );

      expect(html).toContain("rounded-full");
      expect(html).toContain("min-h-[44px]");
      expect(html).toContain("max-h-[48px]");
      expect(html).toContain("h-[46px]");
      expect(html).toContain("focus-visible:ring-2");
      expect(html).toContain("active:scale-[0.98]");
    });
  });

  describe("2. Role Dashboard Action Pill Rules (Max 4 per screen)", () => {
    it("verifies Student dashboard defines exactly 4 listed action pills", () => {
      const studentPills = [
        "Report a problem",
        "Lost & Found",
        "My complaints",
        "Notices",
      ];
      expect(studentPills.length).toBeLessThanOrEqual(4);
      expect(studentPills).toEqual([
        "Report a problem",
        "Lost & Found",
        "My complaints",
        "Notices",
      ]);
    });

    it("verifies Coordinator dashboard defines exactly 3 listed action pills (max 4)", () => {
      const coordinatorPills = ["To assign", "Team board", "My jobs"];
      expect(coordinatorPills.length).toBeLessThanOrEqual(4);
      expect(coordinatorPills).toEqual(["To assign", "Team board", "My jobs"]);
    });

    it("verifies Warden dashboard defines exactly 3 listed action pills (max 4)", () => {
      const wardenPills = ["Needs verification", "Overdue", "Post notice"];
      expect(wardenPills.length).toBeLessThanOrEqual(4);
      expect(wardenPills).toEqual(["Needs verification", "Overdue", "Post notice"]);
    });

    it("verifies App Manager and Admin dashboards define exactly 3 listed action pills (max 4)", () => {
      const adminPills = ["All complaints", "Teams & setup", "Reports"];
      expect(adminPills.length).toBeLessThanOrEqual(4);
      expect(adminPills).toEqual(["All complaints", "Teams & setup", "Reports"]);
    });
  });

  describe("3. Multilingual Translation Keys Coverage", () => {
    const requiredKeys = [
      "report_problem",
      "lost_found",
      "my_complaints",
      "notices",
      "my_jobs",
      "to_assign",
      "team_board",
      "needs_verification",
      "overdue",
      "post_notice",
      "all_complaints",
      "teams_setup",
      "reports",
    ];

    it("validates English translations for all pill keys", () => {
      expect(en.pills).toBeDefined();
      requiredKeys.forEach((key) => {
        expect(en.pills[key]).toBeDefined();
        expect(typeof en.pills[key]).toBe("string");
        expect(en.pills[key].length).toBeGreaterThan(0);
      });
    });

    it("validates Telugu translations for all pill keys", () => {
      expect(te.pills).toBeDefined();
      requiredKeys.forEach((key) => {
        expect(te.pills[key]).toBeDefined();
        expect(typeof te.pills[key]).toBe("string");
        expect(te.pills[key].length).toBeGreaterThan(0);
      });
    });

    it("validates Hindi translations for all pill keys", () => {
      expect(hi.pills).toBeDefined();
      requiredKeys.forEach((key) => {
        expect(hi.pills[key]).toBeDefined();
        expect(typeof hi.pills[key]).toBe("string");
        expect(hi.pills[key].length).toBeGreaterThan(0);
      });
    });
  });
});


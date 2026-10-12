import { useMemo, useState, useEffect } from "react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Home,
  FileText,
  User,
  BarChart3,
  Bell,
  Users,
  Settings,
  MapPin,
  X,
  Package,
  Megaphone,
  Shield,
  ShieldAlert,
  Layers,
  Activity,
  Building,
  HelpCircle,
  Sun,
  Moon,
  Tag,
  Sliders,
  PieChart,
  ChevronDown,
  ChevronRight,
  CheckCircle2,
  UserCheck,
  MessageSquare,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import { ROLES, getRoleDisplayName } from "../utils/constants.js";

export default function Sidebar({ isOpen, onClose }) {
  const { user } = useAuth();
  const { toggleTheme, isDark } = useTheme();
  const location = useLocation();

  const [openSections, setOpenSections] = useState({});

  const roleTitle = useMemo(() => {
    if (!user) return "";
    return getRoleDisplayName(user.role);
  }, [user]);

  const navSections = useMemo(() => {
    const role = (user?.role || "").toLowerCase();

    // 1. SUPER ADMIN (Platform Level)
    if (role === ROLES.SUPER_ADMIN) {
      return [
        {
          title: "PLATFORM",
          items: [
            { to: "/superadmin", label: "Dashboard", icon: Home },
            { to: "/superadmin/institutions", label: "Institutions", icon: Building },
            { to: "/superadmin/support", label: "Support Requests", icon: HelpCircle },
            { to: "/superadmin/health", label: "Platform Health", icon: Activity },
          ],
        },
        {
          title: "ACCOUNT",
          items: [{ to: "/profile", label: "Profile", icon: User }],
        },
      ];
    }

    // 2. ADMINISTRATOR (College Level)
    if (role === ROLES.ADMINISTRATOR) {
      return [
        {
          title: "MAIN",
          items: [
            { to: "/admin", label: "Home", icon: Home },
            { to: "/complaints", label: "Complaints", icon: FileText },
            { to: "/workload", label: "Workload", icon: UserCheck },
            { to: "/resolved", label: "Resolved Views", icon: CheckCircle2 },
            { to: "/lost-found", label: "Lost & Found", icon: Package },
            { to: "/announcements", label: "Announcements", icon: Megaphone },
            { to: "/chat", label: "Chat", icon: MessageSquare },
            { to: "/notifications", label: "Notifications", icon: Bell },
          ],
        },
        {
          title: "MANAGEMENT",
          items: [
            { to: "/admin/users", label: "Users", icon: Users },
            { to: "/admin/teams", label: "Teams", icon: Layers },
            { to: "/admin/locations", label: "Locations", icon: MapPin },
            { to: "/admin/departments", label: "Departments", icon: Building },
            { to: "/admin/coverage-gaps", label: "Coverage Gaps", icon: Activity },
            { to: "/admin/issues", label: "Issues Taxonomy", icon: Tag },
          ],
        },
        {
          title: "INSIGHTS",
          items: [
            { to: "/health-map", label: "Campus Health Map", icon: Activity },
            { to: "/reports", label: "Reports", icon: PieChart },
            { to: "/analytics", label: "Analytics", icon: BarChart3 },
          ],
        },
        {
          title: "SYSTEM",
          items: [
            { to: "/admin/safety-reports", label: "Safety Reports", icon: ShieldAlert },
            { to: "/admin/audit", label: "Audit Log", icon: Shield },
            { to: "/backups", label: "Backups", icon: Activity },
            { to: "/system/settings", label: "Settings", icon: Settings },
            { to: "/admin/support", label: "Technical Support", icon: HelpCircle },
          ],
        },
        {
          title: "ACCOUNT",
          items: [{ to: "/profile", label: "Profile", icon: User }],
        },
      ];
    }

    // 3. APP MANAGER
    if (role === ROLES.APP_MANAGER) {
      return [
        {
          title: "MAIN",
          items: [
            { to: "/manager", label: "Home", icon: Home },
            { to: "/complaints", label: "Complaints", icon: FileText },
            { to: "/workload", label: "Workload", icon: UserCheck },
            { to: "/resolved", label: "Resolved Views", icon: CheckCircle2 },
            { to: "/lost-found", label: "Lost & Found", icon: Package },
            { to: "/announcements", label: "Announcements", icon: Megaphone },
            { to: "/chat", label: "Chat", icon: MessageSquare },
            { to: "/notifications", label: "Notifications", icon: Bell },
          ],
        },
        {
          title: "MANAGEMENT",
          items: [
            { to: "/admin/users", label: "Users", icon: Users },
            { to: "/admin/teams", label: "Teams", icon: Layers },
            { to: "/admin/locations", label: "Locations", icon: MapPin },
            { to: "/admin/departments", label: "Departments", icon: Building },
            { to: "/admin/coverage-gaps", label: "Coverage Gaps", icon: Activity },
          ],
        },
        {
          title: "INSIGHTS",
          items: [
            { to: "/health-map", label: "Campus Health Map", icon: Activity },
            { to: "/reports", label: "Reports", icon: PieChart },
            { to: "/analytics", label: "Analytics", icon: BarChart3 },
          ],
        },
        {
          title: "SYSTEM",
          items: [
            { to: "/admin/audit", label: "Audit Log", icon: Shield },
            { to: "/backups", label: "Backups", icon: Activity },
          ],
        },
        {
          title: "ACCOUNT",
          items: [{ to: "/profile", label: "Profile", icon: User }],
        },
      ];
    }

    // 4. WARDEN / LOCATION IN-CHARGE
    if (role === ROLES.LOCATION_IN_CHARGE) {
      return [
        {
          title: "MAIN",
          items: [
            { to: "/location", label: "Home", icon: Home },
            { to: "/complaints", label: "Complaints", icon: FileText },
            { to: "/workload", label: "Workload", icon: UserCheck },
            { to: "/resolved", label: "Resolved Views", icon: CheckCircle2 },
            { to: "/lost-found", label: "Lost & Found", icon: Package },
            { to: "/announcements", label: "Announcements", icon: Megaphone },
            { to: "/chat", label: "Chat", icon: MessageSquare },
            { to: "/notifications", label: "Notifications", icon: Bell },
          ],
        },
        {
          title: "INSIGHTS",
          items: [
            { to: "/health-map", label: "Campus Health Map", icon: Activity },
            { to: "/reports", label: "Reports", icon: PieChart },
          ],
        },
        {
          title: "ACCOUNT",
          items: [{ to: "/profile", label: "Profile", icon: User }],
        },
      ];
    }

    // 5. COORDINATOR
    if (role === ROLES.COORDINATOR) {
      return [
        {
          title: "MAIN",
          items: [
            { to: "/coordinator", label: "Home", icon: Home },
            { to: "/complaints", label: "Complaints", icon: FileText },
            { to: "/workload", label: "Workload", icon: UserCheck },
            { to: "/resolved", label: "Resolved Views", icon: CheckCircle2 },
            { to: "/lost-found", label: "Lost & Found", icon: Package },
            { to: "/announcements", label: "Announcements", icon: Megaphone },
            { to: "/chat", label: "Chat", icon: MessageSquare },
            { to: "/notifications", label: "Notifications", icon: Bell },
          ],
        },
        {
          title: "ACCOUNT",
          items: [{ to: "/profile", label: "Profile", icon: User }],
        },
      ];
    }

    // 6. EMPLOYEE (Worker)
    if (role === ROLES.EMPLOYEE) {
      return [
        {
          title: "WORK",
          items: [
            { to: "/employee", label: "My Jobs", icon: Home },
            { to: "/notifications", label: "Notifications", icon: Bell },
          ],
        },
        {
          title: "ACCOUNT",
          items: [{ to: "/profile", label: "Profile", icon: User }],
        },
      ];
    }

    // 7. STUDENT (Default)
    return [
      {
        title: "MAIN",
        items: [
          { to: "/student", label: "Home", icon: Home },
          { to: "/complaints", label: "Complaints", icon: FileText },
          { to: "/safety", label: "Report Safely", icon: ShieldAlert },
          { to: "/resolved", label: "Resolved Views", icon: CheckCircle2 },
          { to: "/lost-found", label: "Lost & Found", icon: Package },
          { to: "/announcements", label: "Announcements", icon: Megaphone },
          { to: "/notifications", label: "Notifications", icon: Bell },
        ],
      },
      {
        title: "ACCOUNT",
        items: [{ to: "/profile", label: "Profile", icon: User }],
      },
    ];
  }, [user]);

  // Auto-expand section containing active path
  useEffect(() => {
    const activePath = location.pathname;
    setOpenSections((prev) => {
      const nextState = { ...prev, MAIN: true, PLATFORM: true };
      navSections.forEach((section) => {
        const title = section.title;
        if (title) {
          const hasActive = section.items.some((item) => item.to === activePath);
          if (hasActive) {
            nextState[title] = true;
          }
        }
      });
      return nextState;
    });
  }, [location.pathname, navSections]);

  const toggleSection = (title) => {
    setOpenSections((prev) => ({
      ...prev,
      [title]: !prev[title],
    }));
  };

  const renderNavLinks = () => (
    <nav className="flex flex-col gap-2.5 overflow-y-auto flex-1 pr-1 custom-scrollbar">
      {navSections.map((section, idx) => {
        const title = section.title || `SECTION_${idx}`;
        const isAlwaysOpen = title === "MAIN" || title === "PLATFORM";
        const isOpen = isAlwaysOpen || !!openSections[title];
        const hasActiveChild = section.items.some(
          (item) => item.to === location.pathname
        );

        return (
          <div key={title} className="flex flex-col gap-0.5">
            {section.title && (
              isAlwaysOpen ? (
                <div className="px-3 pt-2 pb-1 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  {section.title}
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => toggleSection(title)}
                  className={`flex w-full items-center justify-between px-3 py-1.5 rounded-xl text-[10px] font-semibold tracking-wider uppercase transition-colors ${
                    hasActiveChild
                      ? "text-primary dark:text-primary bg-primary/5 dark:bg-primary/10 font-semibold"
                      : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-100/70 dark:hover:bg-slate-800/60 font-medium"
                  }`}
                >
                  <span>{section.title}</span>
                  {isOpen ? (
                    <ChevronDown className="h-3 w-3 shrink-0 text-slate-400 dark:text-slate-500" />
                  ) : (
                    <ChevronRight className="h-3 w-3 shrink-0 text-slate-400 dark:text-slate-500" />
                  )}
                </button>
              )
            )}

            {isOpen && (
              <div
                className={`flex flex-col gap-0.5 transition-all ${
                  !isAlwaysOpen ? "pl-2 border-l border-slate-200/80 dark:border-slate-800 ml-3.5 my-0.5" : ""
                }`}
              >
                {section.items.map((link) => (
                  <NavLink
                    key={link.to}
                    to={link.to}
                    onClick={onClose}
                    className={({ isActive }) =>
                      `group flex h-9 items-center gap-3 rounded-xl px-3 text-xs transition-all ${
                        isActive
                          ? "bg-primary/10 text-primary font-semibold dark:bg-primary/15 dark:text-primary shadow-2xs"
                          : "text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100 font-medium"
                      }`
                    }
                  >
                    <link.icon className="h-4 w-4 shrink-0 transition-transform group-hover:scale-105" />
                    <span className="truncate">{link.label}</span>
                  </NavLink>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </nav>
  );

  const brandHeader = (
    <div className="flex flex-col gap-3 pb-4 border-b border-slate-100 dark:border-slate-800/80">
      <div className="flex items-center gap-2.5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-white font-bold text-sm shadow-2xs">
          CP
        </div>
        <div className="min-w-0">
          <div className="text-sm font-bold tracking-tight text-slate-900 dark:text-slate-100 truncate">
            Campus Pulse
          </div>
          <div className="text-[11px] font-normal text-slate-400 dark:text-slate-500 truncate">
            Campus Operations
          </div>
        </div>
      </div>
      {/* Role Pill */}
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-800 text-[11px] font-medium text-slate-600 dark:text-slate-300">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
        <span className="truncate">{roleTitle || "User"}</span>
      </div>
    </div>
  );

  const themeToggleRow = (
    <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 mt-auto flex flex-col gap-2">
      <button
        onClick={toggleTheme}
        className="flex w-full h-9 items-center justify-between rounded-xl px-2.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100/70 dark:hover:bg-slate-800/60 transition-colors cursor-pointer"
      >
        <span className="flex items-center gap-2">
          {isDark ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-500" />
          )}
          <span>{isDark ? "Light Theme" : "Dark Theme"}</span>
        </span>
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
          {isDark ? "Dark" : "Light"}
        </span>
      </button>
    </div>
  );

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-xs lg:hidden"
          onClick={onClose}
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[250px] flex-col border-r border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726] p-4 transition-transform lg:hidden ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="mb-4 flex items-start justify-between">
          <div className="flex-1">{brandHeader}</div>
          <button
            onClick={onClose}
            className="rounded-xl p-1.5 text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800 lg:hidden ml-2"
            aria-label="Close menu"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        {renderNavLinks()}
        {themeToggleRow}
      </aside>
      <aside className="hidden shrink-0 border-r border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726] p-4 lg:flex lg:w-[250px] lg:flex-col">
        <div className="mb-4">{brandHeader}</div>
        {renderNavLinks()}
        {themeToggleRow}
      </aside>
    </>
  );
}

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
  PhoneCall,
  LogOut,
  GraduationCap,
  ShieldCheck,
  Wrench,
} from "lucide-react";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import { ROLES, getRoleDisplayName } from "../utils/constants.js";

export default function Sidebar({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const { toggleTheme, isDark } = useTheme();
  const { language, t } = useLanguage();
  const location = useLocation();
  const [confirmLogout, setConfirmLogout] = useState(false);

  const [openSections, setOpenSections] = useState({});
  const [openSubMenus, setOpenSubMenus] = useState({ "User Management": true });

  const toggleSubMenu = (label) => {
    setOpenSubMenus((prev) => ({
      ...prev,
      [label]: !prev[label],
    }));
  };

  const getNavLabel = (label) => {
    const labelKeyMap = {
      "Dashboard": "nav.dashboard",
      "Home": "nav.dashboard",
      "Complaints": "nav.complaints",
      "Workload": "nav.workload",
      "Resolved Views": "nav.resolved",
      "Lost & Found": "nav.lost_found",
      "Announcements": "nav.announcements",
      "Chat": "nav.chat",
      "Notifications": "nav.notifications",
      "Users": "nav.user_management",
      "User Management": "nav.user_management",
      "Students": "Students",
      "App Managers & Wardens": "App Managers & Wardens",
      "Employees & Coordinators": "Employees & Coordinators",
      "Employee Assignments": "nav.employee_assignments",
      "Locations": "nav.locations",
      "Departments": "nav.departments",
      "Coverage Gaps": "Coverage Gaps",
      "Emergency Setup": "nav.emergency",
      "Issues Taxonomy": "Issues Taxonomy",
      "Campus Health Map": "nav.health_map",
      "Reports": "nav.reports",
      "Analytics": "nav.analytics",
      "Safety Reports": "nav.safety_reports",
      "Report Safely": "nav.safety_reports",
      "Audit Log": "nav.audit_logs",
      "Backups": "Backups",
      "Settings": "nav.settings",
      "Technical Support": "Technical Support",
      "Profile": "nav.profile",
      "My Jobs": "nav.my_tasks",
      "Institutions": "Institutions",
      "Support Requests": "Support Requests",
      "Platform Health": "Platform Health",
    };
    const key = labelKeyMap[label];
    return key ? t(key, label) : label;
  };

  const getSectionTitle = (title) => {
    const titleKeyMap = {
      "MAIN": "nav.main",
      "PLATFORM": "nav.platform",
      "MANAGEMENT": "nav.management",
      "INSIGHTS": "nav.insights",
      "SYSTEM": "nav.system",
      "ACCOUNT": "nav.account",
      "WORK": "nav.work",
    };
    const key = titleKeyMap[title];
    return key ? t(key, title) : title;
  };

  const roleTitle = useMemo(() => {
    if (!user) return "";
    const rawRole = (user.role || "").toLowerCase();
    return t(`roles.${rawRole}`, getRoleDisplayName(user.role));
  }, [user, language, t]);

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
            {
              to: "/admin/users",
              label: "User Management",
              icon: Users,
              subItems: [
                { to: "/admin/users?tab=students", label: "Students", icon: GraduationCap },
                { to: "/admin/users?tab=supervisors", label: "App Managers & Wardens", icon: ShieldCheck },
                { to: "/admin/users?tab=staff", label: "Coordinators", icon: Wrench },
              ],
            },
            { to: "/admin/locations", label: "Locations", icon: MapPin },
            { to: "/admin/departments", label: "Departments", icon: Building },
            { to: "/admin/coverage-gaps", label: "Coverage Gaps", icon: Activity },
            { to: "/admin/emergency", label: "Emergency Setup", icon: PhoneCall },
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
            {
              to: "/admin/users",
              label: "User Management",
              icon: Users,
              subItems: [
                { to: "/admin/users?tab=students", label: "Students", icon: GraduationCap },
                { to: "/admin/users?tab=supervisors", label: "App Managers & Wardens", icon: ShieldCheck },
                { to: "/admin/users?tab=staff", label: "Coordinators", icon: Wrench },
              ],
            },
            { to: "/admin/locations", label: "Locations", icon: MapPin },
            { to: "/admin/departments", label: "Departments", icon: Building },
            { to: "/admin/coverage-gaps", label: "Coverage Gaps", icon: Activity },
            { to: "/admin/emergency", label: "Emergency Setup", icon: PhoneCall },
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
                  {getSectionTitle(section.title)}
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
                  <span>{getSectionTitle(section.title)}</span>
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
                {section.items.map((link) => {
                  if (link.subItems && link.subItems.length > 0) {
                    const isParentActive = location.pathname === link.to;
                    const isSubOpen = openSubMenus[link.label] ?? isParentActive;

                    return (
                      <div key={link.label} className="flex flex-col gap-0.5">
                        <div
                          className={`group flex h-9 items-center justify-between rounded-xl px-3 text-xs transition-all cursor-pointer ${
                            isParentActive
                              ? "bg-primary/10 text-primary font-semibold dark:bg-primary/15 dark:text-primary shadow-2xs"
                              : "text-slate-600 dark:text-slate-400 hover:bg-slate-100/80 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100 font-medium"
                          }`}
                          onClick={() => toggleSubMenu(link.label)}
                        >
                          <NavLink
                            to={link.to}
                            onClick={onClose}
                            className="flex items-center gap-3 flex-1 min-w-0"
                          >
                            <link.icon className="h-4 w-4 shrink-0 transition-transform group-hover:scale-105" />
                            <span className="truncate">{getNavLabel(link.label)}</span>
                          </NavLink>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              toggleSubMenu(link.label);
                            }}
                            className="p-1 hover:bg-slate-200/50 dark:hover:bg-slate-700/50 rounded"
                          >
                            <ChevronDown
                              className={`h-3.5 w-3.5 text-slate-400 dark:text-slate-500 transition-transform duration-200 ${
                                isSubOpen ? "" : "-rotate-90"
                              }`}
                            />
                          </button>
                        </div>

                        {isSubOpen && (
                          <div className="pl-3.5 ml-3 my-0.5 border-l-2 border-slate-200/80 dark:border-slate-800 flex flex-col gap-0.5 animate-in fade-in duration-150">
                            {link.subItems.map((sub) => {
                              const [subPath, subQuery] = sub.to.split("?");
                              const isSubActive =
                                location.pathname === subPath &&
                                (subQuery ? location.search === `?${subQuery}` : !location.search);

                              return (
                                <NavLink
                                  key={sub.to}
                                  to={sub.to}
                                  onClick={onClose}
                                  className={`group flex h-8 items-center gap-2 rounded-lg px-2.5 text-xs transition-all ${
                                    isSubActive
                                      ? "bg-primary/15 text-primary font-bold dark:bg-primary/20 dark:text-primary shadow-2xs"
                                      : "text-slate-500 dark:text-slate-400 hover:bg-slate-100/70 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-slate-100 font-medium"
                                  }`}
                                >
                                  <sub.icon className="h-3.5 w-3.5 shrink-0 transition-transform group-hover:scale-105" />
                                  <span className="truncate">{getNavLabel(sub.label)}</span>
                                </NavLink>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  }

                  return (
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
                      <span className="truncate">{getNavLabel(link.label)}</span>
                    </NavLink>
                  );
                })}
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
      <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200/60 dark:border-slate-800 text-[11px] font-bold text-slate-700 dark:text-slate-200">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
        <span className="truncate">{roleTitle ? `${roleTitle} Portal` : "Portal"}</span>
      </div>
    </div>
  );

  const footerRow = (
    <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 mt-auto flex flex-col gap-1.5">
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

      <button
        onClick={() => setConfirmLogout(true)}
        className="flex w-full h-9 items-center gap-2 rounded-xl px-2.5 text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
        aria-label="Logout"
      >
        <LogOut className="h-4 w-4 text-red-500" />
        <span>{t("nav.logout", "Sign Out")}</span>
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
        {footerRow}
      </aside>
      <aside className="hidden shrink-0 border-r border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726] p-4 lg:flex lg:w-[250px] lg:flex-col">
        <div className="mb-4">{brandHeader}</div>
        {renderNavLinks()}
        {footerRow}
      </aside>

      <ConfirmDialog
        open={confirmLogout}
        title="Logout"
        message="Are you sure you want to logout of Campus Pulse?"
        confirmLabel="Logout"
        tone="danger"
        onCancel={() => setConfirmLogout(false)}
        onConfirm={() => {
          setConfirmLogout(false);
          logout();
        }}
      />
    </>
  );
}

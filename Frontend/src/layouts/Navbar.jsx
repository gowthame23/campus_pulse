import { useState, useRef, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Menu,
  Bell,
  User,
  LogOut,
  Search,
  ChevronRight,
  Settings,
  FileText,
  Users,
  MapPin,
  Folder,
  Sun,
  Moon,
  Monitor,
  Globe,
} from "lucide-react";
import Button from "../components/Button.jsx";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import EmergencyButton from "../components/EmergencyButton.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { useTheme } from "../context/ThemeContext.jsx";
import { useLanguage } from "../context/LanguageContext.jsx";
import { complaintService } from "../services/complaintService.js";
import { userService } from "../services/userService.js";
import { departmentService } from "../services/departmentService.js";
import { locationService } from "../services/locationService.js";
import { ROLES, getRoleDisplayName } from "../utils/constants.js";

import { notificationService } from "../services/notificationService.js";

export default function Navbar({ onMenuClick }) {
  const { user, logout } = useAuth();
  const { themeMode, setThemeMode, toggleTheme, isDark } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const location = useLocation();
  const navigate = useNavigate();
  const [confirmLogout, setConfirmLogout] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const langDropdownRef = useRef(null);

  // Unread Notification Count
  const [unreadNotifCount, setUnreadNotifCount] = useState(0);

  useEffect(() => {
    async function loadUnreadCount() {
      try {
        const res = await notificationService.getUnreadCount();
        setUnreadNotifCount(res.data?.unread_count || 0);
      } catch {
        setUnreadNotifCount(0);
      }
    }
    if (user) loadUnreadCount();
    // Listen for real-time notification events; a burst (e.g. pending
    // notifications delivered on connect) triggers a single refresh.
    let timer;
    const onNotif = () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        if (user) loadUnreadCount();
      }, 500);
    };
    window.addEventListener("campus-pulse-notification", onNotif);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("campus-pulse-notification", onNotif);
    };
  }, [user, location.pathname]);

  // Search Everywhere state
  const [searchVal, setSearchVal] = useState("");
  const [searchResults, setSearchResults] = useState({
    complaints: [],
    users: [],
    departments: [],
    locations: [],
  });
  const [searchOpen, setSearchOpen] = useState(false);
  const searchRef = useRef(null);

  // Data caches for search
  const [dbData, setDbData] = useState({
    complaints: [],
    users: [],
    departments: [],
    locations: [],
  });
  const [hasFetched, setHasFetched] = useState(false);

  // Fetch search source lists on focus
  const handleSearchFocus = async () => {
    setSearchOpen(true);
    if (hasFetched) return;
    try {
      const isAdminOrManager = [
        ROLES.ADMINISTRATOR,
        ROLES.APP_MANAGER,
      ].includes(user?.role);

      const promises = [complaintService.list()];
      if (isAdminOrManager) {
        promises.push(
          userService.list(),
          departmentService.list(),
          locationService.list(),
        );
      }

      const results = await Promise.all(promises);
      setDbData({
        complaints: results[0]?.data || [],
        users: results[1]?.data || [],
        departments: results[2]?.data || [],
        locations: results[3]?.data || [],
      });
      setHasFetched(true);
    } catch (err) {
      console.error("Failed to load search data:", err);
    }
  };

  // Perform search matching
  useEffect(() => {
    if (!searchVal.trim()) {
      setSearchResults({
        complaints: [],
        users: [],
        departments: [],
        locations: [],
      });
      return;
    }
    const val = searchVal.toLowerCase();

    const filteredComplaints = dbData.complaints
      .filter(
        (c) =>
          c.complaint_id.toLowerCase().includes(val) ||
          c.description.toLowerCase().includes(val) ||
          c.complaint_type.toLowerCase().includes(val),
      )
      .slice(0, 4);

    const filteredUsers = dbData.users
      .filter(
        (u) =>
          u.name.toLowerCase().includes(val) ||
          u.email.toLowerCase().includes(val),
      )
      .slice(0, 3);

    const filteredDepts = dbData.departments
      .filter((d) => d.name.toLowerCase().includes(val))
      .slice(0, 3);

    const filteredLocs = dbData.locations
      .filter((l) => l.name.toLowerCase().includes(val))
      .slice(0, 3);

    setSearchResults({
      complaints: filteredComplaints,
      users: filteredUsers,
      departments: filteredDepts,
      locations: filteredLocs,
    });
  }, [searchVal, dbData]);

  // Close search, lang and profile dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
      if (langDropdownRef.current && !langDropdownRef.current.contains(event.target)) {
        setLangDropdownOpen(false);
      }
      if (searchRef.current && !searchRef.current.contains(event.target)) {
        setSearchOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const getBreadcrumbs = () => {
    const path = location.pathname;
    const parts = path.split("/").filter(Boolean);
    if (parts.length === 0) return [{ label: "Dashboard", to: "/" }];

    const crumbs = [{ label: "Dashboard", to: "/" }];

    if (parts[0] === "complaints") {
      crumbs.push({ label: "Complaints", to: "/complaints" });
      if (parts[1] === "new") {
        crumbs.push({ label: "New", to: "/complaints/new" });
      } else if (parts[1]) {
        crumbs.push({
          label: `Complaint #${parts[1].substring(4, 8)}`,
          to: `/complaints/${parts[1]}`,
        });
      }
    } else if (parts[0] === "profile") {
      crumbs.push({ label: "Profile", to: "/profile" });
    } else if (parts[0] === "analytics") {
      crumbs.push({ label: "Analytics", to: "/analytics" });
    } else if (parts[0] === "notifications") {
      crumbs.push({ label: "Notifications", to: "/notifications" });
    } else if (parts[0] === "admin") {
      crumbs.push({ label: "Admin", to: "/admin" });
      if (parts[1] === "users") {
        crumbs.push({ label: "Users", to: "/admin/users" });
      } else if (parts[1] === "departments") {
        crumbs.push({ label: "Departments", to: "/admin/departments" });
      } else if (parts[1] === "locations") {
        crumbs.push({ label: "Locations", to: "/admin/locations" });
      }
    } else if (
      ["student", "coordinator", "manager", "location"].includes(parts[0])
    ) {
      const label =
        parts[0].charAt(0).toUpperCase() + parts[0].slice(1) + " Dashboard";
      crumbs.push({ label, to: `/${parts[0]}` });
    } else {
      crumbs.push({ label: parts[0], to: `/${parts[0]}` });
    }

    return crumbs;
  };

  const crumbs = getBreadcrumbs();
  const hasResults =
    searchResults.complaints.length > 0 ||
    searchResults.users.length > 0 ||
    searchResults.departments.length > 0 ||
    searchResults.locations.length > 0;

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 dark:border-slate-800/80 bg-white/95 dark:bg-[#101726]/95 backdrop-blur-sm h-14 flex items-center text-slate-900 dark:text-slate-100">
      <div className="flex w-full items-center justify-between gap-4 px-4 md:px-6">
        {/* Left Section: Menu Toggle, Portal Badge & Breadcrumbs */}
        <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
          <button
            onClick={onMenuClick}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-200 lg:hidden"
            aria-label="Open menu"
          >
            <Menu className="h-5 w-5" />
          </button>

          {user?.role && (
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-primary/10 text-primary border border-primary/20 text-xs font-bold shrink-0">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
              <span>{getRoleDisplayName(user.role)} Portal</span>
            </div>
          )}

          <nav className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400 max-w-xs md:max-w-md overflow-hidden whitespace-nowrap">
            {crumbs.map((crumb, idx) => (
              <span key={idx} className="flex items-center gap-1.5">
                {idx > 0 && (
                  <ChevronRight className="h-3 w-3 text-slate-300 dark:text-slate-600 shrink-0" />
                )}
                {idx === crumbs.length - 1 ? (
                  <span className="text-slate-900 dark:text-slate-100 font-semibold shrink-0">
                    {crumb.label}
                  </span>
                ) : (
                  <Link
                    to={crumb.to}
                    className="hover:text-slate-900 dark:hover:text-slate-100 shrink-0 transition-colors"
                  >
                    {crumb.label}
                  </Link>
                )}
              </span>
            ))}
          </nav>
        </div>

        {/* Middle Section: Search Everywhere Bar (Desktop) */}
        <div
          className="hidden min-w-0 flex-1 justify-center px-6 md:flex relative"
          ref={searchRef}
        >
          <div className="relative w-full max-w-xs">
            <Search className="pointer-events-none absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
            <input
              type="text"
              className="h-9 w-full rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/80 pl-9 pr-3 text-xs font-medium text-slate-800 dark:text-slate-100 placeholder:text-slate-400 outline-none transition-all duration-150 focus:border-primary focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-primary/10"
              placeholder="Search everywhere..."
              value={searchVal}
              onChange={(e) => setSearchVal(e.target.value)}
              onFocus={handleSearchFocus}
              aria-label="Search Everywhere"
            />
          </div>

          {/* Search Dropdown Overlay */}
          {searchOpen && searchVal.trim() && (
            <div className="absolute top-12 w-full max-w-sm rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 shadow-lg z-50 max-h-[360px] overflow-y-auto">
              {!hasResults ? (
                <div className="text-center text-xs font-medium text-slate-400 dark:text-slate-500 py-6">
                  No matching records found.
                </div>
              ) : (
                <div className="grid gap-3.5 text-xs">
                  {searchResults.complaints.length > 0 && (
                    <div>
                      <div className="font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider text-[10px] mb-1.5">
                        Complaints
                      </div>
                      <div className="grid gap-1">
                        {searchResults.complaints.map((c) => (
                          <Link
                            key={c.complaint_id}
                            to={`/complaints/${c.complaint_id}`}
                            onClick={() => setSearchOpen(false)}
                            className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-50 dark:hover:bg-slate-800/60 font-medium text-slate-700 dark:text-slate-200 truncate transition-colors"
                          >
                            <FileText className="h-4 w-4 text-slate-400 shrink-0" />
                            <span className="text-primary font-semibold">
                              {c.complaint_id}
                            </span>
                            <span className="truncate">{c.description}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {searchResults.users.length > 0 && (
                    <div>
                      <div className="font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider text-[10px] mb-1.5">
                        Users
                      </div>
                      <div className="grid gap-1">
                        {searchResults.users.map((u) => (
                          <Link
                            key={u.user_id}
                            to="/admin/users"
                            onClick={() => setSearchOpen(false)}
                            className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-50 dark:hover:bg-slate-800/60 font-medium text-slate-700 dark:text-slate-200 truncate transition-colors"
                          >
                            <Users className="h-4 w-4 text-slate-400 shrink-0" />
                            <span>{u.name}</span>
                            <span className="text-slate-400 dark:text-slate-500 font-normal truncate">
                              ({u.email})
                            </span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {searchResults.departments.length > 0 && (
                    <div>
                      <div className="font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider text-[10px] mb-1.5">
                        Departments
                      </div>
                      <div className="grid gap-1">
                        {searchResults.departments.map((d) => (
                          <Link
                            key={d.department_id}
                            to="/admin/departments"
                            onClick={() => setSearchOpen(false)}
                            className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-50 dark:hover:bg-slate-800/60 font-medium text-slate-700 dark:text-slate-200 truncate transition-colors"
                          >
                            <Folder className="h-4 w-4 text-slate-400 shrink-0" />
                            <span>{d.name}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}

                  {searchResults.locations.length > 0 && (
                    <div>
                      <div className="font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider text-[10px] mb-1.5">
                        Locations
                      </div>
                      <div className="grid gap-1">
                        {searchResults.locations.map((l) => (
                          <Link
                            key={l.location_id}
                            to="/admin/locations"
                            onClick={() => setSearchOpen(false)}
                            className="flex items-center gap-2 rounded-lg p-1.5 hover:bg-slate-50 dark:hover:bg-slate-800/60 font-medium text-slate-700 dark:text-slate-200 truncate transition-colors"
                          >
                            <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
                            <span>{l.name}</span>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Section: Actions & Dropdown */}
        <div className="flex items-center gap-2 sm:gap-3">
          {user?.role === ROLES.STUDENT && (
            <EmergencyButton compact userLocationId={user?.location_id} />
          )}

          {/* Language Selector Dropdown */}
          <div className="relative" ref={langDropdownRef}>
            <button
              onClick={() => setLangDropdownOpen(!langDropdownOpen)}
              className="flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors border border-slate-200/80 dark:border-slate-800 cursor-pointer shadow-2xs"
              title={t("select_language", "Language")}
              aria-label="Change Language"
            >
              <Globe className="h-4 w-4 text-primary shrink-0" />
              <span className="font-bold text-[11px]">
                {language === "te" ? "తెలుగు" : language === "hi" ? "हिन्दी" : "EN"}
              </span>
            </button>

            {langDropdownOpen && (
              <div className="absolute right-0 mt-1.5 w-36 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#101726] p-1.5 shadow-xl z-50 animate-in fade-in zoom-in-95 duration-150">
                <button
                  type="button"
                  onClick={() => {
                    setLanguage("en");
                    setLangDropdownOpen(false);
                  }}
                  className={`flex w-full items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    language === "en"
                      ? "bg-primary/10 text-primary font-bold"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <span>English</span>
                  <span className="text-[10px] text-slate-400 font-semibold">EN</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setLanguage("te");
                    setLangDropdownOpen(false);
                  }}
                  className={`flex w-full items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    language === "te"
                      ? "bg-primary/10 text-primary font-bold"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <span>తెలుగు</span>
                  <span className="text-[10px] text-slate-400 font-semibold">TE</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setLanguage("hi");
                    setLangDropdownOpen(false);
                  }}
                  className={`flex w-full items-center justify-between px-2.5 py-2 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    language === "hi"
                      ? "bg-primary/10 text-primary font-bold"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <span>हिन्दी</span>
                  <span className="text-[10px] text-slate-400 font-semibold">HI</span>
                </button>
              </div>
            )}
          </div>

          {/* Theme Switcher */}
          <button
            onClick={toggleTheme}
            className="hidden sm:flex items-center justify-center rounded-xl p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100 transition-colors"
            title={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
            aria-label="Toggle theme"
          >
            {isDark ? (
              <Sun className="h-4.5 w-4.5 text-amber-400" />
            ) : (
              <Moon className="h-4.5 w-4.5 text-slate-600" />
            )}
          </button>

          <Link
            to="/notifications"
            className="relative rounded-xl p-2 text-slate-500 hover:bg-slate-50 hover:text-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100 transition-colors"
            aria-label="View notifications"
          >
            <Bell className="h-4.5 w-4.5" />
            {unreadNotifCount > 0 && (
              <span className="absolute top-0.5 right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-white">
                {unreadNotifCount > 9 ? "9+" : unreadNotifCount}
              </span>
            )}
          </Link>

          {/* User Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="User menu"
              title="Account & Portal Menu"
            >
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary/10 text-xs font-bold text-primary capitalize shrink-0">
                {user?.name?.charAt(0) || "U"}
              </div>
              <div className="hidden text-left md:block">
                <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate max-w-[120px]">
                  {user?.name}
                </div>
                <div className="text-[10px] font-bold text-primary dark:text-primary-light uppercase">
                  {getRoleDisplayName(user?.role)}
                </div>
              </div>
            </button>

            {dropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 origin-top-right rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-1.5 shadow-lg animate-in fade-in slide-in-from-top-2 duration-150 z-50 text-slate-900 dark:text-slate-100">
                <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800 mb-1.5">
                  <div className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                    {user?.name}
                  </div>
                  <div className="text-[10px] font-semibold text-slate-400 truncate">
                    {user?.email}
                  </div>
                  <div className="mt-1.5 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-primary/10 text-primary border border-primary/20">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                    <span>{getRoleDisplayName(user?.role)} Portal</span>
                  </div>
                </div>
                <Link
                  to="/profile"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                  <User className="h-4 w-4 text-slate-400" />
                  {t("nav.profile", "My Profile")}
                </Link>
                <Link
                  to="/change-password"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                  <Settings className="h-4 w-4 text-slate-400" />
                  {t("profile.change_password", "Change Password")}
                </Link>

                {/* Theme Selector inside Dropdown */}
                <div className="my-1.5 border-t border-b border-slate-100 dark:border-slate-800 py-2 px-3">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                    {t("nav.appearance", "Appearance")}
                  </div>
                  <div className="grid grid-cols-3 gap-1 bg-slate-100 dark:bg-slate-800 p-1 rounded-lg">
                    <button
                      onClick={() => setThemeMode("light")}
                      className={`flex flex-col items-center justify-center p-1.5 rounded-md text-[10px] font-bold transition-all ${
                        themeMode === "light"
                          ? "bg-white dark:bg-slate-700 text-primary shadow-xs"
                          : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                      }`}
                      title="Light Theme"
                    >
                      <Sun className="h-3.5 w-3.5 mb-0.5" />
                      Light
                    </button>
                    <button
                      onClick={() => setThemeMode("dark")}
                      className={`flex flex-col items-center justify-center p-1.5 rounded-md text-[10px] font-bold transition-all ${
                        themeMode === "dark"
                          ? "bg-white dark:bg-slate-700 text-primary shadow-xs"
                          : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                      }`}
                      title="Dark Theme"
                    >
                      <Moon className="h-3.5 w-3.5 mb-0.5" />
                      Dark
                    </button>
                    <button
                      onClick={() => setThemeMode("system")}
                      className={`flex flex-col items-center justify-center p-1.5 rounded-md text-[10px] font-bold transition-all ${
                        themeMode === "system"
                          ? "bg-white dark:bg-slate-700 text-primary shadow-xs"
                          : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
                      }`}
                      title="System Default Theme"
                    >
                      <Monitor className="h-3.5 w-3.5 mb-0.5" />
                      System
                    </button>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setDropdownOpen(false);
                    setConfirmLogout(true);
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
                >
                  <LogOut className="h-4 w-4" />
                  {t("nav.logout", "Sign Out")}
                </button>
              </div>
            )}
          </div>

          {/* Direct Quick Logout Button */}
          <button
            onClick={() => setConfirmLogout(true)}
            className="hidden sm:flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 border border-red-200/60 dark:border-red-900/40 transition-colors cursor-pointer"
            title="Logout"
            aria-label="Logout"
          >
            <LogOut className="h-4 w-4 shrink-0" />
            <span>Logout</span>
          </button>
        </div>
      </div>

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
          navigate("/login", { replace: true });
        }}
      />
    </header>
  );
}

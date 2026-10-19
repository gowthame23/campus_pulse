import { NavLink } from "react-router-dom";
import { Home, FileText, Bell, User } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import { ROLES } from "../utils/constants.js";

export default function Footer() {
  const { user } = useAuth();
  const showNotifications = [ROLES.ADMINISTRATOR, ROLES.APP_MANAGER].includes(
    user?.role,
  );
  const links = [
    { to: "/", icon: Home, label: "Home" },
    { to: "/complaints", icon: FileText, label: "Complaints" },
    ...(showNotifications
      ? [{ to: "/notifications", icon: Bell, label: "Alerts" }]
      : []),
    { to: "/profile", icon: User, label: "Profile" },
  ];

  return (
    <footer className="fixed inset-x-0 bottom-0 z-30 border-t border-slate-200/80 dark:border-slate-800 bg-white/95 dark:bg-slate-900/95 backdrop-blur-md md:hidden shadow-xs pb-[env(safe-area-inset-bottom,0px)]">
      <nav
        className="grid"
        style={{
          gridTemplateColumns: `repeat(${links.length}, minmax(0, 1fr))`,
        }}
      >
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `grid place-items-center gap-1 px-2 py-2 text-[10px] transition-colors ${
                isActive
                  ? "text-primary dark:text-primary font-medium"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 font-normal"
              }`
            }
          >
            <Icon className="h-4 w-4" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </footer>
  );
}

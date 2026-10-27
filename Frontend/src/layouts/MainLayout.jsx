import { useState } from "react";
import { useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import Footer from "./Footer.jsx";
import Navbar from "./Navbar.jsx";
import Sidebar from "./Sidebar.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function MainLayout({ children }) {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex min-h-screen w-full max-w-full overflow-x-hidden bg-slate-50 dark:bg-[#090d16] text-slate-900 dark:text-slate-100 transition-colors duration-200">
      {/* Sidebar Navigation */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Core Content Body Wrapper */}
      <div className="flex min-w-0 flex-1 w-full max-w-full overflow-x-hidden flex-col pb-16 md:pb-0">
        <Navbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 p-3 sm:p-6 lg:p-8 w-full max-w-full overflow-x-hidden">
          <div className="mx-auto max-w-7xl w-full min-w-0 max-w-full">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
            >
              {children}
            </motion.div>
          </div>
        </main>
        <Footer />
      </div>
    </div>
  );
}

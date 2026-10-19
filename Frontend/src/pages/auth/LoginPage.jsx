import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Loader2, Sun, Moon, Monitor, Globe } from "lucide-react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Toast from "../../components/Toast.jsx";
import { getApiError } from "../../api/axios.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useTheme } from "../../context/ThemeContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";

export default function LoginPage() {
  const { isAuthenticated, login, sessionMessage, clearSessionMessage } =
    useAuth();
  const { themeMode, setThemeMode, activeTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: { email: "", password: "" },
  });

  useEffect(() => {
    if (sessionMessage) {
      const timer = setTimeout(() => {
        clearSessionMessage();
      }, 5000);
      return () => {
        clearTimeout(timer);
        clearSessionMessage();
      };
    }
  }, [sessionMessage, clearSessionMessage]);

  if (isAuthenticated) return <Navigate to="/" replace />;

  const onSubmit = async (values) => {
    setError("");
    clearSessionMessage();
    const identity = (values.email || values.username || "").trim();
    try {
      const user = await login({
        username: identity,
        email: identity,
        password: values.password,
      });
      const target = user.first_login
        ? "/change-password"
        : location.state?.from?.pathname || "/";
      navigate(target, { replace: true });
    } catch (err) {
      const isNetworkErr = err?.message === "Network Error" || !err?.response;
      const fallbackMsg = isNetworkErr
        ? "Cannot connect to backend server (http://127.0.0.1:8000). Please ensure backend is running."
        : "Invalid email, phone number, or password.";
      setError(getApiError(err, fallbackMsg));
    }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 px-4 py-12 transition-colors duration-200">
      {/* Top Right Controls: Compact Language Selector & Compact Theme Selector */}
      <div className="absolute top-4 right-4 flex items-center gap-2 flex-wrap justify-end z-20">
        {/* Compact Language Selector */}
        <div className="flex items-center gap-0.5 rounded-lg border border-slate-200/80 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 p-0.5 shadow-xs backdrop-blur-xs">
          <button
            type="button"
            onClick={() => setLanguage("en")}
            title="English"
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-bold transition-all cursor-pointer ${
              language === "en"
                ? "bg-primary text-white shadow-2xs"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Globe className="h-3 w-3" />
            <span>English</span>
          </button>
          <button
            type="button"
            onClick={() => setLanguage("te")}
            title="తెలుగు (Telugu)"
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-bold transition-all cursor-pointer ${
              language === "te"
                ? "bg-primary text-white shadow-2xs"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <span>తెలుగు</span>
          </button>
          <button
            type="button"
            onClick={() => setLanguage("hi")}
            title="हिन्दी (Hindi)"
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-bold transition-all cursor-pointer ${
              language === "hi"
                ? "bg-primary text-white shadow-2xs"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <span>हिन्दी</span>
          </button>
        </div>

        {/* Compact Theme Selector */}
        <div className="flex items-center gap-0.5 rounded-lg border border-slate-200/80 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 p-0.5 shadow-xs backdrop-blur-xs">
          <button
            type="button"
            onClick={() => setThemeMode("light")}
            title="Light Theme"
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-bold transition-all cursor-pointer ${
              themeMode === "light"
                ? "bg-primary text-white shadow-2xs"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Sun className="h-3 w-3" />
            <span>Light</span>
          </button>
          <button
            type="button"
            onClick={() => setThemeMode("dark")}
            title="Dark Theme"
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-bold transition-all cursor-pointer ${
              themeMode === "dark"
                ? "bg-primary text-white shadow-2xs"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Moon className="h-3 w-3" />
            <span>Dark</span>
          </button>
          <button
            type="button"
            onClick={() => setThemeMode("system")}
            title="System Default Theme"
            className={`flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-bold transition-all cursor-pointer ${
              themeMode === "system"
                ? "bg-primary text-white shadow-2xs"
                : "text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
            }`}
          >
            <Monitor className="h-3 w-3" />
            <span>System</span>
          </button>
        </div>
      </div>

      <div className="w-full max-w-[420px] rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-md md:p-8 animate-in fade-in duration-200">
        {/* Header Branding */}
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-primary text-white font-bold text-lg shadow-sm">
            CP
          </div>
          <h2 className="mt-4 text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            {t("auth.sign_in_title", "Sign in to Campus Pulse")}
          </h2>
          <p className="mt-1.5 text-xs font-medium text-slate-400 dark:text-slate-400">
            {t("auth.sign_in_subtitle", "Enter your credentials to manage campus operations")}
          </p>
        </div>

        <form className="grid gap-4" onSubmit={handleSubmit(onSubmit)}>
          {/* Email or Phone field */}
          <Input
            id="email"
            label={t("auth.email_or_phone", "College Email or Phone")}
            type="text"
            placeholder={t("auth.email_placeholder", "name@campus.edu or 10-digit phone")}
            autoComplete="username"
            error={errors.email?.message}
            {...register("email", {
              required: t("auth.req_email_phone", "Email address or phone number is required."),
              validate: (val) => {
                const trimmed = (val || "").trim();
                if (!trimmed) return t("auth.req_email_phone", "Email address or phone number is required.");
                if (trimmed.includes("@")) {
                  const emailPattern = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
                  return emailPattern.test(trimmed) || t("auth.invalid_email", "Invalid email address format.");
                }
                const digits = trimmed.replace(/[\s\-\(\)\.]/g, "").replace(/^\+91|^91/, "");
                if (/^\d{10,15}$/.test(digits) || /^[A-Za-z0-9_-]+$/.test(trimmed)) {
                  return true;
                }
                return t("auth.invalid_email_phone", "Enter a valid email address or 10-digit mobile number.");
              },
            })}
          />

          {/* Password field */}
          <Input
            id="password"
            label={t("auth.password", "Password")}
            type="password"
            placeholder="••••••••"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register("password", {
              required: t("auth.req_password", "Password is required."),
              minLength: {
                value: 6,
                message: t("auth.password_min_length", "Password must be at least 6 characters."),
              },
            })}
          />

          <div className="flex items-center justify-end text-xs font-semibold">
            <Link
              className="text-primary hover:text-primary-hover hover:underline transition-colors"
              to="/forgot-password"
            >
              {t("auth.forgot_password", "Forgot password?")}
            </Link>
          </div>

          {/* Toast Feedbacks */}
          <Toast
            message={sessionMessage}
            tone="info"
            onClose={clearSessionMessage}
          />
          <Toast message={error} tone="danger" onClose={() => setError("")} />

          {/* Submit Button */}
          <Button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2.5 font-bold cursor-pointer"
          >
            {isSubmitting ? (
              <span className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                {t("auth.signing_in", "Signing in...")}
              </span>
            ) : (
              t("auth.sign_in", "Sign in")
            )}
          </Button>
        </form>
      </div>
    </main>
  );
}

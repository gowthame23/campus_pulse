import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { Loader2, Sun, Moon, Globe, ChevronDown, Check } from "lucide-react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Toast from "../../components/Toast.jsx";
import { getApiError } from "../../api/axios.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useTheme } from "../../context/ThemeContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "te", label: "తెలుగు" },
  { code: "hi", label: "हिन्दी" },
];

export default function LoginPage() {
  const { isAuthenticated, login, sessionMessage, clearSessionMessage } =
    useAuth();
  const { setThemeMode, activeTheme } = useTheme();
  const { language, setLanguage, t } = useLanguage();
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const langRef = useRef(null);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (langRef.current && !langRef.current.contains(e.target)) {
        setLangMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
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
      {/* Top-Right Corner outside the box: Compact Language Dropdown */}
      <div className="absolute top-4 right-4 z-20" ref={langRef}>
        <div className="relative">
          <button
            type="button"
            onClick={() => setLangMenuOpen((prev) => !prev)}
            className="flex items-center gap-1.5 h-8 px-2.5 rounded-lg border border-slate-200/80 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 hover:bg-white dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 shadow-xs backdrop-blur-xs transition-colors cursor-pointer"
            title="Select language"
            aria-label="Select language"
          >
            <Globe className="h-3.5 w-3.5 text-primary" />
            <span>{LANGUAGES.find((l) => l.code === language)?.label || "English"}</span>
            <ChevronDown className={`h-3 w-3 text-slate-400 transition-transform ${langMenuOpen ? "rotate-180" : ""}`} />
          </button>

          {langMenuOpen && (
            <div className="absolute right-0 mt-1 w-28 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-lg py-1 z-30 animate-in fade-in zoom-in-95 duration-100">
              {LANGUAGES.map((l) => (
                <button
                  key={l.code}
                  type="button"
                  onClick={() => {
                    setLanguage(l.code);
                    setLangMenuOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 text-xs font-medium text-left transition-colors cursor-pointer ${
                    language === l.code
                      ? "bg-primary/10 text-primary font-bold"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                >
                  <span>{l.label}</span>
                  {language === l.code && <Check className="h-3.5 w-3.5 text-primary" />}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="relative w-full max-w-[420px] rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-md md:p-8 animate-in fade-in duration-200">
        {/* Single Theme Toggle Button inside corner of Login Card */}
        <button
          type="button"
          onClick={() => setThemeMode(activeTheme === "dark" ? "light" : "dark")}
          title={activeTheme === "dark" ? "Switch to Light mode" : "Switch to Dark mode"}
          aria-label="Toggle theme"
          className="absolute top-3.5 right-3.5 z-20 flex items-center justify-center h-8 w-8 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
        >
          {activeTheme === "dark" ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-600" />
          )}
        </button>

        {/* Header Branding */}
        <div className="mb-8 text-center pt-1 sm:pt-0">
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

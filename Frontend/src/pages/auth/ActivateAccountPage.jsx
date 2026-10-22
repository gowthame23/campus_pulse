import { useEffect, useState, useRef } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import {
  CheckCircle2,
  ShieldCheck,
  KeyRound,
  AlertCircle,
  Loader2,
  Sun,
  Moon,
  Globe,
  ChevronDown,
  Check,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Toast from "../../components/Toast.jsx";
import { authService } from "../../services/authService.js";
import { useTheme } from "../../context/ThemeContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "te", label: "తెలుగు" },
  { code: "hi", label: "हिन्दी" },
];

export default function ActivateAccountPage() {
  const { setThemeMode, activeTheme } = useTheme();
  const { language, setLanguage } = useLanguage();
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const langRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (langRef.current && !langRef.current.contains(e.target)) {
        setLangMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();

  const [verifying, setVerifying] = useState(true);
  const [userInfo, setUserInfo] = useState(null);
  const [verifyError, setVerifyError] = useState("");
  const [isSuccess, setIsSuccess] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  useEffect(() => {
    if (!token) {
      setVerifying(false);
      setVerifyError(
        "No activation token was provided in the link. Please check your activation email or link."
      );
      return;
    }

    const checkToken = async () => {
      try {
        const response = await authService.verifyActivation(token);
        setUserInfo(response.data);
      } catch (err) {
        setVerifyError(
          err?.response?.data?.detail ||
            "Invalid or expired activation link. Please request a new activation link from your Admin."
        );
      } finally {
        setVerifying(false);
      }
    };

    checkToken();
  }, [token]);

  const onActivate = async (values) => {
    setSubmitError("");
    try {
      await authService.completeActivation({
        activation_token: token,
        token,
        password: values.new_password,
        new_password: values.new_password,
        confirm_password: values.confirm_password,
      });
      setIsSuccess(true);
      setTimeout(() => {
        navigate("/login", {
          state: {
            message:
              "Account activated successfully. Please sign in with your new password.",
          },
        });
      }, 2500);
    } catch (err) {
      setSubmitError(
        err?.response?.data?.detail ||
          "Failed to activate account. Please try again."
      );
    }
  };

  const newPassword = watch("new_password");

  return (
    <main className="relative flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 px-4 py-12 transition-colors duration-200">
      {/* Top-Right Corner outside the box: Compact Language Dropdown (Exact match to Login Page) */}
      <div className="fixed top-4 right-4 z-30" ref={langRef}>
        <div className="relative">
          <button
            type="button"
            onClick={() => setLangMenuOpen((prev) => !prev)}
            className="flex items-center gap-1.5 h-8 px-2.5 rounded-lg border border-slate-200/80 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 hover:bg-white dark:hover:bg-slate-800 text-xs font-semibold text-slate-700 dark:text-slate-300 shadow-xs backdrop-blur-xs transition-colors cursor-pointer"
            title="Select language"
            aria-label="Select language"
          >
            <Globe className="h-3.5 w-3.5 text-primary" />
            <span>
              {LANGUAGES.find((l) => l.code === language)?.label || "English"}
            </span>
            <ChevronDown
              className={`h-3 w-3 text-slate-400 transition-transform ${
                langMenuOpen ? "rotate-180" : ""
              }`}
            />
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
                  {language === l.code && (
                    <Check className="h-3.5 w-3.5 text-primary" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="relative w-full max-w-[420px] rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-md md:p-8 animate-in fade-in duration-200">
        {/* Single Theme Toggle Button inside corner of Card (Exact match to Login Page) */}
        <button
          type="button"
          onClick={() =>
            setThemeMode(activeTheme === "dark" ? "light" : "dark")
          }
          title={
            activeTheme === "dark"
              ? "Switch to Light mode"
              : "Switch to Dark mode"
          }
          aria-label="Toggle theme"
          className="absolute top-3.5 right-3.5 z-20 flex items-center justify-center h-8 w-8 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-colors cursor-pointer"
        >
          {activeTheme === "dark" ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-600" />
          )}
        </button>

        {/* Header Section */}
        <div className="mb-6 text-center">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary font-semibold text-lg shadow-sm">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h1 className="mt-4 text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Campus Pulse
          </h1>
          <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400">
            Account Activation & Password Setup
          </p>
        </div>

        {verifying && (
          <div className="flex flex-col items-center justify-center py-8 space-y-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Verifying activation link...
            </p>
          </div>
        )}

        {!verifying && verifyError && (
          <div className="space-y-4">
            <div className="flex items-start gap-3 p-4 rounded-xl bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/50 text-red-700 dark:text-red-200">
              <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 shrink-0" />
              <div className="text-xs">
                <p className="font-semibold text-red-800 dark:text-red-300">
                  Activation Link Invalid
                </p>
                <p className="mt-1 text-red-600 dark:text-red-400">
                  {verifyError}
                </p>
              </div>
            </div>
            <div className="pt-2 text-center">
              <Link
                to="/login"
                className="inline-flex items-center text-xs font-semibold text-primary hover:text-primary/80"
              >
                Return to Login
              </Link>
            </div>
          </div>
        )}

        {!verifying && !verifyError && isSuccess && (
          <div className="text-center space-y-4 py-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-500/40 text-emerald-600 dark:text-emerald-400">
              <CheckCircle2 className="h-7 w-7" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
              Account Activated!
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Your password has been successfully configured. Redirecting to
              login...
            </p>
            <div className="pt-2">
              <Link
                to="/login"
                className="inline-flex items-center justify-center w-full px-4 py-2.5 text-xs font-bold text-white bg-primary rounded-lg hover:bg-primary/90 shadow-sm"
              >
                Sign In Now
              </Link>
            </div>
          </div>
        )}

        {!verifying && !verifyError && !isSuccess && userInfo && (
          <div className="space-y-5">
            <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60">
              <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
                Activating Account For
              </p>
              <p className="text-sm font-bold text-slate-900 dark:text-slate-100 mt-0.5">
                {userInfo.name}
              </p>
              <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mt-1">
                <span>{userInfo.email}</span>
                <span className="capitalize px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 font-mono text-[10px] font-semibold">
                  {userInfo.role}
                </span>
              </div>
            </div>

            {submitError && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/50 text-red-700 dark:text-red-300 text-xs">
                {submitError}
              </div>
            )}

            <form onSubmit={handleSubmit(onActivate)} className="space-y-4">
              <div>
                <Input
                  label="Create New Password"
                  type="password"
                  placeholder="Enter secure password (min 6 chars)"
                  error={errors.new_password?.message}
                  {...register("new_password", {
                    required: "Password is required",
                    minLength: {
                      value: 6,
                      message: "Password must be at least 6 characters",
                    },
                  })}
                />
              </div>

              <div>
                <Input
                  label="Confirm Password"
                  type="password"
                  placeholder="Re-enter password"
                  error={errors.confirm_password?.message}
                  {...register("confirm_password", {
                    required: "Please confirm your password",
                    validate: (val) =>
                      val === newPassword || "Passwords do not match",
                  })}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                className="w-full mt-2 font-bold py-2.5"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <span className="inline-flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Activating Account...
                  </span>
                ) : (
                  "Set Password & Activate"
                )}
              </Button>
            </form>

            <div className="text-center pt-2">
              <Link
                to="/login"
                className="text-xs font-semibold text-slate-500 hover:text-primary transition-colors"
              >
                Already have access? Sign in
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

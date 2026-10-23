import { useState, useEffect, useRef } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  Mail,
  KeyRound,
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

export default function ForgotPasswordPage() {
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
  const [step, setStep] = useState(1);
  const [resetId, setResetId] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm();

  const startReset = async (values) => {
    setMessage("");
    setError("");
    try {
      const response = await authService.requestPasswordReset({
        email: values.email,
      });
      setResetId(response.data.reset_id);
      setRecipientEmail(values.email);
      setMessage(response.data.message || "OTP sent to your email. Enter the verification code below.");
      setStep(2);
    } catch (err) {
      setError(err?.response?.data?.detail || "Email verification failed.");
    }
  };

  const verifyOtp = async (values) => {
    setMessage("");
    setError("");
    try {
      const response = await authService.verifyPasswordReset({
        reset_id: resetId,
        otp: values.otp,
      });
      setResetToken(response.data.reset_token);
      setMessage("OTP verified. Please set your new password.");
      setStep(3);
    } catch (err) {
      setError(err?.response?.data?.detail || "Invalid or expired OTP.");
    }
  };

  const completeReset = async (values) => {
    setMessage("");
    setError("");
    try {
      await authService.completePasswordReset({
        reset_token: resetToken,
        new_password: values.newPassword,
      });
      reset();
      setMessage("Password reset successful.");
      setStep(4);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to reset password.");
    }
  };

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
        {/* Single Theme Toggle Button inside corner of Card (Exact match to Login Page) */}
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

        {/* Header Section */}
        <div className="mb-6 text-center">
          <div className="mx-auto flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary font-semibold text-lg shadow-sm">
            {step === 1 && <Mail className="h-5 w-5" />}
            {step === 2 && <ShieldCheck className="h-5 w-5" />}
            {step === 3 && <KeyRound className="h-5 w-5" />}
            {step === 4 && (
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            )}
          </div>
          <h2 className="mt-4 text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            {step === 4 ? "Reset Complete" : "Reset Password"}
          </h2>
          <p className="mt-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
            {step === 1 && "Enter your email to receive a password reset OTP"}
            {step === 2 && "Enter the verification OTP sent to your email"}
            {step === 3 && "Choose a strong, secure new password"}
            {step === 4 && "Your password has been successfully updated"}
          </p>
        </div>

        {/* Step indicators */}
        {step < 4 && (
          <div className="mb-6 flex items-center justify-center gap-1.5">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-1.5 rounded-full transition-all duration-200 ${
                  s === step
                    ? "w-6 bg-primary"
                    : s < step
                      ? "w-1.5 bg-primary/50"
                      : "w-1.5 bg-slate-200 dark:bg-slate-700"
                }`}
              />
            ))}
          </div>
        )}

        <Toast
          message={message}
          tone="success"
          onClose={() => setMessage("")}
        />
        <Toast message={error} tone="danger" onClose={() => setError("")} />

        {/* STEP 1: Email Form */}
        {step === 1 && (
          <form className="mt-4 grid gap-4" onSubmit={handleSubmit(startReset)}>
            <Input
              label="College Email"
              type="email"
              placeholder="name@campus.edu"
              error={errors.email?.message}
              {...register("email", { required: "College email is required." })}
            />
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 font-bold"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Sending OTP...
                </span>
              ) : (
                "Send OTP"
              )}
            </Button>

            <div className="mt-4 p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 text-center">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Staff or worker without email?
              </p>
              <p className="text-xs font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                Ask your Coordinator or App Manager to reset your password.
              </p>
            </div>
          </form>
        )}

        {/* STEP 2: Verify OTP Form */}
        {step === 2 && (
          <form className="mt-4 grid gap-4" onSubmit={handleSubmit(verifyOtp)}>
            {/* Verification OTP Box with email confirmation */}
            <div className="rounded-xl border border-blue-100 dark:border-blue-900/50 bg-blue-50/50 dark:bg-blue-950/30 p-4 text-xs text-blue-800 dark:text-blue-200 leading-normal space-y-1">
              <div className="font-semibold text-blue-900 dark:text-blue-100 flex items-center gap-1.5">
                <span>&#10003; Verification Code Sent</span>
              </div>
              <p className="text-blue-700 dark:text-blue-300">
                Code sent to <span className="font-bold text-blue-900 dark:text-blue-100">{recipientEmail}</span>. Please check your inbox.
              </p>
              <p className="text-amber-700 dark:text-amber-300 font-medium pt-1 border-t border-blue-200/50 dark:border-blue-800/50">
                &#9888;&#65039; Check your <strong>Spam / Junk</strong> folder if it does not appear in your Primary inbox within 30 seconds.
              </p>
            </div>

            <Input
              label="Enter OTP"
              placeholder="123456"
              error={errors.otp?.message}
              {...register("otp", {
                required: "Verification OTP is required.",
              })}
            />

            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 font-bold"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Verifying...
                </span>
              ) : (
                "Verify OTP"
              )}
            </Button>
          </form>
        )}

        {/* STEP 3: Change Password Form */}
        {step === 3 && (
          <form
            className="mt-4 grid gap-4"
            onSubmit={handleSubmit(completeReset)}
          >
            <Input
              label="New Password"
              type="password"
              placeholder="••••••••"
              error={errors.newPassword?.message}
              {...register("newPassword", {
                required: "New password is required.",
                minLength: {
                  value: 8,
                  message: "Password must be at least 8 characters.",
                },
              })}
            />
            <Input
              label="Confirm New Password"
              type="password"
              placeholder="••••••••"
              error={errors.confirmPassword?.message}
              {...register("confirmPassword", {
                validate: (value) =>
                  value === watch("newPassword") || "Passwords do not match.",
              })}
            />
            <p className="text-[10px] font-medium text-slate-500 dark:text-slate-400">
              Must contain at least 8 characters with 1 uppercase, 1 lowercase,
              and 1 number.
            </p>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-2.5 font-bold"
            >
              {isSubmitting ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Saving...
                </span>
              ) : (
                "Set New Password"
              )}
            </Button>
          </form>
        )}

        {/* STEP 4: Success state */}
        {step === 4 && (
          <div className="mt-4">
            <Link to="/login" className="block w-full">
              <Button className="w-full py-2.5 font-bold">Go to Login</Button>
            </Link>
          </div>
        )}

        {/* Back Link */}
        <div className="mt-6 text-center">
          <Link
            className="inline-flex items-center justify-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
            to="/login"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to login
          </Link>
        </div>
      </div>
    </main>
  );
}

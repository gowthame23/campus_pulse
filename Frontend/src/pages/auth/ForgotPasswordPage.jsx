import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import {
  ArrowLeft,
  CheckCircle2,
  ShieldCheck,
  Mail,
  KeyRound,
  Loader2,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Toast from "../../components/Toast.jsx";
import { authService } from "../../services/authService.js";

export default function ForgotPasswordPage() {
  const [step, setStep] = useState(1);
  const [resetId, setResetId] = useState("");
  const [resetToken, setResetToken] = useState("");
  const [simulatedOtp, setSimulatedOtp] = useState("");
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
      setSimulatedOtp(response.data.simulated_otp);
      setMessage("OTP sent. For local simulation, use the code below.");
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
    <main className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950 px-4 py-12 transition-colors">
      <div className="w-full max-w-[420px] rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-md md:p-8 animate-in fade-in duration-200">
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
          </form>
        )}

        {/* STEP 2: Verify OTP Form */}
        {step === 2 && (
          <form className="mt-4 grid gap-4" onSubmit={handleSubmit(verifyOtp)}>
            {/* Future-proof OTP simulation notice box. Can be replaced with actual email routing. */}
            <div className="rounded-xl border border-blue-100 dark:border-blue-900/50 bg-blue-50/50 dark:bg-blue-950/30 p-4 text-xs text-blue-800 dark:text-blue-200 leading-normal">
              <span className="font-bold">Simulation Notice:</span> Enter the
              code <strong>{simulatedOtp}</strong> below to verify.
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

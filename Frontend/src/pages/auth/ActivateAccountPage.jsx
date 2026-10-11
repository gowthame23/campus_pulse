import { useEffect, useState } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { CheckCircle2, ShieldCheck, KeyRound, AlertCircle, Loader2 } from "lucide-react";
import Button from "../../components/Button.jsx";
import Input from "../../components/Input.jsx";
import Toast from "../../components/Toast.jsx";
import { authService } from "../../services/authService.js";

export default function ActivateAccountPage() {
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
      setVerifyError("No activation token was provided in the link. Please check your activation email or link.");
      return;
    }

    const checkToken = async () => {
      try {
        const response = await authService.verifyActivation(token);
        setUserInfo(response.data);
      } catch (err) {
        setVerifyError(
          err?.response?.data?.detail || "Invalid or expired activation link. Please request a new activation link from your administrator."
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
        token,
        new_password: values.new_password,
      });
      setIsSuccess(true);
      setTimeout(() => {
        navigate("/login", { state: { message: "Account activated successfully. Please sign in with your new password." } });
      }, 2500);
    } catch (err) {
      setSubmitError(err?.response?.data?.detail || "Failed to activate account. Please try again.");
    }
  };

  const newPassword = watch("new_password");

  return (
    <main className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
          <ShieldCheck className="h-8 w-8" />
        </div>
        <h1 className="mt-4 text-2xl font-bold tracking-tight text-white">Campus Pulse</h1>
        <p className="mt-1 text-sm text-slate-400">Account Activation & Password Setup</p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl">
          {verifying && (
            <div className="flex flex-col items-center justify-center py-8 space-y-3">
              <Loader2 className="h-8 w-8 animate-spin text-indigo-500" />
              <p className="text-sm text-slate-400">Verifying activation link...</p>
            </div>
          )}

          {!verifying && verifyError && (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-4 rounded-xl bg-red-950/40 border border-red-800/50 text-red-200">
                <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 shrink-0" />
                <div className="text-sm">
                  <p className="font-semibold text-red-300">Activation Link Invalid</p>
                  <p className="mt-1 text-xs text-red-400">{verifyError}</p>
                </div>
              </div>
              <div className="pt-2 text-center">
                <Link
                  to="/login"
                  className="inline-flex items-center text-sm font-medium text-indigo-400 hover:text-indigo-300"
                >
                  Return to Login
                </Link>
              </div>
            </div>
          )}

          {!verifying && !verifyError && isSuccess && (
            <div className="text-center space-y-4 py-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-950/60 border border-emerald-500/40 text-emerald-400">
                <CheckCircle2 className="h-7 w-7" />
              </div>
              <h2 className="text-lg font-semibold text-white">Account Activated!</h2>
              <p className="text-sm text-slate-400">
                Your password has been successfully configured. Redirecting to login...
              </p>
              <div className="pt-2">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center w-full px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-500"
                >
                  Sign In Now
                </Link>
              </div>
            </div>
          )}

          {!verifying && !verifyError && !isSuccess && userInfo && (
            <div className="space-y-6">
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60">
                <p className="text-xs font-medium text-slate-400">Activating Account For</p>
                <p className="text-sm font-semibold text-white mt-0.5">{userInfo.name}</p>
                <div className="flex items-center justify-between text-xs text-slate-400 mt-1">
                  <span>{userInfo.email}</span>
                  <span className="capitalize px-2 py-0.5 rounded-full bg-indigo-950/60 text-indigo-400 border border-indigo-800/40 font-mono text-[11px]">
                    {userInfo.role}
                  </span>
                </div>
              </div>

              {submitError && (
                <div className="p-3 rounded-lg bg-red-950/40 border border-red-800/50 text-red-300 text-xs">
                  {submitError}
                </div>
              )}

              <form onSubmit={handleSubmit(onActivate)} className="space-y-4">
                <div>
                  <Input
                    label="Create New Password"
                    type="password"
                    placeholder="Enter secure password (min 6 chars)"
                    icon={<KeyRound className="h-4 w-4 text-slate-500" />}
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
                    icon={<KeyRound className="h-4 w-4 text-slate-500" />}
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
                  className="w-full mt-2"
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
                  className="text-xs text-slate-400 hover:text-slate-300"
                >
                  Already have access? Sign in
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

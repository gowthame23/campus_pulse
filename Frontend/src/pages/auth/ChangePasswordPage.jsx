import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import { ArrowLeft, Loader2, KeyRound } from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Toast from "../../components/Toast.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { authService } from "../../services/authService.js";

export default function ChangePasswordPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const { refreshUser } = useAuth();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isSubmitting },
  } = useForm();

  const onSubmit = async (values) => {
    setMessage("");
    setError("");
    try {
      await authService.changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword,
        confirm_password: values.confirmPassword,
      });
      await refreshUser();
      reset();
      setMessage("Password changed successfully.");
      setTimeout(() => navigate("/"), 1000);
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to change password.");
    }
  };

  return (
    <div className="grid gap-6 max-w-md">
      {/* Page Header */}
      <div>
        <Link
          to="/profile"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to profile
        </Link>
        <PageHeader
          title="Change Password"
          description="Update your current password to keep your Campus Pulse account secure."
        />
      </div>

      <Card>
        <form className="grid gap-4" onSubmit={handleSubmit(onSubmit)}>
          <Input
            id="currentPassword"
            label="Current Password"
            type="password"
            placeholder="••••••••"
            error={errors.currentPassword?.message}
            {...register("currentPassword", {
              required: "Current password is required.",
            })}
          />
          <Input
            id="newPassword"
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
            id="confirmPassword"
            label="Confirm New Password"
            type="password"
            placeholder="••••••••"
            error={errors.confirmPassword?.message}
            {...register("confirmPassword", {
              validate: (value) =>
                value === watch("newPassword") || "Passwords do not match.",
            })}
          />
          <p className="text-[10px] font-medium text-slate-400">
            Must contain at least 8 characters with 1 uppercase, 1 lowercase,
            and 1 number.
          </p>

          <Toast
            message={message}
            tone="success"
            onClose={() => setMessage("")}
          />
          <Toast message={error} tone="danger" onClose={() => setError("")} />

          <Button
            type="submit"
            disabled={isSubmitting}
            className="font-bold py-2.5 flex items-center justify-center gap-1.5"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Updating...
              </>
            ) : (
              <>
                <KeyRound className="h-4 w-4" />
                Update Password
              </>
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
}

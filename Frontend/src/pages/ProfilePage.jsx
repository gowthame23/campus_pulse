import { useState, useMemo, useRef } from "react";
import { Link } from "react-router-dom";
import {
  KeyRound,
  Shield,
  Mail,
  UserCheck,
  Calendar,
  Phone,
  Hash,
  Building,
  Home,
  Clock,
  Edit2,
  Save,
  Camera,
  Upload,
} from "lucide-react";
import Badge from "../components/Badge.jsx";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import Input from "../components/Input.jsx";
import PageHeader from "../components/PageHeader.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { formatDate } from "../utils/dateFormatter.js";
import { userService } from "../services/userService.js";

export default function ProfilePage() {
  const { user, setUser, refreshUser } = useAuth();

  const roleTitle = useMemo(() => {
    if (!user) return "";
    const role = (user.role || "").toLowerCase();
    if (role === "location_in_charge") {
      const locName = (user.location_name || user.location_id || "").toLowerCase();
      if (locName.includes("hostel")) return "Hostel Warden";
      if (locName.includes("mess")) return "Mess Supervisor";
      if (locName.includes("sac") || locName.includes("activity")) return "SAC In-Charge";
      if (locName.includes("sport")) return "Sports In-Charge";
      if (locName.includes("academic")) return "Academic Block Supervisor";
      return "General Supervisor";
    }
    return user.role ? user.role.replace("_", " ") : "";
  }, [user]);

  const [isEditing, setIsEditing] = useState(false);
  const [phone, setPhone] = useState(user?.phone_number || "");
  const [photo, setPhoto] = useState(user?.profile_photo || "");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const galleryInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const isStudent = user?.role === "student";
  const isStaff = [
    "coordinator",
    "location_in_charge",
    "app_manager",
    "administrator",
  ].includes(user?.role);

  const handlePhotoChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setErr("Image file size should be under 5MB.");
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        setPhoto(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMsg("");
    setErr("");
    try {
      const res = await userService.update(user.user_id, {
        phone_number: phone,
        profile_photo: photo,
      });
      if (refreshUser) await refreshUser();
      else if (setUser && res.data) setUser(res.data);
      setIsEditing(false);
      setMsg("Profile updated successfully.");
    } catch (error) {
      setErr(error.response?.data?.detail || "Failed to update profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="grid gap-6 max-w-3xl">
      <PageHeader
        title="Account & Profile Settings"
        description="View your personal details, role assignments, and profile settings."
        actions={
          <div className="flex gap-2">
            {!isEditing ? (
              <Button
                onClick={() => setIsEditing(true)}
                variant="subtle"
                className="font-semibold flex items-center gap-1.5"
              >
                <Edit2 className="h-4 w-4" />
                Edit Profile
              </Button>
            ) : (
              <Button
                onClick={() => setIsEditing(false)}
                variant="secondary"
                className="font-semibold"
              >
                Cancel
              </Button>
            )}
            <Link to="/change-password">
              <Button className="font-semibold flex items-center gap-1.5">
                <KeyRound className="h-4 w-4" />
                Change Password
              </Button>
            </Link>
          </div>
        }
      />

      {msg && (
        <div className="p-3 bg-emerald-50 text-emerald-700 text-sm font-semibold rounded-lg border border-emerald-200">
          {msg}
        </div>
      )}
      {err && (
        <div className="p-3 bg-rose-50 text-rose-700 text-sm font-semibold rounded-lg border border-rose-200">
          {err}
        </div>
      )}

      <Card>
        {/* User Card Header */}
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 pb-5">
          <div className="flex items-center gap-4">
            <div className="relative group cursor-pointer" onClick={() => setIsEditing(true)}>
              {photo ? (
                <img
                  src={photo}
                  alt={user?.name}
                  className="h-16 w-16 rounded-xl object-cover border border-slate-200 shadow-xs"
                />
              ) : (
                <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10 text-2xl font-bold text-primary capitalize shadow-xs">
                  {user?.name?.charAt(0) || "U"}
                </div>
              )}
              <label
                htmlFor="profile-photo-upload-avatar"
                className="absolute inset-0 bg-slate-900/40 rounded-xl flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                title="Change Photo"
              >
                <Camera className="h-5 w-5" />
              </label>
              <input
                id="profile-photo-upload-avatar"
                type="file"
                accept="image/*"
                onChange={(e) => {
                  handlePhotoChange(e);
                  setIsEditing(true);
                }}
                className="hidden"
              />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                {user?.name}
              </h2>
              <p className="text-sm font-semibold text-slate-400">
                {user?.email}
              </p>
              {user?.phone_number && (
                <p className="text-xs text-slate-500 font-medium mt-0.5">
                  {user.phone_number}
                </p>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <Badge tone={user?.status === "Active" ? "success" : "warning"}>
              {user?.status || "Active"}
            </Badge>
            <span className="text-xs font-bold text-slate-400 capitalize">
              {roleTitle}
            </span>
          </div>
        </div>

        {isEditing ? (
          <form onSubmit={handleSave} className="mt-6 grid gap-4">
            <Input
              label="Phone Number"
              placeholder="e.g. 9876543210"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />

            <div>
              <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Profile Photo (Upload from Gallery or Take Photo)
              </label>

              <div className="flex items-center gap-4 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                {photo ? (
                  <img
                    src={photo}
                    alt="Preview"
                    className="h-16 w-16 rounded-xl object-cover border border-slate-200 shadow-xs shrink-0"
                  />
                ) : (
                  <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-primary/10 text-2xl font-bold text-primary capitalize shadow-xs shrink-0">
                    {user?.name?.charAt(0) || "U"}
                  </div>
                )}
                <div className="flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    onClick={() => galleryInputRef.current?.click()}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-primary hover:bg-primary/90 text-white text-xs font-bold rounded-lg transition-all shadow-xs active:scale-95"
                  >
                    <Upload className="h-4 w-4" />
                    Choose from Gallery
                  </button>

                  <button
                    type="button"
                    onClick={() => cameraInputRef.current?.click()}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg transition-all shadow-xs active:scale-95"
                  >
                    <Camera className="h-4 w-4" />
                    Take Photo with Camera
                  </button>

                  {photo && (
                    <button
                      type="button"
                      onClick={() => setPhoto("")}
                      className="px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-600 text-xs font-bold rounded-lg transition-all border border-rose-200 active:scale-95"
                    >
                      Remove Photo
                    </button>
                  )}
                </div>
              </div>

              {/* Hidden file inputs */}
              <input
                ref={galleryInputRef}
                type="file"
                accept="image/jpeg,image/png,image/jpg"
                onChange={handlePhotoChange}
                className="hidden"
              />
              <input
                ref={cameraInputRef}
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handlePhotoChange}
                className="hidden"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="submit"
                variant="primary"
                disabled={saving}
                className="font-bold flex items-center gap-1.5"
              >
                <Save className="h-4 w-4" />
                {saving ? "Saving..." : "Save Profile"}
              </Button>
            </div>
          </form>
        ) : (
          /* Profile Details Sections */
          <div className="mt-6 grid gap-6">
            {/* Primary Details */}
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                Primary Information
              </h3>
              <div className="grid gap-4 sm:grid-cols-2 text-sm bg-slate-50/50 p-4 rounded-xl border border-slate-100">
                <div className="flex gap-3">
                  <UserCheck className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                      User ID
                    </div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                      {user?.user_id}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Mail className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                      Email (Read-Only)
                    </div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                      {user?.email}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Phone className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                      Phone Number
                    </div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                      {user?.phone_number || "Not provided"}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Shield className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                      Account Role
                    </div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5 capitalize">
                      {user?.role?.replace("_", " ")}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Student Specific Profile */}
            {isStudent && (
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                  Student Information
                </h3>
                <div className="grid gap-4 sm:grid-cols-2 text-sm bg-slate-50/50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                  <div className="flex gap-3">
                    <Hash className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Roll Number (Immutable)
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.roll_number || "S2023001"}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Building className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Department
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.department || user?.department_id || "CSE"}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Home className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Hostel & Block
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.hostel || "Hostel Block A"} (
                        {user?.block || "Block A"})
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Home className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Room Number
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.room_number || "101"}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Staff Specific Profile */}
            {isStaff && (
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                  Staff Information
                </h3>
                <div className="grid gap-4 sm:grid-cols-2 text-sm bg-slate-50/50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                  <div className="flex gap-3">
                    <Hash className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Employee ID (Immutable)
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.employee_id || "EMP001"}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Building className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Designation
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.designation || "Staff Officer"}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Building className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Department
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.department ||
                          user?.department_id ||
                          "Operations"}
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <Shield className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                    <div>
                      <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                        Assigned Location
                      </div>
                      <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                        {user?.location_id || "All Locations"}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* System Info */}
            <div>
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                System Metrics
              </h3>
              <div className="grid gap-4 sm:grid-cols-2 text-sm bg-slate-50/50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                <div className="flex gap-3">
                  <Calendar className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                      Member Since
                    </div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                      {user?.created_at ? formatDate(user.created_at) : "N/A"}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Clock className="h-5 w-5 text-slate-400 shrink-0 mt-0.5" />
                  <div>
                    <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                      Last Login
                    </div>
                    <div className="font-semibold text-slate-800 dark:text-slate-100 mt-0.5">
                      {user?.last_login ? formatDate(user.last_login) : "Never"}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}

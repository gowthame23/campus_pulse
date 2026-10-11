import { Navigate, useLocation } from "react-router-dom";
import Loader from "../components/Loader.jsx";
import MainLayout from "../layouts/MainLayout.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute({ children, roles }) {
  const { initializing, isAuthenticated, user } = useAuth();
  const location = useLocation();

  if (initializing)
    return (
      <main className="grid min-h-screen place-items-center">
        <Loader label="Restoring session" />
      </main>
    );
  if (!isAuthenticated)
    return <Navigate to="/login" state={{ from: location }} replace />;
  if (roles?.length && !roles.includes(user?.role))
    return <Navigate to="/403" replace />;

  return <MainLayout>{children}</MainLayout>;
}

import { useNavigate, useLocation } from "react-router-dom";
import { useMasterAuth } from "../stores/master-auth.ts";

/**
 * Floating pill button for masters to toggle between master panel and client view.
 * Only renders when the user is a detected master.
 */
export function RoleSwitcher() {
  const role = useMasterAuth((s) => s.role);
  const setRole = useMasterAuth((s) => s.setRole);
  const navigate = useNavigate();
  const location = useLocation();

  // Only masters see the toggle
  if (role !== "master") return null;

  const isInMasterPanel = location.pathname.startsWith("/master");

  const handleToggle = () => {
    if (isInMasterPanel) {
      setRole("client");
      navigate("/my-bookings");
    } else {
      setRole("master");
      navigate("/master/dashboard");
    }
  };

  return (
    <button
      onClick={handleToggle}
      className="fixed top-3 right-3 z-50 bg-white rounded-full shadow-md px-3 py-1.5 text-sm font-medium border border-border active:scale-95 transition-transform"
    >
      {isInMasterPanel ? "\uD83D\uDC64 Мои записи" : "\u2699\uFE0F Панель мастера"}
    </button>
  );
}

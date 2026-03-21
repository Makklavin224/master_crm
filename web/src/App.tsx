import { ConfigProvider, App as AntApp } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "./stores/auth";
import { useThemeStore } from "./stores/theme";
import { lightTheme, darkTheme } from "./theme";
import { AdminLayout } from "./layouts/AdminLayout";
import { LoginPage } from "./pages/LoginPage";
import { CalendarPage } from "./pages/CalendarPage";
import { ClientsPage } from "./pages/ClientsPage";
import { ClientDetailPage } from "./pages/ClientDetailPage";
import { PaymentsPage } from "./pages/PaymentsPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { ServicesPage } from "./pages/ServicesPage";
import { SettingsPage } from "./pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function ProtectedRoute() {
  const isAuthenticated = useAuth((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function MagicLinkCallback() {
  const setToken = useAuth((s) => s.setToken);
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");
    if (token) {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
      fetch(`${API_BASE}/auth/magic/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
      })
        .then((res) => {
          if (!res.ok) throw new Error("Invalid magic link");
          return res.json();
        })
        .then((data) => {
          setToken(data.access_token);
          navigate("/calendar");
        })
        .catch(() => {
          navigate("/login");
        });
    }
  }, [setToken, navigate]);

  return <div style={{ padding: 48, textAlign: "center" }}>Verifying magic link...</div>;
}

export default function App() {
  const isDark = useThemeStore((s) => s.isDark);
  const hydrate = useAuth((s) => s.hydrate);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  return (
    <ConfigProvider theme={isDark ? darkTheme : lightTheme}>
      <AntApp>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter basename="/admin">
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/auth/magic" element={<MagicLinkCallback />} />
              <Route element={<ProtectedRoute />}>
                <Route element={<AdminLayout />}>
                  <Route index element={<Navigate to="/calendar" replace />} />
                  <Route path="/calendar" element={<CalendarPage />} />
                  <Route path="/clients" element={<ClientsPage />} />
                  <Route path="/clients/:id" element={<ClientDetailPage />} />
                  <Route path="/services" element={<ServicesPage />} />
                  <Route path="/payments" element={<PaymentsPage />} />
                  <Route path="/reviews" element={<ReviewsPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Route>
              </Route>
            </Routes>
          </BrowserRouter>
        </QueryClientProvider>
      </AntApp>
    </ConfigProvider>
  );
}

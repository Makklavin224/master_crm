import { ConfigProvider } from "antd";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "./stores/auth";
import { useThemeStore } from "./stores/theme";
import { lightTheme, darkTheme } from "./theme";
import { AdminLayout } from "./layouts/AdminLayout";
import { LoginPage } from "./pages/LoginPage";
import { ClientsPage } from "./pages/ClientsPage";
import { ClientDetailPage } from "./pages/ClientDetailPage";
import { PaymentsPage } from "./pages/PaymentsPage";

const queryClient = new QueryClient();

function ProtectedRoute() {
  const isAuthenticated = useAuth((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <Outlet />;
}

function PlaceholderPage({ title }: { title: string }) {
  return <div><h2>{title}</h2><p>Coming soon...</p></div>;
}

function MagicLinkCallback() {
  const setToken = useAuth((s) => s.setToken);

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
          window.location.href = "/admin/calendar";
        })
        .catch(() => {
          window.location.href = "/admin/login";
        });
    }
  }, [setToken]);

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
      <QueryClientProvider client={queryClient}>
        <BrowserRouter basename="/admin">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/magic" element={<MagicLinkCallback />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AdminLayout />}>
                <Route index element={<Navigate to="/calendar" replace />} />
                <Route path="/calendar" element={<PlaceholderPage title="\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c" />} />
                <Route path="/clients" element={<ClientsPage />} />
                <Route path="/clients/:id" element={<ClientDetailPage />} />
                <Route path="/services" element={<PlaceholderPage title="\u0423\u0441\u043b\u0443\u0433\u0438" />} />
                <Route path="/payments" element={<PaymentsPage />} />
                <Route path="/settings" element={<PlaceholderPage title="\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438" />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ConfigProvider>
  );
}

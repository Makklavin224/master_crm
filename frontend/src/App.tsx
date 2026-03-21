import { useEffect } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useSearchParams,
  useNavigate,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PlatformProvider, usePlatform } from "./platform/context.tsx";
import { ToastContainer } from "./components/ui/Toast.tsx";
import { useMasterAuth } from "./stores/master-auth.ts";
import { RoleSwitcher } from "./components/RoleSwitcher.tsx";
import { ServiceSelection } from "./pages/client/ServiceSelection.tsx";
import { DatePicker } from "./pages/client/DatePicker.tsx";
import { TimePicker } from "./pages/client/TimePicker.tsx";
import { BookingForm } from "./pages/client/BookingForm.tsx";
import { Confirmation } from "./pages/client/Confirmation.tsx";
import { MyBookings } from "./pages/client/MyBookings.tsx";

// Master panel
import { BottomTabBar } from "./components/BottomTabBar.tsx";
import { Dashboard } from "./pages/master/Dashboard.tsx";
import { Services } from "./pages/master/Services.tsx";
import { ServiceForm } from "./pages/master/ServiceForm.tsx";
import { Schedule } from "./pages/master/Schedule.tsx";
import { Bookings } from "./pages/master/Bookings.tsx";
import { Clients } from "./pages/master/Clients.tsx";
import { ClientDetail } from "./pages/master/ClientDetail.tsx";
import { Settings } from "./pages/master/Settings.tsx";
import { PaymentHistory } from "./pages/master/PaymentHistory.tsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function MasterLayout() {
  return (
    <div className="min-h-full flex flex-col bg-white pb-[calc(56px+16px+env(safe-area-inset-bottom,0px))]">
      <Outlet />
      <BottomTabBar />
    </div>
  );
}

/**
 * Role detector: auto-detects if user is a master or client on app load.
 * - Master with no ?master= param -> /master/dashboard
 * - Client or master with ?master= param -> /book/{masterId} or /my-bookings
 */
function RoleDetector() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const bridge = usePlatform();
  const role = useMasterAuth((s) => s.role);

  useEffect(() => {
    useMasterAuth.getState().autoDetectRole(bridge);
  }, [bridge]);

  useEffect(() => {
    if (role === "detecting") return;

    const masterId = searchParams.get("master");

    if (masterId) {
      // ?master= param present -- always go to booking flow (even if user is a master)
      navigate(`/book/${masterId}`, { replace: true });
      return;
    }

    if (role === "master") {
      navigate("/master/dashboard", { replace: true });
    } else {
      navigate("/my-bookings", { replace: true });
    }
  }, [role, searchParams, navigate]);

  if (role === "detecting") {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return null;
}

export default function App() {
  return (
    <PlatformProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter basename="/app">
          <div className="min-h-full flex flex-col bg-white">
            <Routes>
              {/* Client booking flow */}
              <Route path="/book/:masterId" element={<ServiceSelection />} />
              <Route path="/book/:masterId/date" element={<DatePicker />} />
              <Route path="/book/:masterId/time" element={<TimePicker />} />
              <Route path="/book/:masterId/info" element={<BookingForm />} />
              <Route path="/book/:masterId/confirm" element={<Confirmation />} />

              {/* Client bookings */}
              <Route path="/my-bookings" element={<MyBookings />} />

              {/* Master panel with bottom tab bar */}
              <Route path="/master" element={<MasterLayout />}>
                <Route index element={<Navigate to="/master/dashboard" replace />} />
                <Route path="dashboard" element={<Dashboard />} />
                <Route path="bookings" element={<Bookings />} />
                <Route path="services" element={<Services />} />
                <Route path="services/new" element={<ServiceForm />} />
                <Route path="services/:id" element={<ServiceForm />} />
                <Route path="schedule" element={<Schedule />} />
                <Route path="clients" element={<Clients />} />
                <Route path="clients/:id" element={<ClientDetail />} />
                <Route path="settings" element={<Settings />} />
                <Route path="payments" element={<PaymentHistory />} />
              </Route>

              {/* Root: auto-detect role and redirect */}
              <Route index element={<RoleDetector />} />

              {/* Fallback: also detect role for any unmatched route */}
              <Route path="*" element={<RoleDetector />} />
            </Routes>
          </div>
          <RoleSwitcher />
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </PlatformProvider>
  );
}

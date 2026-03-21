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
import { PlatformProvider } from "./platform/context.tsx";
import { ToastContainer } from "./components/ui/Toast.tsx";
import { useMasterAuth } from "./stores/master-auth.ts";
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
 * Entrypoint redirect: detects ?master=UUID query param (from TG bot WebAppInfo URL)
 * and redirects to the booking flow at /book/{masterId}.
 * Falls back to /my-bookings if no master param found.
 */
function EntryRedirect() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const masterId = searchParams.get("master");
    if (masterId) {
      navigate(`/book/${masterId}`, { replace: true });
    } else {
      navigate("/my-bookings", { replace: true });
    }
  }, [searchParams, navigate]);

  return null;
}

export default function App() {
  useEffect(() => {
    useMasterAuth.getState().hydrate();
  }, []);

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

              {/* Root: check ?master= query param, redirect to booking or my-bookings */}
              <Route index element={<EntryRedirect />} />

              {/* Fallback: also check query params for any unmatched route */}
              <Route path="*" element={<EntryRedirect />} />
            </Routes>
          </div>
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </PlatformProvider>
  );
}

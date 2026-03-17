import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { PlatformProvider } from "./platform/context.tsx";
import { ToastContainer } from "./components/ui/Toast.tsx";
import { ServiceSelection } from "./pages/client/ServiceSelection.tsx";
import { DatePicker } from "./pages/client/DatePicker.tsx";
import { TimePicker } from "./pages/client/TimePicker.tsx";
import { BookingForm } from "./pages/client/BookingForm.tsx";
import { Confirmation } from "./pages/client/Confirmation.tsx";
import { MyBookings } from "./pages/client/MyBookings.tsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default function App() {
  return (
    <PlatformProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
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

              {/* Master panel routes (Plan 04) */}
              {/* <Route path="/master/*" element={<MasterPanel />} /> */}

              {/* Default redirect */}
              <Route path="*" element={<Navigate to="/my-bookings" replace />} />
            </Routes>
          </div>
          <ToastContainer />
        </BrowserRouter>
      </QueryClientProvider>
    </PlatformProvider>
  );
}

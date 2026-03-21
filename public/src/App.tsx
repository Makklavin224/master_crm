import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import MasterPage from "./pages/MasterPage.tsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Placeholder pages — will be implemented in Plan 03
function BookingPage() {
  return <div className="p-4">Booking page</div>;
}

function BookingDatePage() {
  return <div className="p-4">Select date</div>;
}

function BookingTimePage() {
  return <div className="p-4">Select time</div>;
}

function BookingInfoPage() {
  return <div className="p-4">Your info</div>;
}

function BookingConfirmPage() {
  return <div className="p-4">Confirm booking</div>;
}

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full p-8 text-center">
      <h1 className="text-2xl font-bold text-text-primary mb-2">404</h1>
      <p className="text-text-secondary">Страница не найдена</p>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/m">
        <div className="min-h-full flex flex-col bg-white">
          <Routes>
            <Route path="/:username" element={<MasterPage />} />
            <Route path="/:username/book" element={<BookingPage />} />
            <Route path="/:username/book/date" element={<BookingDatePage />} />
            <Route path="/:username/book/time" element={<BookingTimePage />} />
            <Route path="/:username/book/info" element={<BookingInfoPage />} />
            <Route path="/:username/book/confirm" element={<BookingConfirmPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

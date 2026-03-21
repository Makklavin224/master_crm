import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import MasterPage from "./pages/MasterPage.tsx";
import ServiceStep from "./pages/booking/ServiceStep.tsx";
import DateStep from "./pages/booking/DateStep.tsx";
import TimeStep from "./pages/booking/TimeStep.tsx";
import InfoStep from "./pages/booking/InfoStep.tsx";
import ConfirmStep from "./pages/booking/ConfirmStep.tsx";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

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
            <Route path="/:username/book" element={<ServiceStep />} />
            <Route path="/:username/book/date" element={<DateStep />} />
            <Route path="/:username/book/time" element={<TimeStep />} />
            <Route path="/:username/book/info" element={<InfoStep />} />
            <Route path="/:username/book/confirm" element={<ConfirmStep />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

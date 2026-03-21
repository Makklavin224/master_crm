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

function ClientCabinetPlaceholder() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full p-8 text-center">
      <h1 className="text-2xl font-bold text-text-primary mb-2">Личный кабинет</h1>
      <p className="text-text-secondary">Скоро здесь появится ваш личный кабинет</p>
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename="/">
        <div className="min-h-full flex flex-col bg-white">
          <Routes>
            {/* Master public pages */}
            <Route path="/m/:username" element={<MasterPage />} />
            <Route path="/m/:username/book" element={<ServiceStep />} />
            <Route path="/m/:username/book/date" element={<DateStep />} />
            <Route path="/m/:username/book/time" element={<TimeStep />} />
            <Route path="/m/:username/book/info" element={<InfoStep />} />
            <Route path="/m/:username/book/confirm" element={<ConfirmStep />} />

            {/* Client cabinet (placeholder -- implemented in Plan 03) */}
            <Route path="/my" element={<ClientCabinetPlaceholder />} />
            <Route path="/my/*" element={<ClientCabinetPlaceholder />} />

            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

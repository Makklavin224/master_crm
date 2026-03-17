import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { StepIndicator } from "../../components/ui/StepIndicator.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { ServiceCard } from "../../components/ServiceCard.tsx";
import { useServices, type ServiceRead } from "../../api/services.ts";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { usePlatform } from "../../platform/context.tsx";
import { CalendarX } from "lucide-react";

export function ServiceSelection() {
  const { masterId } = useParams<{ masterId: string }>();
  const navigate = useNavigate();
  const platform = usePlatform();
  const { data: services, isLoading, error } = useServices(masterId);
  const { selectedService, setMasterId, selectService } = useBookingFlow();

  useEffect(() => {
    if (masterId) {
      setMasterId(masterId);
    }
  }, [masterId, setMasterId]);

  // Back button: close mini-app (first step)
  useEffect(() => {
    platform.hideBackButton();
    // On first step, back button closes the app
    // No back button shown on step 1
  }, [platform]);

  const handleSelect = (service: ServiceRead) => {
    platform.hapticFeedback("light");
    selectService(service);
    // Auto-advance after 300ms
    setTimeout(() => {
      navigate(`/book/${masterId}/date`);
    }, 300);
  };

  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={1} />
      <div className="px-4 pt-2 pb-8 flex-1">
        <h1 className="text-[20px] font-semibold text-text-primary mb-6">
          Выберите услугу
        </h1>

        {isLoading && (
          <div className="flex flex-col gap-3">
            <Skeleton height="80px" className="w-full" />
            <Skeleton height="80px" className="w-full" />
            <Skeleton height="80px" className="w-full" />
          </div>
        )}

        {error && (
          <EmptyState
            icon={<CalendarX className="w-12 h-12" />}
            heading="Не удалось загрузить услуги"
            body="Что-то пошло не так. Попробуйте позже."
          />
        )}

        {!isLoading && !error && services?.length === 0 && (
          <EmptyState
            icon={<CalendarX className="w-12 h-12" />}
            heading="Услуг пока нет"
            body="Мастер ещё не добавил услуги. Попробуйте позже."
          />
        )}

        {!isLoading && services && services.length > 0 && (
          <div className="flex flex-col gap-3">
            {services
              .filter((s) => s.is_active)
              .sort((a, b) => a.sort_order - b.sort_order)
              .map((service) => (
                <ServiceCard
                  key={service.id}
                  emoji={service.category || "\u2728"}
                  name={service.name}
                  durationMinutes={service.duration_minutes}
                  priceKopecks={service.price}
                  selected={selectedService?.id === service.id}
                  onClick={() => handleSelect(service)}
                />
              ))}
          </div>
        )}
      </div>
    </div>
  );
}

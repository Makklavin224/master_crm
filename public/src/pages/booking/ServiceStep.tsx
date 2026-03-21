import { useEffect } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import BookingStepIndicator from "../../components/BookingStepIndicator.tsx";
import { useMasterProfile, useMasterServices } from "../../api/master.ts";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import type { ServiceRead } from "../../api/types.ts";
import { ChevronLeft, Loader2, CalendarX } from "lucide-react";

function formatPrice(kopecks: number): string {
  const rubles = Math.floor(kopecks / 100);
  return rubles.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0") + " \u20BD";
}

function formatDuration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hours > 0 && mins > 0) return `${hours} ч ${mins} мин`;
  if (hours > 0) return `${hours} ч`;
  return `${mins} мин`;
}

export default function ServiceStep() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const { data: profile } = useMasterProfile(username || "");
  const { data: services, isLoading, error } = useMasterServices(username || "");
  const { selectedService, setMaster, selectService } = useBookingFlow();

  // Initialize master info
  useEffect(() => {
    if (username && profile?.id) {
      setMaster(username, profile.id);
    }
  }, [username, profile?.id, setMaster]);

  // Auto-select service from URL query param (?service=UUID)
  useEffect(() => {
    const serviceId = searchParams.get("service");
    if (serviceId && services && profile?.id && username) {
      const service = services.find((s) => s.id === serviceId);
      if (service) {
        setMaster(username, profile.id);
        selectService(service);
        navigate(`/${username}/book/date`, { replace: true });
      }
    }
  }, [searchParams, services, profile?.id, username, setMaster, selectService, navigate]);

  const handleSelect = (service: ServiceRead) => {
    selectService(service);
    setTimeout(() => {
      navigate(`/${username}/book/date`);
    }, 300);
  };

  const activeServices = services
    ?.filter((s) => s.is_active)
    .sort((a, b) => a.sort_order - b.sort_order);

  return (
    <div className="flex flex-col min-h-full">
      <BookingStepIndicator currentStep={1} />
      <div className="px-4 pt-2 pb-8 flex-1">
        {/* Back to master page */}
        <button
          onClick={() => navigate(`/${username}`)}
          className="flex items-center gap-1 text-sm text-text-secondary mb-4 active:opacity-70"
        >
          <ChevronLeft size={18} />
          <span>Назад</span>
        </button>

        <h1 className="text-[20px] font-semibold text-text-primary mb-6">
          Выберите услугу
        </h1>

        {isLoading && (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center py-12 text-center">
            <CalendarX className="w-12 h-12 text-text-secondary mb-3" />
            <p className="text-text-secondary">
              Не удалось загрузить услуги. Попробуйте позже.
            </p>
          </div>
        )}

        {!isLoading && !error && activeServices?.length === 0 && (
          <div className="flex flex-col items-center py-12 text-center">
            <CalendarX className="w-12 h-12 text-text-secondary mb-3" />
            <p className="text-text-primary font-medium mb-1">Услуг пока нет</p>
            <p className="text-text-secondary text-sm">
              Мастер ещё не добавил услуги. Попробуйте позже.
            </p>
          </div>
        )}

        {!isLoading && activeServices && activeServices.length > 0 && (
          <div className="flex flex-col gap-3">
            {activeServices.map((service) => (
              <button
                key={service.id}
                onClick={() => handleSelect(service)}
                className={`w-full text-left rounded-xl border p-4 transition-colors active:bg-surface ${
                  selectedService?.id === service.id
                    ? "border-accent bg-accent-light"
                    : "border-border bg-white"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-lg">{service.category || "\u2728"}</span>
                      <span className="font-medium text-text-primary truncate">
                        {service.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-sm text-text-secondary">
                      <span>{formatDuration(service.duration_minutes)}</span>
                    </div>
                  </div>
                  <span className="font-semibold text-accent whitespace-nowrap">
                    {formatPrice(service.price)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

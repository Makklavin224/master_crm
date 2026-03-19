import { useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { StepIndicator } from "../../components/ui/StepIndicator.tsx";
import { Card } from "../../components/ui/Card.tsx";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { usePlatform } from "../../platform/context.tsx";
import { formatDate, formatTime, formatPrice } from "../../lib/format.ts";
import { Check } from "lucide-react";

export function Confirmation() {
  const navigate = useNavigate();
  const platform = usePlatform();
  const { bookingResult, selectedService, selectedDate, selectedTime, reset } =
    useBookingFlow();

  // Redirect if no booking result
  useEffect(() => {
    if (!bookingResult) {
      navigate("/my-bookings");
    }
  }, [bookingResult, navigate]);

  // Haptic on mount
  useEffect(() => {
    platform.hapticFeedback("medium");
  }, [platform]);

  // Back button: close mini-app
  useEffect(() => {
    platform.showBackButton();
    const cleanup = platform.onBackButtonClick(() => {
      reset();
      platform.close();
    });
    return () => {
      cleanup();
      platform.hideBackButton();
    };
  }, [platform, reset]);

  if (!bookingResult) return null;

  const serviceName = selectedService?.name || bookingResult.service_name;
  const dateStr = selectedDate
    ? formatDate(selectedDate)
    : formatDate(bookingResult.starts_at);
  const timeStr = selectedTime
    ? formatTime(selectedTime)
    : formatTime(
        new Date(bookingResult.starts_at).toLocaleTimeString("ru-RU", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      );

  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={5} />
      <div className="px-4 pt-8 pb-8 flex-1 flex flex-col items-center">
        {/* Checkmark animation */}
        <div className="animate-scale-in w-16 h-16 rounded-full bg-success flex items-center justify-center mb-6">
          <Check className="w-8 h-8 text-white" strokeWidth={3} />
        </div>

        <h1 className="text-[24px] font-semibold text-text-primary mb-2">
          Вы записаны!
        </h1>

        <p className="text-[14px] text-text-secondary text-center mb-6">
          {serviceName}, {dateStr} в {timeStr}.
          <br />
          Мастер получил уведомление.
        </p>

        <Card className="w-full mb-6 animate-slide-up">
          <div className="flex flex-col gap-2">
            <div className="flex justify-between">
              <span className="text-[14px] text-text-secondary">Услуга</span>
              <span className="text-[14px] font-semibold text-text-primary">
                {serviceName}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[14px] text-text-secondary">Дата</span>
              <span className="text-[14px] font-semibold text-text-primary">
                {dateStr}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[14px] text-text-secondary">Время</span>
              <span className="text-[14px] font-semibold text-text-primary">
                {timeStr}
              </span>
            </div>
            {selectedService && (
              <div className="flex justify-between">
                <span className="text-[14px] text-text-secondary">
                  Стоимость
                </span>
                <span className="text-[14px] font-semibold text-text-primary">
                  {formatPrice(selectedService.price)}
                </span>
              </div>
            )}
          </div>
        </Card>

        <Link
          to="/my-bookings"
          onClick={() => reset()}
          className="text-[14px] font-semibold text-accent"
        >
          Мои записи
        </Link>
      </div>
    </div>
  );
}

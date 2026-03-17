import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { StepIndicator } from "../../components/ui/StepIndicator.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { SlotGrid } from "../../components/SlotGrid.tsx";
import { useAvailableSlots } from "../../api/schedule.ts";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { usePlatform } from "../../platform/context.tsx";
import { formatDate } from "../../lib/format.ts";
import { Clock } from "lucide-react";

export function TimePicker() {
  const { masterId } = useParams<{ masterId: string }>();
  const navigate = useNavigate();
  const platform = usePlatform();
  const { selectedService, selectedDate, selectedTime, selectTime, goToStep } =
    useBookingFlow();

  const { data, isLoading, error } = useAvailableSlots(
    masterId,
    selectedDate,
    selectedService?.id ?? null,
  );

  // Redirect if no service or date selected
  useEffect(() => {
    if (!selectedService) {
      navigate(`/book/${masterId}`);
    } else if (!selectedDate) {
      navigate(`/book/${masterId}/date`);
    }
  }, [selectedService, selectedDate, navigate, masterId]);

  // Back button: go to step 2
  useEffect(() => {
    platform.showBackButton();
    const cleanup = platform.onBackButtonClick(() => {
      navigate(`/book/${masterId}/date`);
    });
    return () => {
      cleanup();
      platform.hideBackButton();
    };
  }, [platform, navigate, masterId]);

  const handleSelectTime = (time: string) => {
    platform.hapticFeedback("light");
    selectTime(time);
  };

  const handleNext = () => {
    goToStep(4);
    navigate(`/book/${masterId}/info`);
  };

  const formattedDate = selectedDate ? formatDate(selectedDate) : "";

  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={3} />
      <div className="px-4 pt-2 pb-32 flex-1">
        <h1 className="text-[20px] font-semibold text-text-primary mb-1">
          Выберите время
        </h1>
        {selectedDate && (
          <p className="text-[14px] text-text-secondary mb-6">{formattedDate}</p>
        )}

        {isLoading && (
          <div className="grid grid-cols-3 gap-2">
            {Array.from({ length: 9 }).map((_, i) => (
              <Skeleton key={i} height="48px" className="w-full" />
            ))}
          </div>
        )}

        {error && (
          <EmptyState
            icon={<Clock className="w-12 h-12" />}
            heading="Не удалось загрузить время"
            body="Что-то пошло не так. Попробуйте позже."
          />
        )}

        {!isLoading && !error && data?.slots.length === 0 && (
          <EmptyState
            icon={<Clock className="w-12 h-12" />}
            heading="Нет свободного времени"
            body={`На ${formattedDate} все слоты заняты. Выберите другой день.`}
            action={
              <Button
                variant="secondary"
                fullWidth={false}
                onClick={() => navigate(`/book/${masterId}/date`)}
              >
                Выбрать другой день
              </Button>
            }
          />
        )}

        {!isLoading && data && data.slots.length > 0 && (
          <SlotGrid
            slots={data.slots}
            selectedTime={selectedTime}
            onSelect={handleSelectTime}
          />
        )}
      </div>

      {/* Fixed bottom CTA */}
      {selectedTime && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-border p-4 pb-[calc(16px+env(safe-area-inset-bottom))]">
          <Button onClick={handleNext}>Далее</Button>
        </div>
      )}
    </div>
  );
}

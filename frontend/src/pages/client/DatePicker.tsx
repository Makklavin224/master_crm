import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { DayPicker } from "react-day-picker";
import { ru } from "react-day-picker/locale";
import "react-day-picker/style.css";
import { StepIndicator } from "../../components/ui/StepIndicator.tsx";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { usePlatform } from "../../platform/context.tsx";

export function DatePicker() {
  const { masterId } = useParams<{ masterId: string }>();
  const navigate = useNavigate();
  const platform = usePlatform();
  const { selectedDate, selectDate } = useBookingFlow();
  const [selected, setSelected] = useState<Date | undefined>(
    selectedDate ? new Date(selectedDate + "T00:00:00") : undefined,
  );

  // Back button: go to step 1
  useEffect(() => {
    platform.showBackButton();
    const cleanup = platform.onBackButtonClick(() => {
      navigate(`/book/${masterId}`);
    });
    return () => {
      cleanup();
      platform.hideBackButton();
    };
  }, [platform, navigate, masterId]);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const handleSelect = (date: Date | undefined) => {
    if (!date) return;
    setSelected(date);
    platform.hapticFeedback("light");

    // Format to YYYY-MM-DD
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const dateStr = `${year}-${month}-${day}`;

    selectDate(dateStr);
    // Auto-advance to time picker
    navigate(`/book/${masterId}/time`);
  };

  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={2} />
      <div className="px-4 pt-2 pb-8 flex-1">
        <h1 className="text-[20px] font-semibold text-text-primary mb-6">
          Выберите дату
        </h1>

        <div className="flex justify-center">
          <DayPicker
            mode="single"
            selected={selected}
            onSelect={handleSelect}
            locale={ru}
            weekStartsOn={1}
            disabled={{ before: today }}
            modifiersClassNames={{
              selected: "!bg-accent !text-white !rounded-full",
              today: "!text-accent !font-semibold",
              disabled: "!text-gray-300 !pointer-events-none",
            }}
            className="!font-sans"
          />
        </div>
      </div>
    </div>
  );
}

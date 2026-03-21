import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BookingStepIndicator from "../../components/BookingStepIndicator.tsx";
import { useMasterSlots } from "../../api/master.ts";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { ChevronLeft, Clock, Loader2 } from "lucide-react";

const RUSSIAN_MONTHS = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];

const RUSSIAN_WEEKDAYS = [
  "Воскресенье", "Понедельник", "Вторник", "Среда",
  "Четверг", "Пятница", "Суббота",
];

function formatDateLong(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  const weekday = RUSSIAN_WEEKDAYS[d.getDay()];
  const day = d.getDate();
  const month = RUSSIAN_MONTHS[d.getMonth()];
  return `${weekday}, ${day} ${month}`;
}

/** Trim seconds from "HH:MM:SS" to "HH:MM" */
function trimTime(time: string): string {
  return time.slice(0, 5);
}

export default function TimeStep() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const { selectedService, selectedDate, selectedTime, selectTime, goToStep } =
    useBookingFlow();

  const { data, isLoading, error } = useMasterSlots(
    username || "",
    selectedDate || "",
    selectedService?.id || "",
  );

  // Redirect if prerequisites missing
  useEffect(() => {
    if (!selectedService) {
      navigate(`/m/${username}/book`, { replace: true });
    } else if (!selectedDate) {
      navigate(`/m/${username}/book/date`, { replace: true });
    }
  }, [selectedService, selectedDate, navigate, username]);

  const handleSelectTime = (time: string) => {
    selectTime(time);
  };

  const handleNext = () => {
    goToStep(4);
    navigate(`/m/${username}/book/info`);
  };

  const formattedDate = selectedDate ? formatDateLong(selectedDate) : "";

  return (
    <div className="flex flex-col min-h-full">
      <BookingStepIndicator currentStep={3} />
      <div className="px-4 pt-2 pb-32 flex-1">
        <button
          onClick={() => navigate(`/m/${username}/book/date`)}
          className="flex items-center gap-1 text-sm text-text-secondary mb-4 active:opacity-70"
        >
          <ChevronLeft size={18} />
          <span>Назад</span>
        </button>

        <h1 className="text-[20px] font-semibold text-text-primary mb-1">
          Выберите время
        </h1>
        {selectedDate && (
          <p className="text-sm text-text-secondary mb-6">{formattedDate}</p>
        )}

        {isLoading && (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 text-accent animate-spin" />
          </div>
        )}

        {error && (
          <div className="flex flex-col items-center py-12 text-center">
            <Clock className="w-12 h-12 text-text-secondary mb-3" />
            <p className="text-text-secondary">
              Не удалось загрузить время. Попробуйте позже.
            </p>
          </div>
        )}

        {!isLoading && !error && data?.slots.length === 0 && (
          <div className="flex flex-col items-center py-12 text-center">
            <Clock className="w-12 h-12 text-text-secondary mb-3" />
            <p className="text-text-primary font-medium mb-1">
              Нет свободных окошек
            </p>
            <p className="text-text-secondary text-sm mb-4">
              На этот день все слоты заняты.
            </p>
            <button
              onClick={() => navigate(`/m/${username}/book/date`)}
              className="text-sm font-medium text-accent active:opacity-70"
            >
              Выбрать другую дату
            </button>
          </div>
        )}

        {!isLoading && data && data.slots.length > 0 && (
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
            {data.slots.map((slot) => {
              const time = trimTime(slot.time);
              const isSelected = selectedTime === time;

              return (
                <button
                  key={slot.time}
                  onClick={() => handleSelectTime(time)}
                  className={`rounded-xl py-3 text-center font-medium transition-colors active:opacity-80 ${
                    isSelected
                      ? "bg-accent text-white"
                      : "border border-border bg-white text-text-primary hover:bg-surface"
                  }`}
                >
                  {time}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Fixed bottom CTA */}
      {selectedTime && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-border p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
          <button
            onClick={handleNext}
            className="w-full bg-accent text-white rounded-xl py-3.5 font-semibold text-base active:opacity-90 transition-opacity"
          >
            Далее
          </button>
        </div>
      )}
    </div>
  );
}

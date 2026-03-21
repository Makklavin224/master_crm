import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BookingStepIndicator from "../../components/BookingStepIndicator.tsx";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { ChevronLeft } from "lucide-react";

const RUSSIAN_WEEKDAYS_SHORT = ["вс", "пн", "вт", "ср", "чт", "пт", "сб"];
const RUSSIAN_MONTHS_SHORT = [
  "янв", "фев", "мар", "апр", "мая", "июн",
  "июл", "авг", "сен", "окт", "ноя", "дек",
];

function generateDates(count: number): Date[] {
  const dates: Date[] = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  for (let i = 0; i < count; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    dates.push(d);
  }
  return dates;
}

function toDateString(d: Date): string {
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export default function DateStep() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const { selectedService, selectedDate, selectDate } = useBookingFlow();

  // Redirect if no service selected
  useEffect(() => {
    if (!selectedService) {
      navigate(`/${username}/book`, { replace: true });
    }
  }, [selectedService, navigate, username]);

  const dates = generateDates(14);

  const handleSelect = (date: Date) => {
    const dateStr = toDateString(date);
    selectDate(dateStr);
    setTimeout(() => {
      navigate(`/${username}/book/time`);
    }, 300);
  };

  return (
    <div className="flex flex-col min-h-full">
      <BookingStepIndicator currentStep={2} />
      <div className="px-4 pt-2 pb-8 flex-1">
        <button
          onClick={() => navigate(`/${username}/book`)}
          className="flex items-center gap-1 text-sm text-text-secondary mb-4 active:opacity-70"
        >
          <ChevronLeft size={18} />
          <span>Назад</span>
        </button>

        <h1 className="text-[20px] font-semibold text-text-primary mb-6">
          Выберите дату
        </h1>

        <div className="grid grid-cols-4 gap-2 sm:grid-cols-5">
          {dates.map((date) => {
            const dateStr = toDateString(date);
            const isSelected = selectedDate === dateStr;
            const isToday = toDateString(new Date()) === dateStr;

            return (
              <button
                key={dateStr}
                onClick={() => handleSelect(date)}
                className={`flex flex-col items-center rounded-xl py-3 px-2 transition-colors active:opacity-80 ${
                  isSelected
                    ? "bg-accent text-white"
                    : "border border-border bg-white text-text-primary hover:bg-surface"
                }`}
              >
                <span
                  className={`text-xs uppercase font-medium ${
                    isSelected ? "text-white/80" : "text-text-secondary"
                  }`}
                >
                  {RUSSIAN_WEEKDAYS_SHORT[date.getDay()]}
                </span>
                <span className="text-lg font-semibold">{date.getDate()}</span>
                <span
                  className={`text-xs ${
                    isSelected ? "text-white/80" : "text-text-secondary"
                  }`}
                >
                  {RUSSIAN_MONTHS_SHORT[date.getMonth()]}
                </span>
                {isToday && !isSelected && (
                  <div className="w-1 h-1 rounded-full bg-accent mt-1" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

import { useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BookingStepIndicator from "../../components/BookingStepIndicator.tsx";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { CheckCircle } from "lucide-react";

const RUSSIAN_MONTHS = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];

function formatDateLong(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  const day = d.getDate();
  const month = RUSSIAN_MONTHS[d.getMonth()];
  const year = d.getFullYear();
  return `${day} ${month} ${year}`;
}

function formatPrice(kopecks: number): string {
  const rubles = Math.floor(kopecks / 100);
  return rubles.toString().replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0") + " \u20BD";
}

export default function ConfirmStep() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const { bookingResult, selectedService, selectedDate, selectedTime, reset } =
    useBookingFlow();

  // Redirect if no booking result
  useEffect(() => {
    if (!bookingResult) {
      navigate(`/${username}`, { replace: true });
    }
  }, [bookingResult, navigate, username]);

  if (!bookingResult) return null;

  const serviceName = selectedService?.name || bookingResult.service_name;
  const dateStr = selectedDate
    ? formatDateLong(selectedDate)
    : formatDateLong(bookingResult.starts_at.split("T")[0]);
  const timeStr = selectedTime || bookingResult.starts_at.split("T")[1]?.slice(0, 5) || "";

  const handleReturn = () => {
    reset();
    navigate(`/${username}`);
  };

  return (
    <div className="flex flex-col min-h-full">
      <BookingStepIndicator currentStep={5} />
      <div className="px-4 pt-8 pb-8 flex-1 flex flex-col items-center">
        {/* Success icon */}
        <div className="w-16 h-16 rounded-full bg-success flex items-center justify-center mb-6">
          <CheckCircle className="w-8 h-8 text-white" strokeWidth={2.5} />
        </div>

        <h1 className="text-2xl font-semibold text-text-primary mb-2">
          Вы записаны!
        </h1>

        <p className="text-sm text-text-secondary text-center mb-6">
          {serviceName}, {dateStr} в {timeStr}.
          <br />
          Мастер получил уведомление.
        </p>

        {/* Summary card */}
        <div className="w-full rounded-xl border border-border p-4 mb-6">
          <div className="flex flex-col gap-2">
            <div className="flex justify-between">
              <span className="text-sm text-text-secondary">Услуга</span>
              <span className="text-sm font-semibold text-text-primary">
                {serviceName}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-text-secondary">Дата</span>
              <span className="text-sm font-semibold text-text-primary">
                {dateStr}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-text-secondary">Время</span>
              <span className="text-sm font-semibold text-text-primary">
                {timeStr}
              </span>
            </div>
            {selectedService && (
              <div className="flex justify-between">
                <span className="text-sm text-text-secondary">Стоимость</span>
                <span className="text-sm font-semibold text-text-primary">
                  {formatPrice(selectedService.price)}
                </span>
              </div>
            )}
          </div>
        </div>

        <button
          onClick={handleReturn}
          className="text-sm font-semibold text-accent active:opacity-70"
        >
          Вернуться к мастеру
        </button>
      </div>
    </div>
  );
}

import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import "dayjs/locale/ru";
import type { ClientBookingRead } from "../api/types.ts";

dayjs.locale("ru");

const STATUS_MAP: Record<string, { label: string; className: string }> = {
  confirmed: {
    label: "Подтверждена",
    className: "bg-green-100 text-green-700",
  },
  completed: {
    label: "Завершена",
    className: "bg-blue-100 text-blue-700",
  },
  cancelled_by_client: {
    label: "Отменена",
    className: "bg-gray-100 text-gray-500",
  },
  cancelled_by_master: {
    label: "Отменена",
    className: "bg-gray-100 text-gray-500",
  },
  no_show: {
    label: "Неявка",
    className: "bg-red-100 text-red-600",
  },
};

interface BookingCardProps {
  booking: ClientBookingRead;
  type: "upcoming" | "past";
  onReview: (bookingId: string) => void;
  onCancel: (bookingId: string) => void;
  onReschedule: (bookingId: string) => void;
  isReviewing?: boolean;
  isCancelling?: boolean;
}

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((part) => part.charAt(0))
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

export default function BookingCard({
  booking,
  type,
  onReview,
  onCancel,
  onReschedule,
  isCancelling,
}: BookingCardProps) {
  const navigate = useNavigate();
  const status = STATUS_MAP[booking.status] || {
    label: booking.status,
    className: "bg-gray-100 text-gray-500",
  };

  const start = dayjs(booking.starts_at);
  const end = dayjs(booking.ends_at);
  const dateStr =
    start.format("D MMMM, dd").charAt(0).toUpperCase() +
    start.format("D MMMM, dd").slice(1);
  const timeStr = `${start.format("HH:mm")} \u2013 ${end.format("HH:mm")}`;

  const handleMasterClick = () => {
    if (booking.master_username) {
      navigate(`/m/${booking.master_username}`);
    }
  };

  const handleRebook = () => {
    if (booking.master_username) {
      navigate(
        `/m/${booking.master_username}/book?service=${booking.service_id}`,
      );
    }
  };

  return (
    <div className="rounded-2xl border border-gray-100 shadow-sm p-4">
      {/* Top row: master + service */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-accent/10 flex items-center justify-center text-sm font-semibold text-accent shrink-0">
          {getInitials(booking.master_name)}
        </div>
        <div className="min-w-0 flex-1">
          <button
            onClick={handleMasterClick}
            className="text-sm font-semibold text-text-primary hover:text-accent transition-colors text-left truncate block"
          >
            {booking.master_name}
          </button>
          <p className="text-sm text-text-secondary truncate">
            {booking.service_name}
          </p>
        </div>
        <span
          className={`text-xs font-medium px-2.5 py-1 rounded-full shrink-0 ${status.className}`}
        >
          {status.label}
        </span>
      </div>

      {/* Date/time */}
      <p className="text-sm text-text-primary mb-3">
        {dateStr} &middot; {timeStr}
      </p>

      {/* Actions */}
      <div className="flex gap-2">
        {type === "upcoming" && booking.status === "confirmed" && (
          <>
            <button
              onClick={() => onReschedule(booking.id)}
              className="flex-1 py-2 px-3 text-sm font-medium rounded-xl border border-border text-text-primary active:opacity-70 transition-opacity"
            >
              Перенести
            </button>
            <button
              onClick={() => onCancel(booking.id)}
              disabled={isCancelling}
              className="flex-1 py-2 px-3 text-sm font-medium rounded-xl border border-destructive/30 text-destructive active:opacity-70 transition-opacity disabled:opacity-60"
            >
              {isCancelling ? "Отмена..." : "Отменить"}
            </button>
          </>
        )}

        {type === "past" && booking.status === "completed" && (
          <>
            <button
              onClick={handleRebook}
              className="flex-1 py-2 px-3 text-sm font-medium rounded-xl bg-accent text-white active:opacity-90 transition-opacity"
            >
              Записаться снова
            </button>
            <button
              onClick={() => onReview(booking.id)}
              className="flex-1 py-2 px-3 text-sm font-medium rounded-xl border border-accent/30 text-accent active:opacity-70 transition-opacity"
            >
              Оставить отзыв
            </button>
          </>
        )}
      </div>
    </div>
  );
}

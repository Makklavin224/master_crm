import { Card } from "./ui/Card.tsx";
import { Badge } from "./ui/Badge.tsx";
import { formatDate, formatTime } from "../lib/format.ts";

type BookingStatus = "confirmed" | "pending" | "cancelled" | "completed";

interface BookingCardProps {
  serviceName: string;
  clientName?: string;
  startsAt: string;
  status: BookingStatus;
  action?: React.ReactNode;
}

const statusLabels: Record<BookingStatus, string> = {
  confirmed: "Подтверждена",
  pending: "Ожидает",
  cancelled: "Отменена",
  completed: "Завершена",
};

const statusVariant: Record<BookingStatus, "confirmed" | "pending" | "cancelled"> = {
  confirmed: "confirmed",
  pending: "pending",
  cancelled: "cancelled",
  completed: "confirmed",
};

export function BookingCard({
  serviceName,
  clientName,
  startsAt,
  status,
  action,
}: BookingCardProps) {
  const date = new Date(startsAt);
  const timeStr = date.toLocaleTimeString("ru-RU", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <Card className="flex flex-col gap-2">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="text-[16px] font-semibold text-text-primary">
            {formatTime(timeStr)}
            {clientName && (
              <span className="font-normal text-text-secondary">
                {" "}&middot; {clientName}
              </span>
            )}
          </div>
          <div className="text-[14px] text-text-secondary mt-0.5">
            {serviceName}
          </div>
          <div className="text-[12px] text-text-secondary mt-0.5">
            {formatDate(date)}
          </div>
        </div>
        <Badge variant={statusVariant[status]}>{statusLabels[status]}</Badge>
      </div>
      {action && <div className="mt-1">{action}</div>}
    </Card>
  );
}

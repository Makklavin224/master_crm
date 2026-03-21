import dayjs from "dayjs";
import "dayjs/locale/ru";
import { useMasterSlots } from "../api/master.ts";
import type { ServiceRead } from "../api/types.ts";

dayjs.locale("ru");

interface SlotsSectionProps {
  username: string;
  services: ServiceRead[];
  onSlotClick: (date: string, time: string) => void;
}

function formatSlotTime(time: string): string {
  // time is "HH:MM:SS" - display as "HH:MM"
  return time.slice(0, 5);
}

function DaySlots({
  username,
  date,
  serviceId,
  onSlotClick,
}: {
  username: string;
  date: string;
  serviceId: string;
  onSlotClick: (date: string, time: string) => void;
}) {
  const { data, isLoading } = useMasterSlots(username, date, serviceId);

  const dayLabel = dayjs(date).format("dd, D MMM");

  return (
    <div className="mb-3">
      <p className="text-caption font-medium text-text-secondary mb-1.5 capitalize">
        {dayLabel}
      </p>
      {isLoading ? (
        <div className="flex gap-2">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-8 w-16 rounded-lg bg-surface animate-pulse"
            />
          ))}
        </div>
      ) : !data || data.slots.length === 0 ? (
        <p className="text-caption text-text-secondary">Нет окошек</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {data.slots.slice(0, 4).map((slot) => (
            <button
              key={slot.time}
              onClick={() => onSlotClick(date, slot.time)}
              className="text-sm font-medium text-accent border border-accent/30 rounded-lg px-3 py-1.5 active:bg-accent/5 transition-colors"
            >
              {formatSlotTime(slot.time)}
            </button>
          ))}
          {data.slots.length > 4 && (
            <span className="text-caption text-text-secondary self-center">
              +{data.slots.length - 4}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

export default function SlotsSection({
  username,
  services,
  onSlotClick,
}: SlotsSectionProps) {
  if (services.length === 0) return null;

  const firstService = services[0];
  const dates: string[] = [];
  for (let i = 1; i <= 5; i++) {
    dates.push(dayjs().add(i, "day").format("YYYY-MM-DD"));
  }

  return (
    <section className="px-4 py-5">
      <h2 className="text-lg font-semibold text-text-primary mb-1">
        Ближайшие окошки
      </h2>
      {services.length > 1 && (
        <p className="text-caption text-text-secondary mb-3">
          Время зависит от услуги
        </p>
      )}

      <div className="mt-3">
        {dates.map((date) => (
          <DaySlots
            key={date}
            username={username}
            date={date}
            serviceId={firstService.id}
            onSlotClick={onSlotClick}
          />
        ))}
      </div>
    </section>
  );
}

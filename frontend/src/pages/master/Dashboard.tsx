import { CalendarDays, Share2 } from "lucide-react";
import { useMasterBookings } from "../../api/master-bookings.ts";
import { BookingCard } from "../../components/BookingCard.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { useToast } from "../../components/ui/Toast.tsx";

function getToday(): string {
  const d = new Date();
  return d.toISOString().split("T")[0];
}

export function Dashboard() {
  const today = getToday();
  const { data, isLoading } = useMasterBookings({
    date_from: today,
    date_to: today,
  });
  const toast = useToast();

  const bookings = data?.items ?? [];
  const sorted = [...bookings].sort(
    (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
  );

  const handleShare = async () => {
    const shareUrl = window.location.origin;
    try {
      await navigator.clipboard.writeText(shareUrl);
      toast.success("Ссылка скопирована");
    } catch {
      toast.info(shareUrl);
    }
  };

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4">
        <h1 className="text-[20px] font-semibold text-text-primary">Сегодня</h1>
      </div>

      <div className="flex-1 px-4 pb-4">
        {isLoading ? (
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="96px" className="w-full" />
            ))}
          </div>
        ) : sorted.length === 0 ? (
          <EmptyState
            icon={<CalendarDays className="w-12 h-12" />}
            heading="Сегодня записей нет"
            body="Отличный день, чтобы отдохнуть или принять новых клиентов."
          />
        ) : (
          <div className="flex flex-col gap-4">
            {sorted.map((booking) => (
              <BookingCard
                key={booking.id}
                serviceName={booking.service_name}
                clientName={booking.client_name}
                startsAt={booking.starts_at}
                status={booking.status}
              />
            ))}
          </div>
        )}
      </div>

      <div className="px-4 pb-6">
        <Button variant="secondary" onClick={handleShare} fullWidth>
          <Share2 className="w-4 h-4" />
          Поделиться ссылкой
        </Button>
      </div>
    </div>
  );
}

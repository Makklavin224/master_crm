import { useEffect, useState } from "react";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { BookingCard } from "../../components/BookingCard.tsx";
import { useMyBookings, useCancelBooking } from "../../api/bookings.ts";
import { usePlatform } from "../../platform/context.tsx";
import { useToast } from "../../components/ui/Toast.tsx";
import { formatDate, formatTime } from "../../lib/format.ts";
import { CalendarDays } from "lucide-react";

export function MyBookings() {
  const platform = usePlatform();
  const toast = useToast();
  const userId = platform.getUserId();
  const initDataRaw = platform.getInitDataRaw();
  const { data: bookings, isLoading, error } = useMyBookings(userId, initDataRaw);
  const cancelBooking = useCancelBooking();

  const [confirmCancelId, setConfirmCancelId] = useState<string | null>(null);

  // Back button: close mini-app
  useEffect(() => {
    platform.showBackButton();
    const cleanup = platform.onBackButtonClick(() => {
      platform.close();
    });
    return () => {
      cleanup();
      platform.hideBackButton();
    };
  }, [platform]);

  const handleCancel = async (bookingId: string) => {
    try {
      await cancelBooking.mutateAsync({
        bookingId,
        initDataRaw,
      });
      toast.success("Запись отменена");
      setConfirmCancelId(null);
    } catch {
      toast.error("Что-то пошло не так. Попробуйте позже.");
    }
  };

  const bookingForCancel = bookings?.find((b) => b.id === confirmCancelId);

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-6 pb-8">
        <h1 className="text-[20px] font-semibold text-text-primary mb-4">
          Мои записи
        </h1>

        {isLoading && (
          <div className="flex flex-col gap-3">
            <Skeleton height="100px" className="w-full" />
            <Skeleton height="100px" className="w-full" />
          </div>
        )}

        {error && (
          <EmptyState
            icon={<CalendarDays className="w-12 h-12" />}
            heading="Не удалось загрузить записи"
            body="Что-то пошло не так. Попробуйте позже."
          />
        )}

        {!isLoading && !error && bookings?.length === 0 && (
          <EmptyState
            icon={<CalendarDays className="w-12 h-12" />}
            heading="У вас пока нет записей"
            body="Выберите мастера и запишитесь на удобное время."
          />
        )}

        {!isLoading && bookings && bookings.length > 0 && (
          <div className="flex flex-col gap-3">
            {bookings
              .sort(
                (a, b) =>
                  new Date(b.starts_at).getTime() -
                  new Date(a.starts_at).getTime(),
              )
              .map((booking) => (
                <BookingCard
                  key={booking.id}
                  serviceName={booking.service_name}
                  startsAt={booking.starts_at}
                  status={booking.status}
                  action={
                    booking.status === "confirmed" ? (
                      <Button
                        variant="destructive"
                        fullWidth={false}
                        className="text-[12px] min-h-[44px] px-4"
                        onClick={() => setConfirmCancelId(booking.id)}
                      >
                        Отменить запись
                      </Button>
                    ) : undefined
                  }
                />
              ))}
          </div>
        )}
      </div>

      {/* Cancel confirmation dialog */}
      {confirmCancelId && bookingForCancel && (
        <div
          className="fixed inset-0 bg-black/50 z-50 flex items-end justify-center"
          onClick={() => setConfirmCancelId(null)}
        >
          <div
            className="bg-white rounded-t-[20px] w-full max-w-lg p-6 pb-[calc(24px+env(safe-area-inset-bottom))]"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-[16px] text-text-primary text-center mb-6">
              Отменить запись на{" "}
              {formatTime(
                new Date(bookingForCancel.starts_at).toLocaleTimeString(
                  "ru-RU",
                  { hour: "2-digit", minute: "2-digit" },
                ),
              )}{" "}
              {formatDate(bookingForCancel.starts_at)}?
              <br />
              <span className="text-text-secondary text-[14px]">
                Восстановить её будет нельзя.
              </span>
            </p>
            <div className="flex flex-col gap-2">
              <Button
                variant="destructive"
                onClick={() => handleCancel(confirmCancelId)}
                loading={cancelBooking.isPending}
              >
                Да, отменить
              </Button>
              <Button
                variant="secondary"
                onClick={() => setConfirmCancelId(null)}
              >
                Нет, оставить
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

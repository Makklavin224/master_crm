import { useState } from "react";
import { BookOpen } from "lucide-react";
import {
  useMasterBookings,
  useCancelBookingMaster,
  type MasterBookingRead,
} from "../../api/master-bookings.ts";
import { usePaymentSettings } from "../../api/master-settings.ts";
import { BookingCard } from "../../components/BookingCard.tsx";
import { ConfirmDialog } from "../../components/ConfirmDialog.tsx";
import { PaymentSheet } from "../../components/PaymentSheet.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { useToast } from "../../components/ui/Toast.tsx";

type StatusFilter = "all" | "confirmed" | "cancelled" | "completed";

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "Все" },
  { value: "confirmed", label: "Активные" },
  { value: "cancelled", label: "Отменённые" },
  { value: "completed", label: "Завершённые" },
];

export function Bookings() {
  const toast = useToast();
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [cancelTarget, setCancelTarget] = useState<{
    id: string;
    clientName: string;
    time: string;
  } | null>(null);
  const [paymentBooking, setPaymentBooking] =
    useState<MasterBookingRead | null>(null);

  const { data, isLoading, error } = useMasterBookings({
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    status: statusFilter === "all" ? undefined : statusFilter,
  });
  const cancelBooking = useCancelBookingMaster();
  const { data: paymentSettings } = usePaymentSettings();

  const bookings = data?.items ?? [];

  const hasRobokassa = paymentSettings?.has_robokassa ?? false;
  const hasRequisites = !!(
    paymentSettings?.card_number || paymentSettings?.sbp_phone
  );
  const hasSeenGreyWarning = paymentSettings?.has_seen_grey_warning ?? false;
  const defaultFiscalization =
    paymentSettings?.fiscalization_level ?? "none";

  const handleCancel = () => {
    if (!cancelTarget) return;
    cancelBooking.mutate(cancelTarget.id, {
      onSuccess: () => {
        toast.success("Запись отменена");
        setCancelTarget(null);
      },
      onError: () => {
        toast.error("Не удалось отменить запись");
        setCancelTarget(null);
      },
    });
  };

  const handlePaymentComplete = () => {
    setPaymentBooking(null);
    toast.success("Оплата зафиксирована");
  };

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Все записи
        </h1>
      </div>

      {/* Filters */}
      <div className="px-4 pb-3 flex flex-col gap-3">
        {/* Date range */}
        <div className="flex items-center gap-2">
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            placeholder="От"
            className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
          />
          <span className="text-text-secondary text-[14px]">&mdash;</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            placeholder="До"
            className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
          />
        </div>

        {/* Status pills */}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatusFilter(opt.value)}
              className={`h-[44px] px-4 rounded-full text-[14px] font-medium whitespace-nowrap border transition-colors ${
                statusFilter === opt.value
                  ? "bg-accent/8 border-accent text-accent"
                  : "border-border text-text-secondary hover:border-text-secondary"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Bookings list */}
      <div className="flex-1 px-4 pb-4" aria-live="polite">
        {isLoading ? (
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="96px" className="w-full" />
            ))}
          </div>
        ) : error ? (
          <EmptyState
            icon={<BookOpen className="w-12 h-12" />}
            heading="Не удалось загрузить записи"
            body="Проверьте соединение и попробуйте ещё раз."
          />
        ) : bookings.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="w-12 h-12" />}
            heading="Записей нет"
            body="Когда клиенты начнут записываться, вы увидите их здесь."
          />
        ) : (
          <div className="flex flex-col gap-4">
            {bookings.map((booking) => {
              const time = new Date(booking.starts_at).toLocaleTimeString(
                "ru-RU",
                { hour: "2-digit", minute: "2-digit" },
              );
              return (
                <BookingCard
                  key={booking.id}
                  serviceName={booking.service_name}
                  clientName={booking.client_name}
                  startsAt={booking.starts_at}
                  status={booking.status}
                  action={
                    booking.status === "confirmed" ? (
                      <div className="flex gap-2">
                        <Button
                          variant="primary"
                          fullWidth={false}
                          className="text-[12px] min-h-[44px] px-4"
                          onClick={() => setPaymentBooking(booking)}
                        >
                          Завершить
                        </Button>
                        <Button
                          variant="destructive"
                          fullWidth={false}
                          className="text-[12px] min-h-[44px] px-4"
                          onClick={() =>
                            setCancelTarget({
                              id: booking.id,
                              clientName: booking.client_name,
                              time,
                            })
                          }
                        >
                          Отменить
                        </Button>
                      </div>
                    ) : undefined
                  }
                />
              );
            })}
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!cancelTarget}
        title="Отменить запись?"
        message={`Отменить запись ${cancelTarget?.clientName} на ${cancelTarget?.time}? Клиент получит уведомление.`}
        confirmLabel="Отменить запись"
        cancelLabel="Назад"
        variant="destructive"
        onConfirm={handleCancel}
        onCancel={() => setCancelTarget(null)}
      />

      <PaymentSheet
        open={!!paymentBooking}
        booking={paymentBooking}
        hasRobokassa={hasRobokassa}
        hasRequisites={hasRequisites}
        hasSeenGreyWarning={hasSeenGreyWarning}
        defaultFiscalization={defaultFiscalization}
        onClose={() => setPaymentBooking(null)}
        onPaymentComplete={handlePaymentComplete}
      />
    </div>
  );
}

import { useState } from "react";
import { CreditCard } from "lucide-react";
import {
  usePaymentHistory,
  useReceiptData,
  type PaymentRead,
} from "../../api/payments.ts";
import { Card } from "../../components/ui/Card.tsx";
import { Badge } from "../../components/ui/Badge.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { ReceiptDataCard } from "../../components/ReceiptDataCard.tsx";
import { formatPrice } from "../../lib/format.ts";

type StatusFilter = "all" | "pending" | "paid" | "cancelled";

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "all", label: "Все" },
  { value: "pending", label: "Ожидает" },
  { value: "paid", label: "Оплачено" },
  { value: "cancelled", label: "Отменено" },
];

const STATUS_BADGE: Record<
  string,
  { variant: "confirmed" | "pending" | "cancelled"; label: string }
> = {
  pending: { variant: "pending", label: "Ожидает" },
  paid: { variant: "confirmed", label: "Оплачено" },
  cancelled: { variant: "cancelled", label: "Отменено" },
  refunded: { variant: "cancelled", label: "Возврат" },
};

const RECEIPT_BADGE: Record<string, { color: string; label: string }> = {
  issued: { color: "bg-emerald-50 text-emerald-700", label: "Чек: выдан" },
  pending: { color: "bg-amber-50 text-amber-700", label: "Чек: ожидает" },
  not_applicable: { color: "bg-gray-100 text-gray-500", label: "Нет чека" },
  none: { color: "bg-gray-100 text-gray-500", label: "Нет чека" },
};

const PAGE_SIZE = 20;

export function PaymentHistory() {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [selectedPaymentId, setSelectedPaymentId] = useState<string | null>(
    null,
  );

  const { data, isLoading } = usePaymentHistory({
    status: statusFilter === "all" ? undefined : statusFilter,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
    limit,
    offset: 0,
  });

  const { data: receiptData } = useReceiptData(selectedPaymentId);

  const payments = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasMore = payments.length < total;

  const handlePaymentTap = (payment: PaymentRead) => {
    if (
      payment.status === "paid" &&
      payment.fiscalization_level === "manual"
    ) {
      setSelectedPaymentId(payment.id);
    }
  };

  if (selectedPaymentId && receiptData) {
    return (
      <div className="flex flex-col min-h-full">
        <div className="px-4 pt-8 pb-4">
          <h1 className="text-[20px] font-semibold text-text-primary">
            Платежи
          </h1>
        </div>
        <div className="px-4 pb-4">
          <ReceiptDataCard
            data={receiptData}
            onClose={() => setSelectedPaymentId(null)}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Платежи
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
            className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
          />
          <span className="text-text-secondary text-[14px]">&mdash;</span>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary flex-1 outline-none focus:ring-2 focus:ring-accent/30"
          />
        </div>

        {/* Status pills */}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {STATUS_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => {
                setStatusFilter(opt.value);
                setLimit(PAGE_SIZE);
              }}
              className={`h-[36px] px-4 rounded-full text-[14px] font-medium whitespace-nowrap border transition-colors ${
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

      {/* Payment list */}
      <div className="flex-1 px-4 pb-4">
        {isLoading ? (
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="96px" className="w-full" />
            ))}
          </div>
        ) : payments.length === 0 ? (
          <EmptyState
            icon={<CreditCard className="w-12 h-12" />}
            heading="Платежей пока нет"
            body="Здесь будет история всех оплат"
          />
        ) : (
          <div className="flex flex-col gap-4">
            {payments.map((payment) => {
              const date = new Date(payment.created_at);
              const timeStr = date.toLocaleTimeString("ru-RU", {
                hour: "2-digit",
                minute: "2-digit",
              });
              const dateStr = date.toLocaleDateString("ru-RU", {
                day: "numeric",
                month: "short",
              });
              const statusBadge = STATUS_BADGE[payment.status] ??
                STATUS_BADGE.pending;
              const receiptBadge = RECEIPT_BADGE[payment.receipt_status] ??
                RECEIPT_BADGE.none;

              const isTappable =
                payment.status === "paid" &&
                payment.fiscalization_level === "manual";

              return (
                <button
                  key={payment.id}
                  onClick={() => handlePaymentTap(payment)}
                  disabled={!isTappable}
                  className={`w-full text-left ${isTappable ? "cursor-pointer" : "cursor-default"}`}
                >
                  <Card className="flex flex-col gap-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1 min-w-0">
                        <div className="text-[16px] font-semibold text-text-primary">
                          {payment.service_name}
                        </div>
                        <div className="text-[12px] text-text-secondary">
                          {payment.client_name}
                        </div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-[16px] font-semibold text-text-primary">
                          {formatPrice(payment.amount)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Badge variant={statusBadge.variant}>
                          {statusBadge.label}
                        </Badge>
                        <span
                          className={`rounded-full px-[6px] py-[1px] text-[10px] font-semibold ${receiptBadge.color}`}
                        >
                          {receiptBadge.label}
                        </span>
                      </div>
                      <span className="text-[12px] text-text-secondary whitespace-nowrap">
                        {dateStr}, {timeStr}
                      </span>
                    </div>
                  </Card>
                </button>
              );
            })}

            {/* Pagination */}
            {hasMore && (
              <Button
                variant="secondary"
                onClick={() => setLimit((l) => l + PAGE_SIZE)}
              >
                Показать ещё
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

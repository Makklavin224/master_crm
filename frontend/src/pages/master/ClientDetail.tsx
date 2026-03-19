import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, User } from "lucide-react";
import { useClientDetail } from "../../api/master-clients.ts";
import { BookingCard } from "../../components/BookingCard.tsx";
import { Card } from "../../components/ui/Card.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { formatDate } from "../../lib/format.ts";

function formatPhone(phone: string): string {
  if (phone.startsWith("+7") && phone.length === 12) {
    return `+7 (${phone.slice(2, 5)}) ${phone.slice(5, 8)}-${phone.slice(8, 10)}-${phone.slice(10)}`;
  }
  return phone;
}

export function ClientDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useClientDetail(id);

  return (
    <div className="flex flex-col min-h-full">
      {/* Header */}
      <div className="px-4 pt-8 pb-4 flex items-center gap-3">
        <button
          onClick={() => navigate("/master/clients")}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface transition-colors"
          aria-label="Назад"
        >
          <ArrowLeft className="w-5 h-5 text-text-primary" />
        </button>
        <h1 className="text-[20px] font-semibold text-text-primary truncate">
          {data?.client.name || "Клиент"}
        </h1>
      </div>

      <div className="flex-1 px-4 pb-4" aria-live="polite">
        {isLoading ? (
          <div className="flex flex-col gap-4">
            <Skeleton height="120px" className="w-full" />
            <Skeleton height="80px" className="w-full" />
            <Skeleton height="80px" className="w-full" />
          </div>
        ) : error ? (
          <EmptyState
            icon={<User className="w-12 h-12" />}
            heading="Не удалось загрузить данные клиента"
            body="Проверьте соединение и попробуйте ещё раз."
          />
        ) : data ? (
          <div className="flex flex-col gap-4">
            {/* Client info card */}
            <Card className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-accent/8 flex items-center justify-center shrink-0">
                  <User className="w-6 h-6 text-accent" />
                </div>
                <div>
                  <div className="text-[16px] font-semibold text-text-primary">
                    {data.client.name || "Без имени"}
                  </div>
                  <div className="text-[14px] text-text-secondary">
                    {formatPhone(data.client.phone)}
                  </div>
                </div>
              </div>

              {/* Visit stats */}
              <div className="grid grid-cols-3 gap-3 pt-3 border-t border-border">
                <div className="text-center">
                  <div className="text-[20px] font-semibold text-accent">
                    {data.visit_count}
                  </div>
                  <div className="text-[12px] text-text-secondary">Визитов</div>
                </div>
                <div className="text-center">
                  <div className="text-[14px] font-semibold text-text-primary">
                    {data.first_visit_at
                      ? formatDate(data.first_visit_at)
                      : "—"}
                  </div>
                  <div className="text-[12px] text-text-secondary">
                    Первый визит
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-[14px] font-semibold text-text-primary">
                    {data.last_visit_at
                      ? formatDate(data.last_visit_at)
                      : "—"}
                  </div>
                  <div className="text-[12px] text-text-secondary">
                    Последний визит
                  </div>
                </div>
              </div>
            </Card>

            {/* Booking history */}
            <h2 className="text-[16px] font-semibold text-text-primary">
              История записей
            </h2>
            {data.bookings.length === 0 ? (
              <p className="text-[14px] text-text-secondary text-center py-4">
                Нет записей
              </p>
            ) : (
              <div className="flex flex-col gap-3">
                {data.bookings.map((booking) => (
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
        ) : (
          <p className="text-[14px] text-text-secondary text-center py-8">
            Клиент не найден
          </p>
        )}
      </div>
    </div>
  );
}

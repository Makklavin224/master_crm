import { useNavigate } from "react-router-dom";
import { Users, ChevronRight } from "lucide-react";
import { useMasterClients } from "../../api/master-clients.ts";
import { Card } from "../../components/ui/Card.tsx";
import { Badge } from "../../components/ui/Badge.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { formatDate } from "../../lib/format.ts";

function formatPhone(phone: string): string {
  // Format E.164 phone: +79001234567 -> +7 (900) 123-45-67
  if (phone.startsWith("+7") && phone.length === 12) {
    return `+7 (${phone.slice(2, 5)}) ${phone.slice(5, 8)}-${phone.slice(8, 10)}-${phone.slice(10)}`;
  }
  return phone;
}

export function Clients() {
  const { data: clients, isLoading, error } = useMasterClients();
  const navigate = useNavigate();

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Клиенты
        </h1>
      </div>

      <div className="flex-1 px-4 pb-4" aria-live="polite">
        {isLoading ? (
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="72px" className="w-full" />
            ))}
          </div>
        ) : error ? (
          <EmptyState
            icon={<Users className="w-12 h-12" />}
            heading="Не удалось загрузить клиентов"
            body="Проверьте соединение и попробуйте ещё раз."
          />
        ) : !clients || clients.length === 0 ? (
          <EmptyState
            icon={<Users className="w-12 h-12" />}
            heading="Нет клиентов"
            body="Клиенты появятся автоматически после первой записи."
          />
        ) : (
          <div className="flex flex-col gap-3">
            {clients.map((item) => (
              <Card
                key={item.client.id}
                className="flex items-center gap-3 cursor-pointer active:bg-surface transition-colors"
                onClick={() => navigate(`/master/clients/${item.client.id}`)}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    navigate(`/master/clients/${item.client.id}`);
                  }
                }}
              >
                {/* Avatar placeholder */}
                <div className="w-10 h-10 rounded-full bg-accent/8 flex items-center justify-center shrink-0">
                  <span className="text-[16px] font-semibold text-accent">
                    {item.client.name?.charAt(0)?.toUpperCase() || "?"}
                  </span>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="text-[16px] font-semibold text-text-primary truncate">
                    {item.client.name || "Без имени"}
                  </div>
                  <div className="text-[12px] text-text-secondary">
                    {formatPhone(item.client.phone)}
                    {item.last_visit_at && (
                      <span>
                        {" "}&middot; Последний визит: {formatDate(item.last_visit_at)}
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <Badge variant="confirmed">
                    {item.visit_count} {getVisitWord(item.visit_count)}
                  </Badge>
                  <ChevronRight className="w-4 h-4 text-text-secondary" />
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function getVisitWord(count: number): string {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod100 >= 11 && mod100 <= 14) return "визитов";
  if (mod10 === 1) return "визит";
  if (mod10 >= 2 && mod10 <= 4) return "визита";
  return "визитов";
}

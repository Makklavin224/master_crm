import type { ServiceRead } from "../api/types.ts";

interface ServicesSectionProps {
  services: ServiceRead[];
  onBook: (serviceId: string) => void;
}

function formatPrice(kopecks: number): string {
  const rubles = kopecks / 100;
  return rubles % 1 === 0
    ? `${rubles.toLocaleString("ru-RU")} \u20BD`
    : `${rubles.toLocaleString("ru-RU", { minimumFractionDigits: 2 })} \u20BD`;
}

export default function ServicesSection({
  services,
  onBook,
}: ServicesSectionProps) {
  const sorted = [...services].sort((a, b) => a.sort_order - b.sort_order);

  return (
    <section className="px-4 py-5">
      <h2 className="text-lg font-semibold text-text-primary mb-3">Услуги</h2>

      {sorted.length === 0 ? (
        <p className="text-body text-text-secondary">
          Мастер пока не добавил услуги
        </p>
      ) : (
        <div className="space-y-3">
          {sorted.map((service) => (
            <div
              key={service.id}
              className="rounded-xl border border-border p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-text-primary">
                    {service.name}
                  </p>
                  {service.description && (
                    <p className="text-caption text-text-secondary mt-0.5 line-clamp-2">
                      {service.description}
                    </p>
                  )}
                  <div className="flex items-center gap-2 mt-2">
                    <span className="font-semibold text-accent">
                      {formatPrice(service.price)}
                    </span>
                    <span className="text-caption text-text-secondary">
                      &middot; {service.duration_minutes} мин
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => onBook(service.id)}
                  className="shrink-0 text-sm text-accent font-medium border border-accent rounded-lg px-4 py-2 active:bg-accent/5 transition-colors"
                >
                  Записаться
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

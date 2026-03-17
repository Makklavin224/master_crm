import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Plus, Scissors, Trash2 } from "lucide-react";
import { useMasterServices, useDeleteService } from "../../api/master-services.ts";
import { ServiceCard } from "../../components/ServiceCard.tsx";
import { ConfirmDialog } from "../../components/ConfirmDialog.tsx";
import { EmptyState } from "../../components/ui/EmptyState.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { useToast } from "../../components/ui/Toast.tsx";

export function Services() {
  const { data: services, isLoading } = useMasterServices();
  const deleteService = useDeleteService();
  const navigate = useNavigate();
  const toast = useToast();

  const [deleteTarget, setDeleteTarget] = useState<{
    id: string;
    name: string;
  } | null>(null);

  const handleDelete = () => {
    if (!deleteTarget) return;
    deleteService.mutate(deleteTarget.id, {
      onSuccess: () => {
        toast.success("Услуга удалена");
        setDeleteTarget(null);
      },
      onError: () => {
        toast.error("Не удалось удалить услугу");
        setDeleteTarget(null);
      },
    });
  };

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4 flex items-center justify-between">
        <h1 className="text-[20px] font-semibold text-text-primary">Услуги</h1>
        <button
          onClick={() => navigate("/master/services/new")}
          className="w-10 h-10 flex items-center justify-center rounded-full text-accent hover:bg-surface transition-colors"
          aria-label="Добавить услугу"
        >
          <Plus className="w-6 h-6" />
        </button>
      </div>

      <div className="flex-1 px-4 pb-4">
        {isLoading ? (
          <div className="flex flex-col gap-4">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} height="80px" className="w-full" />
            ))}
          </div>
        ) : !services || services.length === 0 ? (
          <EmptyState
            icon={<Scissors className="w-12 h-12" />}
            heading="Нет услуг"
            body="Добавьте первую услугу, чтобы клиенты могли записаться."
            action={
              <Button onClick={() => navigate("/master/services/new")}>
                Добавить услугу
              </Button>
            }
          />
        ) : (
          <div className="flex flex-col gap-4">
            {services.map((service) => (
              <div key={service.id} className="relative group">
                <ServiceCard
                  emoji={service.category ? getCategoryEmoji(service.category) : "✂️"}
                  name={service.name}
                  durationMinutes={service.duration_minutes}
                  priceKopecks={service.price}
                  onClick={() => navigate(`/master/services/${service.id}`)}
                />
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setDeleteTarget({ id: service.id, name: service.name });
                  }}
                  className="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full bg-red-50 text-destructive opacity-0 group-hover:opacity-100 transition-opacity"
                  aria-label={`Удалить ${service.name}`}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        title="Удалить услугу?"
        message={`Удалить услугу "${deleteTarget?.name}"? Существующие записи сохранятся.`}
        confirmLabel="Удалить"
        cancelLabel="Не удалять"
        variant="destructive"
        onConfirm={handleDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}

function getCategoryEmoji(category: string): string {
  const map: Record<string, string> = {
    "Волосы": "💇",
    "Ногти": "💅",
    "Лицо": "🧖",
    "Тело": "💆",
    "Брови": "🪮",
    "Ресницы": "👁️",
    "Макияж": "💄",
  };
  return map[category] || "✂️";
}

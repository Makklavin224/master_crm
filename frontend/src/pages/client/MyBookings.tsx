import { EmptyState } from "../../components/ui/EmptyState.tsx";

export function MyBookings() {
  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-6 pb-8">
        <h1 className="text-[20px] font-semibold text-text-primary mb-4">
          Мои записи
        </h1>
        <EmptyState
          heading="У вас пока нет записей"
          body="Выберите мастера и запишитесь на удобное время."
        />
      </div>
    </div>
  );
}

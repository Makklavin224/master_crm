import { Tag } from "antd";

const bookingStatusMap: Record<string, { color: string; label: string }> = {
  confirmed: { color: "#6C5CE7", label: "Подтверждена" },
  pending: { color: "gold", label: "Ожидание" },
  completed: { color: "green", label: "Завершена" },
  cancelled: { color: "red", label: "Отменена" },
  cancelled_by_client: { color: "red", label: "Отмена клиентом" },
  cancelled_by_master: { color: "red", label: "Отменена" },
  no_show: { color: "default", label: "Неявка" },
};

const paymentStatusMap: Record<string, { color: string; label: string }> = {
  paid: { color: "green", label: "Оплачен" },
  pending: { color: "gold", label: "Ожидание" },
  refunded: { color: "orange", label: "Возврат" },
  cancelled: { color: "red", label: "Отменён" },
};

export function BookingStatusTag({ status }: { status: string }) {
  const info = bookingStatusMap[status] ?? {
    color: "default",
    label: status,
  };
  return <Tag color={info.color}>{info.label}</Tag>;
}

export function PaymentStatusTag({ status }: { status: string }) {
  const info = paymentStatusMap[status] ?? {
    color: "default",
    label: status,
  };
  return <Tag color={info.color}>{info.label}</Tag>;
}

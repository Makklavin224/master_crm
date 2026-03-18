import { Tag } from "antd";

const bookingStatusMap: Record<string, { color: string; label: string }> = {
  confirmed: { color: "#6C5CE7", label: "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043d\u0430" },
  pending: { color: "gold", label: "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435" },
  completed: { color: "green", label: "\u0417\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u0430" },
  cancelled: { color: "red", label: "\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u0430" },
  cancelled_by_client: { color: "red", label: "\u041e\u0442\u043c\u0435\u043d\u0430 \u043a\u043b\u0438\u0435\u043d\u0442\u043e\u043c" },
  cancelled_by_master: { color: "red", label: "\u041e\u0442\u043c\u0435\u043d\u0435\u043d\u0430" },
  no_show: { color: "default", label: "\u041d\u0435\u044f\u0432\u043a\u0430" },
};

const paymentStatusMap: Record<string, { color: string; label: string }> = {
  paid: { color: "green", label: "\u041e\u043f\u043b\u0430\u0447\u0435\u043d" },
  pending: { color: "gold", label: "\u041e\u0436\u0438\u0434\u0430\u043d\u0438\u0435" },
  refunded: { color: "orange", label: "\u0412\u043e\u0437\u0432\u0440\u0430\u0442" },
  cancelled: { color: "red", label: "\u041e\u0442\u043c\u0435\u043d\u0451\u043d" },
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

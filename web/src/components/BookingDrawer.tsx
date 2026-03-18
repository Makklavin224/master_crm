import { Drawer, Descriptions, Button, Popconfirm, Space, App, Divider } from "antd";
import { PhoneOutlined, CloseOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import type { BookingRead } from "../api/bookings";
import { useCancelBooking } from "../api/bookings";
import { BookingStatusTag } from "./StatusTag";

interface BookingDrawerProps {
  open: boolean;
  booking: BookingRead | null;
  onClose: () => void;
}

const SOURCE_LABELS: Record<string, string> = {
  telegram: "Telegram",
  max: "MAX",
  vk: "VKontakte",
  web: "Веб",
  manual: "Вручную",
};

export function BookingDrawer({ open, booking, onClose }: BookingDrawerProps) {
  const cancelMutation = useCancelBooking();
  const { message: messageApi } = App.useApp();

  if (!booking) return null;

  const canCancel =
    booking.status === "confirmed" || booking.status === "pending";

  const handleCancel = () => {
    cancelMutation.mutate(booking.id, {
      onSuccess: () => {
        messageApi.success("Запись отменена");
        onClose();
      },
      onError: () => {
        messageApi.error("Не удалось отменить запись");
      },
    });
  };

  return (
    <Drawer
      title="Детали записи"
      placement="right"
      width={400}
      open={open}
      onClose={onClose}
      extra={
        <Button
          type="text"
          icon={<CloseOutlined />}
          onClick={onClose}
        />
      }
    >
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="Клиент">
          {booking.client_name || "—"}
        </Descriptions.Item>
        <Descriptions.Item label="Телефон">
          {booking.client_phone ? (
            <Space>
              <PhoneOutlined />
              <a href={`tel:${booking.client_phone}`}>{booking.client_phone}</a>
            </Space>
          ) : (
            "—"
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Услуга">
          {booking.service_name || "—"}
        </Descriptions.Item>
        <Descriptions.Item label="Начало">
          {dayjs(booking.starts_at).format("DD.MM.YYYY HH:mm")}
        </Descriptions.Item>
        <Descriptions.Item label="Окончание">
          {dayjs(booking.ends_at).format("DD.MM.YYYY HH:mm")}
        </Descriptions.Item>
        <Descriptions.Item label="Статус">
          <BookingStatusTag status={booking.status} />
        </Descriptions.Item>
        <Descriptions.Item label="Источник">
          {SOURCE_LABELS[booking.source_platform || ""] ||
            booking.source_platform ||
            "—"}
        </Descriptions.Item>
      </Descriptions>

      {booking.notes && (
        <>
          <Divider orientation="left" style={{ fontSize: 13 }}>
            Заметки
          </Divider>
          <p style={{ whiteSpace: "pre-wrap", color: "#666" }}>
            {booking.notes}
          </p>
        </>
      )}

      {canCancel && (
        <>
          <Divider />
          <Popconfirm
            title="Отменить запись?"
            description="Клиент получит уведомление об отмене"
            onConfirm={handleCancel}
            okText="Да, отменить"
            cancelText="Нет"
            okButtonProps={{ danger: true }}
          >
            <Button
              danger
              block
              loading={cancelMutation.isPending}
            >
              Отменить запись
            </Button>
          </Popconfirm>
        </>
      )}
    </Drawer>
  );
}

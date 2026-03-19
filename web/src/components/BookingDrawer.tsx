import { useState } from "react";
import {
  Drawer,
  Descriptions,
  Button,
  Popconfirm,
  Space,
  App,
  Divider,
  Modal,
  Form,
  DatePicker,
  TimePicker,
} from "antd";
import {
  PhoneOutlined,
  CloseOutlined,
  CheckOutlined,
  StopOutlined,
  CalendarOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import type { BookingRead } from "../api/bookings";
import {
  useCancelBooking,
  useCompleteBooking,
  useMarkNoShow,
  useRescheduleBooking,
} from "../api/bookings";
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
  const completeMutation = useCompleteBooking();
  const noShowMutation = useMarkNoShow();
  const rescheduleMutation = useRescheduleBooking();
  const { message: messageApi } = App.useApp();
  const [rescheduleModalOpen, setRescheduleModalOpen] = useState(false);
  const [rescheduleForm] = Form.useForm();

  if (!booking) return null;

  const canCancel =
    booking.status === "confirmed" || booking.status === "pending";
  const canComplete = booking.status === "confirmed";
  const canNoShow = booking.status === "confirmed";
  const canReschedule =
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

  const handleComplete = () => {
    completeMutation.mutate(booking.id, {
      onSuccess: () => {
        messageApi.success("Запись завершена");
        onClose();
      },
      onError: () => {
        messageApi.error("Не удалось завершить запись");
      },
    });
  };

  const handleNoShow = () => {
    noShowMutation.mutate(booking.id, {
      onSuccess: () => {
        messageApi.success("Отмечена неявка");
        onClose();
      },
      onError: () => {
        messageApi.error("Не удалось отметить неявку");
      },
    });
  };

  const handleReschedule = async () => {
    try {
      const values = await rescheduleForm.validateFields();
      const date = values.date as dayjs.Dayjs;
      const time = values.time as dayjs.Dayjs;
      const newStartsAt = date
        .hour(time.hour())
        .minute(time.minute())
        .second(0)
        .toISOString();
      rescheduleMutation.mutate(
        { bookingId: booking.id, newStartsAt },
        {
          onSuccess: () => {
            messageApi.success("Запись перенесена");
            setRescheduleModalOpen(false);
            rescheduleForm.resetFields();
            onClose();
          },
          onError: () => {
            messageApi.error("Не удалось перенести запись");
          },
        },
      );
    } catch {
      /* validation error */
    }
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

      {(canComplete || canNoShow || canReschedule || canCancel) && (
        <>
          <Divider orientation="left" style={{ fontSize: 13 }}>
            Действия
          </Divider>
          <Space direction="vertical" style={{ width: "100%" }}>
            {canComplete && (
              <Button
                type="primary"
                icon={<CheckOutlined />}
                block
                loading={completeMutation.isPending}
                onClick={handleComplete}
                style={{ background: "#00B894" }}
              >
                Завершить
              </Button>
            )}
            {canNoShow && (
              <Popconfirm
                title="Отметить неявку?"
                description="Статус записи будет изменён на «Неявка»"
                onConfirm={handleNoShow}
                okText="Да"
                cancelText="Нет"
              >
                <Button
                  icon={<StopOutlined />}
                  block
                  loading={noShowMutation.isPending}
                >
                  Неявка
                </Button>
              </Popconfirm>
            )}
            {canReschedule && (
              <Button
                icon={<CalendarOutlined />}
                block
                onClick={() => {
                  rescheduleForm.setFieldsValue({
                    date: dayjs(booking.starts_at),
                    time: dayjs(booking.starts_at),
                  });
                  setRescheduleModalOpen(true);
                }}
              >
                Перенести
              </Button>
            )}
            {canCancel && (
              <Popconfirm
                title="Отменить запись?"
                description="Клиент получит уведомление об отмене"
                onConfirm={handleCancel}
                okText="Да, отменить"
                cancelText="Нет"
                okButtonProps={{ danger: true }}
              >
                <Button danger block loading={cancelMutation.isPending}>
                  Отменить
                </Button>
              </Popconfirm>
            )}
          </Space>
        </>
      )}

      <Modal
        title="Перенести запись"
        open={rescheduleModalOpen}
        onOk={handleReschedule}
        onCancel={() => {
          setRescheduleModalOpen(false);
          rescheduleForm.resetFields();
        }}
        confirmLoading={rescheduleMutation.isPending}
        okText="Перенести"
        cancelText="Отмена"
      >
        <Form form={rescheduleForm} layout="vertical">
          <Form.Item
            name="date"
            label="Новая дата"
            rules={[{ required: true, message: "Выберите дату" }]}
          >
            <DatePicker format="DD.MM.YYYY" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="time"
            label="Новое время"
            rules={[{ required: true, message: "Выберите время" }]}
          >
            <TimePicker
              format="HH:mm"
              minuteStep={15}
              style={{ width: "100%" }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Drawer>
  );
}

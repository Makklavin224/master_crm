import { useState, useMemo, useCallback } from "react";
import {
  Card,
  Button,
  Modal,
  Form,
  Select,
  Input,
  DatePicker,
  TimePicker,
  Space,
  App,
} from "antd";
import { PlusOutlined, LoadingOutlined } from "@ant-design/icons";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { DatesSetArg, EventClickArg } from "@fullcalendar/core";
import type { DateClickArg } from "@fullcalendar/interaction";
import ruLocale from "@fullcalendar/core/locales/ru";
import dayjs from "dayjs";
import { useBookings, useCreateManualBooking, type BookingRead } from "../api/bookings";
import { usePayments } from "../api/payments";
import { useServices } from "../api/services";
import { useScheduleTemplate } from "../api/schedule";
import { BookingDrawer } from "../components/BookingDrawer";

const STATUS_COLORS: Record<string, string> = {
  confirmed: "#6C5CE7",
  pending: "#FDCB6E",
  completed: "#00B894",
  cancelled: "#D63031",
  cancelled_by_client: "#D63031",
  cancelled_by_master: "#D63031",
  no_show: "#636E72",
};

export function CalendarPage() {
  const [dateRange, setDateRange] = useState<{
    date_from: string;
    date_to: string;
  }>({
    date_from: "",
    date_to: "",
  });

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedBooking, setSelectedBooking] = useState<BookingRead | null>(
    null,
  );
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [createForm] = Form.useForm();

  const { data: bookingsData, isLoading: bookingsLoading } = useBookings(
    dateRange.date_from ? dateRange : {},
  );

  const { data: paymentsData } = usePayments({
    date_from: dateRange.date_from
      ? dayjs(dateRange.date_from).format("YYYY-MM-DD")
      : undefined,
    date_to: dateRange.date_to
      ? dayjs(dateRange.date_to).format("YYYY-MM-DD")
      : undefined,
    limit: 100,
    offset: 0,
  });

  const paidBookingIds = useMemo(() => {
    if (!paymentsData?.items) return new Set<string>();
    return new Set(
      paymentsData.items
        .filter((p) => p.status === "paid")
        .map((p) => p.booking_id),
    );
  }, [paymentsData]);

  const { data: schedule } = useScheduleTemplate();
  const { data: servicesData } = useServices();
  const createMutation = useCreateManualBooking();
  const { message: messageApi } = App.useApp();

  const { slotMinTime, slotMaxTime } = useMemo(() => {
    if (!schedule || schedule.length === 0) {
      return { slotMinTime: "08:00:00", slotMaxTime: "22:00:00" };
    }

    const workingDays = schedule.filter((d) => d.is_working);
    if (workingDays.length === 0) {
      return { slotMinTime: "08:00:00", slotMaxTime: "22:00:00" };
    }

    const starts = workingDays
      .map((d) => d.start_time)
      .filter(Boolean)
      .sort();
    const ends = workingDays
      .map((d) => d.end_time)
      .filter(Boolean)
      .sort();

    const earliest = starts[0] || "08:00:00";
    const latest = ends[ends.length - 1] || "22:00:00";

    return {
      slotMinTime: earliest.length === 5 ? `${earliest}:00` : earliest,
      slotMaxTime: latest.length === 5 ? `${latest}:00` : latest,
    };
  }, [schedule]);

  const events = useMemo(() => {
    if (!bookingsData?.bookings) return [];

    return bookingsData.bookings.map((b) => {
      const hasPaid = paidBookingIds.has(b.id);
      const title = [hasPaid ? "₽" : null, b.service_name, b.client_name]
        .filter(Boolean)
        .join(" — ");
      return {
        id: b.id,
        title,
        start: b.starts_at,
        end: b.ends_at,
        backgroundColor: STATUS_COLORS[b.status] || "#636E72",
        borderColor: "transparent",
        extendedProps: { booking: b },
      };
    });
  }, [bookingsData, paidBookingIds]);

  const handleDatesSet = useCallback((arg: DatesSetArg) => {
    const from = arg.start.toISOString();
    const to = arg.end.toISOString();
    setDateRange({ date_from: from, date_to: to });
  }, []);

  const handleEventClick = useCallback((info: EventClickArg) => {
    const booking = info.event.extendedProps.booking as BookingRead;
    setSelectedBooking(booking);
    setDrawerOpen(true);
  }, []);

  const handleDrawerClose = useCallback(() => {
    setDrawerOpen(false);
    setSelectedBooking(null);
  }, []);

  const handleDateClick = useCallback(
    (arg: DateClickArg) => {
      createForm.setFieldsValue({
        date: dayjs(arg.dateStr),
        time: dayjs(arg.dateStr),
      });
      setCreateModalOpen(true);
    },
    [createForm],
  );

  const handleCreateBooking = useCallback(async () => {
    try {
      const values = await createForm.validateFields();
      const date = values.date as dayjs.Dayjs;
      const time = values.time as dayjs.Dayjs;
      const startsAt = date
        .hour(time.hour())
        .minute(time.minute())
        .second(0)
        .toISOString();
      await createMutation.mutateAsync({
        service_id: values.service_id,
        starts_at: startsAt,
        client_name: values.client_name,
        client_phone: values.client_phone,
        notes: values.notes || null,
      });
      messageApi.success("Запись создана");
      setCreateModalOpen(false);
      createForm.resetFields();
    } catch {
      // validation or API error
    }
  }, [createForm, createMutation, messageApi]);

  return (
    <>
      <Card
        styles={{ body: { padding: 16 } }}
        style={{ minHeight: "calc(100vh - 120px)", position: "relative" }}
        extra={
          <Space>
            {bookingsLoading && (
              <LoadingOutlined spin style={{ color: "#6C5CE7" }} />
            )}
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setCreateModalOpen(true)}
            >
              Новая запись
            </Button>
          </Space>
        }
      >
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="timeGridWeek"
          locale={ruLocale}
          firstDay={1}
          allDaySlot={false}
          slotMinTime={slotMinTime}
          slotMaxTime={slotMaxTime}
          headerToolbar={{
            left: "prev,next today",
            center: "title",
            right: "timeGridDay,timeGridWeek,dayGridMonth",
          }}
          buttonText={{
            today: "Сегодня",
            day: "День",
            week: "Неделя",
            month: "Месяц",
          }}
          events={events}
          datesSet={handleDatesSet}
          eventClick={handleEventClick}
          dateClick={handleDateClick}
          height="auto"
          nowIndicator
          slotDuration="00:30:00"
          eventDisplay="block"
        />
      </Card>

      <BookingDrawer
        open={drawerOpen}
        booking={selectedBooking}
        onClose={handleDrawerClose}
      />

      <Modal
        title="Новая запись"
        open={createModalOpen}
        onOk={handleCreateBooking}
        onCancel={() => {
          setCreateModalOpen(false);
          createForm.resetFields();
        }}
        confirmLoading={createMutation.isPending}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form form={createForm} layout="vertical">
          <Form.Item
            name="service_id"
            label="Услуга"
            rules={[{ required: true, message: "Выберите услугу" }]}
          >
            <Select
              placeholder="Выберите услугу"
              options={
                servicesData
                  ?.filter((s) => s.is_active)
                  .map((s) => ({
                    value: s.id,
                    label: `${s.name} (${s.duration_minutes} мин, ${(s.price / 100).toLocaleString("ru-RU")} руб)`,
                  })) ?? []
              }
            />
          </Form.Item>
          <Form.Item
            name="date"
            label="Дата"
            rules={[{ required: true, message: "Выберите дату" }]}
          >
            <DatePicker format="DD.MM.YYYY" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="time"
            label="Время"
            rules={[{ required: true, message: "Выберите время" }]}
          >
            <TimePicker
              format="HH:mm"
              minuteStep={15}
              style={{ width: "100%" }}
            />
          </Form.Item>
          <Form.Item
            name="client_name"
            label="Имя клиента"
            rules={[{ required: true, message: "Введите имя" }]}
          >
            <Input placeholder="Имя клиента" />
          </Form.Item>
          <Form.Item
            name="client_phone"
            label="Телефон клиента"
            rules={[{ required: true, message: "Введите телефон" }]}
          >
            <Input placeholder="+79161234567" />
          </Form.Item>
          <Form.Item name="notes" label="Заметки">
            <Input.TextArea rows={2} placeholder="Необязательно" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

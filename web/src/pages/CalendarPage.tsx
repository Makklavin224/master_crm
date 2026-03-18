import { useState, useMemo, useCallback } from "react";
import { Card, Spin } from "antd";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import type { DatesSetArg, EventClickArg } from "@fullcalendar/core";
import ruLocale from "@fullcalendar/core/locales/ru";
import { useBookings, type BookingRead } from "../api/bookings";
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

  const { data: bookingsData, isLoading: bookingsLoading } = useBookings(
    dateRange.date_from ? dateRange : {},
  );

  const { data: schedule } = useScheduleTemplate();

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

    return bookingsData.bookings.map((b) => ({
      id: b.id,
      title: [b.service_name, b.client_name].filter(Boolean).join(" — "),
      start: b.starts_at,
      end: b.ends_at,
      backgroundColor: STATUS_COLORS[b.status] || "#636E72",
      borderColor: "transparent",
      extendedProps: { booking: b },
    }));
  }, [bookingsData]);

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

  return (
    <>
      <Card
        styles={{ body: { padding: 16 } }}
        style={{ minHeight: "calc(100vh - 120px)" }}
      >
        <Spin spinning={bookingsLoading}>
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
            height="auto"
            nowIndicator
            slotDuration="00:30:00"
            eventDisplay="block"
          />
        </Spin>
      </Card>

      <BookingDrawer
        open={drawerOpen}
        booking={selectedBooking}
        onClose={handleDrawerClose}
      />
    </>
  );
}

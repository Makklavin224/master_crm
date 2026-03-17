// Route paths
export const ROUTES = {
  BOOK_SERVICE: "/book/:masterId",
  BOOK_DATE: "/book/:masterId/date",
  BOOK_TIME: "/book/:masterId/time",
  BOOK_INFO: "/book/:masterId/info",
  BOOK_CONFIRM: "/book/:masterId/confirm",
  MY_BOOKINGS: "/my-bookings",
  // Master panel (Plan 04)
  MASTER_DASHBOARD: "/master/dashboard",
  MASTER_BOOKINGS: "/master/bookings",
  MASTER_SERVICES: "/master/services",
  MASTER_CLIENTS: "/master/clients",
  MASTER_SETTINGS: "/master/settings",
} as const;

// API paths
export const API = {
  MASTER_SERVICES: (masterId: string) => `/masters/${masterId}/services`,
  MASTER_SLOTS: (masterId: string) => `/masters/${masterId}/slots`,
  BOOKINGS: "/bookings",
  BOOKING: (id: string) => `/bookings/${id}`,
  BOOKING_CANCEL: (id: string) => `/bookings/${id}/cancel`,
  BOOKING_RESCHEDULE: (id: string) => `/bookings/${id}/reschedule`,
} as const;

// Booking flow step names
export const BOOKING_STEPS = [
  "Услуга",
  "Дата",
  "Время",
  "Данные",
  "Подтверждение",
] as const;

export const TOTAL_BOOKING_STEPS = BOOKING_STEPS.length;

import { create } from "zustand";
import type { ServiceRead } from "../api/services.ts";
import type { BookingRead } from "../api/bookings.ts";

interface BookingFlowState {
  masterId: string | null;
  step: 1 | 2 | 3 | 4 | 5;
  selectedService: ServiceRead | null;
  selectedDate: string | null; // "YYYY-MM-DD"
  selectedTime: string | null; // "HH:MM"
  clientName: string;
  clientPhone: string;
  bookingResult: BookingRead | null;

  setMasterId: (id: string) => void;
  selectService: (service: ServiceRead) => void;
  selectDate: (date: string) => void;
  selectTime: (time: string) => void;
  setClientInfo: (name: string, phone: string) => void;
  setBookingResult: (booking: BookingRead) => void;
  goToStep: (step: 1 | 2 | 3 | 4 | 5) => void;
  reset: () => void;
}

const initialState = {
  masterId: null,
  step: 1 as const,
  selectedService: null,
  selectedDate: null,
  selectedTime: null,
  clientName: "",
  clientPhone: "",
  bookingResult: null,
};

export const useBookingFlow = create<BookingFlowState>((set) => ({
  ...initialState,

  setMasterId: (masterId) => set({ masterId }),

  selectService: (service) =>
    set({ selectedService: service, step: 2 }),

  selectDate: (date) =>
    set({ selectedDate: date, selectedTime: null, step: 3 }),

  selectTime: (time) =>
    set({ selectedTime: time }),

  setClientInfo: (clientName, clientPhone) =>
    set({ clientName, clientPhone }),

  setBookingResult: (booking) =>
    set({ bookingResult: booking, step: 5 }),

  goToStep: (step) => set({ step }),

  reset: () => set(initialState),
}));

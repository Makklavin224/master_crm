import { create } from "zustand";
import type { ServiceRead, BookingRead } from "../api/types.ts";

interface BookingFlowState {
  username: string | null;
  masterId: string | null;
  step: 1 | 2 | 3 | 4 | 5;
  selectedService: ServiceRead | null;
  selectedDate: string | null; // "YYYY-MM-DD"
  selectedTime: string | null; // "HH:MM"
  clientName: string;
  clientPhone: string;
  bookingResult: BookingRead | null;

  setMaster: (username: string, masterId: string) => void;
  selectService: (service: ServiceRead) => void;
  selectDate: (date: string) => void;
  selectTime: (time: string) => void;
  setClientInfo: (name: string, phone: string) => void;
  setBookingResult: (booking: BookingRead) => void;
  goToStep: (step: 1 | 2 | 3 | 4 | 5) => void;
  reset: () => void;
}

const initialState = {
  username: null as string | null,
  masterId: null as string | null,
  step: 1 as const,
  selectedService: null as ServiceRead | null,
  selectedDate: null as string | null,
  selectedTime: null as string | null,
  clientName: "",
  clientPhone: "",
  bookingResult: null as BookingRead | null,
};

export const useBookingFlow = create<BookingFlowState>((set) => ({
  ...initialState,

  setMaster: (username, masterId) => set({ username, masterId }),

  selectService: (service) => set({ selectedService: service, step: 2 }),

  selectDate: (date) => set({ selectedDate: date, selectedTime: null, step: 3 }),

  selectTime: (time) => set({ selectedTime: time }),

  setClientInfo: (clientName, clientPhone) => set({ clientName, clientPhone }),

  setBookingResult: (booking) => set({ bookingResult: booking, step: 5 }),

  goToStep: (step) => set({ step }),

  reset: () => set(initialState),
}));

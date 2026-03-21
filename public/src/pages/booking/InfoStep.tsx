import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import BookingStepIndicator from "../../components/BookingStepIndicator.tsx";
import { useCreateBooking } from "../../api/booking.ts";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { ApiError } from "../../api/client.ts";
import { ChevronLeft, Loader2 } from "lucide-react";

function formatPhone(value: string): string {
  const digits = value.replace(/\D/g, "");

  let phone = digits;
  if (phone.startsWith("8") && phone.length > 1) {
    phone = "7" + phone.slice(1);
  }
  if (!phone.startsWith("7")) {
    phone = "7" + phone;
  }

  // Cap at 11 digits (7 + 10 digits)
  phone = phone.slice(0, 11);

  // Format as +7 (XXX) XXX-XX-XX
  let formatted = "+7";
  if (phone.length > 1) formatted += " (" + phone.slice(1, 4);
  if (phone.length > 4) formatted += ") " + phone.slice(4, 7);
  if (phone.length > 7) formatted += "-" + phone.slice(7, 9);
  if (phone.length > 9) formatted += "-" + phone.slice(9, 11);

  return formatted;
}

function cleanPhone(formatted: string): string {
  return "+" + formatted.replace(/\D/g, "");
}

export default function InfoStep() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  const createBooking = useCreateBooking();

  const {
    masterId,
    selectedService,
    selectedDate,
    selectedTime,
    clientName,
    clientPhone,
    setClientInfo,
    setBookingResult,
  } = useBookingFlow();

  const [name, setName] = useState(clientName);
  const [phone, setPhone] = useState(clientPhone || "+7");
  const [nameError, setNameError] = useState("");
  const [phoneError, setPhoneError] = useState("");
  const [submitError, setSubmitError] = useState("");

  // Redirect if prerequisites missing
  useEffect(() => {
    if (!selectedService) {
      navigate(`/m/${username}/book`, { replace: true });
    } else if (!selectedDate) {
      navigate(`/m/${username}/book/date`, { replace: true });
    } else if (!selectedTime) {
      navigate(`/m/${username}/book/time`, { replace: true });
    }
  }, [selectedService, selectedDate, selectedTime, navigate, username]);

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPhone(formatPhone(e.target.value));
    setPhoneError("");
    setSubmitError("");
  };

  const validate = (): boolean => {
    let valid = true;

    if (!name.trim()) {
      setNameError("Введите ваше имя");
      valid = false;
    } else {
      setNameError("");
    }

    const cleaned = cleanPhone(phone);
    if (cleaned.length !== 12) {
      setPhoneError("Введите корректный номер телефона");
      valid = false;
    } else {
      setPhoneError("");
    }

    return valid;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    if (!selectedService || !selectedDate || !selectedTime || !masterId) return;

    setClientInfo(name.trim(), phone);
    setSubmitError("");

    const startsAt = `${selectedDate}T${selectedTime}:00`;

    try {
      const booking = await createBooking.mutateAsync({
        master_id: masterId,
        service_id: selectedService.id,
        starts_at: startsAt,
        client_name: name.trim(),
        client_phone: cleanPhone(phone),
        source_platform: "web",
      });

      setBookingResult(booking);
      navigate(`/m/${username}/book/confirm`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSubmitError("Это время уже занято. Выберите другой слот.");
        setTimeout(() => {
          navigate(`/m/${username}/book/time`);
        }, 1500);
      } else {
        setSubmitError("Что-то пошло не так. Попробуйте позже.");
      }
    }
  };

  return (
    <div className="flex flex-col min-h-full">
      <BookingStepIndicator currentStep={4} />
      <div className="px-4 pt-2 pb-32 flex-1">
        <button
          onClick={() => navigate(`/m/${username}/book/time`)}
          className="flex items-center gap-1 text-sm text-text-secondary mb-4 active:opacity-70"
        >
          <ChevronLeft size={18} />
          <span>Назад</span>
        </button>

        <h1 className="text-[20px] font-semibold text-text-primary mb-6">
          Ваши данные
        </h1>

        <div className="flex flex-col gap-4">
          {/* Name input */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Ваше имя
            </label>
            <input
              type="text"
              placeholder="Как к вам обращаться?"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setNameError("");
                setSubmitError("");
              }}
              className={`w-full rounded-xl border px-4 py-3 text-base text-text-primary placeholder:text-gray-400 outline-none transition-colors focus:border-accent ${
                nameError ? "border-destructive" : "border-border"
              }`}
            />
            {nameError && (
              <p className="text-xs text-destructive mt-1">{nameError}</p>
            )}
          </div>

          {/* Phone input */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1.5">
              Телефон
            </label>
            <input
              type="tel"
              placeholder="+7 (___) ___-__-__"
              value={phone}
              onChange={handlePhoneChange}
              className={`w-full rounded-xl border px-4 py-3 text-base text-text-primary placeholder:text-gray-400 outline-none transition-colors focus:border-accent ${
                phoneError ? "border-destructive" : "border-border"
              }`}
            />
            {phoneError && (
              <p className="text-xs text-destructive mt-1">{phoneError}</p>
            )}
          </div>
        </div>

        {/* Submit error message */}
        {submitError && (
          <div className="mt-4 rounded-xl bg-destructive/10 px-4 py-3">
            <p className="text-sm text-destructive">{submitError}</p>
          </div>
        )}
      </div>

      {/* Fixed bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-border p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
        <button
          onClick={handleSubmit}
          disabled={createBooking.isPending}
          className="w-full bg-accent text-white rounded-xl py-3.5 font-semibold text-base active:opacity-90 transition-opacity disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {createBooking.isPending && (
            <Loader2 className="w-5 h-5 animate-spin" />
          )}
          Записаться
        </button>
      </div>
    </div>
  );
}

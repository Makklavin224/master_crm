import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { StepIndicator } from "../../components/ui/StepIndicator.tsx";
import { Input } from "../../components/ui/Input.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { useCreateBooking } from "../../api/bookings.ts";
import { useBookingFlow } from "../../stores/booking-flow.ts";
import { usePlatform } from "../../platform/context.tsx";
import { useToast } from "../../components/ui/Toast.tsx";
import { ApiError } from "../../api/client.ts";

function formatPhone(value: string): string {
  // Strip all non-digit characters
  const digits = value.replace(/\D/g, "");

  // Ensure starts with 7
  let phone = digits;
  if (phone.startsWith("8") && phone.length > 1) {
    phone = "7" + phone.slice(1);
  }
  if (!phone.startsWith("7")) {
    phone = "7" + phone;
  }

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

export function BookingForm() {
  const { masterId } = useParams<{ masterId: string }>();
  const navigate = useNavigate();
  const platform = usePlatform();
  const toast = useToast();
  const createBooking = useCreateBooking();

  const {
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

  // Redirect if missing previous steps
  useEffect(() => {
    if (!selectedService) {
      navigate(`/book/${masterId}`);
    } else if (!selectedDate) {
      navigate(`/book/${masterId}/date`);
    } else if (!selectedTime) {
      navigate(`/book/${masterId}/time`);
    }
  }, [selectedService, selectedDate, selectedTime, navigate, masterId]);

  // Back button: go to step 3
  useEffect(() => {
    platform.showBackButton();
    const cleanup = platform.onBackButtonClick(() => {
      navigate(`/book/${masterId}/time`);
    });
    return () => {
      cleanup();
      platform.hideBackButton();
    };
  }, [platform, navigate, masterId]);

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value;
    setPhone(formatPhone(raw));
    setPhoneError("");
  };

  const validate = (): boolean => {
    let valid = true;

    if (!name.trim()) {
      setNameError("Введите ваше имя");
      valid = false;
    } else {
      setNameError("");
    }

    const cleanedPhone = cleanPhone(phone);
    if (cleanedPhone.length < 12) {
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

    const startsAt = `${selectedDate}T${selectedTime}:00`;
    const initDataRaw = platform.getInitDataRaw();
    const userId = platform.getUserId();

    try {
      const booking = await createBooking.mutateAsync({
        booking: {
          master_id: masterId,
          service_id: selectedService.id,
          starts_at: startsAt,
          client_name: name.trim(),
          client_phone: cleanPhone(phone),
          source_platform: platform.platform,
          ...(userId ? { platform_user_id: userId } : {}),
        },
        initDataRaw,
      });

      platform.hapticFeedback("medium");
      setBookingResult(booking);
      navigate(`/book/${masterId}/confirm`);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        toast.error("Это время уже занято. Выберите другой слот.");
        navigate(`/book/${masterId}/time`);
      } else {
        toast.error("Что-то пошло не так. Попробуйте позже.");
      }
    }
  };

  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={4} />
      <div className="px-4 pt-2 pb-32 flex-1">
        <h1 className="text-[20px] font-semibold text-text-primary mb-6">
          Ваши данные
        </h1>

        <div className="flex flex-col gap-4">
          <Input
            label="Ваше имя"
            placeholder="Как к вам обращаться?"
            value={name}
            onChange={(e) => {
              setName(e.target.value);
              setNameError("");
            }}
            error={nameError}
          />

          <Input
            label="Телефон"
            placeholder="+7 (___) ___-__-__"
            type="tel"
            value={phone}
            onChange={handlePhoneChange}
            error={phoneError}
          />
        </div>
      </div>

      {/* Fixed bottom CTA */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-border p-4 pb-[calc(16px+env(safe-area-inset-bottom))]">
        <Button
          onClick={handleSubmit}
          loading={createBooking.isPending}
          disabled={createBooking.isPending}
        >
          Записаться
        </Button>
      </div>
    </div>
  );
}

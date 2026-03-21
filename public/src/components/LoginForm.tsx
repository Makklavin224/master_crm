import { useState, useRef, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { requestOTP, verifyOTP } from "../api/client-cabinet.ts";
import { useAuth } from "../stores/auth.ts";
import { ApiError } from "../api/client.ts";

function formatPhone(value: string): string {
  const digits = value.replace(/\D/g, "");

  let phone = digits;
  if (phone.startsWith("8") && phone.length > 1) {
    phone = "7" + phone.slice(1);
  }
  if (!phone.startsWith("7")) {
    phone = "7" + phone;
  }

  phone = phone.slice(0, 11);

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

type Phase = "phone" | "otp";

export default function LoginForm() {
  const navigate = useNavigate();
  const { setAuthenticated, setPhone: setAuthPhone } = useAuth();

  const [phase, setPhase] = useState<Phase>("phone");
  const [phone, setPhone] = useState("+7");
  const [phoneError, setPhoneError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // OTP state
  const [otpDigits, setOtpDigits] = useState(["", "", "", "", "", ""]);
  const [otpError, setOtpError] = useState("");
  const [countdown, setCountdown] = useState(0);
  const [shake, setShake] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Countdown timer
  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPhone(formatPhone(e.target.value));
    setPhoneError("");
  };

  const handleRequestCode = async () => {
    const cleaned = cleanPhone(phone);
    if (cleaned.length !== 12) {
      setPhoneError("Введите корректный номер телефона");
      return;
    }

    setIsSubmitting(true);
    setPhoneError("");

    try {
      await requestOTP(cleaned);
      setAuthPhone(cleaned);
      setPhase("otp");
      setCountdown(60);
      // Focus first OTP input after transition
      setTimeout(() => inputRefs.current[0]?.focus(), 100);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 404) {
          setPhoneError(
            "Клиент не найден. Сначала запишитесь к мастеру.",
          );
        } else if (err.status === 429) {
          setPhoneError("Подождите перед повторной отправкой кода");
          setPhase("otp");
          setCountdown(60);
        } else {
          setPhoneError(err.detail);
        }
      } else {
        setPhoneError("Ошибка сети. Попробуйте позже.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const submitOtp = useCallback(
    async (digits: string[]) => {
      const code = digits.join("");
      if (code.length !== 6) return;

      setIsSubmitting(true);
      setOtpError("");

      try {
        await verifyOTP(cleanPhone(phone), code);
        setAuthenticated(true);
        navigate("/my/bookings", { replace: true });
      } catch (err) {
        setShake(true);
        setTimeout(() => setShake(false), 500);
        setOtpDigits(["", "", "", "", "", ""]);
        setTimeout(() => inputRefs.current[0]?.focus(), 100);

        if (err instanceof ApiError) {
          setOtpError(err.detail);
        } else {
          setOtpError("Ошибка сети. Попробуйте позже.");
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [phone, setAuthenticated, navigate],
  );

  const handleOtpChange = (index: number, value: string) => {
    // Handle paste of full code
    if (value.length > 1) {
      const pastedDigits = value.replace(/\D/g, "").slice(0, 6).split("");
      const newDigits = [...otpDigits];
      pastedDigits.forEach((d, i) => {
        if (index + i < 6) newDigits[index + i] = d;
      });
      setOtpDigits(newDigits);
      setOtpError("");

      const nextIndex = Math.min(index + pastedDigits.length, 5);
      inputRefs.current[nextIndex]?.focus();

      if (newDigits.every((d) => d !== "")) {
        submitOtp(newDigits);
      }
      return;
    }

    const digit = value.replace(/\D/g, "");
    const newDigits = [...otpDigits];
    newDigits[index] = digit;
    setOtpDigits(newDigits);
    setOtpError("");

    if (digit && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    if (newDigits.every((d) => d !== "")) {
      submitOtp(newDigits);
    }
  };

  const handleOtpKeyDown = (
    index: number,
    e: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (e.key === "Backspace" && !otpDigits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleResend = async () => {
    if (countdown > 0) return;

    setIsSubmitting(true);
    try {
      await requestOTP(cleanPhone(phone));
      setCountdown(60);
      setOtpDigits(["", "", "", "", "", ""]);
      setOtpError("");
      inputRefs.current[0]?.focus();
    } catch (err) {
      if (err instanceof ApiError) {
        setOtpError(err.detail);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (phase === "phone") {
    return (
      <div className="flex flex-col gap-4 w-full max-w-sm mx-auto">
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1.5">
            Номер телефона
          </label>
          <input
            type="tel"
            placeholder="+7 (___) ___-__-__"
            value={phone}
            onChange={handlePhoneChange}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleRequestCode();
            }}
            className={`w-full rounded-xl border px-4 py-3 text-base text-text-primary placeholder:text-gray-400 outline-none transition-colors focus:border-accent ${
              phoneError ? "border-destructive" : "border-border"
            }`}
          />
          {phoneError && (
            <p className="text-xs text-destructive mt-1">{phoneError}</p>
          )}
        </div>

        <button
          onClick={handleRequestCode}
          disabled={isSubmitting}
          className="w-full bg-accent text-white rounded-xl py-3.5 font-semibold text-base active:opacity-90 transition-opacity disabled:opacity-60 flex items-center justify-center gap-2"
        >
          {isSubmitting && <Loader2 className="w-5 h-5 animate-spin" />}
          Получить код
        </button>
      </div>
    );
  }

  // OTP phase
  return (
    <div className="flex flex-col gap-6 w-full max-w-sm mx-auto items-center">
      <div className="text-center">
        <p className="text-sm text-text-secondary">
          Код отправлен на номер
        </p>
        <p className="text-base font-medium text-text-primary mt-1">
          {phone}
        </p>
        <button
          onClick={() => {
            setPhase("phone");
            setOtpDigits(["", "", "", "", "", ""]);
            setOtpError("");
          }}
          className="text-sm text-accent mt-1"
        >
          Изменить номер
        </button>
      </div>

      <div
        className={`flex gap-2 ${shake ? "animate-[shake_0.5s_ease-in-out]" : ""}`}
      >
        {otpDigits.map((digit, i) => (
          <input
            key={i}
            ref={(el) => {
              inputRefs.current[i] = el;
            }}
            type="tel"
            inputMode="numeric"
            maxLength={6}
            value={digit}
            onChange={(e) => handleOtpChange(i, e.target.value)}
            onKeyDown={(e) => handleOtpKeyDown(i, e)}
            className={`w-12 h-14 text-center text-2xl font-semibold rounded-xl border outline-none transition-colors focus:border-accent ${
              otpError ? "border-destructive" : "border-border"
            }`}
          />
        ))}
      </div>

      {otpError && (
        <p className="text-sm text-destructive text-center">{otpError}</p>
      )}

      {isSubmitting && (
        <Loader2 className="w-6 h-6 animate-spin text-accent" />
      )}

      <div className="text-center">
        {countdown > 0 ? (
          <p className="text-sm text-text-secondary">
            Отправить повторно через {countdown}с
          </p>
        ) : (
          <button
            onClick={handleResend}
            disabled={isSubmitting}
            className="text-sm text-accent font-medium disabled:opacity-60"
          >
            Отправить повторно
          </button>
        )}
      </div>
    </div>
  );
}

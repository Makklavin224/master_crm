import { useState, useEffect } from "react";
import {
  Banknote,
  Link2,
  QrCode,
  Loader2,
  CheckCircle,
  Copy,
  Check,
} from "lucide-react";
import { Card } from "./ui/Card.tsx";
import { Button } from "./ui/Button.tsx";
import { ReceiptDataCard } from "./ReceiptDataCard.tsx";
import {
  useCreateManualPayment,
  useCreateRobokassaPayment,
  useCreateRequisitesPayment,
  useConfirmPayment,
  useReceiptData,
} from "../api/payments.ts";
import { useMarkGreyWarningSeen } from "../api/master-settings.ts";
import type { MasterBookingRead } from "../api/master-bookings.ts";
import type { PaymentRequisites } from "../api/payments.ts";

type SheetState =
  | "options"
  | "manual"
  | "robokassa"
  | "requisites"
  | "receipt"
  | "success";

const PAYMENT_METHODS = [
  { value: "cash", label: "Наличные" },
  { value: "card", label: "Карта" },
  { value: "transfer", label: "Перевод" },
  { value: "sbp", label: "СБП" },
];

const FISCAL_OPTIONS = [
  { value: "none", label: "Без чеков" },
  { value: "manual", label: "Ручной" },
  { value: "auto", label: "Авто" },
];

interface PaymentSheetProps {
  open: boolean;
  booking: MasterBookingRead | null;
  hasRobokassa: boolean;
  hasRequisites: boolean;
  hasSeenGreyWarning: boolean;
  defaultFiscalization: string;
  onClose: () => void;
  onPaymentComplete: () => void;
}

export function PaymentSheet({
  open,
  booking,
  hasRobokassa,
  hasRequisites,
  hasSeenGreyWarning,
  defaultFiscalization,
  onClose,
  onPaymentComplete,
}: PaymentSheetProps) {
  const [state, setState] = useState<SheetState>("options");
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [fiscalization, setFiscalization] = useState(defaultFiscalization);
  const [showGreyWarning, setShowGreyWarning] = useState(false);
  const [seenWarningLocal, setSeenWarningLocal] = useState(hasSeenGreyWarning);
  const [paidPaymentId, setPaidPaymentId] = useState<string | null>(null);
  const [paymentUrl, setPaymentUrl] = useState<string | null>(null);
  const [requisites, setRequisites] = useState<PaymentRequisites | null>(null);
  const [requisitesPaymentId, setRequisitesPaymentId] = useState<string | null>(
    null,
  );
  const [copiedLink, setCopiedLink] = useState(false);

  const manualPayment = useCreateManualPayment();
  const robokassaPayment = useCreateRobokassaPayment();
  const requisitesPayment = useCreateRequisitesPayment();
  const confirmPayment = useConfirmPayment();
  const markGreyWarningSeen = useMarkGreyWarningSeen();

  const { data: receiptData } = useReceiptData(paidPaymentId);

  // Reset state when opened
  useEffect(() => {
    if (open) {
      setState("options");
      setPaymentMethod("cash");
      setFiscalization(defaultFiscalization);
      setShowGreyWarning(false);
      setPaidPaymentId(null);
      setPaymentUrl(null);
      setRequisites(null);
      setRequisitesPaymentId(null);
      setCopiedLink(false);
    }
  }, [open, defaultFiscalization]);

  // Update seenWarningLocal when prop changes
  useEffect(() => {
    setSeenWarningLocal(hasSeenGreyWarning);
  }, [hasSeenGreyWarning]);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  if (!open || !booking) return null;

  const handleFiscalizationChange = (value: string) => {
    setFiscalization(value);
    if (value === "none" && !seenWarningLocal) {
      setShowGreyWarning(true);
    }
  };

  const handleDismissWarning = () => {
    setShowGreyWarning(false);
    setSeenWarningLocal(true);
    markGreyWarningSeen.mutate();
  };

  // --- Manual payment ---
  const handleManualPay = () => {
    manualPayment.mutate(
      {
        booking_id: booking.id,
        payment_method: paymentMethod,
        fiscalization_level: fiscalization,
      },
      {
        onSuccess: (payment) => {
          if (fiscalization === "manual") {
            setPaidPaymentId(payment.id);
            setState("receipt");
          } else {
            onPaymentComplete();
          }
        },
      },
    );
  };

  // --- Robokassa payment ---
  const handleRobokassaPay = () => {
    setState("robokassa");
    robokassaPayment.mutate(
      {
        booking_id: booking.id,
        fiscalization_level: fiscalization,
      },
      {
        onSuccess: (payment) => {
          setPaymentUrl(payment.payment_url);
        },
      },
    );
  };

  // --- Requisites payment ---
  const handleRequisitesPay = () => {
    setState("requisites");
    requisitesPayment.mutate(
      {
        booking_id: booking.id,
        fiscalization_level: fiscalization,
      },
      {
        onSuccess: (response) => {
          setRequisites(response.requisites);
          setRequisitesPaymentId(response.payment.id);
        },
      },
    );
  };

  // --- Confirm requisites payment ---
  const handleConfirmRequisites = () => {
    if (!requisitesPaymentId) return;
    confirmPayment.mutate(requisitesPaymentId, {
      onSuccess: (payment) => {
        if (fiscalization === "manual") {
          setPaidPaymentId(payment.id);
          setState("receipt");
        } else {
          onPaymentComplete();
        }
      },
    });
  };

  const handleCopyLink = async () => {
    if (!paymentUrl) return;
    try {
      await navigator.clipboard.writeText(paymentUrl);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch {
      // Fallback: do nothing
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" />

      {/* Bottom sheet */}
      <div
        className="relative bg-white rounded-t-[20px] w-full max-w-[428px] p-6 pb-[calc(24px+env(safe-area-inset-bottom,0px))] animate-slide-up max-h-[85vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
      >
        {/* State: Option selection */}
        {state === "options" && (
          <div className="flex flex-col gap-4">
            <h3 className="text-[20px] font-semibold text-text-primary">
              Способ оплаты
            </h3>

            {/* Option 1: Manual */}
            <button
              onClick={() => setState("manual")}
              className="w-full text-left"
            >
              <Card className="flex items-center gap-4 active:border-accent transition-colors">
                <div className="w-10 h-10 rounded-full bg-accent/8 flex items-center justify-center shrink-0">
                  <Banknote className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <div className="text-[16px] font-semibold text-text-primary">
                    Внести доход вручную
                  </div>
                  <div className="text-[14px] text-text-secondary">
                    Наличные, карта, перевод
                  </div>
                </div>
              </Card>
            </button>

            {/* Option 2: Robokassa */}
            <button
              onClick={handleRobokassaPay}
              disabled={!hasRobokassa}
              className={`w-full text-left ${!hasRobokassa ? "opacity-50 pointer-events-none" : ""}`}
            >
              <Card className="flex items-center gap-4 active:border-accent transition-colors">
                <div className="w-10 h-10 rounded-full bg-accent/8 flex items-center justify-center shrink-0">
                  <Link2 className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <div className="text-[16px] font-semibold text-text-primary">
                    Отправить ссылку клиенту
                  </div>
                  <div className="text-[14px] text-text-secondary">
                    СБП через Робокассу
                  </div>
                </div>
              </Card>
            </button>

            {/* Option 3: Requisites */}
            <button
              onClick={handleRequisitesPay}
              disabled={!hasRequisites}
              className={`w-full text-left ${!hasRequisites ? "opacity-50 pointer-events-none" : ""}`}
            >
              <Card className="flex items-center gap-4 active:border-accent transition-colors">
                <div className="w-10 h-10 rounded-full bg-accent/8 flex items-center justify-center shrink-0">
                  <QrCode className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <div className="text-[16px] font-semibold text-text-primary">
                    Показать реквизиты + QR
                  </div>
                  <div className="text-[14px] text-text-secondary">
                    Клиент переведёт сам
                  </div>
                </div>
              </Card>
            </button>
          </div>
        )}

        {/* State: Manual payment form */}
        {state === "manual" && (
          <div className="flex flex-col gap-4">
            <h3 className="text-[20px] font-semibold text-text-primary">
              Отметить оплату
            </h3>

            {/* Payment method pills */}
            <div>
              <p className="text-[12px] text-text-secondary mb-2">
                Способ оплаты
              </p>
              <div className="flex flex-wrap gap-2">
                {PAYMENT_METHODS.map((m) => (
                  <button
                    key={m.value}
                    onClick={() => setPaymentMethod(m.value)}
                    className={`h-[44px] px-5 rounded-full text-[14px] font-medium border transition-colors ${
                      paymentMethod === m.value
                        ? "bg-accent/8 border-accent text-accent"
                        : "border-border text-text-secondary hover:border-text-secondary"
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Fiscalization override */}
            <div>
              <p className="text-[12px] text-text-secondary mb-2">
                Фискализация
              </p>
              <div className="flex flex-wrap gap-2">
                {FISCAL_OPTIONS.map((f) => {
                  const isAutoDisabled =
                    f.value === "auto" && !hasRobokassa;
                  return (
                    <button
                      key={f.value}
                      onClick={() => handleFiscalizationChange(f.value)}
                      disabled={isAutoDisabled}
                      className={`h-[44px] px-5 rounded-full text-[14px] font-medium border transition-colors ${
                        fiscalization === f.value
                          ? "bg-accent/8 border-accent text-accent"
                          : "border-border text-text-secondary hover:border-text-secondary"
                      } ${isAutoDisabled ? "opacity-50 pointer-events-none" : ""}`}
                    >
                      {f.label}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Grey warning */}
            {showGreyWarning && (
              <Card className="bg-amber-50 border-amber-200">
                <p className="text-[14px] text-amber-800 mb-3">
                  Рекомендуем выставлять чеки для защиты от штрафов
                </p>
                <Button
                  variant="secondary"
                  onClick={handleDismissWarning}
                  fullWidth={false}
                  className="text-[12px] h-[36px] px-4"
                >
                  Понятно
                </Button>
              </Card>
            )}

            <Button
              onClick={handleManualPay}
              loading={manualPayment.isPending}
            >
              Оплачено
            </Button>
          </div>
        )}

        {/* State: Robokassa result */}
        {state === "robokassa" && (
          <div className="flex flex-col gap-4 items-center text-center">
            {robokassaPayment.isPending ? (
              <>
                <Loader2 className="w-12 h-12 text-accent animate-spin" />
                <p className="text-[14px] text-text-secondary">
                  Отправляем ссылку...
                </p>
              </>
            ) : robokassaPayment.isError ? (
              <>
                <p className="text-[14px] text-red-600">
                  Не удалось создать ссылку на оплату
                </p>
                <Button onClick={onClose}>Закрыть</Button>
              </>
            ) : (
              <>
                <CheckCircle className="w-12 h-12 text-success" />
                <h3 className="text-[20px] font-semibold text-text-primary">
                  Ссылка отправлена клиенту
                </h3>

                {paymentUrl && (
                  <div className="w-full">
                    <p className="text-[12px] text-text-secondary mb-2">
                      Или скопируйте ссылку
                    </p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 text-[14px] text-text-secondary truncate bg-surface rounded-[10px] px-3 py-2 text-left">
                        {paymentUrl}
                      </div>
                      <button
                        onClick={handleCopyLink}
                        className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface transition-colors text-accent shrink-0"
                        aria-label="Скопировать ссылку"
                      >
                        {copiedLink ? (
                          <Check className="w-5 h-5" />
                        ) : (
                          <Copy className="w-5 h-5" />
                        )}
                      </button>
                    </div>
                  </div>
                )}

                <Button onClick={onClose} className="mt-2">
                  Закрыть
                </Button>
              </>
            )}
          </div>
        )}

        {/* State: Requisites display */}
        {state === "requisites" && (
          <div className="flex flex-col gap-4">
            {requisitesPayment.isPending ? (
              <div className="flex flex-col items-center gap-4 py-8">
                <Loader2 className="w-12 h-12 text-accent animate-spin" />
                <p className="text-[14px] text-text-secondary">
                  Генерируем QR-код...
                </p>
              </div>
            ) : requisitesPayment.isError ? (
              <>
                <p className="text-[14px] text-red-600">
                  Не удалось создать реквизиты
                </p>
                <Button onClick={onClose}>Закрыть</Button>
              </>
            ) : requisites ? (
              <>
                <h3 className="text-[20px] font-semibold text-text-primary">
                  Реквизиты для оплаты
                </h3>

                {/* QR Code */}
                <div className="flex justify-center">
                  <img
                    src={`data:image/png;base64,${requisites.qr_code_base64}`}
                    alt="QR-код для оплаты"
                    className="w-48 h-48 rounded-[10px]"
                  />
                </div>

                {/* Card number */}
                {requisites.card_number && (
                  <RequisiteLine
                    label="Номер карты"
                    value={requisites.card_number}
                  />
                )}

                {/* SBP phone */}
                {requisites.sbp_phone && (
                  <RequisiteLine
                    label="Телефон для СБП"
                    value={requisites.sbp_phone}
                  />
                )}

                {/* Bank name */}
                {requisites.bank_name && (
                  <p className="text-[14px] text-text-secondary text-center">
                    {requisites.bank_name}
                  </p>
                )}

                <Button
                  onClick={handleConfirmRequisites}
                  loading={confirmPayment.isPending}
                >
                  Клиент оплатил
                </Button>
              </>
            ) : null}
          </div>
        )}

        {/* State: Receipt data display */}
        {state === "receipt" && receiptData && (
          <ReceiptDataCard
            data={receiptData}
            onClose={() => {
              onPaymentComplete();
            }}
          />
        )}

        {/* Loading receipt data */}
        {state === "receipt" && !receiptData && (
          <div className="flex flex-col items-center gap-4 py-8">
            <Loader2 className="w-12 h-12 text-accent animate-spin" />
            <p className="text-[14px] text-text-secondary">
              Загрузка данных чека...
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function RequisiteLine({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: do nothing
    }
  };

  return (
    <div className="flex items-center justify-between gap-2">
      <div>
        <p className="text-[12px] text-text-secondary">{label}</p>
        <p className="text-[20px] font-semibold text-text-primary tracking-wider">
          {value}
        </p>
      </div>
      <button
        onClick={handleCopy}
        className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface transition-colors text-accent shrink-0"
        aria-label={`Скопировать ${label.toLowerCase()}`}
      >
        {copied ? (
          <Check className="w-5 h-5" />
        ) : (
          <Copy className="w-5 h-5" />
        )}
      </button>
    </div>
  );
}

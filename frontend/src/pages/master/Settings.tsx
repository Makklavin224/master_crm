import { useState, useEffect } from "react";
import { Copy, Check, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import {
  useMasterSettings,
  useUpdateSettings,
  usePaymentSettings,
  useUpdatePaymentSettings,
  useDisconnectRobokassa,
  useMarkGreyWarningSeen,
  useNotificationSettings,
  useUpdateNotificationSettings,
} from "../../api/master-settings.ts";
import { Card } from "../../components/ui/Card.tsx";
import { Badge } from "../../components/ui/Badge.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { useToast } from "../../components/ui/Toast.tsx";
import { ConfirmDialog } from "../../components/ConfirmDialog.tsx";
import { RobokassaWizard } from "../../components/RobokassaWizard.tsx";

const BUFFER_OPTIONS = [
  { value: 0, label: "0 мин" },
  { value: 10, label: "10 мин" },
  { value: 15, label: "15 мин" },
  { value: 30, label: "30 мин" },
];

const DEADLINE_OPTIONS = [
  { value: 2, label: "2 ч" },
  { value: 6, label: "6 ч" },
  { value: 12, label: "12 ч" },
  { value: 24, label: "24 ч" },
];

const INTERVAL_OPTIONS = [
  { value: 15, label: "15 мин" },
  { value: 30, label: "30 мин" },
];

const REMINDER_INTERVAL_OPTIONS = [
  { value: 1, label: "1 ч" },
  { value: 2, label: "2 ч" },
  { value: 6, label: "6 ч" },
  { value: 12, label: "12 ч" },
  { value: 24, label: "24 ч" },
];

const FISCAL_OPTIONS = [
  { value: "none", label: "Без чеков" },
  { value: "manual", label: "Ручной" },
  { value: "auto", label: "Автоматический" },
];

const SNO_OPTIONS = [
  { value: "patent", label: "Патент" },
  { value: "usn_income", label: "УСН доходы" },
  { value: "osn", label: "ОСН" },
];

export function Settings() {
  const navigate = useNavigate();
  const { data: settings, isLoading } = useMasterSettings();
  const { data: paymentSettings, isLoading: paymentLoading } =
    usePaymentSettings();
  const updateSettings = useUpdateSettings();
  const updatePaymentSettings = useUpdatePaymentSettings();
  const disconnectRobokassa = useDisconnectRobokassa();
  const markGreyWarningSeen = useMarkGreyWarningSeen();
  const { data: notificationSettings, isLoading: notifLoading } =
    useNotificationSettings();
  const updateNotificationSettings = useUpdateNotificationSettings();
  const toast = useToast();

  // General settings state
  const [buffer, setBuffer] = useState(15);
  const [deadline, setDeadline] = useState(2);
  const [interval, setInterval_] = useState(30);
  const [copied, setCopied] = useState(false);

  // Payment settings state
  const [cardNumber, setCardNumber] = useState("");
  const [sbpPhone, setSbpPhone] = useState("");
  const [bankName, setBankName] = useState("");
  const [fiscalization, setFiscalization] = useState("none");
  const [receiptSno, setReceiptSno] = useState("patent");
  const [showGreyWarning, setShowGreyWarning] = useState(false);
  const [seenWarningLocal, setSeenWarningLocal] = useState(false);

  // Notification settings state
  const [remindersEnabled, setRemindersEnabled] = useState(true);
  const [reminder1Hours, setReminder1Hours] = useState(24);
  const [reminder2Hours, setReminder2Hours] = useState<number | null>(2);
  const [addressNote, setAddressNote] = useState("");

  // Robokassa state
  const [showWizard, setShowWizard] = useState(false);
  const [showDisconnectDialog, setShowDisconnectDialog] = useState(false);

  useEffect(() => {
    if (settings) {
      setBuffer(settings.buffer_minutes);
      setDeadline(settings.cancellation_deadline_hours);
      setInterval_(settings.slot_interval_minutes);
    }
  }, [settings]);

  useEffect(() => {
    if (notificationSettings) {
      setRemindersEnabled(notificationSettings.reminders_enabled);
      setReminder1Hours(notificationSettings.reminder_1_hours);
      setReminder2Hours(notificationSettings.reminder_2_hours);
      setAddressNote(notificationSettings.address_note ?? "");
    }
  }, [notificationSettings]);

  useEffect(() => {
    if (paymentSettings) {
      setCardNumber(paymentSettings.card_number ?? "");
      setSbpPhone(paymentSettings.sbp_phone ?? "");
      setBankName(paymentSettings.bank_name ?? "");
      setFiscalization(paymentSettings.fiscalization_level);
      setReceiptSno(paymentSettings.receipt_sno ?? "patent");
      setSeenWarningLocal(paymentSettings.has_seen_grey_warning);
    }
  }, [paymentSettings]);

  const handleSave = () => {
    updateSettings.mutate(
      {
        buffer_minutes: buffer,
        cancellation_deadline_hours: deadline,
        slot_interval_minutes: interval,
      },
      {
        onSuccess: () => toast.success("Настройки сохранены"),
        onError: () => toast.error("Не удалось сохранить настройки"),
      },
    );
  };

  const bookingLink = `${window.location.origin}/book/me`;

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(bookingLink);
      setCopied(true);
      toast.success("Ссылка скопирована");
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast.info(bookingLink);
    }
  };

  const handleSaveRequisites = () => {
    updatePaymentSettings.mutate(
      {
        card_number: cardNumber.trim() || null,
        sbp_phone: sbpPhone.trim() || null,
        bank_name: bankName.trim() || null,
      },
      {
        onSuccess: () => toast.success("Реквизиты сохранены"),
        onError: () => toast.error("Не удалось сохранить реквизиты"),
      },
    );
  };

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

  const handleSaveFiscalization = () => {
    updatePaymentSettings.mutate(
      {
        fiscalization_level: fiscalization,
        receipt_sno: receiptSno,
      },
      {
        onSuccess: () => toast.success("Настройки фискализации сохранены"),
        onError: () => toast.error("Не удалось сохранить настройки"),
      },
    );
  };

  const handleDisconnectRobokassa = () => {
    disconnectRobokassa.mutate(undefined, {
      onSuccess: () => {
        toast.success("Робокасса отключена");
        setShowDisconnectDialog(false);
        // If fiscalization was auto, reset to manual
        if (fiscalization === "auto") {
          setFiscalization("manual");
        }
      },
      onError: () => {
        toast.error("Не удалось отключить Робокассу");
        setShowDisconnectDialog(false);
      },
    });
  };

  const handleSaveNotifications = () => {
    updateNotificationSettings.mutate(
      {
        reminders_enabled: remindersEnabled,
        reminder_1_hours: reminder1Hours,
        reminder_2_hours: reminder2Hours,
        address_note: addressNote.trim() || null,
      },
      {
        onSuccess: () => toast.success("Настройки напоминаний сохранены"),
        onError: () =>
          toast.error("Не удалось сохранить настройки напоминаний"),
      },
    );
  };

  const isLoadingAny = isLoading || paymentLoading || notifLoading;
  const hasRobokassa = paymentSettings?.has_robokassa ?? false;

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Настройки
        </h1>
      </div>

      <div className="flex-1 px-4 pb-4 flex flex-col gap-4">
        {isLoadingAny ? (
          <div className="flex flex-col gap-4">
            <Skeleton height="100px" className="w-full" />
            <Skeleton height="100px" className="w-full" />
            <Skeleton height="100px" className="w-full" />
            <Skeleton height="100px" className="w-full" />
            <Skeleton height="100px" className="w-full" />
            <Skeleton height="100px" className="w-full" />
          </div>
        ) : (
          <>
            {/* Buffer time */}
            <Card className="flex flex-col gap-3">
              <h2 className="text-[16px] font-semibold text-text-primary">
                Перерыв между записями
              </h2>
              <div className="flex flex-wrap gap-2">
                {BUFFER_OPTIONS.map((opt) => (
                  <PillButton
                    key={opt.value}
                    label={opt.label}
                    selected={buffer === opt.value}
                    onClick={() => setBuffer(opt.value)}
                  />
                ))}
              </div>
            </Card>

            {/* Cancellation deadline */}
            <Card className="flex flex-col gap-3">
              <h2 className="text-[16px] font-semibold text-text-primary">
                Срок отмены записи
              </h2>
              <p className="text-[12px] text-text-secondary -mt-1">
                Клиент сможет отменить запись не позднее чем за указанное время
              </p>
              <div className="flex flex-wrap gap-2">
                {DEADLINE_OPTIONS.map((opt) => (
                  <PillButton
                    key={opt.value}
                    label={opt.label}
                    selected={deadline === opt.value}
                    onClick={() => setDeadline(opt.value)}
                  />
                ))}
              </div>
            </Card>

            {/* Slot interval */}
            <Card className="flex flex-col gap-3">
              <h2 className="text-[16px] font-semibold text-text-primary">
                Интервал слотов
              </h2>
              <div className="flex flex-wrap gap-2">
                {INTERVAL_OPTIONS.map((opt) => (
                  <PillButton
                    key={opt.value}
                    label={opt.label}
                    selected={interval === opt.value}
                    onClick={() => setInterval_(opt.value)}
                  />
                ))}
              </div>
            </Card>

            {/* Save general settings button */}
            <Button
              onClick={handleSave}
              loading={updateSettings.isPending}
              fullWidth
            >
              Сохранить настройки
            </Button>

            {/* Notification settings separator */}
            <div className="h-px bg-border mt-2" />

            {/* Notification settings */}
            <Card className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <h2 className="text-[16px] font-semibold text-text-primary">
                  Напоминания клиентам
                </h2>
                <button
                  type="button"
                  onClick={() => setRemindersEnabled(!remindersEnabled)}
                  className={`relative w-[44px] h-[24px] rounded-full transition-colors ${
                    remindersEnabled ? "bg-accent" : "bg-border"
                  }`}
                >
                  <div
                    className={`absolute top-[2px] w-[20px] h-[20px] rounded-full bg-white shadow transition-transform ${
                      remindersEnabled
                        ? "translate-x-[22px]"
                        : "translate-x-[2px]"
                    }`}
                  />
                </button>
              </div>

              {remindersEnabled && (
                <div className="flex flex-col gap-3">
                  <div>
                    <p className="text-[12px] text-text-secondary mb-2">
                      Первое напоминание
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {REMINDER_INTERVAL_OPTIONS.map((opt) => (
                        <PillButton
                          key={opt.value}
                          label={opt.label}
                          selected={reminder1Hours === opt.value}
                          onClick={() => setReminder1Hours(opt.value)}
                        />
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="text-[12px] text-text-secondary mb-2">
                      Второе напоминание
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {REMINDER_INTERVAL_OPTIONS.map((opt) => (
                        <PillButton
                          key={opt.value}
                          label={opt.label}
                          selected={reminder2Hours === opt.value}
                          onClick={() => setReminder2Hours(opt.value)}
                        />
                      ))}
                      <PillButton
                        label="Выкл"
                        selected={reminder2Hours === null}
                        onClick={() => setReminder2Hours(null)}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[12px] text-text-secondary mb-1 block">
                      Адрес / заметка
                    </label>
                    <textarea
                      rows={2}
                      value={addressNote}
                      onChange={(e) => setAddressNote(e.target.value)}
                      placeholder="ул. Ленина 5, кв 12"
                      className="w-full rounded-[10px] border border-border px-3 py-2 text-[14px] text-text-primary outline-none focus:ring-2 focus:ring-accent/30 resize-none"
                    />
                    <p className="text-[12px] text-text-secondary mt-1">
                      Будет добавлен в напоминания клиентам
                    </p>
                  </div>

                  <Button
                    onClick={handleSaveNotifications}
                    loading={updateNotificationSettings.isPending}
                  >
                    Сохранить
                  </Button>
                </div>
              )}
            </Card>

            {/* Booking link */}
            <Card className="flex flex-col gap-3 mt-2">
              <h2 className="text-[16px] font-semibold text-text-primary">
                Моя ссылка
              </h2>
              <div className="flex items-center gap-2">
                <div className="flex-1 text-[14px] text-text-secondary truncate bg-surface rounded-[10px] px-3 py-2">
                  {bookingLink}
                </div>
                <button
                  onClick={handleCopyLink}
                  className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface transition-colors text-accent"
                  aria-label="Скопировать ссылку"
                >
                  {copied ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <Copy className="w-5 h-5" />
                  )}
                </button>
              </div>
            </Card>

            {/* === PAYMENT SECTIONS === */}

            <div className="h-px bg-border mt-2" />

            {/* Section: Requisites */}
            <Card className="flex flex-col gap-3">
              <h2 className="text-[16px] font-semibold text-text-primary">
                Реквизиты для оплаты
              </h2>

              <div className="flex flex-col gap-3">
                <div>
                  <label className="text-[12px] text-text-secondary mb-1 block">
                    Номер карты
                  </label>
                  <input
                    type="text"
                    value={cardNumber}
                    onChange={(e) => setCardNumber(e.target.value)}
                    placeholder="2200 1234 5678 9012"
                    className="w-full h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary outline-none focus:ring-2 focus:ring-accent/30"
                  />
                </div>
                <div>
                  <label className="text-[12px] text-text-secondary mb-1 block">
                    Телефон для СБП
                  </label>
                  <input
                    type="text"
                    value={sbpPhone}
                    onChange={(e) => setSbpPhone(e.target.value)}
                    placeholder="+7 916 123 45 67"
                    className="w-full h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary outline-none focus:ring-2 focus:ring-accent/30"
                  />
                </div>
                <div>
                  <label className="text-[12px] text-text-secondary mb-1 block">
                    Название банка
                  </label>
                  <input
                    type="text"
                    value={bankName}
                    onChange={(e) => setBankName(e.target.value)}
                    placeholder="Сбербанк"
                    className="w-full h-[44px] rounded-[10px] border border-border px-3 text-[14px] text-text-primary outline-none focus:ring-2 focus:ring-accent/30"
                  />
                </div>
              </div>

              <Button
                onClick={handleSaveRequisites}
                loading={updatePaymentSettings.isPending}
              >
                Сохранить
              </Button>

              <p className="text-[12px] text-text-secondary">
                Эти данные увидит клиент при оплате
              </p>
            </Card>

            {/* Section: Robokassa */}
            <Card className="flex flex-col gap-3">
              <h2 className="text-[16px] font-semibold text-text-primary">
                Робокасса
              </h2>

              {showWizard ? (
                <RobokassaWizard
                  onComplete={() => setShowWizard(false)}
                  onCancel={() => setShowWizard(false)}
                />
              ) : hasRobokassa ? (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center gap-2">
                    <Badge variant="confirmed">Подключена</Badge>
                    {paymentSettings?.robokassa_is_test && (
                      <span className="text-[12px] text-amber-600 font-medium">
                        Тестовый режим
                      </span>
                    )}
                  </div>
                  <Button
                    variant="destructive"
                    onClick={() => setShowDisconnectDialog(true)}
                  >
                    Отключить
                  </Button>
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  <p className="text-[14px] text-text-secondary">
                    Робокасса не подключена
                  </p>
                  <Button
                    variant="secondary"
                    onClick={() => setShowWizard(true)}
                  >
                    Подключить
                  </Button>
                </div>
              )}
            </Card>

            {/* Section: Fiscalization */}
            <Card className="flex flex-col gap-3">
              <h2 className="text-[16px] font-semibold text-text-primary">
                Чеки и фискализация
              </h2>

              <div className="flex flex-wrap gap-2">
                {FISCAL_OPTIONS.map((f) => {
                  const isAutoDisabled =
                    f.value === "auto" && !hasRobokassa;
                  return (
                    <PillButton
                      key={f.value}
                      label={f.label}
                      selected={fiscalization === f.value}
                      onClick={() => handleFiscalizationChange(f.value)}
                      disabled={isAutoDisabled}
                    />
                  );
                })}
              </div>

              {/* Auto disabled caption */}
              {!hasRobokassa && (
                <p className="text-[12px] text-text-secondary -mt-1">
                  Автоматический режим требует подключения Робокассы
                </p>
              )}

              {/* Grey warning */}
              {showGreyWarning && (
                <Card className="bg-amber-50 border-amber-200">
                  <p className="text-[14px] text-amber-800 mb-3">
                    Рекомендуем выставлять чеки самозанятым для защиты от
                    штрафов ФНС
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

              {/* Receipt SNO selector */}
              {fiscalization !== "none" && (
                <div>
                  <p className="text-[12px] text-text-secondary mb-2">
                    Система налогообложения
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {SNO_OPTIONS.map((opt) => (
                      <PillButton
                        key={opt.value}
                        label={opt.label}
                        selected={receiptSno === opt.value}
                        onClick={() => setReceiptSno(opt.value)}
                      />
                    ))}
                  </div>
                </div>
              )}

              <Button
                onClick={handleSaveFiscalization}
                loading={updatePaymentSettings.isPending}
              >
                Сохранить
              </Button>

              <p className="text-[12px] text-text-secondary">
                Уровень по умолчанию. Можно изменить при каждой оплате.
              </p>
            </Card>

            {/* Payment history link */}
            <button
              onClick={() => navigate("/master/payments")}
              className="w-full text-left"
            >
              <Card className="flex items-center justify-between">
                <h2 className="text-[16px] font-semibold text-text-primary">
                  История платежей
                </h2>
                <ChevronRight className="w-5 h-5 text-text-secondary" />
              </Card>
            </button>
          </>
        )}
      </div>

      {/* Disconnect Robokassa dialog */}
      <ConfirmDialog
        isOpen={showDisconnectDialog}
        title="Отключить Робокассу?"
        message="Вы не сможете отправлять ссылки на оплату."
        confirmLabel="Отключить"
        cancelLabel="Отмена"
        variant="destructive"
        onConfirm={handleDisconnectRobokassa}
        onCancel={() => setShowDisconnectDialog(false)}
      />
    </div>
  );
}

function PillButton({
  label,
  selected,
  onClick,
  disabled = false,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`h-[44px] px-5 rounded-full text-[14px] font-medium border transition-colors ${
        selected
          ? "bg-accent/8 border-accent text-accent"
          : "border-border text-text-secondary hover:border-text-secondary"
      } ${disabled ? "opacity-50 pointer-events-none" : ""}`}
    >
      {label}
    </button>
  );
}

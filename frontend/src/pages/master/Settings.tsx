import { useState, useEffect } from "react";
import { Copy, Check } from "lucide-react";
import {
  useMasterSettings,
  useUpdateSettings,
} from "../../api/master-settings.ts";
import { Card } from "../../components/ui/Card.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { Skeleton } from "../../components/ui/Skeleton.tsx";
import { useToast } from "../../components/ui/Toast.tsx";

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

export function Settings() {
  const { data: settings, isLoading } = useMasterSettings();
  const updateSettings = useUpdateSettings();
  const toast = useToast();

  const [buffer, setBuffer] = useState(15);
  const [deadline, setDeadline] = useState(2);
  const [interval, setInterval_] = useState(30);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (settings) {
      setBuffer(settings.buffer_minutes);
      setDeadline(settings.cancellation_deadline_hours);
      setInterval_(settings.slot_interval_minutes);
    }
  }, [settings]);

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

  return (
    <div className="flex flex-col min-h-full">
      <div className="px-4 pt-8 pb-4">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Настройки
        </h1>
      </div>

      <div className="flex-1 px-4 pb-4 flex flex-col gap-4">
        {isLoading ? (
          <div className="flex flex-col gap-4">
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

            {/* Save button */}
            <Button
              onClick={handleSave}
              loading={updateSettings.isPending}
              fullWidth
            >
              Сохранить настройки
            </Button>

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
          </>
        )}
      </div>
    </div>
  );
}

function PillButton({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`h-[44px] px-5 rounded-full text-[14px] font-medium border transition-colors ${
        selected
          ? "bg-accent/8 border-accent text-accent"
          : "border-border text-text-secondary hover:border-text-secondary"
      }`}
    >
      {label}
    </button>
  );
}

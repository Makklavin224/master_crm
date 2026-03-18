import { useState } from "react";
import { Copy, Check, ExternalLink } from "lucide-react";
import { Card } from "./ui/Card.tsx";
import { Button } from "./ui/Button.tsx";
import type { ManualReceiptData } from "../api/payments.ts";

interface ReceiptDataCardProps {
  data: ManualReceiptData;
  onClose: () => void;
}

export function ReceiptDataCard({ data, onClose }: ReceiptDataCardProps) {
  const [copied, setCopied] = useState(false);

  const formattedText = [
    `Сумма: ${data.amount_display}`,
    `Услуга: ${data.service_name}`,
    `Клиент: ${data.client_name}`,
    `Дата: ${data.date}`,
  ].join("\n");

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(formattedText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: do nothing
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-[20px] font-semibold text-text-primary">
        Данные для чека
      </h3>

      <Card className="flex flex-col gap-3">
        <ReceiptLine label="Сумма" value={data.amount_display} />
        <ReceiptLine label="Услуга" value={data.service_name} />
        <ReceiptLine label="Клиент" value={data.client_name} />
        <ReceiptLine label="Дата" value={data.date} />
      </Card>

      <Button onClick={handleCopy} variant="secondary">
        {copied ? (
          <>
            <Check className="w-4 h-4" />
            Скопировано
          </>
        ) : (
          <>
            <Copy className="w-4 h-4" />
            Скопировать данные
          </>
        )}
      </Button>

      <a
        href="https://lknpd.nalog.ru/"
        target="_blank"
        rel="noopener noreferrer"
        className="h-[44px] rounded-[12px] font-semibold text-[14px] flex items-center justify-center gap-2 w-full border border-accent text-accent bg-white transition-opacity active:opacity-80"
      >
        <ExternalLink className="w-4 h-4" />
        Открыть Мой Налог
      </a>

      <Button onClick={onClose}>Готово</Button>
    </div>
  );
}

function ReceiptLine({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-baseline">
      <span className="text-[12px] text-text-secondary">{label}</span>
      <span className="text-[16px] font-semibold text-text-primary">
        {value}
      </span>
    </div>
  );
}

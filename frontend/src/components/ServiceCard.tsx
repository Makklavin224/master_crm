import { Check } from "lucide-react";
import { Card } from "./ui/Card.tsx";
import { formatPrice, formatDuration } from "../lib/format.ts";

interface ServiceCardProps {
  emoji: string;
  name: string;
  durationMinutes: number;
  priceKopecks: number;
  selected?: boolean;
  onClick?: () => void;
}

export function ServiceCard({
  emoji,
  name,
  durationMinutes,
  priceKopecks,
  selected = false,
  onClick,
}: ServiceCardProps) {
  return (
    <Card
      className={`flex items-start gap-3 cursor-pointer transition-colors active:bg-surface ${
        selected ? "border-accent ring-1 ring-accent" : ""
      }`}
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onClick?.();
        }
      }}
    >
      <span className="text-[32px] leading-none shrink-0">{emoji}</span>
      <div className="flex-1 min-w-0">
        <div className="text-[16px] font-semibold text-text-primary truncate">
          {name}
        </div>
        <div className="text-[14px] text-text-secondary mt-0.5">
          {formatDuration(durationMinutes)} &middot; {formatPrice(priceKopecks)}
        </div>
      </div>
      {selected && (
        <div className="shrink-0 w-6 h-6 rounded-full bg-accent flex items-center justify-center">
          <Check className="w-4 h-4 text-white" />
        </div>
      )}
    </Card>
  );
}

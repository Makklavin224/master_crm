interface Slot {
  time: string;
}

interface SlotGridProps {
  slots: Slot[];
  selectedTime: string | null;
  onSelect: (time: string) => void;
}

export function SlotGrid({ slots, selectedTime, onSelect }: SlotGridProps) {
  return (
    <div className="grid grid-cols-3 max-[374px]:grid-cols-2 gap-2">
      {slots.map((slot) => {
        const isSelected = slot.time === selectedTime;

        return (
          <button
            key={slot.time}
            onClick={() => onSelect(slot.time)}
            className={`h-[48px] rounded-[10px] text-[14px] font-semibold transition-colors ${
              isSelected
                ? "bg-accent-light border border-accent text-accent"
                : "bg-white border border-border text-text-primary hover:bg-surface"
            }`}
          >
            {slot.time}
          </button>
        );
      })}
    </div>
  );
}

interface PillButtonProps {
  label: string;
  selected: boolean;
  onClick: () => void;
  disabled?: boolean;
}

export function PillButton({ label, selected, onClick, disabled = false }: PillButtonProps) {
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

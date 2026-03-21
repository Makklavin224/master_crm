interface StickyBookButtonProps {
  onClick: () => void;
}

export default function StickyBookButton({ onClick }: StickyBookButtonProps) {
  return (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-border px-4 pt-3 pb-[max(0.75rem,env(safe-area-inset-bottom))] z-50">
      <button
        onClick={onClick}
        className="w-full bg-accent text-white rounded-xl py-3.5 font-semibold text-base active:opacity-90 transition-opacity"
      >
        Записаться
      </button>
    </div>
  );
}

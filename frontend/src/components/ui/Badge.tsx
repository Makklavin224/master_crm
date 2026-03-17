type BadgeVariant = "confirmed" | "pending" | "cancelled";

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, string> = {
  confirmed: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  cancelled: "bg-red-50 text-red-700",
};

export function Badge({ variant, children }: BadgeProps) {
  return (
    <span
      className={`rounded-full px-[8px] py-[2px] text-[12px] font-semibold inline-block ${variantStyles[variant]}`}
    >
      {children}
    </span>
  );
}

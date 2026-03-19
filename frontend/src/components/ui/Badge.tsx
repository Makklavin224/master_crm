type BadgeVariant = "confirmed" | "pending" | "cancelled";

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
}

const variantStyles: Record<BadgeVariant, { bg: string; text: string }> = {
  confirmed: { bg: "var(--color-badge-confirmed-bg, #ecfdf5)", text: "var(--color-badge-confirmed-text, #047857)" },
  pending: { bg: "var(--color-badge-pending-bg, #fffbeb)", text: "var(--color-badge-pending-text, #b45309)" },
  cancelled: { bg: "var(--color-badge-cancelled-bg, #fef2f2)", text: "var(--color-badge-cancelled-text, #b91c1c)" },
};

export function Badge({ variant, children }: BadgeProps) {
  const colors = variantStyles[variant];
  return (
    <span
      className="rounded-full px-[8px] py-[2px] text-[12px] font-semibold inline-block"
      style={{ backgroundColor: colors.bg, color: colors.text }}
    >
      {children}
    </span>
  );
}

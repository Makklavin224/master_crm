import { type ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive";
  loading?: boolean;
  fullWidth?: boolean;
}

export function Button({
  variant = "primary",
  loading = false,
  fullWidth = true,
  disabled,
  children,
  className = "",
  ...props
}: ButtonProps) {
  const base =
    "h-[44px] rounded-[12px] font-semibold text-[14px] flex items-center justify-center gap-2 transition-opacity active:opacity-80";
  const width = fullWidth ? "w-full" : "";

  const variants: Record<string, string> = {
    primary: "bg-accent text-white",
    secondary: "bg-white text-accent border border-accent",
    destructive: "bg-destructive text-white",
  };

  const disabledStyle =
    disabled || loading ? "opacity-50 pointer-events-none" : "";

  return (
    <button
      className={`${base} ${width} ${variants[variant]} ${disabledStyle} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}

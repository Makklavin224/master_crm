import { type InputHTMLAttributes, useId } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = "", id, ...props }: InputProps) {
  const generatedId = useId();
  const inputId = id || generatedId;
  const errorId = `${inputId}-error`;

  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={inputId} className="text-[14px] text-text-primary font-medium">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`h-[44px] rounded-[10px] border px-3 text-[14px] text-text-primary placeholder:text-[12px] placeholder:text-text-secondary outline-none transition-colors focus:ring-2 focus:ring-accent/30 ${
          error ? "border-destructive" : "border-border"
        } ${className}`}
        aria-describedby={error ? errorId : undefined}
        aria-invalid={error ? true : undefined}
        {...props}
      />
      {error && (
        <span id={errorId} className="text-[12px] text-destructive">
          {error}
        </span>
      )}
    </div>
  );
}

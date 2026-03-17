import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  heading: string;
  body?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, heading, body, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-4">
      {icon && (
        <div className="text-text-secondary mb-3" style={{ fontSize: "48px" }}>
          {icon}
        </div>
      )}
      <h3 className="text-[16px] font-semibold text-text-primary mb-1">
        {heading}
      </h3>
      {body && (
        <p className="text-[14px] text-text-secondary max-w-[280px]">{body}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

import { TOTAL_BOOKING_STEPS } from "../../lib/constants.ts";

interface StepIndicatorProps {
  currentStep: number;
  totalSteps?: number;
}

export function StepIndicator({
  currentStep,
  totalSteps = TOTAL_BOOKING_STEPS,
}: StepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-3">
      {Array.from({ length: totalSteps }, (_, i) => {
        const step = i + 1;
        const isCompleted = step < currentStep;
        const isCurrent = step === currentStep;

        return (
          <div
            key={step}
            className={`w-2 h-2 rounded-full transition-colors ${
              isCompleted || isCurrent ? "bg-accent" : "bg-gray-300"
            }`}
            aria-label={`Шаг ${step}${isCurrent ? " (текущий)" : ""}${isCompleted ? " (завершён)" : ""}`}
          />
        );
      })}
    </div>
  );
}

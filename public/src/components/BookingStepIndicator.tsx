const STEP_LABELS = ["Услуга", "Дата", "Время", "Данные", "Готово"];

interface BookingStepIndicatorProps {
  currentStep: number;
  totalSteps?: number;
}

export default function BookingStepIndicator({
  currentStep,
  totalSteps = 5,
}: BookingStepIndicatorProps) {
  return (
    <div className="flex items-center justify-center gap-2 py-3 px-4">
      {Array.from({ length: totalSteps }, (_, i) => {
        const step = i + 1;
        const isCompleted = step < currentStep;
        const isCurrent = step === currentStep;

        return (
          <div key={step} className="flex flex-col items-center gap-1">
            <div className="flex items-center">
              {/* Dot */}
              <div
                className={`w-2 h-2 rounded-full transition-colors ${
                  isCompleted || isCurrent ? "bg-accent" : "bg-gray-300"
                }`}
                aria-label={`Шаг ${step}${isCurrent ? " (текущий)" : ""}${isCompleted ? " (завершён)" : ""}`}
              />
              {/* Connector line */}
              {step < totalSteps && (
                <div
                  className={`w-8 h-0.5 ml-2 transition-colors ${
                    isCompleted ? "bg-accent" : "bg-gray-300"
                  }`}
                />
              )}
            </div>
            <span
              className={`text-[10px] leading-tight ${
                isCurrent
                  ? "text-accent font-medium"
                  : isCompleted
                    ? "text-text-secondary"
                    : "text-gray-400"
              }`}
            >
              {STEP_LABELS[i]}
            </span>
          </div>
        );
      })}
    </div>
  );
}

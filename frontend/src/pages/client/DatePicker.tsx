import { StepIndicator } from "../../components/ui/StepIndicator.tsx";

export function DatePicker() {
  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={2} />
      <div className="px-4 pt-2 pb-8">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Выберите дату
        </h1>
      </div>
    </div>
  );
}

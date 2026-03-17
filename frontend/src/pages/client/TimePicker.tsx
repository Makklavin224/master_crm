import { StepIndicator } from "../../components/ui/StepIndicator.tsx";

export function TimePicker() {
  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={3} />
      <div className="px-4 pt-2 pb-8">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Выберите время
        </h1>
      </div>
    </div>
  );
}

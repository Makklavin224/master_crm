import { StepIndicator } from "../../components/ui/StepIndicator.tsx";

export function BookingForm() {
  return (
    <div className="flex flex-col min-h-full">
      <StepIndicator currentStep={4} />
      <div className="px-4 pt-2 pb-8">
        <h1 className="text-[20px] font-semibold text-text-primary">
          Ваши данные
        </h1>
      </div>
    </div>
  );
}

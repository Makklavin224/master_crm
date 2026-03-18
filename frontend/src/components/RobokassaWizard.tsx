import { useState } from "react";
import { CheckCircle, ExternalLink } from "lucide-react";
import { Card } from "./ui/Card.tsx";
import { Button } from "./ui/Button.tsx";
import { useSetupRobokassa } from "../api/master-settings.ts";
import { useToast } from "./ui/Toast.tsx";

const HASH_ALGORITHMS = [
  { value: "md5", label: "MD5" },
  { value: "sha256", label: "SHA-256" },
  { value: "sha512", label: "SHA-512" },
];

interface RobokassaWizardProps {
  onComplete: () => void;
  onCancel: () => void;
}

export function RobokassaWizard({
  onComplete,
  onCancel,
}: RobokassaWizardProps) {
  const [step, setStep] = useState(1);
  const [merchantLogin, setMerchantLogin] = useState("");
  const [password1, setPassword1] = useState("");
  const [password2, setPassword2] = useState("");
  const [isTest, setIsTest] = useState(false);
  const [hashAlgorithm, setHashAlgorithm] = useState("sha256");
  const [errors, setErrors] = useState<Record<string, string>>({});

  const setupRobokassa = useSetupRobokassa();
  const toast = useToast();

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!merchantLogin.trim()) {
      newErrors.merchantLogin = "Введите логин магазина";
    }
    if (!password1.trim()) {
      newErrors.password1 = "Введите пароль #1";
    }
    if (!password2.trim()) {
      newErrors.password2 = "Введите пароль #2";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;
    setupRobokassa.mutate(
      {
        merchant_login: merchantLogin.trim(),
        password1: password1.trim(),
        password2: password2.trim(),
        is_test: isTest,
        hash_algorithm: hashAlgorithm,
      },
      {
        onSuccess: () => setStep(3),
        onError: () => toast.error("Не удалось подключить Робокассу"),
      },
    );
  };

  // --- Step 1: Instructions ---
  if (step === 1) {
    return (
      <div className="flex flex-col gap-4">
        <h3 className="text-[16px] font-semibold text-text-primary">
          Подключение Робокассы
        </h3>

        <Card className="flex flex-col gap-3">
          <InstructionStep number={1}>
            Зарегистрируйтесь на{" "}
            <a
              href="https://robokassa.com"
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent underline inline-flex items-center gap-1"
            >
              robokassa.com
              <ExternalLink className="w-3 h-3 inline" />
            </a>
          </InstructionStep>
          <InstructionStep number={2}>
            Создайте магазин в личном кабинете
          </InstructionStep>
          <InstructionStep number={3}>
            Скопируйте данные со страницы технических настроек
          </InstructionStep>
        </Card>

        <div className="flex gap-2">
          <Button variant="secondary" onClick={onCancel} fullWidth>
            Отмена
          </Button>
          <Button onClick={() => setStep(2)} fullWidth>
            Далее
          </Button>
        </div>
      </div>
    );
  }

  // --- Step 2: Credentials Form ---
  if (step === 2) {
    return (
      <div className="flex flex-col gap-4">
        <h3 className="text-[16px] font-semibold text-text-primary">
          Технические настройки
        </h3>

        <div className="flex flex-col gap-3">
          <InputField
            label="Логин магазина"
            value={merchantLogin}
            onChange={setMerchantLogin}
            error={errors.merchantLogin}
            placeholder="my_shop"
          />
          <InputField
            label="Пароль #1"
            value={password1}
            onChange={setPassword1}
            error={errors.password1}
            type="password"
          />
          <InputField
            label="Пароль #2"
            value={password2}
            onChange={setPassword2}
            error={errors.password2}
            type="password"
          />
        </div>

        {/* Test mode toggle */}
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={isTest}
            onChange={(e) => setIsTest(e.target.checked)}
            className="w-5 h-5 rounded accent-accent"
          />
          <span className="text-[14px] text-text-primary">Тестовый режим</span>
        </label>

        {/* Hash algorithm */}
        <div>
          <p className="text-[12px] text-text-secondary mb-2">
            Алгоритм хеширования
          </p>
          <div className="flex flex-wrap gap-2">
            {HASH_ALGORITHMS.map((alg) => (
              <button
                key={alg.value}
                onClick={() => setHashAlgorithm(alg.value)}
                className={`h-[44px] px-5 rounded-full text-[14px] font-medium border transition-colors ${
                  hashAlgorithm === alg.value
                    ? "bg-accent/8 border-accent text-accent"
                    : "border-border text-text-secondary hover:border-text-secondary"
                }`}
              >
                {alg.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setStep(1)} fullWidth>
            Назад
          </Button>
          <Button
            onClick={handleSubmit}
            loading={setupRobokassa.isPending}
            fullWidth
          >
            Подключить
          </Button>
        </div>
      </div>
    );
  }

  // --- Step 3: Success ---
  return (
    <div className="flex flex-col gap-4 items-center text-center py-4">
      <CheckCircle className="w-16 h-16 text-success" />
      <h3 className="text-[20px] font-semibold text-text-primary">
        Робокасса подключена!
      </h3>
      <p className="text-[14px] text-text-secondary">
        Теперь вы можете отправлять ссылки на оплату через СБП
      </p>
      <Button onClick={onComplete} className="mt-2">
        Готово
      </Button>
    </div>
  );
}

function InstructionStep({
  number,
  children,
}: {
  number: number;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3 items-start">
      <div className="w-6 h-6 rounded-full bg-accent/8 text-accent text-[12px] font-semibold flex items-center justify-center shrink-0 mt-0.5">
        {number}
      </div>
      <p className="text-[14px] text-text-primary leading-snug">{children}</p>
    </div>
  );
}

function InputField({
  label,
  value,
  onChange,
  error,
  type = "text",
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
  type?: string;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="text-[12px] text-text-secondary mb-1 block">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full h-[44px] rounded-[10px] border px-3 text-[14px] text-text-primary outline-none focus:ring-2 focus:ring-accent/30 ${
          error ? "border-red-500" : "border-border"
        }`}
      />
      {error && (
        <p className="text-[12px] text-red-500 mt-1">{error}</p>
      )}
    </div>
  );
}

import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import {
  useMasterServices,
  useCreateService,
  useUpdateService,
  type ServiceCreate,
} from "../../api/master-services.ts";
import { Input } from "../../components/ui/Input.tsx";
import { Button } from "../../components/ui/Button.tsx";
import { useToast } from "../../components/ui/Toast.tsx";

const DURATION_OPTIONS = [15, 30, 45, 60, 90, 120];

export function ServiceForm() {
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id && id !== "new";
  const navigate = useNavigate();
  const toast = useToast();

  const { data: services } = useMasterServices();
  const createService = useCreateService();
  const updateService = useUpdateService();

  const [name, setName] = useState("");
  const [duration, setDuration] = useState(60);
  const [priceRubles, setPriceRubles] = useState("");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Prefill for edit mode
  useEffect(() => {
    if (isEdit && services) {
      const service = services.find((s) => s.id === id);
      if (service) {
        setName(service.name);
        setDuration(service.duration_minutes);
        setPriceRubles(String(Math.floor(service.price / 100)));
        setCategory(service.category || "");
        setDescription(service.description || "");
      }
    }
  }, [isEdit, id, services]);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "Укажите название услуги";
    if (!priceRubles.trim() || isNaN(Number(priceRubles)))
      errs.price = "Укажите стоимость";
    if (!duration) errs.duration = "Укажите длительность";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = () => {
    if (!validate()) return;

    const data: ServiceCreate = {
      name: name.trim(),
      duration_minutes: duration,
      price: Math.round(Number(priceRubles) * 100), // rubles -> kopecks
      category: category.trim() || null,
      description: description.trim() || null,
    };

    if (isEdit) {
      updateService.mutate(
        { id: id!, data },
        {
          onSuccess: () => {
            toast.success("Услуга сохранена");
            navigate("/master/services");
          },
          onError: () => toast.error("Не удалось сохранить"),
        },
      );
    } else {
      createService.mutate(data, {
        onSuccess: () => {
          toast.success("Услуга сохранена");
          navigate("/master/services");
        },
        onError: () => toast.error("Не удалось создать услугу"),
      });
    }
  };

  const isSubmitting = createService.isPending || updateService.isPending;

  return (
    <div className="flex flex-col min-h-full">
      {/* Header */}
      <div className="px-4 pt-8 pb-4 flex items-center gap-3">
        <button
          onClick={() => navigate("/master/services")}
          className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-surface transition-colors"
          aria-label="Назад"
        >
          <ArrowLeft className="w-5 h-5 text-text-primary" />
        </button>
        <h1 className="text-[20px] font-semibold text-text-primary">
          {isEdit ? "Редактировать услугу" : "Новая услуга"}
        </h1>
      </div>

      {/* Form */}
      <div className="flex-1 px-4 pb-4 flex flex-col gap-4">
        <Input
          label="Название услуги"
          placeholder="Стрижка мужская"
          value={name}
          onChange={(e) => setName(e.target.value)}
          error={errors.name}
        />

        {/* Duration selector */}
        <div className="flex flex-col gap-1">
          <label className="text-[14px] text-text-primary font-medium">
            Длительность
          </label>
          <div className="flex flex-wrap gap-2">
            {DURATION_OPTIONS.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => setDuration(opt)}
                className={`h-[44px] px-4 rounded-[10px] text-[14px] font-medium border transition-colors ${
                  duration === opt
                    ? "bg-accent/8 border-accent text-accent"
                    : "border-border text-text-secondary hover:border-text-secondary"
                }`}
              >
                {opt >= 60 ? `${opt / 60} ч` : `${opt} мин`}
                {opt >= 60 && opt % 60 !== 0
                  ? ` ${opt % 60} мин`
                  : ""}
              </button>
            ))}
          </div>
          {errors.duration && (
            <span className="text-[12px] text-destructive">
              {errors.duration}
            </span>
          )}
        </div>

        <Input
          label="Стоимость, ₽"
          placeholder="0"
          type="number"
          inputMode="numeric"
          value={priceRubles}
          onChange={(e) => setPriceRubles(e.target.value)}
          error={errors.price}
        />

        <Input
          label="Категория"
          placeholder="Волосы"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        />

        <div className="flex flex-col gap-1">
          <label className="text-[14px] text-text-primary font-medium">
            Описание
          </label>
          <textarea
            placeholder="Расскажите подробнее об услуге"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            className="rounded-[10px] border border-border px-3 py-3 text-[14px] text-text-primary placeholder:text-[12px] placeholder:text-text-secondary outline-none transition-colors focus:ring-2 focus:ring-accent/30 resize-none"
          />
        </div>
      </div>

      {/* Submit */}
      <div className="px-4 pb-6">
        <Button onClick={handleSubmit} loading={isSubmitting} fullWidth>
          Сохранить настройки
        </Button>
      </div>
    </div>
  );
}

import { useEffect } from "react";
import { Modal, Form, Input, InputNumber, Switch, App } from "antd";
import type { ServiceRead } from "../api/services";
import { useCreateService, useUpdateService } from "../api/services";

interface ServiceModalProps {
  open: boolean;
  onClose: () => void;
  service: ServiceRead | null;
}

interface ServiceFormValues {
  name: string;
  description?: string;
  duration_minutes: number;
  price: number;
  category?: string;
  is_active?: boolean;
}

export function ServiceModal({ open, onClose, service }: ServiceModalProps) {
  const [form] = Form.useForm<ServiceFormValues>();
  const createMutation = useCreateService();
  const updateMutation = useUpdateService();
  const { message: messageApi } = App.useApp();

  const isEdit = service !== null;

  useEffect(() => {
    if (open) {
      if (service) {
        form.setFieldsValue({
          name: service.name,
          description: service.description || undefined,
          duration_minutes: service.duration_minutes,
          price: service.price / 100,
          category: service.category || undefined,
          is_active: service.is_active,
        });
      } else {
        form.resetFields();
      }
    }
  }, [open, service, form]);

  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      const payload = {
        ...values,
        price: Math.round(values.price * 100),
      };

      if (isEdit && service) {
        await updateMutation.mutateAsync({
          id: service.id,
          data: payload,
        });
        messageApi.success("Услуга обновлена");
      } else {
        await createMutation.mutateAsync(payload);
        messageApi.success("Услуга создана");
      }
      onClose();
    } catch {
      // Validation or mutation error -- antd form shows field errors
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;

  return (
    <Modal
      title={isEdit ? "Редактировать услугу" : "Новая услуга"}
      open={open}
      onOk={handleOk}
      onCancel={onClose}
      okText={isEdit ? "Сохранить" : "Создать"}
      cancelText="Отмена"
      confirmLoading={isPending}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        style={{ marginTop: 16 }}
      >
        <Form.Item
          name="name"
          label="Название"
          rules={[
            { required: true, message: "Введите название" },
            { max: 255, message: "Максимум 255 символов" },
          ]}
        >
          <Input placeholder="Например: Стрижка женская" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Описание"
        >
          <Input.TextArea
            rows={3}
            placeholder="Описание услуги (необязательно)"
          />
        </Form.Item>

        <Form.Item
          name="duration_minutes"
          label="Длительность"
          rules={[
            { required: true, message: "Укажите длительность" },
            {
              type: "number",
              min: 5,
              max: 480,
              message: "От 5 до 480 минут",
            },
          ]}
        >
          <InputNumber
            min={5}
            max={480}
            suffix="мин"
            style={{ width: "100%" }}
            placeholder="60"
          />
        </Form.Item>

        <Form.Item
          name="price"
          label="Цена"
          rules={[
            { required: true, message: "Укажите цену" },
            { type: "number", min: 0, message: "Цена не может быть отрицательной" },
          ]}
        >
          <InputNumber
            min={0}
            step={50}
            suffix="руб"
            style={{ width: "100%" }}
            placeholder="1500"
          />
        </Form.Item>

        <Form.Item
          name="category"
          label="Категория"
        >
          <Input placeholder="Например: Стрижки, Маникюр" />
        </Form.Item>

        {isEdit && (
          <Form.Item
            name="is_active"
            label="Активна"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        )}
      </Form>
    </Modal>
  );
}

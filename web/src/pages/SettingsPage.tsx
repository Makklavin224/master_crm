import { useState, useEffect, useCallback } from "react";
import {
  App,
  Badge,
  Button,
  Card,
  DatePicker,
  Descriptions,
  Form,
  Input,
  Modal,
  Popconfirm,
  Radio,
  Select,
  Spin,
  Switch,
  Table,
  Tabs,
  TimePicker,
  Upload,
} from "antd";
import { DeleteOutlined, LeftOutlined, PlusOutlined, RightOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import {
  useSettings,
  useUpdateSettings,
  useNotificationSettings,
  useUpdateNotificationSettings,
  usePaymentSettings,
  useUpdatePaymentSettings,
  useBindInn,
  useUnbindInn,
  useSetupRobokassa,
  useDisconnectRobokassa,
  useProfileSettings,
  useUpdateProfileSettings,
  useScheduleTemplate,
  useUpdateScheduleTemplate,
  useScheduleExceptions,
  useCreateScheduleException,
  useDeleteScheduleException,
  usePortfolio,
  useUploadPhoto,
  useDeletePhoto,
  useUpdatePhoto,
  useReorderPhotos,
  type ScheduleDayEntry,
} from "../api/settings";
import { useServices } from "../api/services";
import { QRCodeSVG } from "qrcode.react";
import { useAuth } from "../stores/auth";
import type { ColumnsType } from "antd/es/table";

// --- Day names ---
const DAY_NAMES = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

const PUBLIC_DOMAIN = "https://moiokoshki.ru";

// =============================================
// Tab 0: My Page (booking link + QR code)
// =============================================

function MyPageTab({ onSwitchTab }: { onSwitchTab?: (key: string) => void }) {
  const { data: profileSettings, isLoading } = useProfileSettings();
  const profile = useAuth((s) => s.profile);
  const { message: messageApi } = App.useApp();

  if (isLoading) return <Spin />;

  const username = profileSettings?.username;

  if (!username) {
    return (
      <Card>
        <div style={{ textAlign: "center", padding: "32px 0" }}>
          <p style={{ fontSize: 16, marginBottom: 16 }}>
            Задайте имя пользователя в разделе &laquo;Профиль&raquo; чтобы получить ссылку на вашу страницу
          </p>
          <Button type="primary" onClick={() => onSwitchTab?.("profile")}>
            Перейти в Профиль
          </Button>
        </div>
      </Card>
    );
  }

  const bookingUrl = `${PUBLIC_DOMAIN}/m/${username}`;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(bookingUrl);
      messageApi.success("Ссылка скопирована");
    } catch {
      messageApi.error("Не удалось скопировать");
    }
  };

  return (
    <>
      {/* Booking link */}
      <Card title="Ссылка для записи" size="small" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <Input
            value={bookingUrl}
            readOnly
            style={{ flex: 1 }}
          />
          <Button type="primary" onClick={handleCopy}>
            Скопировать
          </Button>
        </div>
      </Card>

      {/* QR Code */}
      <Card title="QR-код" size="small" style={{ marginBottom: 24 }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
          <QRCodeSVG value={bookingUrl} size={200} />
          <p style={{ color: "#888", textAlign: "center", margin: 0 }}>
            Распечатайте и повесьте в салоне или добавьте на визитку
          </p>
        </div>
      </Card>

      {/* Preview */}
      <Card title="Предпросмотр" size="small">
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="Имя">
            {profile?.name ?? profileSettings?.name ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label="Специализация">
            {profileSettings?.specialization ?? "Не указана"}
          </Descriptions.Item>
          <Descriptions.Item label="Город">
            {profileSettings?.city ?? "Не указан"}
          </Descriptions.Item>
          <Descriptions.Item label="URL">
            {`moiokoshki.ru/m/${username}`}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </>
  );
}

// =============================================
// Tab 1: Schedule
// =============================================

function BookingSettingsSection() {
  const { data, isLoading } = useSettings();
  const mutation = useUpdateSettings();
  const [form] = Form.useForm();
  const { message: messageApi } = App.useApp();

  useEffect(() => {
    if (data) {
      form.setFieldsValue(data);
    }
  }, [data, form]);

  const onFinish = useCallback(
    async (values: Record<string, unknown>) => {
      try {
        await mutation.mutateAsync(values);
        messageApi.success("Настройки сохранены");
      } catch {
        messageApi.error("Ошибка сохранения");
      }
    },
    [mutation, messageApi],
  );

  if (isLoading) return <Spin />;

  return (
    <Card title="Настройки записи" size="small" style={{ marginBottom: 24 }}>
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item
          name="buffer_minutes"
          label="Буфер между записями"
        >
          <Select
            options={[
              { value: 0, label: "0 мин" },
              { value: 5, label: "5 мин" },
              { value: 10, label: "10 мин" },
              { value: 15, label: "15 мин" },
              { value: 30, label: "30 мин" },
              { value: 60, label: "60 мин" },
            ]}
            style={{ maxWidth: 200 }}
          />
        </Form.Item>
        <Form.Item
          name="cancellation_deadline_hours"
          label="Дедлайн отмены"
        >
          <Select
            options={[
              { value: 0, label: "0 ч" },
              { value: 1, label: "1 ч" },
              { value: 2, label: "2 ч" },
              { value: 4, label: "4 ч" },
              { value: 6, label: "6 ч" },
              { value: 12, label: "12 ч" },
              { value: 24, label: "24 ч" },
              { value: 48, label: "48 ч" },
            ]}
            style={{ maxWidth: 200 }}
          />
        </Form.Item>
        <Form.Item
          name="slot_interval_minutes"
          label="Интервал слотов"
        >
          <Radio.Group>
            <Radio value={15}>15 мин</Radio>
            <Radio value={30}>30 мин</Radio>
          </Radio.Group>
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={mutation.isPending}>
          Сохранить
        </Button>
      </Form>
    </Card>
  );
}

interface ScheduleRow extends ScheduleDayEntry {
  key: number;
  dayName: string;
}

function WeeklyScheduleSection() {
  const { data, isLoading } = useScheduleTemplate();
  const mutation = useUpdateScheduleTemplate();
  const [rows, setRows] = useState<ScheduleRow[]>([]);
  const { message: messageApi } = App.useApp();

  useEffect(() => {
    if (data && data.length === 7) {
      const sorted = [...data].sort((a, b) => a.day_of_week - b.day_of_week);
      setRows(
        sorted.map((d) => ({
          ...d,
          key: d.day_of_week,
          dayName: DAY_NAMES[d.day_of_week],
        })),
      );
    }
  }, [data]);

  const updateRow = useCallback(
    (idx: number, patch: Partial<ScheduleRow>) => {
      setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
    },
    [],
  );

  const handleSave = useCallback(async () => {
    try {
      const days: ScheduleDayEntry[] = rows.map(
        ({ day_of_week, start_time, end_time, break_start, break_end, is_working }) => ({
          day_of_week,
          start_time,
          end_time,
          break_start,
          break_end,
          is_working,
        }),
      );
      await mutation.mutateAsync({ days });
      messageApi.success("Расписание сохранено");
    } catch {
      messageApi.error("Ошибка сохранения");
    }
  }, [rows, mutation, messageApi]);

  if (isLoading) return <Spin />;

  const columns: ColumnsType<ScheduleRow> = [
    { title: "День", dataIndex: "dayName", width: 60 },
    {
      title: "Рабочий",
      width: 80,
      render: (_, record, idx) => (
        <Switch
          checked={record.is_working}
          onChange={(v) => updateRow(idx, { is_working: v })}
        />
      ),
    },
    {
      title: "Начало",
      width: 120,
      render: (_, record, idx) => (
        <TimePicker
          value={record.start_time ? dayjs(record.start_time, "HH:mm:ss") : null}
          format="HH:mm"
          disabled={!record.is_working}
          minuteStep={15}
          onChange={(v) => updateRow(idx, { start_time: v?.format("HH:mm:ss") ?? "09:00:00" })}
        />
      ),
    },
    {
      title: "Конец",
      width: 120,
      render: (_, record, idx) => (
        <TimePicker
          value={record.end_time ? dayjs(record.end_time, "HH:mm:ss") : null}
          format="HH:mm"
          disabled={!record.is_working}
          minuteStep={15}
          onChange={(v) => updateRow(idx, { end_time: v?.format("HH:mm:ss") ?? "18:00:00" })}
        />
      ),
    },
    {
      title: "Перерыв",
      width: 220,
      render: (_, record, idx) => (
        <TimePicker.RangePicker
          value={
            record.break_start && record.break_end
              ? [dayjs(record.break_start, "HH:mm:ss"), dayjs(record.break_end, "HH:mm:ss")]
              : null
          }
          format="HH:mm"
          disabled={!record.is_working}
          minuteStep={15}
          onChange={(values) => {
            if (values && values[0] && values[1]) {
              updateRow(idx, {
                break_start: values[0].format("HH:mm:ss"),
                break_end: values[1].format("HH:mm:ss"),
              });
            } else {
              updateRow(idx, { break_start: null, break_end: null });
            }
          }}
        />
      ),
    },
  ];

  return (
    <Card title="Еженедельное расписание" size="small" style={{ marginBottom: 24 }}>
      <Table<ScheduleRow>
        columns={columns}
        dataSource={rows}
        pagination={false}
        size="small"
      />
      <Button
        type="primary"
        onClick={handleSave}
        loading={mutation.isPending}
        style={{ marginTop: 16 }}
      >
        Сохранить расписание
      </Button>
    </Card>
  );
}

interface ExceptionRow {
  id: string;
  exception_date: string;
  is_day_off: boolean;
  start_time: string | null;
  end_time: string | null;
  reason: string | null;
}

function ExceptionsSection() {
  const { data, isLoading } = useScheduleExceptions();
  const createMutation = useCreateScheduleException();
  const deleteMutation = useDeleteScheduleException();
  const [modalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const { message: messageApi } = App.useApp();
  const isDayOff = Form.useWatch("is_day_off", form);

  const handleCreate = useCallback(async () => {
    try {
      const values = await form.validateFields();
      await createMutation.mutateAsync({
        exception_date: values.exception_date.format("YYYY-MM-DD"),
        is_day_off: values.is_day_off ?? true,
        start_time: values.start_time?.format("HH:mm:ss") ?? null,
        end_time: values.end_time?.format("HH:mm:ss") ?? null,
        reason: values.reason || null,
      });
      messageApi.success("Исключение добавлено");
      setModalOpen(false);
      form.resetFields();
    } catch {
      // Validation failed or API error
    }
  }, [form, createMutation, messageApi]);

  const handleDelete = useCallback(
    async (id: string) => {
      try {
        await deleteMutation.mutateAsync(id);
        messageApi.success("Исключение удалено");
      } catch {
        messageApi.error("Ошибка удаления");
      }
    },
    [deleteMutation, messageApi],
  );

  const columns: ColumnsType<ExceptionRow> = [
    {
      title: "Дата",
      dataIndex: "exception_date",
      render: (val: string) => dayjs(val).format("DD.MM.YYYY"),
    },
    {
      title: "Тип",
      dataIndex: "is_day_off",
      render: (v: boolean) => (v ? "Выходной" : "Изменённый график"),
    },
    {
      title: "Причина",
      dataIndex: "reason",
      render: (val: string | null) => val ?? "-",
    },
    {
      title: "",
      width: 60,
      render: (_, record) => (
        <Popconfirm title="Удалить исключение?" onConfirm={() => handleDelete(record.id)}>
          <Button type="text" danger icon={<DeleteOutlined />} size="small" />
        </Popconfirm>
      ),
    },
  ];

  return (
    <Card
      title="Исключения"
      size="small"
      extra={
        <Button
          icon={<PlusOutlined />}
          type="primary"
          size="small"
          onClick={() => setModalOpen(true)}
        >
          Добавить
        </Button>
      }
    >
      <Table<ExceptionRow>
        columns={columns}
        dataSource={(data as ExceptionRow[]) ?? []}
        loading={isLoading}
        rowKey="id"
        pagination={false}
        size="small"
      />
      <Modal
        title="Новое исключение"
        open={modalOpen}
        onOk={handleCreate}
        onCancel={() => {
          setModalOpen(false);
          form.resetFields();
        }}
        confirmLoading={createMutation.isPending}
      >
        <Form form={form} layout="vertical" initialValues={{ is_day_off: true }}>
          <Form.Item
            name="exception_date"
            label="Дата"
            rules={[{ required: true, message: "Выберите дату" }]}
          >
            <DatePicker format="DD.MM.YYYY" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="is_day_off" label="Выходной" valuePropName="checked">
            <Switch />
          </Form.Item>
          {!isDayOff && (
            <>
              <Form.Item name="start_time" label="Начало">
                <TimePicker format="HH:mm" minuteStep={15} style={{ width: "100%" }} />
              </Form.Item>
              <Form.Item name="end_time" label="Конец">
                <TimePicker format="HH:mm" minuteStep={15} style={{ width: "100%" }} />
              </Form.Item>
            </>
          )}
          <Form.Item name="reason" label="Причина">
            <Input placeholder="Необязательно" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
}

function ScheduleTab() {
  return (
    <>
      <BookingSettingsSection />
      <WeeklyScheduleSection />
      <ExceptionsSection />
    </>
  );
}

// =============================================
// Tab 2: Notifications
// =============================================

function NotificationsTab() {
  const { data, isLoading } = useNotificationSettings();
  const mutation = useUpdateNotificationSettings();
  const [form] = Form.useForm();
  const { message: messageApi } = App.useApp();

  useEffect(() => {
    if (data) {
      form.setFieldsValue(data);
    }
  }, [data, form]);

  const remindersEnabled = Form.useWatch("reminders_enabled", form);

  const onFinish = useCallback(
    async (values: Record<string, unknown>) => {
      try {
        await mutation.mutateAsync(values);
        messageApi.success("Настройки уведомлений сохранены");
      } catch {
        messageApi.error("Ошибка сохранения");
      }
    },
    [mutation, messageApi],
  );

  if (isLoading) return <Spin />;

  const hourOptions = [
    { value: 1, label: "1 ч" },
    { value: 2, label: "2 ч" },
    { value: 6, label: "6 ч" },
    { value: 12, label: "12 ч" },
    { value: 24, label: "24 ч" },
  ];

  return (
    <Card title="Уведомления">
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item
          name="reminders_enabled"
          label="Автоматические напоминания"
          valuePropName="checked"
        >
          <Switch />
        </Form.Item>
        <Form.Item name="reminder_1_hours" label="Первое напоминание">
          <Select
            options={hourOptions}
            disabled={!remindersEnabled}
            style={{ maxWidth: 200 }}
          />
        </Form.Item>
        <Form.Item name="reminder_2_hours" label="Второе напоминание">
          <Select
            options={[{ value: null, label: "Нет" }, ...hourOptions]}
            disabled={!remindersEnabled}
            style={{ maxWidth: 200 }}
          />
        </Form.Item>
        <Form.Item
          name="address_note"
          label="Адрес/примечание (добавляется к напоминаниям)"
        >
          <Input.TextArea rows={3} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={mutation.isPending}>
          Сохранить
        </Button>
      </Form>
    </Card>
  );
}

// =============================================
// Tab 3: Payments
// =============================================

const fiscalizationLabels: Record<string, { status: "default" | "processing" | "success"; text: string }> = {
  none: { status: "default", text: "Отключена" },
  manual: { status: "processing", text: "Ручная" },
  auto: { status: "success", text: "Автоматическая" },
};

function PaymentsTab() {
  const { data, isLoading } = usePaymentSettings();
  const updatePayment = useUpdatePaymentSettings();
  const bindInn = useBindInn();
  const unbindInn = useUnbindInn();
  const setupRobokassa = useSetupRobokassa();
  const disconnectRobokassa = useDisconnectRobokassa();
  const [innInput, setInnInput] = useState("");
  const [showRobokassaForm, setShowRobokassaForm] = useState(false);
  const [robokassaForm] = Form.useForm();
  const [requisitesForm] = Form.useForm();
  const { message: messageApi } = App.useApp();

  useEffect(() => {
    if (data) {
      requisitesForm.setFieldsValue({
        card_number: data.card_number ?? "",
        sbp_phone: data.sbp_phone ?? "",
        bank_name: data.bank_name ?? "",
      });
    }
  }, [data, requisitesForm]);

  const handleSaveRequisites = useCallback(async () => {
    try {
      const values = await requisitesForm.validateFields();
      await updatePayment.mutateAsync({
        card_number: values.card_number || null,
        sbp_phone: values.sbp_phone || null,
        bank_name: values.bank_name || null,
      });
      messageApi.success("Реквизиты сохранены");
    } catch {
      messageApi.error("Ошибка сохранения");
    }
  }, [requisitesForm, updatePayment, messageApi]);

  const handleBindInn = useCallback(async () => {
    try {
      await bindInn.mutateAsync(innInput);
      messageApi.success("Авточеки подключены");
      setInnInput("");
    } catch {
      messageApi.error("Не удалось подключить авточеки");
    }
  }, [bindInn, innInput, messageApi]);

  const handleUnbindInn = useCallback(async () => {
    try {
      await unbindInn.mutateAsync();
      messageApi.success("Авточеки отключены");
    } catch {
      messageApi.error("Не удалось отключить авточеки");
    }
  }, [unbindInn, messageApi]);

  const handleSetupRobokassa = useCallback(async () => {
    try {
      const values = await robokassaForm.validateFields();
      await setupRobokassa.mutateAsync({
        merchant_login: values.merchant_login,
        password1: values.password1,
        password2: values.password2,
        is_test: values.is_test ?? false,
        hash_algorithm: values.hash_algorithm ?? "sha256",
      });
      messageApi.success("Робокасса подключена");
      setShowRobokassaForm(false);
      robokassaForm.resetFields();
    } catch {
      messageApi.error("Не удалось подключить Робокассу");
    }
  }, [robokassaForm, setupRobokassa, messageApi]);

  const handleDisconnectRobokassa = useCallback(async () => {
    try {
      await disconnectRobokassa.mutateAsync();
      messageApi.success("Робокасса отключена");
    } catch {
      messageApi.error("Не удалось отключить Робокассу");
    }
  }, [disconnectRobokassa, messageApi]);

  if (isLoading) return <Spin />;
  if (!data) return null;

  const fisc = fiscalizationLabels[data.fiscalization_level] ?? {
    status: "default" as const,
    text: data.fiscalization_level,
  };

  return (
    <>
      {/* Payment requisites */}
      <Card title="Реквизиты для оплаты" size="small" style={{ marginBottom: 24 }}>
        <Form form={requisitesForm} layout="vertical">
          <Form.Item name="card_number" label="Номер карты">
            <Input placeholder="0000 0000 0000 0000" />
          </Form.Item>
          <Form.Item name="sbp_phone" label="Телефон СБП">
            <Input placeholder="+7 900 000-00-00" />
          </Form.Item>
          <Form.Item name="bank_name" label="Банк">
            <Input placeholder="Сбербанк, Тинькофф..." />
          </Form.Item>
          <Button
            type="primary"
            onClick={handleSaveRequisites}
            loading={updatePayment.isPending}
          >
            Сохранить реквизиты
          </Button>
        </Form>
      </Card>

      {/* Robokassa */}
      <Card
        title="Робокасса"
        size="small"
        style={{ marginBottom: 24 }}
        extra={
          data.has_robokassa ? (
            <Popconfirm
              title="Отключить Робокассу?"
              description="Приём оплаты через Робокассу будет недоступен"
              onConfirm={handleDisconnectRobokassa}
            >
              <Button type="link" danger size="small" loading={disconnectRobokassa.isPending}>
                Отключить
              </Button>
            </Popconfirm>
          ) : null
        }
      >
        {data.has_robokassa ? (
          <div>
            <Badge status="success" text="Подключена" />
            {data.robokassa_is_test && (
              <Badge status="warning" text="тестовый режим" style={{ marginLeft: 12 }} />
            )}
          </div>
        ) : showRobokassaForm ? (
          <Form
            form={robokassaForm}
            layout="vertical"
            initialValues={{ is_test: false, hash_algorithm: "sha256" }}
          >
            <Form.Item
              name="merchant_login"
              label="Логин магазина"
              rules={[{ required: true, message: "Введите логин" }]}
            >
              <Input placeholder="my_shop" />
            </Form.Item>
            <Form.Item
              name="password1"
              label="Пароль #1"
              rules={[{ required: true, message: "Введите пароль #1" }]}
            >
              <Input.Password />
            </Form.Item>
            <Form.Item
              name="password2"
              label="Пароль #2"
              rules={[{ required: true, message: "Введите пароль #2" }]}
            >
              <Input.Password />
            </Form.Item>
            <Form.Item name="hash_algorithm" label="Алгоритм хеширования">
              <Radio.Group>
                <Radio value="md5">MD5</Radio>
                <Radio value="sha256">SHA-256</Radio>
                <Radio value="sha512">SHA-512</Radio>
              </Radio.Group>
            </Form.Item>
            <Form.Item name="is_test" label="Тестовый режим" valuePropName="checked">
              <Switch />
            </Form.Item>
            <div style={{ display: "flex", gap: 8 }}>
              <Button
                type="primary"
                onClick={handleSetupRobokassa}
                loading={setupRobokassa.isPending}
              >
                Подключить
              </Button>
              <Button onClick={() => { setShowRobokassaForm(false); robokassaForm.resetFields(); }}>
                Отмена
              </Button>
            </div>
          </Form>
        ) : (
          <div style={{ textAlign: "center", padding: "16px 0" }}>
            <p style={{ marginBottom: 12, color: "#888" }}>
              Подключите Робокассу для приёма онлайн-оплаты через СБП
            </p>
            <Button type="primary" onClick={() => setShowRobokassaForm(true)}>
              Подключить Робокассу
            </Button>
          </div>
        )}
      </Card>

      {/* Fiscalization & INN */}
      <Card title="Фискализация и ИНН" size="small">
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="Фискализация">
            <Badge status={fisc.status} text={fisc.text} />
          </Descriptions.Item>
          <Descriptions.Item label="Авточеки (ФНС)">
            {data.fns_connected ? (
              <>
                <Badge status="success" text="Подключены" />
                <span style={{ marginLeft: 8 }}>ИНН: {data.inn}</span>
                <Popconfirm
                  title="Отключить авточеки?"
                  description="Чеки не будут автоматически отправляться в ФНС"
                  onConfirm={handleUnbindInn}
                >
                  <Button type="link" danger size="small" style={{ marginLeft: 8 }}>
                    Отключить
                  </Button>
                </Popconfirm>
              </>
            ) : data.has_robokassa ? (
              <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <Input
                  value={innInput}
                  onChange={(e) =>
                    setInnInput(e.target.value.replace(/\D/g, "").slice(0, 12))
                  }
                  placeholder="ИНН (12 цифр)"
                  maxLength={12}
                  style={{ width: 180 }}
                />
                <Button
                  type="primary"
                  size="small"
                  onClick={handleBindInn}
                  loading={bindInn.isPending}
                  disabled={innInput.length !== 12}
                >
                  Подключить
                </Button>
              </div>
            ) : (
              <span style={{ color: "#888" }}>Сначала подключите Робокассу</span>
            )}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </>
  );
}

// =============================================
// Tab 4: Profile (from auth store)
// =============================================

function ProfileTab() {
  const profile = useAuth((s) => s.profile);
  const { data: profileSettings, isLoading } = useProfileSettings();
  const mutation = useUpdateProfileSettings();
  const [form] = Form.useForm();
  const { message: messageApi } = App.useApp();

  useEffect(() => {
    if (profileSettings) {
      form.setFieldsValue({
        name: profileSettings.name,
        username: profileSettings.username ?? "",
        specialization: profileSettings.specialization ?? "",
        city: profileSettings.city ?? "",
        instagram_url: profileSettings.instagram_url ?? "",
      });
    }
  }, [profileSettings, form]);

  const onFinish = useCallback(
    async (values: Record<string, unknown>) => {
      try {
        await mutation.mutateAsync({
          name: values.name as string,
          username: (values.username as string) || null,
          specialization: (values.specialization as string) || null,
          city: (values.city as string) || null,
          instagram_url: (values.instagram_url as string) || null,
        });
        messageApi.success("Профиль сохранён");
      } catch (e: unknown) {
        const detail = (e as { message?: string })?.message ?? "";
        if (detail.includes("409") || detail.toLowerCase().includes("already taken")) {
          messageApi.error("Это имя пользователя уже занято");
        } else {
          messageApi.error("Ошибка сохранения");
        }
      }
    },
    [mutation, messageApi],
  );

  if (isLoading || !profile) return <Spin />;

  return (
    <>
      <Card title="Публичный профиль" size="small" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item
            name="name"
            label="Имя"
            rules={[{ required: true, message: "Введите имя" }]}
          >
            <Input placeholder="Ваше имя" />
          </Form.Item>
          <Form.Item
            name="username"
            label="Имя пользователя (для ссылки)"
            tooltip="Латиница, цифры, подчёркивания. Будет использовано в ссылке: moiokoshki.ru/m/ваше_имя"
            rules={[
              {
                pattern: /^[a-zA-Z0-9_]{3,30}$/,
                message: "3-30 символов: латиница, цифры, подчёркивания",
              },
            ]}
          >
            <Input
              placeholder="your_username"
              addonBefore="moiokoshki.ru/m/"
            />
          </Form.Item>
          <Form.Item name="specialization" label="Специализация">
            <Input placeholder="Например: маникюр, наращивание ресниц" />
          </Form.Item>
          <Form.Item name="city" label="Город">
            <Input placeholder="Москва" />
          </Form.Item>
          <Form.Item name="instagram_url" label="Instagram">
            <Input placeholder="https://instagram.com/username" />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={mutation.isPending}>
            Сохранить
          </Button>
        </Form>
      </Card>
      <Card title="Аккаунт" size="small">
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="Email">
            {profile.email || "Не указан"}
          </Descriptions.Item>
          <Descriptions.Item label="Телефон">
            {profile.phone || "Не указан"}
          </Descriptions.Item>
          <Descriptions.Item label="Название бизнеса">
            {profile.business_name || "Не указано"}
          </Descriptions.Item>
          <Descriptions.Item label="Часовой пояс">
            {profile.timezone}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </>
  );
}

// =============================================
// Tab 5: Portfolio ("Мои работы")
// =============================================

const MAX_PHOTOS = 30;
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
const ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp"];

function PortfolioTab() {
  const { data: photos = [], isLoading } = usePortfolio();
  const { data: services = [] } = useServices();
  const uploadMutation = useUploadPhoto();
  const deleteMutation = useDeletePhoto();
  const updateMutation = useUpdatePhoto();
  const reorderMutation = useReorderPhotos();
  const { message: messageApi } = App.useApp();

  const sorted = [...photos].sort((a, b) => a.sort_order - b.sort_order);

  const handleMovePhoto = useCallback(
    (fromIndex: number, toIndex: number) => {
      const updated = [...sorted];
      const [moved] = updated.splice(fromIndex, 1);
      updated.splice(toIndex, 0, moved);
      const items = updated.map((p, i) => ({ id: p.id, sort_order: i }));
      reorderMutation.mutate(items);
    },
    [sorted, reorderMutation],
  );

  if (isLoading) return <Spin />;

  return (
    <Card
      title="Мои работы"
      extra={<Badge count={photos.length} showZero />}
    >
      <Upload.Dragger
        accept=".jpg,.jpeg,.png,.webp"
        beforeUpload={(file) => {
          if (!ALLOWED_TYPES.includes(file.type)) {
            messageApi.error("Допустимые форматы: JPEG, PNG, WebP");
            return false;
          }
          if (file.size > MAX_FILE_SIZE) {
            messageApi.error("Максимальный размер файла — 5 МБ");
            return false;
          }
          if (photos.length >= MAX_PHOTOS) {
            messageApi.error(`Максимум ${MAX_PHOTOS} фотографий`);
            return false;
          }
          uploadMutation.mutate(
            { file },
            {
              onSuccess: () => messageApi.success("Фото загружено"),
              onError: () => messageApi.error("Ошибка загрузки"),
            },
          );
          return false;
        }}
        showUploadList={false}
        multiple={false}
        disabled={photos.length >= MAX_PHOTOS}
      >
        <p style={{ fontSize: 16 }}>Нажмите или перетащите фото</p>
        <p className="ant-upload-hint">
          JPEG, PNG, WebP. Макс 5 МБ. Фото: {photos.length}/{MAX_PHOTOS}
        </p>
      </Upload.Dragger>

      {sorted.length > 0 && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(150px, 1fr))",
            gap: 12,
            marginTop: 16,
          }}
        >
          {sorted.map((photo, index) => (
            <Card
              key={photo.id}
              size="small"
              cover={
                <img
                  src={`/api/v1/media/${photo.thumbnail_path}`}
                  alt={photo.caption ?? "Фото работы"}
                  style={{ height: 150, objectFit: "cover" }}
                />
              }
              actions={[
                <Button
                  key="left"
                  icon={<LeftOutlined />}
                  size="small"
                  type="text"
                  disabled={index === 0}
                  onClick={() => handleMovePhoto(index, index - 1)}
                />,
                <Button
                  key="right"
                  icon={<RightOutlined />}
                  size="small"
                  type="text"
                  disabled={index === sorted.length - 1}
                  onClick={() => handleMovePhoto(index, index + 1)}
                />,
                <Popconfirm
                  key="delete"
                  title="Удалить фото?"
                  onConfirm={() => deleteMutation.mutate(photo.id)}
                >
                  <Button icon={<DeleteOutlined />} size="small" type="text" danger />
                </Popconfirm>,
              ]}
            >
              <Select
                placeholder="Тег услуги"
                allowClear
                size="small"
                style={{ width: "100%" }}
                value={photo.service_tag}
                onChange={(value) =>
                  updateMutation.mutate({ id: photo.id, service_tag: value ?? null })
                }
              >
                {services.map((s) => (
                  <Select.Option key={s.id} value={s.name}>
                    {s.name}
                  </Select.Option>
                ))}
              </Select>
            </Card>
          ))}
        </div>
      )}
    </Card>
  );
}

// =============================================
// Main Settings Page
// =============================================

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState("my-page");

  return (
    <Tabs
      activeKey={activeTab}
      onChange={setActiveTab}
      tabPosition="left"
      items={[
        { key: "my-page", label: "Моя страница", children: <MyPageTab onSwitchTab={setActiveTab} /> },
        { key: "schedule", label: "Расписание", children: <ScheduleTab /> },
        { key: "notifications", label: "Уведомления", children: <NotificationsTab /> },
        { key: "payments", label: "Платежи", children: <PaymentsTab /> },
        { key: "profile", label: "Профиль", children: <ProfileTab /> },
        { key: "portfolio", label: "Мои работы", children: <PortfolioTab /> },
      ]}
    />
  );
}

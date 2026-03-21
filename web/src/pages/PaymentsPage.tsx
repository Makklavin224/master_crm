import { useState, useCallback } from "react";
import {
  Button,
  Card,
  DatePicker,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
} from "antd";
import { DownloadOutlined } from "@ant-design/icons";
import dayjs, { type Dayjs } from "dayjs";
import { usePayments, exportPaymentsCsv, type PaymentRead } from "../api/payments";
import { PaymentStatusTag } from "../components/StatusTag";
import type { ColumnsType } from "antd/es/table";

const { RangePicker } = DatePicker;

const statusOptions = [
  { value: "pending", label: "Ожидание" },
  { value: "paid", label: "Оплачен" },
  { value: "cancelled", label: "Отменён" },
  { value: "refunded", label: "Возврат" },
];

const paymentMethodLabels: Record<string, string> = {
  cash: "Наличные",
  card_to_card: "Перевод на карту",
  transfer: "Перевод",
  sbp: "СБП",
  sbp_robokassa: "СБП (Robokassa)",
};

const receiptStatusMap: Record<string, { color: string; label: string }> = {
  not_applicable: { color: "default", label: "Не требуется" },
  pending: { color: "gold", label: "Ожидание" },
  issued: { color: "green", label: "Выдан" },
  failed: { color: "red", label: "Ошибка" },
  cancelled: { color: "default", label: "Отменён" },
};

const PAGE_SIZE = 20;

const paymentMethodOptions = [
  { value: "cash", label: "Наличные" },
  { value: "card_to_card", label: "Перевод на карту" },
  { value: "sbp", label: "СБП" },
  { value: "sbp_robokassa", label: "СБП (Robokassa)" },
];

export function PaymentsPage() {
  const [status, setStatus] = useState<string | undefined>();
  const [paymentMethod, setPaymentMethod] = useState<string | undefined>();
  const [dateRange, setDateRange] = useState<
    [Dayjs | null, Dayjs | null] | null
  >(null);
  const [page, setPage] = useState(1);
  const [exporting, setExporting] = useState(false);

  const filters = {
    status,
    payment_method: paymentMethod,
    date_from: dateRange?.[0]?.format("YYYY-MM-DD"),
    date_to: dateRange?.[1]?.format("YYYY-MM-DD"),
    limit: PAGE_SIZE,
    offset: (page - 1) * PAGE_SIZE,
  };

  const { data, isLoading } = usePayments(filters);

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const columns: ColumnsType<PaymentRead> = [
    {
      title: "Дата",
      dataIndex: "created_at",
      render: (val: string) => dayjs(val).format("DD.MM.YYYY HH:mm"),
      sorter: (a, b) => a.created_at.localeCompare(b.created_at),
      defaultSortOrder: "descend",
    },
    {
      title: "Клиент",
      dataIndex: "client_name",
      render: (val: string | null) => val ?? "-",
    },
    {
      title: "Услуга",
      dataIndex: "service_name",
      render: (val: string | null) => val ?? "-",
    },
    {
      title: "Сумма",
      dataIndex: "amount",
      render: (amount: number) =>
        `${(amount / 100).toLocaleString("ru-RU")} руб`,
      sorter: (a, b) => a.amount - b.amount,
    },
    {
      title: "Способ оплаты",
      dataIndex: "payment_method",
      render: (val: string | null) =>
        val ? (paymentMethodLabels[val] ?? val) : "-",
    },
    {
      title: "Статус",
      dataIndex: "status",
      render: (s: string) => <PaymentStatusTag status={s} />,
    },
    {
      title: "Чек",
      dataIndex: "receipt_status",
      render: (s: string) => {
        const info = receiptStatusMap[s] ?? { color: "default", label: s };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
  ];

  return (
    <Card title="Платежи">
      <Space style={{ marginBottom: 16 }} wrap>
        <RangePicker
          format="DD.MM.YYYY"
          onChange={(dates) => {
            setDateRange(dates as [Dayjs | null, Dayjs | null] | null);
            setPage(1);
          }}
          placeholder={["Дата от", "Дата до"]}
        />
        <Select
          placeholder="Статус"
          allowClear
          options={statusOptions}
          value={status}
          onChange={(val) => {
            setStatus(val);
            setPage(1);
          }}
          style={{ minWidth: 150 }}
        />
        <Select
          placeholder="Способ оплаты"
          allowClear
          options={paymentMethodOptions}
          value={paymentMethod}
          onChange={(val) => {
            setPaymentMethod(val);
            setPage(1);
          }}
          style={{ minWidth: 180 }}
        />
        {data && (
          <>
            <Statistic
              title="Платежей"
              value={data.total}
              style={{ marginLeft: 16 }}
            />
            <Statistic
              title="Выручка"
              value={(data.total_revenue || 0) / 100}
              suffix="₽"
              precision={0}
              formatter={(val) => Number(val).toLocaleString("ru-RU")}
              style={{ marginLeft: 16 }}
            />
          </>
        )}
        <Button
          icon={<DownloadOutlined />}
          loading={exporting}
          onClick={async () => {
            setExporting(true);
            try {
              await exportPaymentsCsv({
                status,
                payment_method: paymentMethod,
                date_from: dateRange?.[0]?.format("YYYY-MM-DD"),
                date_to: dateRange?.[1]?.format("YYYY-MM-DD"),
              });
            } finally {
              setExporting(false);
            }
          }}
          style={{ marginLeft: 16 }}
        >
          Экспорт CSV
        </Button>
      </Space>
      <Table<PaymentRead>
        columns={columns}
        dataSource={data?.items}
        loading={isLoading}
        rowKey="id"
        pagination={{
          current: page,
          pageSize: PAGE_SIZE,
          total: data?.total ?? 0,
          onChange: handlePageChange,
          showSizeChanger: false,
        }}
      />
    </Card>
  );
}

import { useParams, useNavigate } from "react-router-dom";
import { Button, Card, Descriptions, Empty, Spin, Table, Alert } from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import dayjs from "dayjs";
import { useClientDetail, type BookingRead } from "../api/clients";
import { BookingStatusTag } from "../components/StatusTag";
import type { ColumnsType } from "antd/es/table";

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, error } = useClientDetail(id ?? "");

  if (isLoading) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <Alert
        type="error"
        message="Ошибка загрузки"
        description="Не удалось загрузить данные клиента"
        style={{ margin: 24 }}
      />
    );
  }

  const { client, bookings, visit_count } = data;

  const columns: ColumnsType<BookingRead> = [
    {
      title: "Дата",
      dataIndex: "starts_at",
      render: (val: string) => dayjs(val).format("DD.MM.YYYY HH:mm"),
      sorter: (a, b) => a.starts_at.localeCompare(b.starts_at),
      defaultSortOrder: "descend",
    },
    {
      title: "Услуга",
      dataIndex: "service_name",
      render: (val: string | null) => val ?? "-",
    },
    {
      title: "Статус",
      dataIndex: "status",
      render: (status: string) => <BookingStatusTag status={status} />,
    },
    {
      title: "Длительность",
      render: (_: unknown, record: BookingRead) => {
        const start = dayjs(record.starts_at);
        const end = dayjs(record.ends_at);
        const mins = end.diff(start, "minute");
        return `${mins} мин`;
      },
    },
  ];

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        type="link"
        onClick={() => navigate("/clients")}
        style={{ marginBottom: 16, paddingLeft: 0 }}
      >
        Назад к клиентам
      </Button>

      <Descriptions bordered column={2} style={{ marginBottom: 24 }}>
        <Descriptions.Item label="Имя">{client.name}</Descriptions.Item>
        <Descriptions.Item label="Телефон">
          <span style={{ userSelect: "all" }}>{client.phone}</span>
        </Descriptions.Item>
        <Descriptions.Item label="Всего визитов">
          {visit_count}
        </Descriptions.Item>
        <Descriptions.Item label="В базе с">
          {dayjs(client.created_at).format("DD.MM.YYYY")}
        </Descriptions.Item>
      </Descriptions>

      <Card title="История визитов">
        <Table<BookingRead>
          columns={columns}
          dataSource={bookings}
          rowKey="id"
          locale={{ emptyText: <Empty description="Нет визитов" /> }}
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  );
}

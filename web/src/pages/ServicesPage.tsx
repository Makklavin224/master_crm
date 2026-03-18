import { useState } from "react";
import { Card, Table, Button, Tag, Badge, Space, Popconfirm, Empty, App } from "antd";
import { PlusOutlined, EditOutlined, DeleteOutlined } from "@ant-design/icons";
import type { ColumnsType } from "antd/es/table";
import { useServices, useDeleteService, type ServiceRead } from "../api/services";
import { ServiceModal } from "../components/ServiceModal";

export function ServicesPage() {
  const { data: services, isLoading } = useServices();
  const deleteMutation = useDeleteService();
  const { message: messageApi } = App.useApp();

  const [modalOpen, setModalOpen] = useState(false);
  const [editingService, setEditingService] = useState<ServiceRead | null>(null);

  const handleAdd = () => {
    setEditingService(null);
    setModalOpen(true);
  };

  const handleEdit = (record: ServiceRead) => {
    setEditingService(record);
    setModalOpen(true);
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id, {
      onSuccess: () => {
        messageApi.success("Услуга удалена");
      },
      onError: () => {
        messageApi.error("Не удалось удалить услугу");
      },
    });
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setEditingService(null);
  };

  const columns: ColumnsType<ServiceRead> = [
    {
      title: "Название",
      dataIndex: "name",
      key: "name",
      sorter: (a, b) => a.name.localeCompare(b.name),
    },
    {
      title: "Длительность",
      dataIndex: "duration_minutes",
      key: "duration_minutes",
      render: (minutes: number) => `${minutes} мин`,
      width: 140,
      sorter: (a, b) => a.duration_minutes - b.duration_minutes,
    },
    {
      title: "Цена",
      dataIndex: "price",
      key: "price",
      render: (price: number) =>
        `${(price / 100).toLocaleString("ru-RU")} руб`,
      width: 140,
      sorter: (a, b) => a.price - b.price,
    },
    {
      title: "Категория",
      dataIndex: "category",
      key: "category",
      render: (category: string | null) =>
        category ? <Tag>{category}</Tag> : "—",
      width: 160,
    },
    {
      title: "Статус",
      dataIndex: "is_active",
      key: "is_active",
      render: (active: boolean) => (
        <Badge
          status={active ? "success" : "error"}
          text={active ? "Активна" : "Неактивна"}
        />
      ),
      width: 130,
    },
    {
      title: "Действия",
      key: "actions",
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Удалить услугу?"
            description="Это действие нельзя отменить"
            onConfirm={() => handleDelete(record.id)}
            okText="Удалить"
            cancelText="Нет"
            okButtonProps={{ danger: true }}
          >
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <>
      <Card
        title="Услуги"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleAdd}
          >
            Добавить
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={services || []}
          rowKey="id"
          loading={isLoading}
          locale={{
            emptyText: (
              <Empty description="Нет услуг" />
            ),
          }}
          pagination={{
            pageSize: 20,
            showSizeChanger: false,
            hideOnSinglePage: true,
          }}
        />
      </Card>

      <ServiceModal
        open={modalOpen}
        onClose={handleModalClose}
        service={editingService}
      />
    </>
  );
}

import { useState, useMemo } from "react";
import { Card, Empty, Input, Table } from "antd";
import { SearchOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import dayjs from "dayjs";
import { useClients, type MasterClientRead } from "../api/clients";
import type { ColumnsType } from "antd/es/table";

export function ClientsPage() {
  const { data, isLoading } = useClients();
  const [search, setSearch] = useState("");
  const navigate = useNavigate();

  const filtered = useMemo(() => {
    if (!data) return [];
    if (!search.trim()) return data;
    const q = search.trim().toLowerCase();
    return data.filter(
      (r) =>
        r.client.name.toLowerCase().includes(q) ||
        r.client.phone.includes(q),
    );
  }, [data, search]);

  const columns: ColumnsType<MasterClientRead> = [
    {
      title: "Имя",
      dataIndex: ["client", "name"],
      sorter: (a, b) => a.client.name.localeCompare(b.client.name),
    },
    {
      title: "Телефон",
      dataIndex: ["client", "phone"],
    },
    {
      title: "Визиты",
      dataIndex: "visit_count",
      sorter: (a, b) => a.visit_count - b.visit_count,
    },
    {
      title: "Первый визит",
      dataIndex: "first_visit_at",
      render: (val: string | null) =>
        val ? dayjs(val).format("DD.MM.YYYY") : "-",
      sorter: (a, b) =>
        (a.first_visit_at ?? "").localeCompare(b.first_visit_at ?? ""),
    },
    {
      title: "Последний визит",
      dataIndex: "last_visit_at",
      render: (val: string | null) =>
        val ? dayjs(val).format("DD.MM.YYYY") : "-",
      sorter: (a, b) =>
        (a.last_visit_at ?? "").localeCompare(b.last_visit_at ?? ""),
    },
  ];

  return (
    <Card title={<>Клиенты {data && <span style={{ color: "#999", fontWeight: 400 }}>({filtered.length})</span>}</>}>
      <Input
        prefix={<SearchOutlined />}
        placeholder="Поиск по имени или телефону"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        allowClear
        style={{ maxWidth: 400, marginBottom: 16 }}
      />
      <Table<MasterClientRead>
        columns={columns}
        dataSource={filtered}
        loading={isLoading}
        rowKey={(r) => r.client.id}
        locale={{ emptyText: <Empty description="Нет клиентов" /> }}
        pagination={{
          pageSize: 20,
          showTotal: (total) => `Всего: ${total}`,
          showSizeChanger: false,
        }}
        onRow={(record) => ({
          onClick: () => navigate(`/clients/${record.client.id}`),
          style: { cursor: "pointer" },
        })}
      />
    </Card>
  );
}

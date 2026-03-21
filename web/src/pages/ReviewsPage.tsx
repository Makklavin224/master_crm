import { useState, useCallback } from "react";
import {
  Button,
  Card,
  Empty,
  Input,
  Modal,
  Rate,
  Segmented,
  Table,
  Tag,
  Tooltip,
  Typography,
  App,
} from "antd";
import dayjs from "dayjs";
import {
  useReviews,
  useReplyToReview,
  type ReviewAdminRead,
} from "../api/reviews";
import type { ColumnsType } from "antd/es/table";

const { TextArea } = Input;
const { Text } = Typography;

const PAGE_SIZE = 20;

const statusOptions = [
  { value: "all", label: "Все" },
  { value: "published", label: "Опубликованные" },
  { value: "pending_reply", label: "Ожидают ответа" },
];

const statusTagMap: Record<string, { color: string; label: string }> = {
  published: { color: "green", label: "Опубликован" },
  pending_reply: { color: "orange", label: "Ожидает ответа" },
};

export function ReviewsPage() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [replyModal, setReplyModal] = useState<ReviewAdminRead | null>(null);
  const [replyText, setReplyText] = useState("");

  const { message } = App.useApp();

  const { data, isLoading } = useReviews({
    status: statusFilter,
    page,
    page_size: PAGE_SIZE,
  });

  const replyMutation = useReplyToReview();

  const handlePageChange = useCallback((newPage: number) => {
    setPage(newPage);
  }, []);

  const openReplyModal = useCallback((review: ReviewAdminRead) => {
    setReplyModal(review);
    setReplyText(review.master_reply || "");
  }, []);

  const handleReply = useCallback(async () => {
    if (!replyModal || !replyText.trim()) return;
    try {
      await replyMutation.mutateAsync({
        reviewId: replyModal.id,
        reply_text: replyText.trim(),
      });
      message.success("Ответ отправлен");
      setReplyModal(null);
      setReplyText("");
    } catch {
      message.error("Не удалось отправить ответ");
    }
  }, [replyModal, replyText, replyMutation, message]);

  const columns: ColumnsType<ReviewAdminRead> = [
    {
      title: "Дата",
      dataIndex: "created_at",
      width: 120,
      render: (val: string) => dayjs(val).format("DD.MM.YYYY"),
      sorter: (a, b) => a.created_at.localeCompare(b.created_at),
      defaultSortOrder: "descend",
    },
    {
      title: "Клиент",
      dataIndex: "client_name",
      width: 160,
      render: (val: string) => val || "-",
    },
    {
      title: "Услуга",
      dataIndex: "service_name",
      width: 160,
      render: (val: string) => val || "-",
    },
    {
      title: "Оценка",
      dataIndex: "rating",
      width: 150,
      render: (val: number) => <Rate disabled value={val} count={5} />,
      sorter: (a, b) => a.rating - b.rating,
    },
    {
      title: "Текст",
      dataIndex: "text",
      ellipsis: true,
      render: (val: string | null) =>
        val ? (
          val.length > 100 ? (
            <Tooltip title={val}>
              <span>{val.slice(0, 100)}...</span>
            </Tooltip>
          ) : (
            val
          )
        ) : (
          <Text type="secondary">-</Text>
        ),
    },
    {
      title: "Статус",
      dataIndex: "status",
      width: 150,
      render: (s: string) => {
        const info = statusTagMap[s] ?? { color: "default", label: s };
        return <Tag color={info.color}>{info.label}</Tag>;
      },
    },
    {
      title: "Действия",
      width: 130,
      render: (_: unknown, record: ReviewAdminRead) => {
        const canReply =
          record.status === "pending_reply" ||
          (record.status === "published" && !record.master_reply);
        return canReply ? (
          <Button type="link" onClick={() => openReplyModal(record)}>
            Ответить
          </Button>
        ) : record.master_reply ? (
          <Tooltip title={record.master_reply}>
            <Text type="secondary" style={{ cursor: "pointer" }}>
              Ответ дан
            </Text>
          </Tooltip>
        ) : null;
      },
    },
  ];

  return (
    <Card title="Отзывы">
      <div style={{ marginBottom: 16 }}>
        <Segmented
          options={statusOptions}
          value={statusFilter}
          onChange={(val) => {
            setStatusFilter(val as string);
            setPage(1);
          }}
        />
      </div>
      <Table<ReviewAdminRead>
        columns={columns}
        dataSource={data?.reviews}
        loading={isLoading}
        rowKey="id"
        locale={{ emptyText: <Empty description="Пока нет отзывов" /> }}
        pagination={{
          current: page,
          pageSize: PAGE_SIZE,
          total: data?.total ?? 0,
          onChange: handlePageChange,
          showSizeChanger: false,
          showTotal: (total) => `Всего: ${total}`,
        }}
      />

      <Modal
        title="Ответить на отзыв"
        open={!!replyModal}
        onCancel={() => {
          setReplyModal(null);
          setReplyText("");
        }}
        onOk={handleReply}
        okText="Отправить ответ"
        cancelText="Отмена"
        confirmLoading={replyMutation.isPending}
        okButtonProps={{ disabled: !replyText.trim() }}
      >
        {replyModal && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ marginBottom: 8 }}>
              <Text strong>{replyModal.client_name}</Text>
            </div>
            <div style={{ marginBottom: 8 }}>
              <Rate disabled value={replyModal.rating} count={5} />
            </div>
            {replyModal.text && (
              <div
                style={{
                  padding: 12,
                  borderRadius: 8,
                  marginBottom: 16,
                  background: "rgba(0, 0, 0, 0.04)",
                }}
              >
                <Text>{replyModal.text}</Text>
              </div>
            )}
            <TextArea
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              maxLength={500}
              rows={4}
              placeholder="Ваш ответ клиенту..."
              showCount
            />
          </div>
        )}
      </Modal>
    </Card>
  );
}

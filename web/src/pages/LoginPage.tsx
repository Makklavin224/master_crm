import { useState, useEffect, useRef, useCallback } from "react";
import { Card, Typography, Tabs, Form, Input, Button, Alert, Spin, Space } from "antd";
import { MailOutlined, LockOutlined, QrcodeOutlined, LinkOutlined } from "@ant-design/icons";
import { QRCodeSVG } from "qrcode.react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../stores/auth";

const { Title, Text, Paragraph } = Typography;

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

/* ---------- Tab 1: Email Login ---------- */

function EmailTab() {
  const loginEmail = useAuth((s) => s.loginEmail);
  const isLoading = useAuth((s) => s.isLoading);
  const error = useAuth((s) => s.error);
  const navigate = useNavigate();
  const [form] = Form.useForm();

  const handleSubmit = async (values: { email: string; password: string }) => {
    const ok = await loginEmail(values.email, values.password);
    if (ok) {
      navigate("/calendar", { replace: true });
    }
  };

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      {error && (
        <Alert
          message={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      <Form.Item
        name="email"
        rules={[
          { required: true, message: "Введите email" },
          { type: "email", message: "Некорректный email" },
        ]}
      >
        <Input
          prefix={<MailOutlined />}
          placeholder="Email"
          size="large"
          autoComplete="email"
        />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[{ required: true, message: "Введите пароль" }]}
      >
        <Input.Password
          prefix={<LockOutlined />}
          placeholder="Пароль"
          size="large"
          autoComplete="current-password"
        />
      </Form.Item>
      <Form.Item>
        <Button
          type="primary"
          htmlType="submit"
          size="large"
          block
          loading={isLoading}
        >
          Войти
        </Button>
      </Form.Item>
    </Form>
  );
}

/* ---------- Tab 2: QR Code Login ---------- */

interface QrState {
  sessionId: string | null;
  qrPayload: string | null;
  status: "idle" | "loading" | "pending" | "confirmed" | "expired" | "error";
  error: string | null;
}

function QrTab() {
  const setToken = useAuth((s) => s.setToken);
  const navigate = useNavigate();
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [qr, setQr] = useState<QrState>({
    sessionId: null,
    qrPayload: null,
    status: "idle",
    error: null,
  });

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }, []);

  const initQr = useCallback(async () => {
    stopPolling();
    setQr({ sessionId: null, qrPayload: null, status: "loading", error: null });
    try {
      const res = await fetch(`${API_BASE}/auth/qr/init`, { method: "POST" });
      if (!res.ok) throw new Error("Не удалось создать QR-сессию");
      const data = await res.json();
      setQr({
        sessionId: data.session_id,
        qrPayload: data.qr_payload,
        status: "pending",
        error: null,
      });
    } catch {
      setQr((prev) => ({ ...prev, status: "error", error: "Не удалось создать QR-код" }));
    }
  }, [stopPolling]);

  // Poll for QR status
  useEffect(() => {
    if (qr.status !== "pending" || !qr.sessionId) return;

    pollRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/qr/status/${qr.sessionId}`);
        if (!res.ok) return;
        const data = await res.json();

        if (data.status === "confirmed" && data.access_token) {
          stopPolling();
          setToken(data.access_token);
          navigate("/calendar", { replace: true });
        } else if (data.status === "expired") {
          stopPolling();
          setQr((prev) => ({ ...prev, status: "expired" }));
        }
      } catch {
        // Silently retry on next interval
      }
    }, 3000);

    return stopPolling;
  }, [qr.status, qr.sessionId, stopPolling, setToken, navigate]);

  // Auto-init on mount
  useEffect(() => {
    initQr();
    return stopPolling;
  }, [initQr, stopPolling]);

  return (
    <div style={{ textAlign: "center", padding: "16px 0" }}>
      {qr.status === "loading" && <Spin size="large" />}

      {qr.status === "pending" && qr.qrPayload && (
        <Space direction="vertical" size="middle" align="center">
          <QRCodeSVG value={qr.qrPayload} size={200} />
          <Text type="secondary">
            Отсканируйте QR-код камерой Telegram
          </Text>
          <Spin size="small" />
          <Text type="secondary" style={{ fontSize: 12 }}>
            Ожидание подтверждения...
          </Text>
        </Space>
      )}

      {qr.status === "expired" && (
        <Space direction="vertical" size="middle" align="center">
          <Text type="danger">QR-код истёк</Text>
          <Button onClick={initQr}>Сгенерировать новый</Button>
        </Space>
      )}

      {qr.status === "error" && (
        <Space direction="vertical" size="middle" align="center">
          <Alert message={qr.error} type="error" showIcon />
          <Button onClick={initQr}>Повторить</Button>
        </Space>
      )}
    </div>
  );
}

/* ---------- Tab 3: Magic Link ---------- */

function MagicLinkTab() {
  return (
    <div style={{ padding: "16px 0" }}>
      <Paragraph>
        <Text strong>Как войти через Telegram:</Text>
      </Paragraph>
      <ol style={{ paddingLeft: 20 }}>
        <li>
          <Paragraph>
            Откройте <Text code>@MasterCRMBot</Text> в Telegram
          </Paragraph>
        </li>
        <li>
          <Paragraph>
            Отправьте команду <Text code>/login</Text>
          </Paragraph>
        </li>
        <li>
          <Paragraph>
            Нажмите на ссылку, которую пришлёт бот
          </Paragraph>
        </li>
      </ol>
      <Alert
        message="Вы будете автоматически авторизованы при переходе по ссылке"
        type="info"
        showIcon
        style={{ marginTop: 16 }}
      />
    </div>
  );
}

/* ---------- Login Page ---------- */

export function LoginPage() {
  const isAuthenticated = useAuth((s) => s.isAuthenticated);
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/calendar", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const tabItems = [
    {
      key: "email",
      label: (
        <span>
          <MailOutlined /> Email
        </span>
      ),
      children: <EmailTab />,
    },
    {
      key: "qr",
      label: (
        <span>
          <QrcodeOutlined /> QR-код
        </span>
      ),
      children: <QrTab />,
    },
    {
      key: "magic",
      label: (
        <span>
          <LinkOutlined /> Magic link
        </span>
      ),
      children: <MagicLinkTab />,
    },
  ];

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#f5f5f5",
      }}
    >
      <Card style={{ width: 420 }}>
        <Title
          level={3}
          style={{ textAlign: "center", color: "#6C5CE7", marginBottom: 24 }}
        >
          MasterCRM
        </Title>
        <Tabs items={tabItems} centered />
      </Card>
    </div>
  );
}

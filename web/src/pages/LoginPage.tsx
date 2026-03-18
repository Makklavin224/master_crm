import { Card, Typography } from "antd";

const { Title } = Typography;

export function LoginPage() {
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
        <Title level={3} style={{ textAlign: "center", color: "#6C5CE7" }}>
          MasterCRM
        </Title>
        <p style={{ textAlign: "center" }}>Login page placeholder - will be fully implemented in Task 2</p>
      </Card>
    </div>
  );
}

import { Layout, Menu, Button, Switch } from "antd";
import {
  CalendarOutlined,
  TeamOutlined,
  AppstoreOutlined,
  DollarOutlined,
  SettingOutlined,
  LogoutOutlined,
  BulbOutlined,
} from "@ant-design/icons";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../stores/auth";
import { useThemeStore } from "../stores/theme";

const { Sider, Content, Header } = Layout;

const menuItems = [
  { key: "/calendar", icon: <CalendarOutlined />, label: "\u041a\u0430\u043b\u0435\u043d\u0434\u0430\u0440\u044c" },
  { key: "/clients", icon: <TeamOutlined />, label: "\u041a\u043b\u0438\u0435\u043d\u0442\u044b" },
  { key: "/services", icon: <AppstoreOutlined />, label: "\u0423\u0441\u043b\u0443\u0433\u0438" },
  { key: "/payments", icon: <DollarOutlined />, label: "\u041f\u043b\u0430\u0442\u0435\u0436\u0438" },
  { key: "/settings", icon: <SettingOutlined />, label: "\u041d\u0430\u0441\u0442\u0440\u043e\u0439\u043a\u0438" },
];

export function AdminLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const logout = useAuth((s) => s.logout);
  const { isDark, toggle } = useThemeStore();

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        breakpoint="lg"
        theme={isDark ? "dark" : "light"}
      >
        <div
          style={{
            padding: 16,
            textAlign: "center",
            fontWeight: 700,
            fontSize: collapsed ? 20 : 16,
            color: isDark ? "#fff" : "#6C5CE7",
          }}
        >
          {collapsed ? "M" : "MasterCRM"}
        </div>
        <Menu
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          theme={isDark ? "dark" : "light"}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: "0 24px",
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
            gap: 16,
            background: isDark ? "#141414" : "#fff",
          }}
        >
          <Switch
            checked={isDark}
            onChange={toggle}
            checkedChildren={<BulbOutlined />}
            unCheckedChildren={<BulbOutlined />}
          />
          <Button type="text" icon={<LogoutOutlined />} onClick={logout} />
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
